# Release Notes

## v0.19.0 - 2026-04-29

- Added event-based agent autolog guidance for real mistakes, token waste, user corrections, stale context, and repeated process failures.
- Added `references/agent-autolog-template.md`.
- Connected `AI_AGENT_LOG.md` to project context without making it part of normal startup.

## v0.18.0 - 2026-04-29

- Added caveman-inspired compression pass for prompts, handoffs, docs, commit/PR text, and final answers.
- Added `references/compression-pass.md`.
- Added explicit preserve rules for security, breaking changes, migrations, auth, deploy risk, irreversible actions, and future-debug context.

## v0.17.0 - 2026-04-29

- Added deterministic skill validator script.
- Validator checks frontmatter, reference coverage, progressive loading coverage, duplicate headings, required sections, and line limits.
- Connected validation to maintenance and compaction workflow.

## v0.16.0 - 2026-04-29

- Added coordinator self-check gate, decision confidence, and optional Red Team rules.
- Added `references/coordinator-safety.md`.
- Connected coordinator safety to definition of done, progressive loading, and risk gates.
- Cleaned up core formatting/reference wording during self-improvement.
- Compressed role profiles and core sections to reduce prompt length without removing behavior.

## v0.15.0 - 2026-04-29

- Added optional specialist agents for Security/Auth, UX/Product, Data/Migration, DevOps/Release, and Performance.
- Added `references/specialist-agents.md` with strict triggers and compact output contract.
- Updated role profiles, progressive loading, coordinator rules, and definition of done specialist routing.

## v0.14.0 - 2026-04-29

- Added optional QA/Test role and `references/qa-test-agent.md`.
- Added QA/Test trigger for frontend/backend workflows, contract/auth/data changes, bug fixes, and push/PR validation.
- Connected QA/Test to definition of done and sub-agent usage.

## v0.13.0 - 2026-04-29

- Added structured sub-agent handoff protocol.
- Added `references/agent-handoff.md` for compact communication, conflict handling, and final integration.
- Updated progressive loading and delegation gates for multi-agent coordination.

## v0.12.0 - 2026-04-29

- Added `AI_DECISIONS.md` second brain guidance and `references/second-brain-template.md`.
- Updated project context routing for durable decisions, tradeoffs, constraints, and revisit triggers.
- Updated skill description to include project context and decision memory.

## v0.11.1 - 2026-04-29

- Compacted improvement log after local self-tests.
- Renamed a duplicate template heading to reduce ambiguity.
- Clarified scoped approval wording and progressive-loading self-reference after deeper self-tests.
- Compacted `SKILL.md` and `project-context-template.md` by relying on existing references.
- No new behavior added.

## v0.11.0 - 2026-04-29

- Added skill sync protocol to avoid drift between repo source and installed skill copies.
- Added `references/skill-sync.md`.

## v0.10.0 - 2026-04-29

- Added maintenance and compaction protocol to prevent prompt debt.
- Added `references/maintenance-compaction.md`.

## v0.9.0 - 2026-04-29

- Added progressive loading so references are read only when triggered.
- Added `references/progressive-loading.md`.

## v0.8.0 - 2026-04-29

- Added decision, risk, and quality gates.
- Added `references/decision-risk-gates.md`.

## v0.7.0 - 2026-04-29

- Added role profiles for frontend, backend, full-stack, review/audit, and skill maintenance.
- Added `references/role-profiles.md`.

## v0.6.0 - 2026-04-29

- Added structure memory protocol and `AI_STRUCTURE.md` guidance.
- Added `references/structure-memory-template.md`.

## v0.5.0 - 2026-04-29

- Added response economy protocol and compact answer templates.
- Added `references/response-economy.md`.

## v0.4.0 - 2026-04-29

- Added app creation blueprint for frontend/backend planning.
- Updated project context template with `app-contract.md`.

## v0.1.0-v0.3.0 - 2026-04-29

- Initial coordinator workflow, budget modes, model policy, task routing, working loop, definition of done, sub-agent dispatch, project context template, and improvement loop.
