# App Creation Blueprint

Use this reference for new apps, full-stack features, or rebuilds where frontend and backend need to agree.

## First Usable Slice

Define the smallest workflow that feels real:

- target user and job to be done;
- entry route or screen;
- primary action;
- backend operation or persisted state;
- success result;
- empty, loading, and error states;
- one verification path.

Avoid building detached pages, generic dashboards, or placeholder flows before the first usable slice works.

## Frontend Contract

Capture only what affects implementation:

- routes and screen ownership;
- component boundaries;
- shared UI primitives or design system;
- responsive behavior for mobile and desktop;
- form states, validation display, loading, empty, error, and success states;
- accessibility basics: labels, focus, keyboard access, contrast;
- user-facing copy that must match backend states.

Frontend checks should match risk: component or smoke checks for narrow UI work, visual/manual checks for layout-heavy work, and end-to-end checks when the UI depends on backend behavior.

## Backend Contract

Capture the behavior the UI and tests can rely on:

- endpoint, server action, command, or job name;
- request and response shape;
- validation rules;
- auth and permission rules;
- persistence model and transaction boundaries;
- idempotency or retry behavior when relevant;
- error codes and user-safe messages;
- logging or observability expectations for important failures.

Backend checks should cover validation, auth, data changes, and failure modes before broad refactors.

## Backend Contract Gate

Before implementing medium/high-risk backend, API, RPC, server action, job, or integration work, define:

- caller: which UI, job, command, or external service uses it;
- input/output: required fields, optional fields, and user-safe error shape;
- permission: who may read/write and where enforcement happens;
- data effect: create/update/delete/archive, transaction boundary, and idempotency;
- compatibility: existing callers, existing data, migration or rollback needs;
- verification: one success path, one invalid input, one permission/failure path.

If any item is unknown and changes behavior or risk, ask before editing.

## Data And Security

Before implementing persistence, identify:

- entities and ownership;
- lifecycle: create, read, update, delete, archive;
- migrations and seed data;
- privacy constraints and sensitive fields;
- destructive operations and rollback expectations;
- rate limits, abuse cases, and audit needs when relevant.

Use stronger model policy and broader review for auth, payments, privacy, migrations, or destructive operations.

## Full-Stack Verification

For any workflow crossing frontend and backend, verify at least:

- the UI sends the expected data;
- the backend validates and persists or rejects it correctly;
- the UI shows loading, success, and error states;
- permissions are enforced server-side;
- a refreshed page or repeated action behaves correctly.

Prefer one high-signal end-to-end path over many shallow checks when budget is limited.

## Delivery Slices

When building in steps, prefer this order:

1. Contract: define the first usable slice and frontend/backend/data shapes.
2. Skeleton: create routes, screens, API/server actions, and data placeholders with clear boundaries.
3. Happy path: make the main workflow work end to end.
4. States: add loading, empty, validation, error, and success states.
5. Hardening: add auth, permissions, persistence edge cases, and targeted tests.
6. Polish: refine responsive layout, accessibility, copy, and performance.

Do not polish a screen whose backend contract is still unknown, and do not finalize backend behavior that the UI cannot clearly express.
