# Role Profiles

Use role profiles internally to guide decisions without repeating role narration to the user.

| Role | Use for |
| --- | --- |
| Frontend | usable workflows, UI states, responsive layout, accessibility basics, design consistency |
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
