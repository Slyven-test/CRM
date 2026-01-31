# SECURITY REVIEW — L2-auth-tenants-rbac-rls-base

Date: 2026-01-31

## Scope
LOT `L2-auth-tenants-rbac-rls-base` introduces the core security foundation: multi-tenant identity, Postgres RLS tenant isolation, API-layer RBAC permission checks, and audit logging. This review focuses on tenant isolation correctness (DB as source of truth), authorization enforcement at the API layer, and secret/config leakage.

References:
- `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`
- `docs/packs/IMPL_L2-auth-tenants-rbac-rls-base.md`
- `docs/packs/VERIFICATION_L2-auth-tenants-rbac-rls-base.md`

Reviewed implementation files (non-exhaustive, security-relevant):
- `backend/alembic/versions/20260131_0001_security_schema.py`
- `backend/alembic/versions/20260131_0002_rls_and_auth_helpers.py`
- `backend/alembic/versions/20260131_0003_seed_permissions_and_system_roles.py`
- `backend/db/init.sql`
- `backend/app/db/session.py`
- `backend/app/db/context.py`
- `backend/app/auth/deps.py`
- `backend/app/auth/jwt.py`
- `backend/app/settings.py`
- `backend/app/api/auth.py`
- `backend/app/api/tenants.py`
- `backend/app/api/members.py`
- `backend/app/api/roles.py`
- `backend/app/api/audit.py`
- `backend/tests/test_security_rls.py`
- `docker-compose.yml`
- `scripts/check_policy.sh`

Verification executed (local, security-focused):
- `./scripts/check_policy.sh` (PASS)
- Repo scan for common secret patterns (PASS)

## 1) DB / RLS tenant isolation
What looks correct:
- `ENABLE` + `FORCE ROW LEVEL SECURITY` is applied to tenant-scoped tables (`tenants`, `memberships`, `roles`, `role_permissions`, `audit_log`) and to `users`.
- Policies for tenant-scoped tables consistently require `app_current_tenant_id()` + membership checks (`app_is_member`) for writes.
- Request code uses `set_config(..., true)` inside an explicit SQLAlchemy transaction (`backend/app/db/session.py`), which is the right shape for `SET LOCAL`-style per-request context.

Critical issues (blockers):
1) **RLS + migrations/bootstrap are currently incompatible with the configured DB role.**
   - The app DB role created by `backend/db/init.sql` (`ia_app`) does **not** have `BYPASSRLS`.
   - With `FORCE ROW LEVEL SECURITY`, `SECURITY DEFINER` functions owned by `ia_app` do **not** bypass RLS.
   - As a result, `backend/alembic/versions/20260131_0003_seed_permissions_and_system_roles.py` will attempt to seed `roles`/`role_permissions` via `app_seed_system_roles()` without any `app.user_id` / `app.tenant_id` context, and those inserts are rejected by RLS policies (roles insert policy requires `app_current_tenant_id()` + membership).
   - Similarly, the runtime bootstrap path (`app_bootstrap`, `app_upsert_user`, `app_get_user_for_login`, `app_users_count`) relies on `SECURITY DEFINER` to work “around” `users`/`tenants` RLS, but under `FORCE` RLS and a non-`BYPASSRLS` owner these functions cannot read/insert the required rows.

2) **Missing `INSERT` policies on `tenants` and `users` makes bootstrap inherently impossible under `FORCE` RLS without a privileged execution path.**
   - `tenants` has a `FOR SELECT` policy only; no `FOR INSERT`.
   - `users` has `FOR SELECT`/`FOR UPDATE` self policies only; no `FOR INSERT`.
   - Any attempt to create the first tenant/user/membership via the app connection will be blocked unless migrations/bootstrap run with a separate privileged role (or a deliberate bypass/escape hatch is introduced).

High-risk notes:
- `memberships` policy uses `app_is_member(...)`, which itself queries `memberships`. This can create policy self-dependence / recursion risk and can become a performance hotspot as tenant size grows.

Result: **FAIL** (tenant isolation intent is good, but current RLS policy/role/function wiring blocks seed/bootstrap/login flows and is likely to fail migrations).

## 2) API authz / data filtering (RBAC)
What looks correct:
- Tenant-scoped endpoints (`/members`, `/roles`, `/audit`) require both `X-Tenant-ID` and a permission via `require_permission(...)`.
- `require_tenant_context` verifies membership and sets `app.tenant_id`; `get_current_user_id` sets `app.user_id` and verifies `users.is_active`.
- Queries consistently filter by `tenant_id = :tenant_id` in addition to relying on RLS (defense in depth).

Risk notes:
- `require_permission` does not explicitly constrain `role_permissions` by `tenant_id` (it relies on `role_id` join and RLS). This is probably fine with correct RLS, but adding `AND rp.tenant_id = m.tenant_id` would harden against accidental RLS regressions.
- `/roles/permissions` is auth-protected but not permission-gated; acceptable for now (permission codes are not sensitive), but document expected behavior.

Result: **PASS** for API-layer RBAC shape, conditional on the DB layer being functional and correctly enforced.

## 3) Secrets / config / anti-leak
Findings:
- No committed `.env` files beyond `.env.example`; `scripts/check_policy.sh` enforces this in diffs.
- `docker-compose.yml` and `.env.example` default `JWT_SECRET` to `dev-jwt-secret-change-me`. This is acceptable for local/dev, but is dangerous if compose is ever used outside `ENVIRONMENT=local/dev`. Prefer leaving `JWT_SECRET` unset by default and relying on `backend/app/settings.py` to generate a local/dev default only when `ENVIRONMENT` is explicitly local/dev.
- `BOOTSTRAP_TOKEN` is optional; when unset, bootstrap guard relies on `app_users_count()`. With current `users` RLS, `app_users_count()` cannot work unless it has a privileged execution path; this can accidentally keep bootstrap open.

Result: **PASS (local/dev)** with the hardening notes above.

## Result
**FAIL** for `L2-auth-tenants-rbac-rls-base` due to DB/RLS integration blockers (migrations + bootstrap/login are not viable with `FORCE RLS` under the current DB role model).

## Recommended fixes (next steps)
Choose one cohesive approach and standardize it for all future lots:
1) **Two-role model (recommended):**
   - Use a dedicated migration/admin role (not used by the API) to run Alembic and any one-time bootstrap/provisioning.
   - Keep the runtime `ia_app` role non-privileged (no `CREATE` on schema, no `BYPASSRLS`).
   - Move bootstrap to an out-of-band admin-only flow (or restrict it to local/dev environments with a separate admin DSN).

2) **Privileged helper functions owned by a `BYPASSRLS` role (use with care):**
   - Create a narrowly-scoped role with `BYPASSRLS` that owns *only* specific `SECURITY DEFINER` functions needed for login/bootstrap/email lookup.
   - Explicitly manage `EXECUTE` grants, and ensure functions return the minimal fields needed.
   - Document that DB credentials imply the ability to call these helpers (threat model clarity).

3) **Policy adjustments (not preferred for bootstrap):**
   - Add explicit `INSERT` policies to `tenants` and `users` that allow only under a tightly controlled condition. Be careful: any condition based on session GUCs is not a security boundary against a compromised app DB connection.

Hardening follow-ups:
- Remove `GRANT CREATE ON SCHEMA public TO ia_app` for non-local environments.
- Rework `memberships` policy to avoid calling a membership-check helper that queries `memberships` (reduce recursion/perf risk).
- Add explicit tenant join conditions in RBAC queries (`rp.tenant_id = m.tenant_id`) as defense in depth.

