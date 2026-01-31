# SPEC PACK — L2-auth-tenants-rbac-rls-base

## 1) Context & Goal
IA-CRM v2 needs a security foundation that makes multi-tenant isolation *non-optional* and *database-enforced* before any business entities ship.

**Goal:** Implement the baseline security architecture:
- Multi-tenant identity (users + tenant memberships)
- Role-based access control (RBAC) via role → permission mapping
- Postgres Row-Level Security (RLS) with `FORCE ROW LEVEL SECURITY` as the backstop against cross-tenant access
- Minimal UI flows for login + tenant selection, plus “security admin” CRUD (members, roles) and read-only audit log

This lot must stay within ~1–3 days and establish the “tenant + RLS + RBAC + audit” pattern that every future business table and endpoint must follow.

## 2) In-scope / Out-of-scope
**In scope**
- DB schema + Alembic migrations for:
  - `tenants`, `users`, `memberships`
  - `roles`, `permissions`, `role_permissions`
  - `audit_log` (tenant-scoped; used for security mutations in this lot and as the baseline for future lots)
- Postgres functions/triggers to support safe bootstrapping and idempotent seeds.
- Postgres RLS:
  - `ENABLE` + `FORCE` RLS on all tenant-scoped business tables introduced in this lot
  - Session context variables `app.user_id` and `app.tenant_id` set per-request/transaction with `SET LOCAL`
  - Policies that prevent cross-tenant access even if application-layer checks fail
- Backend (FastAPI):
  - Auth: guarded bootstrap (dev/early-stage only), login, current user (`/auth/me`)
  - Tenant discovery (list the tenants the user belongs to)
  - Tenant-scoped RBAC enforcement via permission checks on every tenant-scoped route
  - Request-scoped DB context that sets `app.user_id` + `app.tenant_id` appropriately before any tenant-scoped queries
  - Audit logging for security mutations (members/roles)
  - Automated “anti-leak” tests demonstrating RLS isolation between two tenants
- Frontend (React):
  - Login page + tenant selection page
  - Members / Roles / Audit pages with standard list UX (loading/empty/error, search, sort, pagination)

**Out of scope**
- SSO/OAuth, magic links, MFA, password reset emails
- Invitation flows (email sending); acceptable approach for now is “create user with password”
- Fine-grained, DB-level authorization beyond tenant isolation (RLS focuses on tenant boundary; RBAC is enforced at the API layer)
- Any non-security business entities (contacts, accounts, deals, etc.)

## 3) Data model (tables, columns, indexes, RLS policies, migrations strategy)
### 3.1 Conventions
- Primary keys: `uuid` via `gen_random_uuid()`.
- Email uniqueness: `citext` (case-insensitive).
- Tenant-scoped tables include `tenant_id uuid not null`.
- Timestamps:
  - Tenant-scoped tables include `created_at` and `updated_at` (`timestamptz not null default now()`).
- DB context variables (per transaction):
  - `set_config('app.user_id', '<uuid>', true)`
  - `set_config('app.tenant_id', '<uuid>', true)` (only for tenant-scoped routes; do not set it for login/tenant discovery unless needed)

### 3.2 Required Postgres extensions
- `pgcrypto` (for `gen_random_uuid()`)
- `citext`

### 3.3 Tables (minimum)
#### `tenants`
- Columns: `id`, `name`, `slug`, `created_at`, `updated_at`
- Constraints/indexes:
  - unique: `slug`
- RLS:
  - `FORCE` RLS enabled.
  - Select allowed only if the current user is a member of that tenant.

#### `users` (global)
- Columns: `id`, `email citext unique`, `password_hash`, `is_active`, `created_at`, `updated_at`
- RLS:
  - `FORCE` RLS enabled.
  - User can select/update only their own row.
  - Tenant member listing should not require returning arbitrary `users` rows; use a helper function to fetch member emails safely (see functions section).

#### `memberships` (tenant-scoped)
- Columns: `id`, `tenant_id`, `user_id`, `role_id`, `created_at`, `updated_at`
- Constraints/indexes:
  - unique: `(tenant_id, user_id)`
  - index: `(tenant_id, role_id)`
  - index: `(user_id)`
- RLS:
  - `FORCE` RLS enabled.
  - Allow reading *own memberships across tenants* (supports login + tenant discovery without `app.tenant_id`).
  - Allow tenant admin reads/writes only inside `app.tenant_id` and only if the user is a member of that tenant.

#### `roles` (tenant-scoped)
- Columns: `id`, `tenant_id`, `name`, `is_system`, `created_at`, `updated_at`
- Constraints/indexes:
  - unique: `(tenant_id, name)`
