#!/usr/bin/env bash
set -euo pipefail

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

