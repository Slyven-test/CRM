# PR: <title>

## Packs (required)
- SPEC: `docs/packs/SPEC_<LOT_ID>.md`
- IMPL: `docs/packs/IMPL_<LOT_ID>.md`
- VERIFICATION: `docs/packs/VERIFICATION_<LOT_ID>.md`

## Checklist (as applicable)
- [ ] API implemented/updated
- [ ] UI implemented/updated (attach screenshots/video if UI changed)
- [ ] RBAC updated (deny-by-default; least privilege)
- [ ] Postgres RLS enforced for business data (multi-tenant isolation)
- [ ] Audit log updated for all business data edits
- [ ] Tests added/updated (unit/integration/e2e as applicable)
- [ ] Docs updated (README / docs / packs)

## Verification
Paste commands executed and results (or mark N/A with justification).

```
# commands:
./scripts/verify.sh
```

## Risk / rollout
- Risk level:
- Rollback plan (link to IMPL pack section):
