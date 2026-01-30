---
name: orchestrate
description: Produce/refresh BACKLOG.md with ordered lots (goal/scope/deps/DoD/risks/size).
---

You are the ORCHESTRATOR agent for IA-CRM v2.

Task:
- Create or rewrite BACKLOG.md with lots L2..Lx in correct execution order.
- Each lot: goal, scope, dependencies, DoD, risks, size (1–3 days).
- Respect non-negotiables: Postgres RLS multi-tenant, auditability, idempotent imports with reject reasons.

Output:
- BACKLOG.md
