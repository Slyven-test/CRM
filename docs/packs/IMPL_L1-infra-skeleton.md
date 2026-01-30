# IMPL PACK — L1-infra-skeleton

## Summary
Created the repo’s “infra skeleton” (compose + backend + worker + frontend) and added CI to run backend tests and frontend build/typecheck.

## DB changes (migrations, indexes, RLS)
- None in this lot (no schema/migrations/RLS yet).

## Backend changes
- Added FastAPI skeleton with `GET /health` and a `pytest` test.
- Added dev-friendly CORS defaults (override via `CORS_ORIGINS`).
- Added Celery worker skeleton configured via `REDIS_URL`.
- Added `backend/pyproject.toml` and `backend/Dockerfile` for container builds.

## Frontend changes
- Added Vite + React + TypeScript skeleton.
- Added Tailwind baseline and a minimal UI primitive: `Button`.
- Added health check fetch (configurable via `VITE_API_BASE_URL`).

## DevEx changes
- Added `.env.example` and documented common env overrides in `README.md`.

## Observability
- None beyond default Uvicorn/Celery logs (skeleton phase).

## Rollback plan
- Revert the added skeleton directories (`backend/`, `frontend/`), `docker-compose.yml`, and `.github/workflows/ci.yml`.
