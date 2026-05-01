# Role Profiles

Use role profiles internally to guide decisions without repeating role narration to the user.

| Role | Use for |
| --- | --- |
| Frontend | usable workflows, UI states, responsive layout, accessibility basics, local design consistency |
| Backend | contracts, validation, auth, persistence, transactions, idempotency, safe errors |
| Full-stack | UI/backend/data/auth contract and one high-signal verification path |
| QA/Test | first usable slice, UI states, API contracts, validation, auth, smoke checks, residual risk |
| Security/Auth | permissions, protected data, server-side enforcement, secrets, abuse cases |
| UX/Product | user intent, workflow clarity, friction, empty/error copy, product tradeoffs |
| Data/Migration | schemas, migrations, seed/import/export, rollback, destructive operations |
| DevOps/Release | env vars, build, CI/CD, deploy, hosting, secrets, release risk |
| Performance | expensive queries, bundle size, large lists, realtime, images, latency |
| Review/Audit | bugs, regressions, missing tests, security, data loss, production risks |
| Skill Maintenance | shorter rules, lower token cost, safer routing, durable behavior |

For QA details, use `qa-test-agent.md`.
For specialist triggers and output contracts, use `specialist-agents.md`.

## Frontend Local Consistency

For new screens, panels, dashboards, forms, or redesigns, first identify 2-4 existing screens/components in the same app. Match the local design language: layout density, spacing, card radius, typography hierarchy, palette, controls, CTA style, empty/error/loading states, mobile behavior, and copy tone. Do not impose a generic style across apps.

## Design Intent Brief

For medium/high-risk UI work, define the design direction before coding:

- Mode: close screenshot fidelity, local app consistency, or intentional redesign.
- Audience/job: who uses it and what they need to do first.
- Tone: utilitarian, premium, playful, editorial, dense operational, etc.
- Must keep: elements, data, layout, or behavior that cannot change.
- Flexible: elements that may be improved if it helps usability.
- Verification: screenshot, viewport, or workflow check that proves the intent.

Ask only when the answer changes the route. Otherwise choose the safest mode from context and state it briefly in the plan.

## High-Fidelity Visual Work

When the user provides a screenshot, mockup, or design reference and asks for close fidelity, treat the task as at least medium UI risk. Before coding, clarify only priorities that change the path: pixel-like fidelity vs local app consistency, mobile vs desktop priority, mandatory vs flexible elements, and speed vs maintainability. Use stronger visual checks when possible, such as before/after screenshots and mobile/desktop review. Consider UX/design or QA visual sub-agents when the layout is complex, responsive states matter, or a second pass is likely to catch meaningful differences.

## Playwright UI Check

Consider Playwright automatically for new pages, redesigns, important forms, dashboards, charts, navigation, responsive layout, or screenshot/mockup fidelity. Prefer screenshots at the most relevant desktop/mobile viewport plus a small interaction smoke check when behavior matters.

Skip Playwright for tiny copy changes, backend-only work, mechanical refactors, or CSS tweaks that can be checked locally without a browser. If Playwright requires starting a server, installing browsers, logging in, seeded data, or broad viewport coverage, use a cost checkpoint first.

When Playwright is used, keep it targeted: screenshot, console errors, one primary workflow, and only states affected by the change.
