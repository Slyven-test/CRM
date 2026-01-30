# PR NOTE — L0-foundations

## Packs
- SPEC: `docs/packs/SPEC_L0-foundations.md`
- IMPL: `docs/packs/IMPL_L0-foundations.md`
- VERIFICATION: `docs/packs/VERIFICATION_L0-foundations.md`
- QA: `docs/packs/QA_L0-foundations.md`
- SECURITY: `docs/packs/SECURITY_L0-foundations.md`

## Summary of changes
Establishes repo “delivery foundations”:
- Standard pack templates and naming convention for SPEC/IMPL/VERIFICATION packs.
- PR template requiring pack links + verification checklist.
- CI “packs” gate that fails PRs missing the required packs.
- Local pack-check script used by CI and optionally by local verification.
- Minimal workflow documentation updates.

## Verification summary
Local verification is documented in `docs/packs/VERIFICATION_L0-foundations.md` and reviewed in `docs/packs/QA_L0-foundations.md`.

Highlights:
- `bash -n scripts/ci/check_packs.sh`
- `./scripts/verify.sh`
- Behavior checks against a temporary git repo under `/tmp` for PASS/FAIL scenarios.

Notes:
- Some checks are environment-dependent (e.g., `pytest`/`npm install`) and may be skipped in minimal dev containers; see QA notes.

## Release checklist
- [ ] Packs present for this lot: SPEC/IMPL/VERIFICATION/QA/SECURITY
- [ ] CI “packs” gate is green on PR
- [ ] PR template updated and renders correctly in GitHub PR UI
- [ ] Local `./scripts/verify.sh` passes (or skips are justified)
- [ ] Docs updated (README/workflow section) and accurate

## Rollback summary
If this causes friction or CI churn, revert:
- `.github/workflows/ci.yml` (remove the “packs” job)
- `.github/pull_request_template.md`
- `docs/packs/*_PACK_TEMPLATE.md`
- `scripts/ci/check_packs.sh`
- `scripts/verify.sh`
- Any workflow documentation changes (e.g., `README.md`)
