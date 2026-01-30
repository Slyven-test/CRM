# IA-CRM v2 — Agent Rules (L0)

## Golden rules
- Never work directly on production without PR + CI green.
- Small diffs: one logical change per PR.
- Every change must ship with verification (tests / smoke / checks).

## Mandatory workflow
- Feature branches only.
- PR required + CI required.
- Each PR must include:
  1) SPEC PACK
  2) IMPL PACK
  3) VERIFICATION PACK

## Non-negotiables
- Multi-tenant isolation via Postgres RLS.
- All business data editable from web UI (CRUD) with audit log.
- Any import must be idempotent with reject reasons.

## Definition of Done
API + UI + RBAC + audit + tests + docs updated.
