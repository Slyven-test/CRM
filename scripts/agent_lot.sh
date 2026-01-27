#!/usr/bin/env bash
set -euo pipefail

LOT_ID="${1:-}"
GOAL="${2:-}"

if [[ -z "$LOT_ID" || -z "$GOAL" ]]; then
  echo "Usage: $0 <LOT_ID> <GOAL>"
  exit 1
fi

# 0) Orchestrator hint (optional but useful to ensure scope)
# codex exec --profile spec "Use skill orchestrate. Ensure BACKLOG reflects this lot: ${LOT_ID}."

# 1) SPEC
codex exec --profile spec \
  "Use skill spec-pack. LOT_ID=$LOT_ID. Goal: $GOAL"

# 2) BUILD
codex exec --profile build --full-auto \
  "Use skill build-lot. LOT_ID=$LOT_ID. Implement from docs/packs/SPEC_${LOT_ID}.md"

# 3) SECURITY
codex exec --profile qa \
  "Use skill security-review. LOT_ID=$LOT_ID. Review security/isolation for this lot."

# 4) QA
codex exec --profile qa \
  "Use skill qa-review. LOT_ID=$LOT_ID. Review current branch changes vs SPEC."

# 5) RELEASE PR doc
codex exec --profile spec \
  "Use skill release-pr. LOT_ID=$LOT_ID. Create PR doc linking packs."
