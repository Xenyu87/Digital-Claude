# AI Handoff

## Current Goal

Make the Lavagna the main simple/powerful dashboard area and keep the dashboard organized into clear tabs.

## State

- Done: Lavagna has action-focused `blueprint-view-v1` payload and React Flow UI.
- Done: dashboard tabs exist: Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer cleanup after the remote major cleanup merge.
- In progress: split `render_html()` into section render helpers.
- Done in current step: extracted `render_runner_config_form()` from the Automazione section.
- Done in current step: extracted full `render_automation_section()`.
- Done in current step: extracted full `render_lavagna_section()` while preserving React Flow, design wizard, and screenshot paste markup.
- Done in current step: extracted full `render_actions_section()` while preserving resume, warning tasks, prompts, and expert feedback markup.
- Done in current step: extracted full `render_diagnostics_section()` and removed the unused `estimates` local from `render_html()`.
- Done in current step: Lavagna first panel is now action-first; wizard/screenshot moved under `Strumenti lavagna`; React Flow shows a `Prossima azione` bar above counters.

## Changed Files

- `AI_RESUME.md`: cheap latest-state entry point.
- `AI_HANDOFF.md`: current handoff.
- `scripts/generate_dashboard.py`: Lavagna panel now starts from next task, counters, and direct scan/save commands.
- `frontend/blueprint-flow/src/main.jsx`: added primary action summary above map counters.
- `frontend/blueprint-flow/src/styles.css`: styled primary action bar.
- `scripts/dashboard_smoke_test.py`, `scripts/self_test.py`: updated markers for the new Lavagna UX.

## Decisions

- Use tabs/client-side sections before true server routes for the dashboard split. This keeps existing forms and React Flow mount safer.
- Keep diagnostics visible but moved out of the first screen.
- React Flow is the canonical Lavagna renderer; the old inline SVG renderer should not return.

## Open Risks

- `render_html()` remains large and should be split incrementally.
- Visual/manual browser verification is still useful after larger UI rearrangements.

## Next Step

Run verification, commit/push, then do a visual/manual pass and improve task-copy or empty states if needed.

## Do Not Repeat

- Do not run dashboard generation concurrently with tests that read/write the same `reports` or event files.
