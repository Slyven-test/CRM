# PR NOTE — L2-auth-tenants-rbac-rls-base

## Packs
- SPEC: `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`
- IMPL: `docs/packs/IMPL_L2-auth-tenants-rbac-rls-base.md`
- VERIFICATION: `docs/packs/VERIFICATION_L2-auth-tenants-rbac-rls-base.md`
- QA: `docs/packs/QA_L2-auth-tenants-rbac-rls-base.md`
- SECURITY: `docs/packs/SECURITY_L2-auth-tenants-rbac-rls-base.md`

## Summary of changes
Implements the baseline multi-tenant security foundation:
- DB schema for tenants/users/memberships/roles/permissions + audit log; RLS (`ENABLE` + `FORCE`) and helper functions for request-scoped auth context.
- Backend auth + tenancy + RBAC: bootstrap/login/me endpoints, tenant discovery, tenant-scoped Members/Roles/Audit endpoints with permission checks and audit events for security mutations.
- Frontend auth flows (login + tenant selection) and minimal admin pages for Members/Roles/Audit.

## Verification summary
Verification steps are defined in `docs/packs/VERIFICATION_L2-auth-tenants-rbac-rls-base.md` and reviewed in `docs/packs/QA_L2-auth-tenants-rbac-rls-base.md`.

Current status:
- QA verdict: **FAIL** — DB/RLS integration blockers likely prevent migrations/seed/bootstrap/login from succeeding under the configured DB role. See `docs/packs/QA_L2-auth-tenants-rbac-rls-base.md`.
- Security verdict: **FAIL** — RLS intent is good, but the current RLS/role/function wiring blocks the seed/bootstrap path. See `docs/packs/SECURITY_L2-auth-tenants-rbac-rls-base.md`.

Local/sandbox highlights:
- `./scripts/check_policy.sh` (PASS)
- `./scripts/verify.sh` (PASS with skips; DB-backed `pytest` and frontend checks may be skipped when dependencies/services are unavailable)

## Release checklist
- [ ] Packs present for this lot: SPEC/IMPL/VERIFICATION/QA/SECURITY
- [ ] Resolve DB/RLS blockers called out in QA/SECURITY packs (seed/migrations/bootstrap/login viability under `FORCE RLS`)
- [ ] CI is green on PR (backend DB-backed tests + frontend `typecheck`/`build`)
- [ ] `./scripts/verify.sh` passes locally (or skips are justified)
- [ ] Docker E2E smoke from the VERIFICATION pack succeeds: migrate → bootstrap → login → tenant-scoped reads
- [ ] Confirm tenant isolation is enforced (API + DB backstop) and cross-tenant access is rejected

## Rollback summary
Rollback is a full revert of the PR for this lot.

DB rollback (dev/test):
- Downgrade Alembic stepwise to pre-L2 revision, or wipe local volumes (`docker compose down -v`) and re-run migrations.

