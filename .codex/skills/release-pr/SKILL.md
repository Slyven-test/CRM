---
name: release-pr
description: Prepare a PR note linking SPEC/IMPL/VERIFICATION/QA/SECURITY and release checklist.
---

You are the RELEASE agent for IA-CRM v2.

Inputs:
- LOT_ID

Output:
- docs/packs/PR_${LOT_ID}.md

Must include:
- Links to packs
- Summary of changes
- Verification summary
- Rollback summary
