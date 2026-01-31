# PR NOTE — L1-infra-skeleton

## Packs
- SPEC: `docs/packs/SPEC_L1-infra-skeleton.md`
- IMPL: `docs/packs/IMPL_L1-infra-skeleton.md`
- VERIFICATION: `docs/packs/VERIFICATION_L1-infra-skeleton.md`
- QA: `docs/packs/QA_L1-infra-skeleton.md`
- SECURITY: `docs/packs/SECURITY_L1-infra-skeleton.md`

## Summary of changes
Adds a local/dev “infra skeleton” so a developer can run IA-CRM v2 end-to-end without any production deployment work:
- `docker-compose.yml` for `postgres`, `redis`, `api` (FastAPI), and `worker` (Celery).
- Backend `GET /health` endpoint + minimal `pytest` coverage.
- Worker `tasks.ping` to validate async execution via Redis broker/backend.
- Frontend (Vite + React + TS + Tailwind) with a minimal landing page and health check fetch.
- Dev ergonomics: `.env.example`, `./scripts/verify.sh`, and GitHub Actions CI for backend tests + frontend typecheck/build.

## Verification summary
Verification is defined in `docs/packs/VERIFICATION_L1-infra-skeleton.md` and reviewed in `docs/packs/QA_L1-infra-skeleton.md`.

Highlights:
- `./scripts/verify.sh` (PASS)
- `RUN_DOCKER_SMOKE=1 ./scripts/verify.sh` (PASS; Docker smoke skipped when Docker daemon is unavailable)

Notes:
- Backend/frontend dependency-based checks may be skipped in environments without network access (see QA notes).

## Release checklist
- [ ] Packs present for this lot: SPEC/IMPL/VERIFICATION/QA/SECURITY
- [ ] CI is green on PR (backend `pytest` + frontend `typecheck`/`build`)
- [ ] `./scripts/verify.sh` passes locally (or skips are justified)
- [ ] `docker compose up --build` starts cleanly on a dev machine with Docker Desktop / Compose v2
- [ ] `/health` returns `{"status":"ok"}` and `tasks.ping` returns `pong` in a normal Docker-enabled environment

## Rollback summary
If this skeleton introduces friction, revert the PR to remove:
- `docker-compose.yml`
- `backend/` and `frontend/` skeletons
- `.github/workflows/ci.yml`
- `.env.example`
- `scripts/verify.sh` and related CI scripts
