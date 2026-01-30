#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOT_ID="${1:-}"
GOAL="${2:-}"

if [[ -z "$LOT_ID" || -z "$GOAL" ]]; then
  echo "Usage: $0 <LOT_ID> <GOAL>"
  exit 1
fi

# IMPORTANT: si OPENAI_API_KEY existe (même invalide), ça peut casser l'auth Codex
unset OPENAI_API_KEY || true

# SPEC (read-only)
codex -C "$ROOT" -p spec -a never -s read-only exec \
  "Use skill spec-pack. LOT_ID=$LOT_ID. Goal: $GOAL"

# BUILD (workspace-write)
codex -C "$ROOT" -p build -a never -s workspace-write exec \
  "Use skill build-lot. LOT_ID=$LOT_ID. Implement from docs/packs/SPEC_${LOT_ID}.md"

# SECURITY (read-only)
codex -C "$ROOT" -p qa -a never -s read-only exec \
  "Use skill security-review. LOT_ID=$LOT_ID. Review security/isolation for this lot."

# QA (read-only) — garde ce bloc seulement si le skill qa-review existe
codex -C "$ROOT" -p qa -a never -s read-only exec \
  "Use skill qa-review. LOT_ID=$LOT_ID. Review current branch changes vs SPEC."
