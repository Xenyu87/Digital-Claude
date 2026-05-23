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
- Done in current step: Blueprint scanner creates granular UI nodes for visible buttons and charts, adds component parent/child relations, and exposes chart/button subnodes in the React Flow detail panel.
- Done in current step: Playwright installed and configured; Lavagna canvas now supports opening/closing child UI nodes from global controls and component node toggles, with expanded children positioned beside their parent component.
- Done in current step: Lavagna now has a side-by-side frontend preview pane. It embeds a live `frontend_preview_url`/`preview_url` when configured, otherwise uses `/frontend-preview?project=...` generated from scanner nodes. Node selection highlights matching generated preview elements.

## Changed Files

- `AI_RESUME.md`, `AI_HANDOFF.md`, `AI_CONTEXT.md`: latest state and scanner contract memory.
- `scripts/blueprint_board.py`: button/chart scanner, action descriptions, UI hierarchy relations, subnodes in doctor output.
- `scripts/dashboard_components.py`: passes `uiRole`, `actionDescription`, and `subnodes` to React Flow.
- `scripts/serve_dashboard.py`: serves `/frontend-preview` generated from Blueprint frontend nodes and supports highlight/selection messages.
- `frontend/blueprint-flow/src/main.jsx`, `frontend/blueprint-flow/src/styles.css`: node footer shows subnode count; detail panel shows "Cosa fa" and clickable "Sotto-nodi"; canvas supports expand/collapse of child UI nodes.
- `package.json`, `package-lock.json`, `playwright.config.js`: Playwright visual test setup.
- `tests/visual/blueprint-board.spec.js`, `tests/fixtures/visual-blueprint-app`: deterministic visual regression for Lavagna UI details.
- `docs/ai/visual-testing.md`, `docs/ai/app-contract.md`: Playwright setup and Lavagna UI node contract.
- `scripts/blueprint_board_test.py`, `scripts/self_test.py`: regression coverage for button nodes, chart nodes, and UI hierarchy.

## Decisions

- Use tabs/client-side sections before true server routes for the dashboard split. This keeps existing forms and React Flow mount safer.
- Keep diagnostics visible but moved out of the first screen.
- React Flow is the canonical Lavagna renderer; the old inline SVG renderer should not return.
- Keep nodes simple on canvas; precision lives in parent/child links, detail panel, and optional expand/collapse.

## Open Risks

- `render_html()` remains large and should be split incrementally.
- Playwright requires local server socket permissions and Chromium system dependencies. In restricted environments, run `npm run test:visual` with elevated permissions.

## Next Step

Commit/push the frontend preview split-view. Next functional step: make preview click select/focus the canvas node reliably for live previews, then add guided dev-server URL setup.

## Do Not Repeat

- Do not run dashboard generation concurrently with tests that read/write the same `reports` or event files.
