# SPEC PACK — L1-infra-skeleton

## Goal
Stand up a runnable local/dev “infra skeleton” for IA-CRM v2 with:
- `docker compose up` bringing up Postgres, Redis, API, and Worker
- A minimal FastAPI backend skeleton with a health endpoint and test
- A minimal frontend skeleton with a small design system baseline and build/typecheck in CI
- CI that runs real backend tests and real frontend build

## Scope (in/out)
**In scope**
- `docker-compose.yml` for `postgres`, `redis`, `api`, `worker`
- Backend skeleton (FastAPI) with:
  - `/health` endpoint
  - env-based configuration
  - minimal test suite executed by CI
- Worker skeleton (Celery) that can run alongside the API
- Frontend skeleton (Vite + React + TS) with:
  - base styling/design system primitives (Tailwind baseline + a `Button` component)
  - build + typecheck executed by CI
- Basic developer docs: how to run locally and run checks

**Out of scope**
- Tenant model, RBAC, Postgres RLS policies (planned for L2)
- Any production deployment (K8s/Terraform/etc.)
- Business CRUD screens and audit logs (planned for later lots)

## Data & Rules (entities, validation, RLS/RBAC)
- No business entities in this lot.
- No RLS/RBAC changes in this lot.

## UX Acceptance Criteria (screens, filters/sort/search/export, error states)
- Frontend renders a minimal page that:
  - Shows a title
  - Includes at least one reusable UI primitive (e.g. `Button`)
  - Can call the backend health endpoint (or is prepared to, via an env var base URL)

## APIs (endpoints)
- `GET /health` returns JSON with `status: "ok"`.

## NFR (perf, security, logs)
- API exposes no business endpoints yet.
- All services must be configurable via environment variables (compose `.env`).
- CI must run:
  - `pytest` for backend
  - `npm run typecheck` + `npm run build` for frontend

## Risks & edge cases
- Local port collisions (document default ports and allow overrides).
- API/worker startup ordering: compose should wait on dependencies where possible.
