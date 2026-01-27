#!/usr/bin/env bash
set -euo pipefail

LOT_ID="${1:-}"
GOAL="${2:-}"

if [[ -z "$LOT_ID" || -z "$GOAL" ]]; then
  echo "Usage: $0 <LOT_ID> <GOAL>"
  exit 1
fi

# Avoid Codex mistakenly using a broken API key from environment
unset OPENAI_API_KEY

# 1) SPEC
codex exec --profile spec \
  "Use skill spec-pack. LOT_ID=${LOT_ID}. Goal: ${GOAL}"

# 2) BUILD (no approvals, workspace-write)
codex exec --profile build \
  "Use skill build-lot. LOT_ID=${LOT_ID}. Implement strictly from docs/packs/SPEC_${LOT_ID}.md"

# 3) SECURITY
codex exec --profile qa \
  "Use skill security-review. LOT_ID=${LOT_ID}. Audit security/isolation and write docs/packs/SECURITY_${LOT_ID}.md"

# 4) QA
codex exec --profile qa \
  "Use skill qa-review. LOT_ID=${LOT_ID}. Check SPEC compliance + tests + UX requirements. Write docs/packs/QA_${LOT_ID}.md"

# 5) RELEASE PR PACK
codex exec --profile release \
  "Use skill release-pr. LOT_ID=${LOT_ID}. Create docs/packs/PR_${LOT_ID}.md"
