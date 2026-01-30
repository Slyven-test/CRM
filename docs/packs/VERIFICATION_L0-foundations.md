# VERIFICATION PACK — L0-foundations

## Commands executed
In repo:
- `bash -n scripts/ci/check_packs.sh`

Pack-check behavior (temporary repo under `/tmp`):
- `rm -rf /tmp/check-packs-test && mkdir -p /tmp/check-packs-test`
- `cd /tmp/check-packs-test && git init && git commit --allow-empty -m "base"` (plus test commits)
- `bash /opt/ia-crm-v2/scripts/ci/check_packs.sh <base-sha>` for each scenario (outputs captured below)

## Expected outputs
- Code change without packs exits non-zero and prints missing pack types + expected filenames.
- Single `SPEC_<LOT_ID>.md` without matching `IMPL_`/`VERIFICATION_` exits non-zero and prints expected matching filenames.
- Code change with matching `SPEC_`/`IMPL_`/`VERIFICATION_` prints `Packs check: PASS` and exits 0.

Observed results (from `/tmp/check-packs-test`, base `27bb8ad3d36cc3e0320eb1d9145e3242b141ee39`):
- Code change without packs: exit `1`; output includes `FAIL: missing SPEC pack...` and lists `backend/foo.txt`
- Code change with matching packs: exit `0`; output starts with `Packs check: PASS`
- Spec-only change: exit `1`; output includes `FAIL: SPEC_L98-demo.md changed, but matching IMPL pack is missing.`

## RLS / RBAC / security checks
N/A (no application data changes). Verified that the pack-check script relies only on local git data (no secrets / no API calls).

## Result (PASS/FAIL + CI link)
PASS (local). CI: N/A for this workspace run.
