#!/usr/bin/env bash
set -euo pipefail

if [[ "${SKIP_PACKS:-0}" != "1" && -x ./scripts/ci/check_packs.sh ]]; then
  packs_base_ref="${PACKS_BASE_REF:-origin/main}"
  if git rev-parse --verify "${packs_base_ref}^{commit}" >/dev/null 2>&1; then
    echo "==> Packs check (${packs_base_ref})"
    ./scripts/ci/check_packs.sh "${packs_base_ref}"
  else
    echo "==> Packs check skipped (base ref '${packs_base_ref}' not found; set PACKS_BASE_REF or fetch the base branch)"
  fi
fi

echo "==> Python syntax check"
python -m compileall backend/app backend/tests

if command -v pytest >/dev/null 2>&1; then
  echo "==> Backend tests"
  (cd backend && pytest)
else
  echo "==> Backend tests skipped (pytest not installed)"
fi

if command -v npm >/dev/null 2>&1; then
  if [[ -d frontend/node_modules ]]; then
    echo "==> Frontend typecheck"
    (cd frontend && npm run typecheck)
    echo "==> Frontend build"
    (cd frontend && npm run build)
  else
    echo "==> Frontend checks skipped (run 'cd frontend && npm install' first)"
  fi
else
  echo "==> Frontend checks skipped (npm not installed)"
fi
