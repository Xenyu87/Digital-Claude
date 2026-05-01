# Release Notes

## v0.27.0 - 2026-05-01

- Added universal plan gates for bug fixes, full-stack features, migrations, auth, deploy, refactors, and new apps.
- Added a compact domain question bank for decisions that affect direction, cost, risk, or rework.
- Added cost checkpoints before broad reads, sub-agents, wide tests, schema/data changes, deploys, paid services, or production actions.

## v0.26.0 - 2026-05-01

- Added plan-first behavior for ambiguous, product/design, or high-impact tasks.
- Added 1-3 precise question guidance before implementation when answers change direction, cost, or rework.
- Added high-fidelity screenshot/mockup handling with stronger visual verification and optional UX/design or QA visual agents when useful.

## v0.25.0 - 2026-05-01

- Added a flexible local UI consistency rule for new screens and redesigns.
- New UI should compare against 2-4 existing screens/components in the same app instead of using app-specific or generic design rules.

## v0.24.0 - 2026-04-30

- Restricted progress updates to only sub-agent usage, errors, blockers, risks, explicit status requests, and user actions.
- Removed long-wait status as a default reason to speak.

## v0.23.0 - 2026-04-30

- Suppressed routine announcements of skill name, budget mode, model policy, role/design lens, file intent, checks, and commit preparation.
- Added forbidden routine update examples from real app testing.

## v0.22.0 - 2026-04-30

- Made progress updates silent by default during routine work.
- Added a progress update gate: speak only for blockers, user decisions, risky actions, long waits, or explicit status requests.

## v0.21.0 - 2026-04-29

- Added cross-agent handoff support for projects worked on by Codex and Claude Code.
- Added `AI_HANDOFF.md` guidance and `references/cross-agent-handoff-template.md`.
- Updated project context routing so active work can pass between agents without relying on hidden memory.

## v0.20.0 - 2026-04-29

- Tightened response economy: routine fixes should be reported as done, not explained.
- Added explicit precision rule for only the items the user must do, choose, configure, pay for, or test manually.
- Simplified final answer templates around `Fatto`, `Verifica`, and optional `Da fare per te`.

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

## v0.1.0-v0.11.1 - 2026-04-29

- Initial coordinator, budget/model policy, routing, app blueprint, response economy, structure memory, roles, gates, progressive loading, maintenance, skill sync, and compaction.
