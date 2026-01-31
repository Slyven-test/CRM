# IA-CRM v2

## Local dev (infra skeleton)
### Backend + worker + Postgres + Redis
- `cp .env.example .env` (optional overrides)
- `docker compose up --build`
- API: `http://localhost:8000/health`
- Liveness: `curl -sS http://localhost:8000/health`
- Worker task (in another terminal): `docker compose exec -T api python -c "from app.worker import celery_app; print(celery_app.send_task('tasks.ping').get(timeout=10))"`

### Frontend
- `cd frontend`
- `npm install`
- `npm run dev`
- App: `http://localhost:5173` (default)

### Backend tests
- `cd backend`
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`
- `pytest`

### Frontend checks
- `cd frontend`
- `npm run typecheck`
- `npm run build`

## Verification
- `./scripts/verify.sh`
- Optional Docker smoke (starts compose + checks `/health` + runs `tasks.ping`): `RUN_DOCKER_SMOKE=1 ./scripts/verify.sh`

## Delivery workflow (packs)
Every PR is expected to include “packs” under `docs/packs/`:
- `docs/packs/SPEC_<LOT_ID>.md`
- `docs/packs/IMPL_<LOT_ID>.md`
- `docs/packs/VERIFICATION_<LOT_ID>.md`

CI enforces pack presence on pull requests. You can run the same check locally:
- `./scripts/ci/check_packs.sh origin/main`

If you don't have the base ref locally, fetch it:
- `git fetch origin main --depth=1`

## Configuration
- Compose service ports: `POSTGRES_PORT`, `REDIS_PORT`, `API_PORT`
- API settings: `ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS` (comma-separated)
- Frontend: `VITE_API_BASE_URL` (defaults to `http://localhost:8000`)
