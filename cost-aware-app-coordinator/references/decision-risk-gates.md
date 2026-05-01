# Decision And Risk Gates

Use this reference when the next step is unclear, costly, risky, or broad.

## Act

Act without asking when:

- the user request is clear;
- the change is reversible;
- the affected files are discoverable locally;
- no external account, payment, production system, credential, or destructive operation is involved.

## Ask

Ask 1-3 precise questions when the answer changes direction, cost, risk, or rework:

- product direction;
- UX/design priority or fidelity target;
- budget mode;
- data model;
- auth or permission behavior;
- irreversible/destructive action;
- external service choice;
- deployment target;
- paid resource usage.

Do not ask broad questions. Prefer choices like pixel-like fidelity vs local app consistency, speed vs maintainability, or mandatory vs optional elements.

Use domain questions when they fit:

- Bug: fix rapido della causa visibile, o diagnosi piu profonda prima del codice?
- Feature: MVP minimo, o base piu scalabile anche se costa di piu?
- Data/migration: effetto solo sui nuovi dati, o anche retroattivo sui dati esistenti?
- Auth/permissions: chi puo vedere, creare, modificare, eliminare, esportare?
- Deploy/production: locale, staging, o produzione? Serve rollback?
- Refactor: mantenere identico il comportamento, o e permesso migliorarlo?
- External service: usare servizio gia presente, o introdurne uno nuovo?

## Plan

Plan briefly when:

- frontend and backend contracts must align;
- the change crosses modules;
- tests or migrations are involved;
- the implementation path has multiple viable approaches;
- product/design/UX tradeoffs are ambiguous;
- the user asks to lower errors, work by plan, or approve the route first;
- a wrong choice would cause rework.

Use three to six bullets: goal, recommended route, tradeoffs, likely areas touched, validation, and cost/risk. After approval, implement.

Use a domain-specific mini-plan:

- Bug/fix: symptom, suspected cause, smallest fix, verification, residual risk.
- Full-stack feature: user flow, UI contract, backend/data contract, validation path, rollout risk.
- Data/migration: schema/data effect, retroactivity, rollback, verification, data-loss risk.
- Auth/permissions: actors, allowed actions, server-side enforcement, abuse cases, tests.
- Deploy/production: environment, config/secrets, rollout, rollback, monitoring check.
- Refactor: invariant behavior, files/modules, compatibility, tests proving no behavior drift.
- New app: target user, first usable workflow, stack constraints, context docs, first slice.

Keep the plan short. If implementation can start safely after one recommended route, do not over-plan.

## Cost Checkpoint

Before moving from targeted work to a higher-cost route, state:

- next expensive step;
- cost estimate: basso, medio, or alto;
- why it is useful;
- cheaper alternative and tradeoff;
- whether approval is needed.

Use a checkpoint before broad code reading, sub-agents, wide tests, schema/data changes, production deploys, paid services, or long-running external operations. Skip it for cheap, local, reversible actions.

## Delegate

Delegate only when:

- the slice is independent;
- ownership is clear;
- the model label and stop condition are explicit;
- the coordinator can keep working locally without waiting immediately;
- integration risk is lower than doing everything in one pass.

When delegated slices depend on each other, require structured handoffs instead of free-form discussion.

## Stop

Stop and report when:

- credentials or secrets are missing;
- production systems or paid services would be changed;
- a destructive action is requested ambiguously;
- the repository state makes the requested work unsafe;
- tests indicate a serious unrelated failure that changes the risk profile.

## Verify

Match verification to risk:

- Low: narrow lint, unit, type, smoke, or manual check.
- Medium: targeted tests around touched modules and contracts.
- High: broader tests, migration/auth/security checks, and explicit residual risk.

## Confidence

- High: proceed with normal checks.
- Medium: verify assumptions, use a specialist, or run a targeted check before implementation/closure.
- Low: ask the user, reduce scope, or run Red Team before proceeding.
