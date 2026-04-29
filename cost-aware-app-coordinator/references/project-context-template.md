# Project Context Template

Use this template when a project lacks a lightweight AI context system. Adapt it to the project; do not copy sections that are not relevant.

## AGENTS.md

```markdown
# Agent Instructions

## Project Context

Read `AI_CONTEXT.md` before non-trivial changes. It is an index, not a full project dump.

## Doc Reading Protocol

1. Read `AI_CONTEXT.md`.
2. Open only docs linked to the current task.
3. Read code only after the relevant docs identify likely files.
4. Update docs when architecture, APIs, data shapes, setup, deploy, or workflows change.

## Working Rules

- Prefer small, focused changes.
- Do not rewrite unrelated code.
- Ask before destructive or irreversible actions.
- Keep explanations practical and clear.
```

## AI_CONTEXT.md

```markdown
# AI Context - Index

## Goal

[One short paragraph: what the app does, for whom, and why.]

## Stack

[Framework, language, database, auth, deploy target, major services.]

## Routing Table

| If the task touches... | Read... |
| --- | --- |
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

## Pending Work

- [ ] ...

## Documentation Maintenance

Update the relevant doc when changing architecture, APIs, data shapes, setup, deploy, or workflows.
```

## docs/ai Guidance

Create only the docs that the project needs. Keep each file short and navigational.

Suggested files:

- `docs/ai/ui.md`
- `docs/ai/data-model.md`
- `docs/ai/api.md`
- `docs/ai/auth-security.md`
- `docs/ai/deploy.md`

Avoid documenting every file. Document decisions, contracts, invariants, and where to look next.
