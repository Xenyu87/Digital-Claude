# Progressive Loading

Use this reference when the skill itself is becoming too large to use cheaply.

## Core First

Always rely on `SKILL.md` for:

- task type;
- budget mode;
- decision/risk gate;
- response economy;
- whether to read project context;
- whether a specialist reference is needed.

## Reference Triggers

Load a reference only when its trigger appears:

| Reference | Trigger |
| --- | --- |
| `budget-modes.md` | budget changes, large/risky/ambiguous work |
| `progressive-loading.md` | checking or tuning reference-loading behavior |
| `decision-risk-gates.md` | unclear, costly, risky, destructive, external, or broad next step |
| `coordinator-safety.md` | medium/low confidence, high risk, or Red Team needed |
| `response-economy.md` | output is getting long or needs a compact format |
| `compression-pass.md` | aggressive safe compression for prompts, handoffs, context docs, commit/PR text |
| `role-profiles.md` | frontend/backend/full-stack/QA/security/UX/data/DevOps/performance/review lens matters |
| `qa-test-agent.md` | frontend+backend workflow, contract/auth/data change, non-trivial bug fix, or push/PR validation |
| `specialist-agents.md` | selecting security/auth, UX/product, data/migration, DevOps/release, or performance specialist |
| `agent-handoff.md` | multiple sub-agents need shared decisions, blockers, contracts, or integration notes |
| `task-routing.md` | mixed, broad, audit, bug rescue, or over-reading risk |
| `app-creation-blueprint.md` | new app, full-stack feature, rebuild, app contract |
| `project-context-template.md` | missing project context system |
| `structure-memory-template.md` | app structure memory needed |
| `second-brain-template.md` | durable decision memory, tradeoffs, constraints, or revisit triggers needed |
| `agent-autolog-template.md` | actual agent mistake, token waste, user correction, stale context, or repeated process failure |
| `maintenance-compaction.md` | cleanup pass, version consolidation, or stop/diminishing-return decision |
| `skill-sync.md` | install, sync, release, publish, or future-session version question |
| `improvement-log.md` | recording behavior changes |
| `release-notes.md` | updating or reporting versions |

## Do Not Load

Do not load references:

- just because they exist;
- after the decision has already been made;
- when a compact rule in `SKILL.md` is enough;
- when the task is a one-file local edit.
