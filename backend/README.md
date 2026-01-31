# IA-CRM v2 — Backend

## Run (local)
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`
- `uvicorn app.main:app --reload`

## Tests
- `pytest`

## Env
- `ENVIRONMENT` (default: `local`)
- `DATABASE_URL`
- `REDIS_URL`
- `CORS_ORIGINS` (comma-separated; default allows `http://localhost:5173` in `local`/`dev`)
- `JWT_SECRET` (required outside `local`/`dev`)
- `JWT_ALG` (default: `HS256`)
- `ACCESS_TOKEN_TTL_SECONDS` (default: `3600`)
- `BOOTSTRAP_TOKEN` (optional; if set, required for `POST /auth/bootstrap`)
