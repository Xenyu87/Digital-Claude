# AI Handoff

## Current Goal

Make the Lavagna the main simple/powerful dashboard area and keep the dashboard organized into clear tabs.

## State

- Done: Lavagna has action-focused `blueprint-view-v1` payload and React Flow UI.
- Done: dashboard tabs exist: Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer cleanup after the remote major cleanup merge.
- In progress: split `render_html()` into section render helpers.
- Done in current step: extracted `render_runner_config_form()` from the Automazione section.

## Changed Files

- `AI_RESUME.md`: cheap latest-state entry point.
- `AI_HANDOFF.md`: current handoff.
- `scripts/generate_dashboard.py`: extracted dashboard header, tabs, guidance cards, Home section helper, and runner config form.

## Decisions

- Use tabs/client-side sections before true server routes for the dashboard split. This keeps existing forms and React Flow mount safer.
- Keep diagnostics visible but moved out of the first screen.
- React Flow is the canonical Lavagna renderer; the old inline SVG renderer should not return.

## Open Risks

- `render_html()` remains large and should be split incrementally.
- Visual/manual browser verification is still useful after larger UI rearrangements.

## Next Step

Run verification, commit/push, then continue with `render_automation_section`, `render_lavagna_section`, `render_actions_section`, `render_diagnostics_section`.

## Do Not Repeat

- Do not run dashboard generation concurrently with tests that read/write the same `reports` or event files.
