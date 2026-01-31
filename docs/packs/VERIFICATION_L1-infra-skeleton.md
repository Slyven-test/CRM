# VERIFICATION PACK — L1-infra-skeleton

## Spec link
- `docs/packs/SPEC_L1-infra-skeleton.md`

## Tests executed
- `./scripts/verify.sh` (PASS)
- `RUN_DOCKER_SMOKE=1 ./scripts/verify.sh` (PASS; Docker smoke auto-skipped because Docker daemon access was unavailable)

## Expected outputs (high-signal)
- `./scripts/verify.sh`
  - Should print `==> Packs check` and `packs check: PASS`
  - Should print `==> Python syntax check`
- `RUN_DOCKER_SMOKE=1 ./scripts/verify.sh`
  - If Docker daemon is accessible: should run compose smoke and validate `/health` + `tasks.ping`
  - If Docker daemon is not accessible: should print `==> Docker smoke skipped (cannot access Docker daemon)` and continue

## Notes on constraints
- Backend `pytest` requires dependencies installed via `pip install -e ".[dev]"`.
- Frontend `npm run typecheck`/`npm run build` are gated behind `npm install` (the verification script skips if `frontend/node_modules` is missing).
- Docker smoke checks (`RUN_DOCKER_SMOKE=1`) require access to a running Docker daemon; the script skips if it cannot connect.

## How to reproduce
### Docker (API + worker + Postgres + Redis)
- `cp .env.example .env` (optional overrides)
- `docker compose up --build`
- `curl http://localhost:8000/health` → `{"status":"ok"}`
- Worker task (in another terminal): `docker compose exec -T api python -c "from app.worker import celery_app; print(celery_app.send_task('tasks.ping').get(timeout=10))"` → `pong`

### Backend tests
- `cd backend`
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`
- `pytest`

### Frontend checks
- `cd frontend`
- `npm install`
- `npm run typecheck`
- `npm run build`
- Optional dev server: `npm run dev`

## RLS / security checks
- Not applicable in this lot (no tenant/RLS/RBAC yet).

## Performance checks
- Not applicable in this lot (skeleton endpoints only).

## Result (PASS/FAIL + CI link)
- Local verification script: PASS
- Full test/build matrix: PENDING (run via GitHub Actions CI on PR)