- RLS:
  - `FORCE` RLS enabled.
  - Select allowed for tenants the current user is a member of (even without `app.tenant_id`), but inserts/updates/deletes require the current tenant context (`app.tenant_id`) and membership in that tenant.

#### `permissions` (global)
- Columns: `code` (pk), `description`
- Seeded codes (minimum for this lot):
  - `tenants:read`
  - `members:read`, `members:write`
  - `roles:read`, `roles:write`
  - `audit:read`
- RLS:
  - Acceptable in this lot to keep `permissions` without RLS (read-only list exposed via API).

#### `role_permissions` (tenant-scoped via denormalized `tenant_id`)
- Columns: `role_id`, `permission_code`, `tenant_id`, `created_at`, `updated_at`
- Keys/indexes:
  - primary key: `(role_id, permission_code)`
  - index: `(tenant_id, role_id)`
- Integrity:
  - `tenant_id` must always match the referenced role’s `tenant_id`; enforce via trigger (preferred) so application code can’t create inconsistent rows.
- RLS:
  - `FORCE` RLS enabled; tenant access is constrained by both `app.tenant_id` and membership.

#### `audit_log` (tenant-scoped)
- Columns:
  - `id`, `tenant_id`, `actor_user_id`
  - `action`, `entity_type`, `entity_id`
  - `before jsonb`, `after jsonb`
  - `created_at`
- Indexes:
  - `(tenant_id, created_at desc, id desc)` (keyset pagination)
  - `(tenant_id, entity_type, entity_id)`
- RLS:
  - `FORCE` RLS enabled; tenant access is constrained by both `app.tenant_id` and membership.

### 3.4 RLS helper functions / triggers (required)
Session helpers (SQL, `STABLE`):
- `app_current_user_id() returns uuid` from `current_setting('app.user_id', true)`
- `app_current_tenant_id() returns uuid` from `current_setting('app.tenant_id', true)`

Membership / identity helpers (must be `SECURITY DEFINER`, `SET search_path = public`):
- `app_is_member(tenant_id uuid, user_id uuid) returns boolean`
- `app_user_email(user_id uuid) returns text` (used for member lists and audit actor display without widening `users` access)
- `app_users_count() returns int` (used for bootstrap guard)
- `app_get_user_for_login(email citext) returns (id, email, password_hash, is_active)` (login needs to bypass strict `users` RLS)
- `app_upsert_user(email citext, password_hash text) returns uuid` (create-if-missing user by email; idempotent)

Seed / integrity helpers (plpgsql, `SECURITY DEFINER`, `SET search_path = public`):
- `app_role_permissions_set_tenant_id()` trigger function:
  - before insert/update on `role_permissions`, set `NEW.tenant_id` from `roles.tenant_id` for `NEW.role_id`
- `app_seed_system_roles(tenant_id uuid) returns void`:
  - ensure `Owner`, `Admin`, `Member` roles exist for the tenant
  - seed role permissions:
    - Owner/Admin get all permission codes
    - Member gets `tenants:read` (and nothing else)
- `app_on_tenant_created()` trigger function:
  - after insert on `tenants`, call `app_seed_system_roles(new.id)`
- `app_bootstrap(tenant_name, tenant_slug, email, password_hash) returns (user_id, tenant_id)`:
  - creates tenant, seeds roles, upserts user, creates membership as Owner

### 3.5 RLS policies (required baseline)
**Non-negotiable:** For all tenant-scoped tables in this lot: `ENABLE` + `FORCE` RLS.

Policies must satisfy:
- Missing `app.user_id` must not allow reads/writes.
- Missing `app.tenant_id` must not allow tenant-scoped *writes*, and must not allow tenant-scoped reads other than “self discovery” paths required for login (e.g., memberships for the current user).
- Even if the app sets `app.tenant_id` incorrectly, the DB must not allow access unless the user is a member of that tenant.

Concrete minimum policy behavior (names can vary):
- `tenants`: `SELECT` allowed if `app_is_member(tenants.id, app_current_user_id())`.
- `users`: allow `SELECT`/`UPDATE` only for `users.id = app_current_user_id()`.
- `memberships`: allow `SELECT` when `memberships.user_id = app_current_user_id()` OR when within current tenant context + membership.
- `roles`: allow `SELECT` for tenants where user is a member; require current tenant context + membership for `INSERT/UPDATE/DELETE`.
- `role_permissions`, `audit_log`: require current tenant context + membership for all actions.

