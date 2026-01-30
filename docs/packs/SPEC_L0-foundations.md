# SPEC PACK — L0-foundations

## 1) Context & Goal
IA-CRM v2 already has baseline repo rules (`AGENTS.md`), a backlog (`BACKLOG.md`), pack placeholders in `docs/packs/`, and a basic CI workflow (`.github/workflows/ci.yml`) that runs backend tests and frontend typecheck/build.

This lot establishes “delivery foundations” so every change ships with consistent documentation and gates:
- Standardize pack templates (SPEC/IMPL/VERIFICATION) to a single required structure.
- Add a PR template that forces linking the packs and running verification.
- Add CI gates that fail PRs missing the required packs.

Goal: Establish repo rules, pack templates, and CI gates for consistent delivery.

## 2) In-scope / Out-of-scope
**In scope**
- Pack naming convention and required structure:
  - `docs/packs/SPEC_<LOT_ID>.md`
  - `docs/packs/IMPL_<LOT_ID>.md`
  - `docs/packs/VERIFICATION_<LOT_ID>.md`
- Update pack templates in `docs/packs/*_PACK_TEMPLATE.md` to match the required structure and include placeholders for RLS/RBAC, rollback, and verification commands.
- Add `.github/pull_request_template.md` that requires:
  - Links to the three packs for the lot
  - A checklist aligned to Definition of Done (API/UI/RBAC/audit/tests/docs as applicable)
  - Verification commands executed (or explicitly marked N/A with justification)
- Add CI “delivery gates”:
  - A job that verifies PRs include the required packs (see “Verification” for exact behavior)
  - Keep existing backend/frontend CI jobs intact
- Add a repo-local script used by CI (and optionally by `./scripts/verify.sh`) to validate pack presence and basic consistency.
- Minimal docs update (README or `docs/`) explaining the workflow and where packs live.

**Out of scope**
- Any business features, DB schema changes, tenant/RBAC/RLS implementation (planned for L2+).
- Adding/mandating additional linters/formatters beyond what exists today (can be a later lot if desired).
- Release automation, deployments, or environments beyond current CI.

## 3) Data model (tables, columns, indexes, RLS policies, migrations strategy)
No data model changes in this lot.
- Tables/columns/indexes: N/A
- RLS policies: N/A
- Migrations: N/A

## 4) Backend (routes, schemas, services, errors)
No application backend changes. “Backend” scope in this lot is repo automation:
- Add a script (e.g. `scripts/ci/check_packs.sh` or `scripts/ci/check_packs.py`) that:
  - Detects changed files in a PR (via git diff against the PR base)
  - Enforces presence of all three pack types in the PR changes:
    - at least one `docs/packs/SPEC_*.md`
    - at least one `docs/packs/IMPL_*.md`
    - at least one `docs/packs/VERIFICATION_*.md`
  - Optionally enforces LOT consistency when possible (preferred):
    - if exactly one `SPEC_<LOT_ID>` is changed, require the matching `IMPL_<LOT_ID>` and `VERIFICATION_<LOT_ID>` are also changed
  - Prints actionable failure messages (missing file(s), expected filenames, how to fix).
- Recommended implementation detail (keeps it GitHub-API-free):
  - In CI, check out with full history (`fetch-depth: 0`) or fetch the PR base ref.
  - Compute changed files with `git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD"`.
  - Run the script with an explicit base ref, e.g. `./scripts/ci/check_packs.sh "origin/${GITHUB_BASE_REF}"`.
- Update `.github/workflows/ci.yml` to run the pack check job on `pull_request`.
- Optional: call the pack check from `./scripts/verify.sh` so local verification matches CI.

Error behavior:
- Non-zero exit code on failure with clear output including expected filenames.

## 5) Frontend (pages, components, states: loading/empty/error, tables with sort/filter/search/pagination)
No frontend product/UI changes.

Frontend-related scope is only process/docs:
- PR template includes a reminder to attach UI screenshots/video when the PR changes UI.

## 6) Security (RLS/RBAC, anti-leak checks, secrets)
No RLS/RBAC changes in this lot.

Security requirements for the delivery gates:
- The pack-check job must not require elevated secrets; it should rely only on git history available in the checkout.
- Ensure no accidental token logging (if GitHub API is used, avoid echoing tokens; prefer purely git-based checks).
- Keep multi-tenant isolation as a non-negotiable documented rule (already in `AGENTS.md`), and ensure templates include explicit RLS/RBAC sections for later lots.

## 7) DoD / Acceptance criteria
- `docs/packs/SPEC_PACK_TEMPLATE.md` matches the required SPEC structure:
  1) Context & Goal
  2) In-scope / Out-of-scope
  3) Data model (tables, columns, indexes, RLS policies, migrations strategy)
  4) Backend (routes, schemas, services, errors)
  5) Frontend (pages, components, states: loading/empty/error, tables with sort/filter/search/pagination)
  6) Security (RLS/RBAC, anti-leak checks, secrets)
  7) DoD / Acceptance criteria
  8) Verification (exact commands)
  9) Rollback plan
- `docs/packs/IMPL_PACK_TEMPLATE.md` and `docs/packs/VERIFICATION_PACK_TEMPLATE.md` are updated to mirror the workflow and explicitly include rollback + verification + RLS/RBAC considerations.
- `.github/pull_request_template.md` exists and includes:
  - Pack links (SPEC/IMPL/VERIFICATION)
  - A verification checklist and a place to paste command output / CI links
- CI adds a “packs” (or similarly named) job that runs on PRs and fails if the required packs are missing from the PR changes.
- `./scripts/verify.sh` (or a new dedicated script) includes a way to run the pack check locally.
- Documentation explains the expected pack filenames and where they live.

## 8) Verification (exact commands)
Local (developer):
- `./scripts/verify.sh`
- `./scripts/ci/check_packs.sh origin/main` (if introduced; requires the base ref to exist locally)

CI:
- “packs” job runs something equivalent to:
  - `git fetch origin "${GITHUB_BASE_REF}" --depth=1`
  - `./scripts/ci/check_packs.sh "origin/${GITHUB_BASE_REF}"`
- Open a PR that changes code but does not add/update all three packs → CI “packs” job FAILS.
- Open a PR that changes code and adds/updates:
  - `docs/packs/SPEC_<LOT_ID>.md`
  - `docs/packs/IMPL_<LOT_ID>.md`
  - `docs/packs/VERIFICATION_<LOT_ID>.md`
  → CI “packs” job PASSES.

## 9) Rollback plan
- Revert changes to:
  - `.github/workflows/ci.yml`
  - `.github/pull_request_template.md`
  - `docs/packs/*_PACK_TEMPLATE.md`
  - any new scripts added under `scripts/`
- Removing the “packs” CI job restores the prior CI behavior (backend/frontend checks only).
