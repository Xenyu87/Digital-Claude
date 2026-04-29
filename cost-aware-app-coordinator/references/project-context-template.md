# Project Context Template

Use this when a project lacks lightweight AI context. Adapt it; do not copy irrelevant sections.

## AGENTS.md

```markdown
# Agent Instructions

Read `AI_CONTEXT.md` before non-trivial changes. Read `AI_STRUCTURE.md` when route, module, or data-flow orientation matters. Read `AI_DECISIONS.md` when architecture, stack, auth, data, design, deployment, cost, or past tradeoffs matter. Read `AI_AGENT_LOG.md` only when similar mistakes or token waste may repeat.

Working rules:

- Prefer small, focused changes.
- Do not rewrite unrelated code.
- Ask before destructive or irreversible actions.
- Update docs when architecture, APIs, data shapes, setup, deploy, workflows, or structure memory change.
```

## AI_CONTEXT.md

```markdown
# AI Context - Index

## Goal

[What the app does, for whom, and why.]

## Stack

[Framework, language, database, auth, deploy target, major services.]

## Routing Table

| If the task touches... | Read... |
| --- | --- |
| app layout/routes/modules | AI_STRUCTURE.md |
| durable decisions/tradeoffs | AI_DECISIONS.md |
| repeated agent mistakes/token waste | AI_AGENT_LOG.md |
| full-stack workflow contracts | docs/ai/app-contract.md |
| UI/components/layout | docs/ai/ui.md |
| data model/database/types | docs/ai/data-model.md |
| API/routes/contracts | docs/ai/api.md |
| auth/security/permissions | docs/ai/auth-security.md |
| deploy/env/runtime | docs/ai/deploy.md |

## Current Decisions

- Language:
- Theme/design:
- Auth:
- Database:
- Deploy:
- Privacy constraints:

## First Usable Slice

- User:
- Main workflow:
- Frontend entry point:
- Backend/data operation:
- Success state:
- Empty/loading/error states:
- Verification path:

## Pending Work

- [ ] ...

## Documentation Maintenance

Update the relevant doc when architecture, APIs, data shapes, setup, deploy, workflows, or structure memory change.
```

## AI_STRUCTURE.md

Use `references/structure-memory-template.md` as the source template. Create it only when repeated structure discovery is wasting time or tokens.

## AI_DECISIONS.md

Use `references/second-brain-template.md` as the source template. Create it when decisions, rejected options, constraints, or revisit triggers would prevent future rework.

## AI_AGENT_LOG.md

Use `references/agent-autolog-template.md` as the source template. Create it only after a real mistake, repeated correction, or measurable token waste.

## docs/ai Guidance

Create only docs the project needs. Keep each file short and navigational.

Suggested files:

- `docs/ai/app-contract.md`
- `docs/ai/ui.md`
- `docs/ai/data-model.md`
- `docs/ai/api.md`
- `docs/ai/auth-security.md`
- `docs/ai/deploy.md`

Prefer one `docs/ai/app-contract.md` for small full-stack apps. Split into area docs only when the contract becomes too dense.

Use `references/app-creation-blueprint.md` as the source template for `docs/ai/app-contract.md`.
