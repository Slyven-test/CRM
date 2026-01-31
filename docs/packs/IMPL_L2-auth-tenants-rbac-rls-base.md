# IMPL PACK — L2-auth-tenants-rbac-rls-base

## Summary
Implements the baseline multi-tenant security foundation: tenant/user/membership schema, DB-enforced tenant isolation via Postgres RLS, API-layer RBAC permission checks, audit logging for security mutations, and minimal frontend flows for login/tenant selection plus Members/Roles/Audit admin pages.

## Spec link
- `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`

## DB changes (migrations, indexes, RLS)
- Alembic migrations (already present in repo for this lot):
  - `backend/alembic/versions/20260131_0001_security_schema.py`: extensions (`pgcrypto`, `citext`), tables (`tenants`, `users`, `memberships`, `roles`, `permissions`, `role_permissions`, `audit_log`) + indexes.
  - `backend/alembic/versions/20260131_0002_rls_and_auth_helpers.py`: session context functions (`app_current_user_id`, `app_current_tenant_id`), membership + identity helpers (`app_is_member`, `app_user_email`, `app_users_count`, `app_get_user_for_login`, `app_upsert_user`), `ENABLE` + `FORCE` RLS, and baseline policies.
  - `backend/alembic/versions/20260131_0003_seed_permissions_and_system_roles.py`: permission seed data, role-permission tenant integrity trigger, system roles seeding, tenant-created trigger, and bootstrap helper (`app_bootstrap`).

## Backend changes
- Auth + tenant context + RBAC dependencies in `backend/app/auth/deps.py`:
  - JWT bearer auth (`get_current_user_id`) sets `app.user_id` per request/transaction.
  - Tenant-scoped dependency (`require_tenant_context`) validates `X-Tenant-ID` + membership and sets `app.tenant_id`.
  - RBAC permission checks (`require_permission`) via `memberships → role_permissions`.
- Routes:
  - `backend/app/api/auth.py`: `POST /auth/bootstrap`, `POST /auth/login`, `GET /auth/me`.
  - `backend/app/api/tenants.py`: `GET /tenants` (no `X-Tenant-ID`).
  - `backend/app/api/members.py`: `GET /members`, `POST /members` with audit entry `member.created`.
  - `backend/app/api/roles.py`: `GET /permissions`, `GET/POST/PATCH /roles` with audit entries `role.created` / `role.updated`.
  - `backend/app/api/audit.py`: `GET /audit` with keyset cursor pagination.
- Error envelope standardization in `backend/app/main.py` (maps `HTTPException.detail` dicts to `{ "error": { "code", "message" } }`).

## Frontend changes
- Replaced the skeleton health-check UI with an auth-aware router in `frontend/src/App.tsx`.
- Auth state + persistence in `frontend/src/lib/auth.tsx` (JWT + selected tenant stored in `localStorage`).
- Pages:
  - `frontend/src/pages/LoginPage.tsx`: email/password login.
  - `frontend/src/pages/SelectTenantPage.tsx`: tenant selection when multiple memberships exist.
  - `frontend/src/pages/AppLayout.tsx`: authenticated layout + navigation + switch tenant + logout.
  - `frontend/src/pages/MembersPage.tsx`: members list with search + pagination and “create member” modal.
  - `frontend/src/pages/RolesPage.tsx`: roles list with search + pagination and create/edit role modals (permission multi-select).
  - `frontend/src/pages/AuditPage.tsx`: audit list with search + entity-type filter + cursor pagination (“load more”).

## Security changes
- Enforces DB tenant boundary with `ENABLE` + `FORCE ROW LEVEL SECURITY` and policies for tenant-scoped tables.
- Enforces API-layer RBAC permission checks on all tenant-scoped routes.
- Adds automated anti-leak tests to exercise tenant header validation, membership rejection, and DB-level RLS backstop.

## Observability
- Audit log (`audit_log`) records security mutations (memberships and roles) as the baseline audit pattern for future lots.

## Rollback plan
- Revert the PR for this lot (API + UI + CI + tests + docs).
- DB rollback (dev/test): `alembic downgrade -1` stepwise to pre-L2 revision, or wipe local volumes (`docker compose down -v`) and re-run migrations.

