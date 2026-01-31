# QA REVIEW — L2-auth-tenants-rbac-rls-base

Date (UTC): 2026-01-31 01:30:17Z

## Verdict
FAIL (DB/RLS integration blockers; verification gaps noted below).

## Scope reviewed
- SPEC: `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`
- IMPL: `docs/packs/IMPL_L2-auth-tenants-rbac-rls-base.md`
- VERIFICATION: `docs/packs/VERIFICATION_L2-auth-tenants-rbac-rls-base.md`
- SECURITY: `docs/packs/SECURITY_L2-auth-tenants-rbac-rls-base.md`

## Acceptance criteria check (SPEC §7)
- Fresh Postgres can be migrated to head and produce required tables/functions/policies: FAIL (likely)
  - `docker-compose.yml` runs migrations using `ia_app` (`DATABASE_URL` default).
  - `backend/alembic/versions/20260131_0002_rls_and_auth_helpers.py` enables + forces RLS on `roles`, `memberships`, `role_permissions`, etc.
  - `backend/alembic/versions/20260131_0003_seed_permissions_and_system_roles.py` seeds system roles via `app_seed_system_roles(...)`, which inserts into `roles` / `role_permissions` with no `app.user_id`/`app.tenant_id` context; those inserts appear to be rejected by the RLS policies.
- Bootstrap works on an empty DB and returns a valid token + tenant/user payload: FAIL (likely)
  - `backend/app/api/auth.py` uses `app_users_count()` and `app_bootstrap(...)` which rely on `SECURITY DEFINER` functions reading/inserting into `users`/`tenants` under `FORCE RLS`.
  - `backend/db/init.sql` creates `ia_app` without `BYPASSRLS`; under `FORCE RLS`, `SECURITY DEFINER` owned by `ia_app` does not bypass RLS.
- Login works and returns the user’s tenant memberships: FAIL (likely, same RLS/function-owner constraints as bootstrap)
  - `backend/app/api/auth.py` uses `app_get_user_for_login(...)` (SECURITY DEFINER) without an `app.user_id` context.
- Tenant-scoped routes require `X-Tenant-ID`, enforce membership + permission checks, and write audit events on mutations: PASS (implementation present)
  - `backend/app/auth/deps.py` (`require_tenant_id`, `require_tenant_context`, `require_permission`)
  - `backend/app/api/members.py`, `backend/app/api/roles.py`, `backend/app/api/audit.py`
- RLS backstop is proven by tests (no cross-tenant reads/writes): FAIL (not verifiable here; and tests depend on bootstrap)
  - `backend/tests/test_security_rls.py` exists, but requires `pytest` + a reachable Postgres with migrations applied.
- Frontend provides login + tenant selection + Members/Roles/Audit pages with standard list UX: PASS (implementation present; build not executed here)
  - `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/SelectTenantPage.tsx`, `frontend/src/pages/MembersPage.tsx`, `frontend/src/pages/RolesPage.tsx`, `frontend/src/pages/AuditPage.tsx`
- Docs cover required env vars, migrations, and local bootstrap: PASS
  - `README.md`, `backend/README.md`, `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`

## Verification executed (SPEC §8)
### Repo commands
- `./scripts/check_policy.sh` → PASS
- `./scripts/verify.sh` → PASS (with skips)
  - Packs check: PASS
  - Python syntax check (`python -m compileall backend/app backend/tests`): PASS
  - Backend tests: SKIP (pytest not installed in this environment)
  - Frontend checks: SKIP (no `frontend/node_modules` present)

## Notes / deltas
- The lot’s DB/RLS strategy is directionally correct (RLS `FORCE` + per-request `set_config` context), but the current role model + seed/bootstrap path is not viable as shipped when migrations/bootstrap run using `ia_app`.
- This matches the security review verdict and blocker analysis: `docs/packs/SECURITY_L2-auth-tenants-rbac-rls-base.md`.

