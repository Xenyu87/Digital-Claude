# App Contract

## User Workflow

- Actor: developer using Codex to coordinate app projects.
- Main job: understand current project state, choose the next safe action, inspect Blueprint flows, and resume work without rediscovering context.
- Happy path: open dashboard, select project, read Home next action, inspect Lavagna for flows/problems, run targeted checks, update resume/checkpoint.
- Empty/loading/error states: no project selected, missing AI docs, stale checkpoint, clean repo, generated report missing, smoke markers missing.

## Frontend Contract

- Primary surface: generated `reports/skill-dashboard.html`.
- Planned sections: Home, Lavagna, Azioni, Automazione, Diagnostica.
- React surface: `data-blueprint-flow-root` mounts the interactive Blueprint canvas from built Vite assets.
- Interactions: project select, background mode, runner controls, learning feedback, Blueprint design wizard, screenshot upload, layout save.

## Blueprint Board Contract

- Purpose: the Lavagna is the operational map of the app work, not a raw map of files.
- Default question: what should be fixed, clarified, or verified next?
- Default visible scope: show at most 15-20 high-value nodes or flow objects before drill-down.
- Primary objects: focus, flows, issues, actions, evidence, and confirmed/ignored learning feedback.
- Technical nodes such as buttons, scripts, endpoints, and models are drill-down details unless they affect a user-facing flow.
- Issue classes:
  - `real_issue`: high-confidence problem or confirmed user-facing break.
  - `scanner_hypothesis`: plausible scanner signal that needs confirmation.
  - `known_noise`: scanner signal ignored or classified as internal tool noise.
  - `technical_detail`: valid implementation detail that should not drive the board.
- The main board should show at most 3 recommended actions and keep raw audit tables in diagnostics.
- Every visible issue should include a next action and a verification check.
- User feedback (`useful`, `wrong`, `ignore`, `confirm_edge`, `ignore_edge`) should reduce repeated noise over time.

## Backend/Data Contract

- Report generation: `scripts/generate_dashboard.py`.
- Local server/actions: `scripts/serve_dashboard.py`.
- Blueprint data: project `app-blueprint.json` when saved; otherwise scanner preview.
- Dashboard state: `reports/skill-dashboard.json`, `reports/dashboard-config.json`, `reports/*status*.json`, `reports/*events*.jsonl`.
- Validation: scripts should cap output, tolerate missing state files, and avoid autonomous code edits.
- Blueprint view model: dashboard graph payload should expose `blueprintView` with `focus`, `stats`, `nodes`, `edges`, `flows`, `issues`, `actions`, and `views`.

## Verification

- Minimum check: `python3 scripts/test_all.py --json --no-write`.
- Frontend build: `npm run build:blueprint-flow`.
- Manual acceptance: Home fits in one useful screen; Lavagna is primary for graph work; automation and diagnostics are not mixed with next-action guidance.
- Lavagna acceptance: next step is understandable within 10 seconds; default board has fewer than 20 nodes; toolbar/internal canvas controls are not promoted as top problems.
