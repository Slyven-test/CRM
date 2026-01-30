#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

unset OPENAI_API_KEY CODEX_API_KEY || true

ts="$(date +%F_%H%M%S)"
LOGDIR="$ROOT/runlogs/$ts"
mkdir -p "$LOGDIR"

# Auth sanity check (fail fast)
codex exec -C "$ROOT" "Say OK" >/dev/null

# Parse BACKLOG.md: "## Lx-..." + "- Goal: ..."
mapfile -t entries < <(awk '
  { sub(/\r$/, "", $0) }
  /^##[[:space:]]*L[0-9]+-/{ sub(/^##[[:space:]]*/, "", $0); lot=$0; active=1; next }
  active && /^[[:space:]]*-[[:space:]]*Goal:/{ sub(/^[[:space:]]*-[[:space:]]*Goal:[[:space:]]*/, "", $0); goal=$0; printf "%s\t%s\n", lot, goal; active=0 }
' BACKLOG.md)

if [[ ${#entries[@]} -eq 0 ]]; then
  {
    echo "Found lots: 0"
    echo "Expected format example:"
    echo "## L2-something"
    echo "- Goal: ..."
    echo
    echo "BACKLOG head:"
    head -n 80 BACKLOG.md
  } | tee "$LOGDIR/_error.txt"
  exit 1
fi

printf "%s\n" "${entries[@]}" > "$LOGDIR/_lots.txt"
SUMMARY="$LOGDIR/_summary.tsv"
echo -e "lot\tstatus\texit_code" > "$SUMMARY"

for entry in "${entries[@]}"; do
  LOT_ID="${entry%%$'\t'*}"
  GOAL="${entry#*$'\t'}"
  LOG="$LOGDIR/${LOT_ID}.log"

  {
    echo "==== RUN $LOT_ID ===="
    echo "Goal: $GOAL"
    echo "Time: $(date -Is)"
    echo

    git fetch origin --prune || true
    git switch -C "lot/$LOT_ID" main

    set +e
    ./scripts/agent_lot.sh "$LOT_ID" "$GOAL"
    rc=$?
    set -e

    git add -A
    git commit -m "$LOT_ID: implement" || echo "No changes to commit for $LOT_ID"
    git push -u origin "lot/$LOT_ID" --force-with-lease || echo "WARN: push failed for $LOT_ID"

    echo
    echo "==== END $LOT_ID (rc=$rc) ===="
    echo "Time: $(date -Is)"
  } |& tee -a "$LOG"

  if [[ $rc -eq 0 ]]; then
    echo -e "${LOT_ID}\tPASS\t0" >> "$SUMMARY"
  else
    echo -e "${LOT_ID}\tFAIL\t${rc}" >> "$SUMMARY"
  fi
done

echo "DONE. Logs: $LOGDIR"
echo "Summary: $SUMMARY"
