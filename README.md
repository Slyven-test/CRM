# IA-CRM v2

## Local dev (infra skeleton)
### Backend + worker + Postgres + Redis
- `cp .env.example .env` (optional overrides)
- `docker compose up --build`
- API: `http://localhost:8000/health`

### Frontend
- `cd frontend`
- `npm install`
- `npm run dev`
- App: `http://localhost:5173` (default)

## Verification
- `./scripts/verify.sh`

## Configuration
- Compose service ports: `POSTGRES_PORT`, `REDIS_PORT`, `API_PORT`
- API settings: `ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS` (comma-separated)
- Frontend: `VITE_API_BASE_URL` (defaults to `http://localhost:8000`)
