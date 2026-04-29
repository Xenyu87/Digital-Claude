# Structure Memory Template

Use this template to create `AI_STRUCTURE.md` when a project has enough app structure that repeated rediscovery wastes tokens.

Keep it short. It is a routing map, not documentation for every file.

```markdown
# AI Structure Memory

Last updated: YYYY-MM-DD

## Map

- Frontend routes:
- Shared UI:
- Feature modules:
- State/client data:
- API routes/server actions:
- Backend services:
- Database/schema:
- Auth/security:
- Config/env:
- Tests:

## Key Flows

- [Flow]: UI -> API/action -> service/data -> UI state

## Invariants

- [Architecture, auth, data, or API rule that must stay true]

## Read First

- UI task:
- Backend/API task:
- Data task:
- Auth/security task:
- Test/debug task:

## Staleness Notes

- Update when routes, module ownership, key flows, or invariants change.
- Trust code over this file when they disagree.
- Remove obsolete paths instead of keeping historical clutter.
```

Good memory entries are concrete:

- `src/app/dashboard/page.tsx`: dashboard entry route.
- `src/components/ui/*`: shared primitives.
- `src/server/projects/*`: project commands and queries.

Bad memory entries are vague:

- `src` contains the app.
- Components are in many places.
- Backend is somewhere in server files.

