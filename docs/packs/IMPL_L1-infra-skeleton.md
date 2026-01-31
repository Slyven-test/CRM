# IMPL PACK — L1-infra-skeleton

## Summary
Created the repo’s “infra skeleton” (compose + backend + worker + frontend) and added CI + a local verification script to run checks consistently.

## Spec link
- `docs/packs/SPEC_L1-infra-skeleton.md`

## DB changes (migrations, indexes, RLS)
- None in this lot (no schema/migrations/RLS yet).

## Backend changes
- Added FastAPI skeleton with `GET /health` and a `pytest` test.
- Added dev-friendly CORS defaults (override via `CORS_ORIGINS`).
- Added Celery worker skeleton configured via `REDIS_URL`.
- Added `backend/pyproject.toml` and `backend/Dockerfile` for container builds.
- Added `docker-compose.yml` services for `postgres`, `redis`, `api`, and `worker` (canonical worker invocation: `celery -A app.worker:celery_app worker -l info`).
- Added API and worker container healthchecks for more reliable local startup.

## Frontend changes
- Added Vite + React + TypeScript skeleton.
- Added Tailwind baseline and a minimal UI primitive: `Button`.
- Added health check fetch (configurable via `VITE_API_BASE_URL`).

## DevEx changes
- Added `.env.example` and documented common env overrides in `README.md`.
- Added repo verification script `./scripts/verify.sh`.
- Added optional Docker smoke checks to `./scripts/verify.sh` (gated via `RUN_DOCKER_SMOKE=1`).
- Added GitHub Actions CI to run backend `pytest` and frontend `npm run typecheck` / `npm run build`.

## Security changes
- No auth/RBAC/RLS introduced (skeleton scope).
- Added policy checks to block committing `.env` and common key/cert filenames.

## Observability
- None beyond default Uvicorn/Celery logs (skeleton phase).

## Rollback plan
- Revert the added skeleton directories (`backend/`, `frontend/`), `docker-compose.yml`, and `.github/workflows/ci.yml`.
