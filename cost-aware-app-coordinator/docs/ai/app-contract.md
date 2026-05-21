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

## Backend/Data Contract

- Report generation: `scripts/generate_dashboard.py`.
- Local server/actions: `scripts/serve_dashboard.py`.
- Blueprint data: project `app-blueprint.json` when saved; otherwise scanner preview.
- Dashboard state: `reports/skill-dashboard.json`, `reports/dashboard-config.json`, `reports/*status*.json`, `reports/*events*.jsonl`.
- Validation: scripts should cap output, tolerate missing state files, and avoid autonomous code edits.

## Verification

- Minimum check: `python3 scripts/test_all.py --json --no-write`.
- Frontend build: `npm run build:blueprint-flow`.
- Manual acceptance: Home fits in one useful screen; Lavagna is primary for graph work; automation and diagnostics are not mixed with next-action guidance.