### 3.6 Migrations strategy
- Use Alembic.
- Ship separate migrations for:
  1) schema + extensions + indexes
  2) RLS enable/force + policies + helper functions
  3) idempotent seed data + triggers (permissions list; system roles seeding hooks)

## 4) Backend (routes, schemas, services, errors)
### 4.1 Auth + tenant context model
- Auth: JWT bearer token in `Authorization: Bearer <token>`.
- Token payload includes:
  - `sub` = user_id
  - `exp`
- Tenant context:
  - Tenant-scoped routes require `X-Tenant-ID: <uuid>`.
  - Dependency checks membership and sets DB context:
    - Always set `app.user_id` (required for any protected work)
    - For tenant-scoped routes set `app.tenant_id`
  - Permission checks query `memberships → role_permissions` inside the current tenant.

### 4.2 Routes (minimum)
**Auth**
- `POST /auth/bootstrap`
  - Purpose: initialize a fresh system by creating the first tenant + first Owner user.
  - Guard:
    - If `BOOTSTRAP_TOKEN` is set, require `X-Bootstrap-Token` to match.
    - Otherwise only allow when `users` is empty (via `app_users_count()`).
  - Body: `{ "tenant_name": string, "tenant_slug": string, "email": string, "password": string }`
  - Response: `{ "token": string, "user": { "id": uuid, "email": string }, "tenant": { "id": uuid, "name": string, "slug": string } }`
- `POST /auth/login`
  - Body: `{ "email": string, "password": string }`
  - Response: `{ "token": string, "user": { "id": uuid, "email": string }, "tenants": [ { "id": uuid, "name": string, "slug": string, "role": { "id": uuid, "name": string } } ] }`
  - Errors:
    - `401` invalid credentials
    - `403` inactive user
- `GET /auth/me`
  - Auth required
  - Response: `{ "user": {..}, "tenants": [..] }`

**Tenants**
- `GET /tenants`
  - Auth required
  - Returns the tenants the current user is a member of (no `X-Tenant-ID` required)

**Members** (tenant-scoped; requires `X-Tenant-ID`)
- `GET /members` (permission `members:read`)
  - Response includes membership id, user id, email, role id/name, created_at
- `POST /members` (permission `members:write`)
  - Body: `{ "email": string, "password": string, "role_id": uuid }`
  - Behavior:
    - Upsert user by email, then create membership if not already present
    - Write audit log `member.created`
  - Errors:
    - `409` already a member

**Roles** (tenant-scoped; requires `X-Tenant-ID`)
- `GET /roles` (permission `roles:read`)
  - Response includes `permission_codes` list
- `POST /roles` (permission `roles:write`) body `{ "name": string, "permission_codes": string[] }`
  - Write audit log `role.created`
- `PATCH /roles/{role_id}` (permission `roles:write`) supports rename and full permission set replace
  - Write audit log `role.updated` with before/after snapshots
- `GET /permissions` (auth required; global list)

**Audit** (tenant-scoped; requires `X-Tenant-ID`)
- `GET /audit` (permission `audit:read`)
  - Query params: `q`, `entity_type`, `limit`, `cursor`
  - Keyset pagination ordered by `(created_at desc, id desc)` with opaque cursor

### 4.3 Errors (standard)
- Error body: `{ "error": { "code": string, "message": string } }`
- Validation error body (422): `{ "error": { "code": "VALIDATION_ERROR", "message": "Invalid request", "details": [...] } }`

## 5) Frontend (pages, components, states: loading/empty/error, tables with sort/filter/search/pagination)
### 5.1 Routing + layout
- Client routes:
  - `/login`
  - `/select-tenant` (only when user has multiple tenants and no selected tenant)
  - `/app/members`
  - `/app/roles`
  - `/app/audit`
- `AppLayout` must:
  - redirect to `/login` when unauthenticated
  - redirect to `/select-tenant` when needed
  - provide nav to Members/Roles/Audit and a “Switch tenant” action if multiple

### 5.2 Auth + tenant selection
- Store JWT token in `localStorage` (acceptable for this lot; see Security section).
- Store selected `tenantId` in `localStorage`.
- API calls include:
  - `Authorization: Bearer <token>`
  - `X-Tenant-ID: <tenantId>` for tenant-scoped endpoints

### 5.3 Pages (minimum)
**Login**
- Email + password form.
- States: submitting, error, success redirect.

**Tenant selection**
- Searchable tenant list (by name/slug).
- Selecting a tenant saves `tenantId` and redirects to `/app/members`.

