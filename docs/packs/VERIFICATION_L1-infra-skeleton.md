# VERIFICATION PACK — L1-infra-skeleton

## Tests executed
- `python -m compileall backend/app backend/tests` (PASS in this workspace)
- `./scripts/verify.sh` (PASS; backend/frontend steps may skip if deps aren’t installed locally)

## How to reproduce
### Docker (API + worker + Postgres + Redis)
- `cp .env.example .env` (optional overrides)
- `docker compose up --build`
- `curl http://localhost:8000/health` → `{"status":"ok"}`

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
- Local syntax check: PASS
- Full test/build matrix: PENDING (run via GitHub Actions CI on PR)
