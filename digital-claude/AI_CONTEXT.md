# AI Context - Index

## Goal

Cost-aware Codex coordinator skill for app work. It provides operating rules, project context scaffolding, a local dashboard, Blueprint Board, checkpoint/resume memory, and safe automation controls.

## Stack

- Python scripts generate and serve the dashboard.
- Static HTML/CSS plus embedded server-side rendered panels.
- React/Vite/React Flow powers the interactive Blueprint canvas in `frontend/blueprint-flow`.
- Playwright validates the Lavagna UI against `tests/fixtures/visual-blueprint-app`.
- State lives in `reports/*.json`, project docs, and optional per-project `app-blueprint.json`.
- No autonomous AI execution is enabled by default; runner controls are preparatory and approval-gated.

## Routing Table

| If the task touches... | Read... |
| --- | --- |
| latest state / resume | AI_RESUME.md |
| active handoff | AI_HANDOFF.md |
| durable tradeoffs | AI_DECISIONS.md |
| dashboard HTML/data generation | scripts/generate_dashboard.py, scripts/dashboard_components.py |
| dashboard local server/actions | scripts/serve_dashboard.py |
| Blueprint scanner/audit/flow logic | scripts/blueprint_board.py |
| Blueprint React canvas | frontend/blueprint-flow/src/main.jsx, frontend/blueprint-flow/src/styles.css |
| Lavagna preview and visual tests | scripts/serve_dashboard.py, frontend/blueprint-flow/src/main.jsx, playwright.config.js, tests/visual/blueprint-board.spec.js, tests/fixtures/visual-blueprint-app, docs/ai/visual-testing.md |
| project context scaffolding | scripts/bootstrap_project_context.py, scripts/update_ai_resume.py |
| runner/background automation | scripts/persistent_runner.py, scripts/background_sentinel.py |
| task resume/checkpoints | scripts/task_checkpoint.py |
| verification | scripts/test_all.py, scripts/self_test.py, scripts/dashboard_smoke_test.py, scripts/blueprint_board_test.py |
| app workflow contract | docs/ai/app-contract.md |

## Current Decisions

- Language: Italian for user-facing dashboard and coordinator defaults.
- Dashboard port: default `3002`.
- Dashboard architecture: generated static report plus small local Python server for forms/actions.
- Blueprint canvas: React Flow assets built into `reports/blueprint-flow-assets`.
- Blueprint scanner contract: visible UI buttons and charts should become granular frontend nodes; component nodes may expose `subnodes`, `uiRole`, `actionDescription`, and parent/child `contains_ui` relations.
- Lavagna canvas supports component expand/collapse for child UI nodes and positions expanded children beside the parent component.
- Lavagna can show a side-by-side frontend preview. Live preview comes from `frontend_preview_url`/`preview_url` in `app-blueprint.json`; fallback generated preview is rendered directly in React from scanner nodes, avoiding iframe 404s.
- Automation: safe/report-only by default; AI autonomous execution remains disabled.
- Project memory: use `AI_RESUME.md` as the cheap first-read file for new chats.

## First Usable Slice

- User: developer coordinating app projects with Codex.
- Main workflow: select project, inspect next action/warnings, use Blueprint Board, run targeted checks, resume work safely.
- Frontend entry point: `reports/skill-dashboard.html`.
- Backend/data operation: `scripts/generate_dashboard.py` builds JSON/HTML; `scripts/serve_dashboard.py` handles local actions.
- Success state: dashboard shows project status, board, checks, runner state, and resume hints without reading the whole repo.
- Empty/loading/error states: dashboard smoke test checks required markers; scripts fall back to compact JSON defaults.
- Verification path: `python3 scripts/test_all.py --json --no-write`, `npm run build:blueprint-flow`, and `npm run test:visual` when UI behavior changed.

## Pending Work

- [x] Split dashboard into clearer sections/tabs: Home, Lavagna, Azioni, Automazione, Diagnostica.
- [x] Keep Home as a decision cockpit; move raw logs and technical tables out of the first screen.
- [x] Reduce Blueprint scanner false positives around generated dashboard forms and local Python endpoints.
- [x] Add granular Lavagna nodes for UI buttons/charts with parent-child relations and detail subnodes.
- [x] Add canvas-level expand/collapse for component nodes if detail-panel subnodes are not enough.
- [ ] Keep runner controls visibly safe and separated from informational panels.

## Documentation Maintenance

Update this file when dashboard architecture, scanner contracts, runner safety rules, or project memory conventions change.
