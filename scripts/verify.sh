#!/usr/bin/env bash
set -euo pipefail

run_docker_smoke="${RUN_DOCKER_SMOKE:-0}"
force_docker_smoke="${FORCE_DOCKER_SMOKE:-0}"
keep_docker="${KEEP_DOCKER:-0}"
started_compose=0

have_docker_compose() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

can_access_docker_daemon() {
  docker info >/dev/null 2>&1
}

python_http_get() {
  local url="$1"
  python -c "import urllib.request; print(urllib.request.urlopen('${url}', timeout=5).read().decode())"
}

if [[ "${SKIP_PACKS:-0}" != "1" && -x ./scripts/ci/check_packs.sh ]]; then
  packs_base_ref="${PACKS_BASE_REF:-origin/main}"
  if git rev-parse --verify "${packs_base_ref}^{commit}" >/dev/null 2>&1; then
    echo "==> Packs check (${packs_base_ref})"
    ./scripts/ci/check_packs.sh "${packs_base_ref}"
  else
    echo "==> Packs check skipped (base ref '${packs_base_ref}' not found; set PACKS_BASE_REF or fetch the base branch)"
  fi
fi

if [[ "${run_docker_smoke}" == "1" ]]; then
  if have_docker_compose; then
    if ! can_access_docker_daemon; then
      echo "==> Docker smoke skipped (cannot access Docker daemon)"
    elif [[ "${force_docker_smoke}" != "1" ]] && [[ -n "$(docker compose ps -q 2>/dev/null || true)" ]]; then
      echo "==> Docker smoke skipped (compose already running; set FORCE_DOCKER_SMOKE=1 to run checks anyway)"
    else
      if [[ -z "$(docker compose ps -q 2>/dev/null || true)" ]]; then
        started_compose=1
        trap 'docker compose down' EXIT
        echo "==> Docker compose up (smoke)"
        docker compose up -d --build
      else
        echo "==> Docker compose reuse (smoke)"
      fi

      api_port="${API_PORT:-8000}"
      echo "==> API health (docker smoke)"
      python_http_get "http://localhost:${api_port}/health" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' || {
        echo "API health check did not return status ok"
        exit 1
      }

      echo "==> Worker ping task (docker smoke)"
      docker compose exec -T api python -c "from app.worker import celery_app; print(celery_app.send_task('tasks.ping').get(timeout=10))" | grep -Eq '^pong$'

      if [[ "${started_compose}" == "1" && "${keep_docker}" == "1" ]]; then
        trap - EXIT
        echo "==> Docker compose left running (KEEP_DOCKER=1)"
      fi
    fi
  else
    echo "==> Docker smoke skipped (docker compose not available)"
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
