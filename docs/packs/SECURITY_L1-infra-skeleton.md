# SECURITY REVIEW — L1-infra-skeleton

Date: 2026-01-31

## Scope
LOT `L1-infra-skeleton` is local/dev infrastructure scaffolding (Docker Compose for Postgres/Redis/API/worker + minimal frontend). No tenant model, RBAC, RLS, or business schema is introduced in this lot (explicitly out of scope).

References:
- `docs/packs/SPEC_L1-infra-skeleton.md`
- `docs/packs/IMPL_L1-infra-skeleton.md`
- `docs/packs/VERIFICATION_L1-infra-skeleton.md`

Reviewed implementation files:
- `docker-compose.yml`
- `backend/app/main.py`
- `backend/app/api/health.py`
- `backend/app/settings.py`
- `backend/app/worker.py`
- `backend/Dockerfile`
- `.env.example`
- `scripts/check_policy.sh`
- `scripts/verify.sh`

Verification executed (local):
- `./scripts/check_policy.sh` (PASS)
- `./scripts/ci/check_packs.sh HEAD` (PASS)
- `./scripts/verify.sh` (PASS; backend/frontend dependency-based checks skipped in this environment)

## 1) DB / RLS tenant isolation
- No Postgres schema or migrations in this lot.
- No RLS policies added/changed.
- No tenant context plumbing (e.g., `SET app.tenant_id`) added/changed.

Result: **N/A for this lot** (no business-data surface area introduced).

## 2) API authz / data filtering
- API surface introduced here is intentionally minimal (`GET /health`) and returns a constant response.
- There is no authentication/authorization layer in this lot (expected for a skeleton).

Risk notes (expected for local/dev):
- FastAPI defaults expose OpenAPI + interactive docs endpoints (e.g., `/openapi.json`, `/docs`) unless explicitly disabled; this is fine for local/dev, but should be turned off (or gated) in any production environment.

Result: **N/A for this lot** (no protected resources exist yet), with the note above.

## 3) Infra / container security review (dev-focused)
Reviewed `docker-compose.yml` and `backend/Dockerfile`.

Findings:
- Postgres and Redis ports are published on the host (defaults `5432` and `6379`) and will bind to all interfaces by default. This is convenient for local dev, but can be risky on shared networks. Prefer binding to `127.0.0.1` (or not publishing at all) for safer defaults.
- Default dev credentials are hard-coded via compose defaults (Postgres `postgres/postgres`) and Redis has no auth/TLS. Acceptable for local-only development, but must not be carried into production deployments.
- Backend container runs as root (no `USER` directive) and compose runs Uvicorn with `--reload`. Both are reasonable for a dev skeleton, but production images should run as a non-root user and avoid `--reload`.
- Images are referenced by tags (e.g., `postgres:16`, `redis:7`, `python:3.12-slim`) rather than digests; consider pinning to digests for stronger supply-chain controls (future hardening lot).

## 4) Secrets / anti-leak checks
Findings:
- `.env` is gitignored and `.env.example` contains only dev defaults; no committed secret material detected.
- Repo includes `scripts/check_policy.sh` which blocks `.env` files (except `.env.example`) and common private-key filenames in diffs (defense-in-depth for PR hygiene).

## Result
**PASS** for `L1-infra-skeleton` as a local/dev skeleton (no RLS/RBAC/business data introduced).

## Follow-ups (not required for this lot)
- Bind Postgres/Redis published ports to `127.0.0.1` by default (or avoid publishing) to reduce accidental exposure.
- Run the backend container as a non-root user (and consider `read_only: true` + drop capabilities) if/when hardening the dev image.
- Disable/gate FastAPI docs/OpenAPI outside `local`/`dev`.
- Pin Docker images and (optionally) Python/Node deps for supply-chain hardening.
