# Release Notes

## v0.11.0 - 2026-04-29

- Added skill sync protocol to avoid drift between repo source and installed skill copies.
- Added `references/skill-sync.md` with check, report, sync rules, and release checklist.
- Clarified not to claim future sessions use repo changes unless the installed path is known.

## v0.10.0 - 2026-04-29

- Added maintenance and compaction protocol to prevent prompt debt.
- Added `references/maintenance-compaction.md` with keep, move, compress, merge, and stop criteria.
- Added a stop rule for when further improvements are cosmetic or cost more tokens than they save.

## v0.9.0 - 2026-04-29

- Added progressive loading rules so references are read only when triggered.
- Added `references/progressive-loading.md` with core-first and reference trigger guidance.
- Reduced expected token use as the skill grows by avoiding default full-reference loading.

## v0.8.0 - 2026-04-29

- Added decision and risk gates for acting, asking, planning, delegating, stopping, and verifying.
- Added quality gate for first usable slice, frontend/backend consistency, server-side authority, checks, and docs updates.
- Added `references/decision-risk-gates.md` for compact operational rules.

## v0.7.0 - 2026-04-29

- Added role profiles for frontend, backend, full-stack, review/audit, and skill maintenance work.
- Added `references/role-profiles.md` for compact internal role guidance.
- Clarified that role profiles should guide behavior without repeated user-facing narration.

## v0.6.0 - 2026-04-29

- Added structure memory protocol for remembering app layout without repeatedly scanning files.
- Added `AI_STRUCTURE.md` guidance to project context and doc reading protocol.
- Added `references/structure-memory-template.md` with compact map, flows, invariants, and read-first hints.

## v0.5.0 - 2026-04-29

- Added response economy protocol to reduce unnecessary token use.
- Added concise default shapes for status updates, plans, final answers, and audits.
- Added anti-verbosity rules for tool output, diffs, inspected files, and generic follow-ups.
- Added `references/response-economy.md` with compact answer templates.

## v0.4.0 - 2026-04-29

- Added app creation blueprint for frontend/backend planning.
- Added first usable slice guidance for new apps and full-stack features.
- Added frontend, backend, data/security, and full-stack verification contracts.
- Updated project context template with `app-contract.md` and first usable slice fields.
- Added an `app-contract.md` template and delivery slice order for full-stack app creation.

## v0.3.0 - 2026-04-29

- Added task routing for new projects, existing changes, audits, bug rescue, and skill improvement.
- Added a practical working loop from budget/model choice through verification and final response.
- Added a definition of done for scoped edits, checks, and concise outcomes.
- Added a task routing reference for broad or mixed requests.
- Added sub-agent dispatch fields for ownership, model label, reasoning effort, and stop condition.

## v0.2.0 - 2026-04-29

- Added model selection protocol by task risk and budget mode.
- Added guidance for mini/default/coding/frontier model labels.
- Added reasoning effort guidance for simple, normal, and high-risk work.

## v0.1.0 - 2026-04-29

Initial local version.

- Added coordinator-first workflow.
- Added budget modes: Economico, Bilanciato, Massima sicurezza.
- Added simple cost estimate: basso, medio, alto.
- Added sub-agent rules and compact output format.
- Added generic project context template.
- Added approval-based skill improvement loop.
- Added lightweight improvement log.
