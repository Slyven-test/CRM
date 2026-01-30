#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOT_ID="${1:-}"
GOAL="${2:-}"

if [[ -z "$LOT_ID" || -z "$GOAL" ]]; then
  echo "Usage: $0 <LOT_ID> <GOAL>"
  exit 1
fi

# IMPORTANT: évite que OPENAI_API_KEY (même invalide) casse l'auth ChatGPT
unset OPENAI_API_KEY || true

mkdir -p "$ROOT/docs/packs"

# 1) SPEC
codex exec -C "$ROOT" --full-auto \
  "Use skill spec-pack. LOT_ID=$LOT_ID. Goal: $GOAL"

# 2) BUILD
codex exec -C "$ROOT" --full-auto \
  "Use skill build-lot. LOT_ID=$LOT_ID. Implement from docs/packs/SPEC_${LOT_ID}.md"

# 3) SECURITY
codex exec -C "$ROOT" --full-auto \
  "Use skill security-review. LOT_ID=$LOT_ID."

# 4) QA
codex exec -C "$ROOT" --full-auto \
  "Use skill qa-review. LOT_ID=$LOT_ID."

# 5) RELEASE NOTE
codex exec -C "$ROOT" --full-auto \
  "Use skill release-pr. LOT_ID=$LOT_ID."
