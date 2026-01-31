# VERIFICATION PACK — L2-auth-tenants-rbac-rls-base

## Spec link
- `docs/packs/SPEC_L2-auth-tenants-rbac-rls-base.md`

## Tests executed
Executed in this workspace:
- `python -m compileall backend/app backend/tests`

Expected to be executed in CI / dev (see below):
- `cd backend && pip install -e ".[dev]" && alembic upgrade head && pytest`
- `cd frontend && npm install && npm run typecheck && npm run build`

## How to reproduce
Local (Docker) end-to-end smoke, per SPEC:
1) Start services:
   - `cp .env.example .env` (optional)
   - `docker compose up -d --build`
2) Run migrations:
   - `docker compose exec -T api alembic upgrade head`
3) Bootstrap:
   - `RESP="$(curl -sS -X POST http://localhost:8000/auth/bootstrap -H 'Content-Type: application/json' -d '{\"tenant_name\":\"Acme\",\"tenant_slug\":\"acme\",\"email\":\"owner@acme.test\",\"password\":\"passw0rd\"}')"`
   - `TOKEN="$(python -c 'import json,sys; print(json.load(sys.stdin)[\"token\"])' <<<\"$RESP\")"`
   - `TENANT_ID="$(python -c 'import json,sys; print(json.load(sys.stdin)[\"tenant\"][\"id\"])' <<<\"$RESP\")"`
4) Confirm auth + tenant discovery:
   - `curl -sS http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"`
   - `curl -sS http://localhost:8000/tenants -H "Authorization: Bearer $TOKEN"`
5) Tenant-scoped reads:
   - `curl -sS http://localhost:8000/members -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`
   - `curl -sS http://localhost:8000/roles -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`
   - `curl -sS http://localhost:8000/audit -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: $TENANT_ID"`
6) Frontend:
   - `cd frontend && npm install && npm run dev`
   - Visit `http://localhost:5173/login` → sign in → select tenant (if needed) → browse Members/Roles/Audit.

## RLS / security checks
Automated (pytest, requires Postgres + migrations):
- `backend/tests/test_security_rls.py`:
  - Missing `X-Tenant-ID` returns `400` on tenant-scoped endpoints.
  - Cross-tenant `X-Tenant-ID` returns `403` (membership check).
  - Direct DB queries with mismatched `app.user_id`/`app.tenant_id` demonstrate:
    - cross-tenant reads return zero rows under RLS
    - cross-tenant writes are rejected by RLS

Manual spot checks (curl):
- Omit `X-Tenant-ID` on `/members`, `/roles`, `/audit` → expect `400` with `{ "error": { "code": "VALIDATION_ERROR", ... } }`.
- Use `X-Tenant-ID` for a tenant the user is not a member of → expect `403` with `{ "error": { "code": "FORBIDDEN", ... } }`.

## Performance checks
- Not performed for this lot (baseline security foundation; low data volumes expected).

## Result (PASS/FAIL + CI link)
- FAIL (not fully executed in this sandbox: no Docker daemon and `pytest`/`npm install` are unavailable here). CI should execute DB-backed tests and frontend build.

