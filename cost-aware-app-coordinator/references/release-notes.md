# Release Notes

## v0.32.0 - 2026-05-01

- Added a Design Intent Brief for medium/high-risk UI work: fidelity mode, audience/job, tone, must-keep elements, flexible elements, and visual verification.
- Added a UI/design routing question to distinguish screenshot fidelity, local app consistency, and intentional redesign.

## v0.31.0 - 2026-05-01

- Added memory hygiene write filters for `AI_DECISIONS.md` and `AI_AGENT_LOG.md`: memory must be verified, durable, actionable, and safe.
- Added guidance to avoid storing untrusted external content, one-off preferences, normal progress, or contradictory active decisions.

## v0.30.0 - 2026-05-01

- Added bounded auto-improvement run rules: auto-accepted edits are scoped to the current run, must change behavior, and stop when remaining ideas are cosmetic, speculative, duplicate, or prompt-costly.
- Added plain `Come provarlo` guidance for user-facing changes so non-programmer users can verify visual or functional behavior without reading code.

## v0.29.0 - 2026-05-01

- Added conditional Playwright UI checks for new pages, redesigns, screenshot fidelity, responsive layouts, forms, charts, dashboards, and navigation.
- Added cost checkpoint guidance before expensive Playwright setup such as servers, browser installs, login, seeded data, or broad viewport suites.

## v0.28.0 - 2026-05-01

- Added a plain-language plan contract for non-programmer users: goal, success criteria, decisions, likely areas, minimum verification, and residual risk.
- Added final user-facing acceptance feedback for medium/high-risk visual or functional work.
- Added autolog guidance to record missed visual or functional intent only when it reveals a repeatable agent mistake.

## v0.27.0 - 2026-05-01

- Added universal plan gates for bug fixes, full-stack features, migrations, auth, deploy, refactors, and new apps.
- Added a compact domain question bank for decisions that affect direction, cost, risk, or rework.
- Added cost checkpoints before broad reads, sub-agents, wide tests, schema/data changes, deploys, paid services, or production actions.

## v0.25.0-v0.26.0 - 2026-05-01

- Added flexible local UI consistency for new screens/redesigns across any app.
- Added plan-first questions for ambiguous/high-impact work.
- Added high-fidelity screenshot/mockup handling with stronger visual verification and optional UX/design or QA visual agents when useful.

## v0.19.0-v0.24.0 - 2026-04-29 to 2026-04-30

- Added event-based `AI_AGENT_LOG.md` for real mistakes, token waste, stale context, and repeated process failures.
- Tightened response economy: routine work stays quiet; precision is reserved for user actions, risks, choices, blockers, and useful final summaries.
- Added `AI_HANDOFF.md` support for Codex, Claude Code, and other agents.

## v0.12.0-v0.18.0 - 2026-04-29

- Added `AI_DECISIONS.md`, structured sub-agent handoff, QA/Test role, specialist agent triggers, coordinator self-check, Red Team rules, validation script, and safe compression pass.

## v0.1.0-v0.11.1 - 2026-04-29

- Initial coordinator, budget/model policy, routing, app blueprint, response economy, structure memory, roles, gates, progressive loading, maintenance, skill sync, and compaction.
