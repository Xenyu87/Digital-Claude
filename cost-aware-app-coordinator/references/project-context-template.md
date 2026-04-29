# Project Context Template

Use this template when a project lacks a lightweight AI context system. Adapt it to the project; do not copy sections that are not relevant.

## AGENTS.md

```markdown
# Agent Instructions

## Project Context

Read `AI_CONTEXT.md` before non-trivial changes. Read `AI_STRUCTURE.md` when the task needs app layout. These files are indexes, not full project dumps.

## Doc Reading Protocol

1. Read `AI_CONTEXT.md`.
2. Read `AI_STRUCTURE.md` if route/module/data-flow orientation matters.
3. Open only docs linked to the current task.
4. Read code only after the relevant docs identify likely files.
5. Update docs when architecture, APIs, data shapes, setup, deploy, workflows, or structure memory change.

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
| app layout/routes/modules | AI_STRUCTURE.md |
| UI/components/layout | docs/ai/ui.md |
| full-stack workflow contracts | docs/ai/app-contract.md |
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

Update the relevant doc when changing architecture, APIs, data shapes, setup, deploy, or workflows.
```

## AI_STRUCTURE.md

Use this only when the project has enough structure to make repeated rediscovery wasteful.

```markdown
# AI Structure Memory

Last updated: YYYY-MM-DD

## Map

- Frontend routes:
- Shared UI:
- State/client data:
- API/server actions:
- Backend services:
- Database/schema:
- Auth/security:
- Config/env:
- Tests:

## Key Flows

- [Flow name]: UI -> API/action -> data/service -> result state

## Invariants

- [Rule that should stay true]

## Read First

- UI task:
- Backend task:
- Data task:
- Auth/security task:

## Staleness Notes

- Update this file when routes, module ownership, key flows, or invariants change.
- Trust code over this memory if they disagree.
```

## docs/ai Guidance

Create only the docs that the project needs. Keep each file short and navigational.

Suggested files:

- `docs/ai/app-contract.md`
- `docs/ai/ui.md`
- `docs/ai/data-model.md`
- `docs/ai/api.md`
- `docs/ai/auth-security.md`
- `docs/ai/deploy.md`

Prefer one `docs/ai/app-contract.md` for small full-stack apps. Split into area docs only when the contract becomes too dense.

Avoid documenting every file. Document decisions, contracts, invariants, and where to look next.

## docs/ai/app-contract.md

```markdown
# App Contract

## First Usable Slice

- User:
- Main workflow:
- Entry route/screen:
- Primary action:
- Backend operation:
- Persisted state:
- Success state:
- Empty/loading/error states:

## Frontend

- Routes:
- Key components:
- Forms and validation display:
- Loading/empty/error/success behavior:
- Responsive requirements:
- Accessibility notes:

## Backend

- Endpoint/server action/job:
- Request shape:
- Response shape:
- Validation rules:
- Auth/permission rules:
- Persistence behavior:
- Error behavior:

## Data

- Entities:
- Ownership:
- Lifecycle:
- Migration/seed needs:
- Privacy or sensitive fields:

## Verification

- Frontend check:
- Backend check:
- Full-stack smoke path:
- Known risks:
```
