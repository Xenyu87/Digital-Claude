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
