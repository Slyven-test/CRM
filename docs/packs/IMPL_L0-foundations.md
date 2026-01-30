# IMPL PACK — L0-foundations

## Summary
Established delivery foundations: standardized pack templates, PR template, and CI gates that require packs on pull requests.

## DB changes (migrations, indexes, RLS)
N/A

## Backend changes
N/A (application).

Repo automation:
- Added `scripts/ci/check_packs.sh` to enforce that PR diffs include `SPEC_*.md`, `IMPL_*.md`, and `VERIFICATION_*.md` under `docs/packs/`.
- When exactly one `SPEC_<LOT_ID>.md` is changed, the script requires matching `IMPL_<LOT_ID>.md` and `VERIFICATION_<LOT_ID>.md` in the diff.

## Frontend changes
N/A

## Observability (logs/metrics/traces)
`scripts/ci/check_packs.sh` prints actionable failure messages (missing pack types and expected filenames) and lists the changed files on failure.

## Security notes (RLS/RBAC/anti-leak/secrets)
- Pack-check job uses only git history from the CI checkout; no secrets or GitHub API calls required.
- Pack templates include explicit sections for RLS/RBAC/security to keep tenant isolation requirements front-and-center for future lots.

## Verification notes
- Local: `./scripts/ci/check_packs.sh origin/main`
- CI: “packs” job runs `./scripts/ci/check_packs.sh "origin/${GITHUB_BASE_REF}"`
- Local full suite: `./scripts/verify.sh` (pack check runs when base ref exists; set `SKIP_PACKS=1` to skip)

## Rollback plan
Revert changes to:
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `docs/packs/*_PACK_TEMPLATE.md`
- `scripts/ci/check_packs.sh`
- `scripts/verify.sh`
- `README.md`
