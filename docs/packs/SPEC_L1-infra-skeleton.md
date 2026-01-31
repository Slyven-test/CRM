# SPEC PACK — L1-infra-skeleton

## 1) Context & Goal
IA-CRM v2 needs a runnable “local/dev infra skeleton” that developers can start quickly, end-to-end, without any production deployment work. This lot is intentionally small (1–3 days) and focuses on wiring and ergonomics rather than business features.

**Goal:** Stand up local/dev infrastructure for:
- Postgres
- Redis
- API service
- Worker service
- Frontend dev app (run locally via Node tooling; not in Docker Compose for this lot)

So that a new developer can:
- start dependencies via `docker compose up --build`
- hit a backend health endpoint
- run backend tests
- run frontend typecheck/build (and optionally dev server)

**Risks / mitigations**
- Cross-platform dev drift (Docker/Desktop differences): keep compose as simple as possible; rely on healthchecks and explicit ports.
- “Skeleton creep” into business scope: keep this lot limited to `/health`, a single worker task, and basic docs/verify scripts.

## 2) In-scope / Out-of-scope
**In scope**
- `docker-compose.yml` providing `postgres`, `redis`, `api`, `worker` with healthchecks and sane defaults.
- A minimal FastAPI backend skeleton:
  - `GET /health` endpoint
  - env-driven settings (`DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT`, `CORS_ORIGINS`)
  - minimal `pytest` suite suitable for CI
- A minimal worker skeleton using Celery + Redis broker/backend:
  - a trivial task (`tasks.ping`) to validate end-to-end worker execution
  - worker starts via a stable import path (Celery `-A` target)
- A minimal frontend skeleton (Vite + React + TypeScript + Tailwind baseline):
  - renders a landing page
  - includes at least one reusable UI primitive (`Button`)
  - calls the backend health endpoint using `VITE_API_BASE_URL` (defaulting to `http://localhost:8000`)
- Developer docs and a single local verification script to run checks consistently.

**Out of scope**
- Any business features (CRUD screens, audit log UI, imports).
- Tenant model, RBAC, and Postgres RLS policies (planned for a subsequent lot).
- Production infrastructure/deployments (Terraform/K8s, managed Postgres/Redis, secrets managers, etc.).

## 3) Data model (tables, columns, indexes, RLS policies, migrations strategy)
**Schema changes**
- None in this lot: no application tables, no indexes, no migrations shipped.

**Postgres container contract (dev-only)**
- Database: `${POSTGRES_DB}` (default: `ia_crm`)
- User/password: `${POSTGRES_USER}` / `${POSTGRES_PASSWORD}` (default: `postgres` / `postgres`)
- Port mapping: `${POSTGRES_PORT}:5432` (default host port `5432`)

**Redis container contract (dev-only)**
- Port mapping: `${REDIS_PORT}:6379` (default host port `6379`)

**API container contract (dev-only)**
- Port mapping: `${API_PORT}:8000` (default host port `8000`)

**Migration strategy (future-facing; not implemented in this lot)**
- Adopt a migration tool (e.g. Alembic) in a later lot once the first RLS-protected tables are introduced.
- Any future business tables must include a `tenant_id` and enforce tenant isolation via Postgres RLS.

## 4) Backend (routes, schemas, services, errors)
**Routes**
- `GET /health`
  - Response: `{"status":"ok"}`
  - Purpose: simple liveness check for dev and smoke tests.

**Settings**
- Read from environment variables (with local defaults):
  - `ENVIRONMENT` (default `local`)
  - `DATABASE_URL` (used by later lots; may remain unused in this lot)
  - `REDIS_URL` (used by worker and any async tasks)
  - `CORS_ORIGINS` (comma-separated; optional override)

**CORS behavior**
- When `CORS_ORIGINS` is set: allow exactly those origins (comma-separated).
- When `ENVIRONMENT` is `local`/`dev` and `CORS_ORIGINS` is not set: allow `http://localhost:5173` and `http://127.0.0.1:5173`.

**Worker invocation**
- Celery app should be importable in a stable way; the canonical worker command for compose should be:
  - `celery -A app.worker:celery_app worker -l info`

**Errors**
- `/health` must not throw; in case of internal error, respond with a non-2xx and a minimal error body (standard FastAPI behavior is acceptable for this skeleton).

## 5) Frontend (pages, components, states: loading/empty/error, tables with sort/filter/search/pagination)
**Pages / flows**
- Single landing page (no routing required).
- Fetch `GET /health` from the API base URL:
  - `VITE_API_BASE_URL` if set
  - otherwise default `http://localhost:8000`

**UI components**
- One reusable primitive in `frontend/src/components/ui/` (minimum: `Button`).
- Tailwind baseline styling via `frontend/src/index.css`.

**States**
- Loading state while health request is in-flight.
- Error state showing a brief message if the request fails.
- Success state showing `status: ok`.

**Tables / list UX**
- N/A in this lot (no business entities). Table patterns (sort/filter/search/pagination) will be introduced when CRUD screens exist.

## 6) Security (RLS/RBAC, anti-leak checks, secrets)
**RLS/RBAC**
- No RLS/RBAC policies are introduced in this lot; no business data exists yet.
- This lot must not introduce any multi-tenant data model without RLS (explicitly out of scope).

**Secrets**
- `.env` must be treated as local-only; keep `.env.example` as the committed reference.
- Default dev credentials are acceptable for local compose only.

**Anti-leak / exposure**
- Backend exposes only `/health` (no business endpoints).
- CORS is restricted to local dev origins by default; `CORS_ORIGINS` can override for specific dev needs.

## 7) DoD / Acceptance criteria
- `docker compose up --build` starts `postgres`, `redis`, `api`, and `worker` successfully on a clean machine with Docker installed.
- `curl http://localhost:8000/health` returns HTTP 200 with `{"status":"ok"}`.
- Worker can execute a trivial task end-to-end (broker + worker + result backend), e.g. `tasks.ping` returns `pong`.
- Backend tests run in CI via `pytest` and pass.
- Frontend `npm run typecheck` and `npm run build` run in CI and pass.
- `README.md` documents how to run services locally and how to run verification checks.
- A repo-level verification script exists and is runnable (`./scripts/verify.sh`).

## 8) Verification (exact commands)
**Prereqs**
- Docker + Docker Compose v2
- Python (for local backend tests)
- Node + npm (for local frontend checks)

**Start infra (compose)**
- `cp .env.example .env` (optional; edit overrides as needed)
- `docker compose up --build`
- Optional: `docker compose ps`
  - If you need non-default ports, set `POSTGRES_PORT`, `REDIS_PORT`, and/or `API_PORT` in `.env`.

**Backend liveness**
- `curl -sS http://localhost:8000/health`

**Worker end-to-end task**
- In another terminal while compose is running:
  - `docker compose exec -T api python -c "from app.worker import celery_app; print(celery_app.send_task('tasks.ping').get(timeout=10))"`

**Backend tests**
- `cd backend`
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e \".[dev]\"`
- `pytest`

**Frontend checks**
- `cd frontend`
- `npm install`
- `npm run typecheck`
- `npm run build`
- Optional dev server: `npm run dev`

**Repo verification**
- `./scripts/verify.sh`

## 9) Rollback plan
- Code rollback: revert the PR that introduced the skeleton (`docker-compose.yml`, `backend/`, `frontend/`, docs/scripts/CI additions).
- Local environment rollback:
  - Stop services: `docker compose down`
  - Remove persisted Postgres data if needed: `docker compose down -v`
