# SECURITY REVIEW — L0-foundations

Date: 2026-01-30

## Scope
LOT `L0-foundations` is delivery-process automation (packs/templates/CI gates). No application schema, tenant model, RBAC, or RLS is introduced in this lot. Primary review focus is isolation assumptions, CI/script safety, and secret leakage risk.

References:
- `docs/packs/SPEC_L0-foundations.md`
- `docs/packs/IMPL_L0-foundations.md`
- `docs/packs/VERIFICATION_L0-foundations.md`

## 1) DB / RLS tenant isolation
- No Postgres schema or migrations in this lot.
- No RLS policies added/changed.
- No tenant context plumbing (e.g., `SET app.tenant_id`) added/changed.

Result: **N/A for this lot** (no DB business-data surface area introduced).

## 2) API authz / data filtering
- No new API routes beyond the existing skeleton; no authorization changes in this lot.
- CI “packs” job and pack-check script operate only on git diff metadata (filenames), not on application data.

Result: **N/A for this lot** (no authz/data access paths introduced).

## 3) CI & scripts: safety review
Reviewed:
- `scripts/ci/check_packs.sh`
- `.github/workflows/ci.yml`
- `scripts/verify.sh`
- `.github/pull_request_template.md`

Findings:
- `scripts/ci/check_packs.sh` uses `set -euo pipefail` and computes changed files via `git diff --name-only <base>...HEAD`; no network calls, no GitHub API usage, no secret env var reads, and no `set -x` tracing.
- The CI `packs` job uses `actions/checkout@v4` with `fetch-depth: 0` and a plain `git fetch` of the base ref, then runs the local script. No secrets are required for the job beyond default checkout behavior.
- `scripts/verify.sh` runs the pack check only when a base ref exists locally (or can be provided via `PACKS_BASE_REF`) and supports skipping via `SKIP_PACKS=1`; it doesn’t print or require secrets.

Risk notes (low):
- GitHub Actions are referenced by version tags (e.g., `actions/checkout@v4`) rather than pinned commit SHAs; if supply-chain hardening is desired, pin to SHAs (future lot).
- Local dev defaults include `postgres/postgres` in `docker-compose.yml`/`backend/app/settings.py`; fine for local, but production should require explicit secrets/config (future lots).

## 4) Secrets / anti-leak checks
Checked repo for common secret patterns (keys/tokens) and disallowed filenames; no committed `.env` files or key material detected.

Existing guardrails:
- `scripts/check_policy.sh` blocks `.env` (except `.env.example`) and common private-key filenames in diffs; good defense-in-depth for PR hygiene.

## Result
**PASS** for `L0-foundations` (process-only changes; no RLS/RBAC introduced; CI automation does not require or leak secrets).

## Follow-ups (not required for this lot)
- Consider pinning GitHub Actions to commit SHAs and pinning Docker images by digest for stronger supply-chain controls.
- Add CI enforcement for `scripts/check_policy.sh` (or equivalent) if the repo wants an automated “no secrets in diff” gate.