**Members**
- Table: email, role, created_at.
- Controls: search (email), sort newest-first, pagination (default page size 25).
- Action: create member modal (email + password + role).

**Roles**
- Table: name, system badge, permissions count.
- Controls: search (name), sort, pagination.
- Actions:
  - create role (name + permission multi-select)
  - edit role (rename + permission set)

**Audit**
- Table: created_at, actor_email, action, entity_type, entity_id.
- Controls: search, filter entity_type, pagination via cursor.
- Read-only.

## 6) Security (RLS/RBAC, anti-leak checks, secrets)
### 6.1 RLS (tenant boundary backstop)
- All tenant-scoped tables introduced in this lot must have `FORCE` RLS.
- Policies must validate *both*:
  - tenant context (`app.tenant_id`) where appropriate, and
  - membership (user must belong to that tenant)
- The API must still enforce membership/permissions explicitly; RLS is the final guardrail.

### 6.2 RBAC
- RBAC checks are application-layer:
  - permission is granted when `memberships.role_id → role_permissions.permission_code` contains the required permission code for the current tenant.
- System roles:
  - Owner/Admin: all permissions
  - Member: only `tenants:read`

### 6.3 Anti-leak verification (required tests)
Add automated tests proving:
- Tenant A user cannot read/write tenant B rows even with crafted queries.
- Missing `X-Tenant-ID` blocks tenant-scoped endpoints at the API layer (400).
- Even if `X-Tenant-ID` is provided for a tenant the user is not a member of, the request is rejected (403) and RLS would also prevent access if reached.

### 6.4 Secrets / configuration
- Backend env vars:
  - `JWT_SECRET` (required outside local/dev)
  - `JWT_ALG` (default `HS256`)
  - `ACCESS_TOKEN_TTL_SECONDS` (default `3600`)
  - `BOOTSTRAP_TOKEN` (optional; if set, required for bootstrap)
- Frontend env vars:
  - `VITE_API_BASE_URL` (default `http://localhost:8000`)

### 6.5 Known trade-offs
- Storing JWT in `localStorage` is vulnerable to XSS token theft; acceptable for this lot only.
  - Follow-up hardening (future lot): HttpOnly cookies + CSRF protection + CSP.

## 7) DoD / Acceptance criteria
- Fresh Postgres can be migrated to head and produce all required tables/functions/policies.
- Bootstrap works on an empty DB and returns a valid token and tenant/user payload.
- Login works and returns the user’s tenant memberships.
- All tenant-scoped routes require `X-Tenant-ID`, enforce membership + permission checks, and write audit events on mutations.
- RLS backstop is proven by tests (no cross-tenant reads/writes).
- Frontend provides login + tenant selection + Members/Roles/Audit pages with standard list UX.
- Docs cover:
  - required env vars
  - how to run migrations
  - how to bootstrap locally

## 8) Verification (exact commands)
**Local setup**
- `cp .env.example .env` (optional; edit overrides as needed)
- `docker compose up -d --build`

**Migrations**
- `docker compose exec -T api alembic upgrade head`

**Bootstrap + auth smoke (curl)**
1) Bootstrap and capture token + tenant id:
- `RESP="$(curl -sS -X POST http://localhost:8000/auth/bootstrap -H 'Content-Type: application/json' -d '{"tenant_name":"Acme","tenant_slug":"acme","email":"owner@acme.test","password":"passw0rd"}')"`
- `TOKEN="$(python -c 'import json,sys; print(json.load(sys.stdin)[\"token\"])' <<<\"$RESP\")"`
- `TENANT_ID="$(python -c 'import json,sys; print(json.load(sys.stdin)[\"tenant\"][\"id\"])' <<<\"$RESP\")"`
2) Confirm current user:
- `curl -sS http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"`
3) List tenants (no tenant header):
- `curl -sS http://localhost:8000/tenants -H "Authorization: Bearer $TOKEN"`
4) Tenant-scoped reads:
- `curl -sS http://localhost:8000/members -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`
- `curl -sS http://localhost:8000/roles -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`
- `curl -sS http://localhost:8000/audit -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`

**Backend tests**
- `cd backend && pytest`

**Frontend checks**
- `cd frontend && npm install && npm run typecheck && npm run build`

**Repo checks (optional)**
- `./scripts/verify.sh`

## 9) Rollback plan
- Code rollback: revert the PR implementing this lot (migrations + API + UI).
- Database rollback:
  - Preferred: `docker compose exec -T api alembic downgrade -1` stepwise to the pre-L2 revision (only if safe).
  - Dev-only reset: `docker compose down -v` to wipe local Postgres volume and restart.
