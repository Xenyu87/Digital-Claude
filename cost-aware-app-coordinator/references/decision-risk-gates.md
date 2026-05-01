# Decision And Risk Gates

Use this reference when the next step is unclear, costly, risky, or broad.

## Act

Act without asking when the request is clear, reversible, locally inspectable, and does not involve external accounts, payments, production systems, credentials, or destructive operations.

## Ask

Ask 1-3 precise questions when the answer changes direction, cost, risk, or rework: product direction, UX/design fidelity, budget, data model, auth/permissions, irreversible actions, external services, deployment target, or paid resources.

Do not ask broad questions. Prefer choices like pixel-like fidelity vs local app consistency, speed vs maintainability, or mandatory vs optional elements.

Useful domain questions:

- Bug: fix rapido della causa visibile, o diagnosi piu profonda?
- Feature: MVP minimo, o base piu scalabile?
- UI/design: fedelta allo screen, coerenza con app esistente, o redesign piu deciso?
- Data/migration: solo nuovi dati, o anche dati esistenti?
- Auth: chi puo vedere, creare, modificare, eliminare, esportare?
- Backend: quale chiamante usa il contratto e quali errori deve vedere l'utente?
- Deploy: locale, staging, o produzione? Serve rollback?
- Refactor: comportamento identico, o si puo migliorare?
- External service: servizio gia presente, o nuovo servizio?

## Plan

Plan briefly when contracts must align, modules are crossed, tests/migrations are involved, multiple routes exist, product/design/UX tradeoffs are ambiguous, the user asks to lower errors, or a wrong choice would cause rework.

Use three to six bullets: goal, recommended route, tradeoffs, likely areas, validation, cost/risk. After approval, implement.

For users who are not programmers, write a plain-language plan contract:

- Obiettivo: what the user should get.
- Criteri di successo: how the user can judge visual or functional correctness.
- Decisioni da approvare: choices that change behavior, cost, or risk.
- Aree probabili: app areas or screens, not code jargon unless needed.
- Verifica minima: what Codex will check.
- Rischio residuo: what may still need the user's eye or manual test.

Domain mini-plan hints:

- Bug/fix: symptom, suspected cause, smallest fix, verification, residual risk.
- Full-stack: user flow, UI contract, backend/data contract, validation path, rollout risk.
- UI/design: intent mode, user job, must-keep elements, flexible elements, visual verification.
- Data/migration: schema/data effect, retroactivity, rollback, verification, data-loss risk.
- Auth: actors, allowed actions, server-side enforcement, abuse cases, tests.
- Backend/API: caller, input/output, permissions, data effect, compatibility, verification.
- Deploy: environment, config/secrets, rollout, rollback, monitoring check.
- Refactor: invariant behavior, modules, compatibility, tests proving no drift.
- New app: target user, first workflow, stack constraints, context docs, first slice.

Keep the plan short. If implementation can start safely after one recommended route, do not over-plan.

## Cost Checkpoint

Before moving from targeted work to a higher-cost route, state the next expensive step, cost estimate (`basso`, `medio`, `alto`), why it is useful, cheaper alternative/tradeoff, and whether approval is needed.

Use a checkpoint before broad code reading, sub-agents, wide tests, schema/data changes, production deploys, paid services, or long-running external operations. Skip it for cheap, local, reversible actions.

## User Acceptance Feedback

After medium/high-risk visual or functional work, ask:

`Per te lato visivo e funzionale rispecchia quello che avevi chiesto?`

If the user says no, ask for the smallest concrete mismatch, fix it, and log the lesson in `AI_AGENT_LOG.md` only when it reveals a repeatable agent mistake or missed intent. Do not log normal preference changes.

## Delegate

Delegate only when the slice is independent, ownership is clear, model label and stop condition are explicit, the coordinator can keep working without waiting immediately, and integration risk is lower than doing everything in one pass.

When delegated slices depend on each other, require structured handoffs instead of free-form discussion.

## Stop

Stop and report when credentials or secrets are missing, production systems or paid services would be changed, a destructive action is ambiguous, repository state is unsafe, or tests reveal serious unrelated risk.

## Verify

- Low: narrow lint, unit, type, smoke, or manual check.
- Medium: targeted tests around touched modules and contracts.
- High: broader tests, migration/auth/security checks, and explicit residual risk.

## Confidence

- High: proceed with normal checks.
- Medium: verify assumptions, use a specialist, or run a targeted check before implementation/closure.
- Low: ask the user, reduce scope, or run Red Team before proceeding.
