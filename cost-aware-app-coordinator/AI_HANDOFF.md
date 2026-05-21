# AI Handoff

## Current Goal

Clean up the coordinator dashboard context and prepare a serious dashboard reorganization plan.

## State

- Done: repo context files created for the skill project.
- Done: `AI_CONTEXT.md` now describes real dashboard/skill routing.
- In progress: closing stale checkpoint and reducing Blueprint scanner false positives.
- Not started: implementing the dashboard page/tab split.

## Changed Files

- `AGENTS.md`: project-level agent entry instructions.
- `AI_RESUME.md`: cheap latest-state entry point.
- `AI_CONTEXT.md`: real routing/context for this skill repo.
- `AI_HANDOFF.md`: current handoff.
- `AI_DECISIONS.md`: durable decisions.
- `docs/ai/app-contract.md`: dashboard workflow contract.
- `scripts/blueprint_board.py`: scanner prioritization work.

## Decisions

- Use tabs/client-side sections before true server routes for the dashboard split. This keeps existing forms and React Flow mount safer.
- Keep diagnostics visible but moved out of the first screen.

## Open Risks

- Blueprint scanner can still confuse generated report UI with source UI when `reports/skill-dashboard.html` is scanned.
- `render_html()` remains large and should be split incrementally.

## Next Step

Run verification after scanner/context cleanup, then plan the dashboard IA implementation in phases.

## Do Not Repeat

- Do not run dashboard generation concurrently with tests that read/write the same `reports` or event files.
