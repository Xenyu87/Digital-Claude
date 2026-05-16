# Release Notes

## v0.77.0 - 2026-05-16
- Added Proxmox/LXC dashboard service scripts, remote-workstation guide, and `serve_dashboard.py --host`.

## v0.76.0 - 2026-05-16
- Added a larger Blueprint board graph with connected nodes, descriptions, and expanded node visibility.

## v0.75.0 - 2026-05-16
- Added readable Blueprint node descriptions in dashboard cards and Doctor output.

## v0.74.0 - 2026-05-16
- Added dashboard Blueprint scan/confirm buttons and bounded session scanning to avoid memory spikes.

## v0.73.0 - 2026-05-15
- Added `scripts/test_all.py` as one-command verification for validation, fixtures, Blueprint, and dashboard smoke.

## v0.72.0 - 2026-05-15
- Added `blueprint_board.py seed` to create first app Blueprint nodes from a free-text description.

## v0.71.0 - 2026-05-15
- Added smarter Blueprint import for pages, components, routes, services, and tests.

## v0.70.0 - 2026-05-15
- Added a clearer Blueprint dashboard panel with focus card, node cards, health chips, and mobile layout.

## v0.69.0 - 2026-05-15
- Added prudent Blueprint Auto-Update suggestions and optional metadata-only writes.

## v0.68.0 - 2026-05-15
- Added read-only Blueprint Doctor drift signals for node health, related files, tests, and next focus.

## v0.67.0 - 2026-05-15
- Added Blueprint domains, tags, compact summaries, and per-node implementation steps.

## v0.66.0 - 2026-05-15
- Added Blueprint Board Core POC: local intent graph, commands, fixture test, and dashboard summary.

## v0.65.0 - 2026-05-15
- Added visible fresh/cache status for dashboard checks.

## v0.64.0 - 2026-05-14
- Added short-lived smart cache for heavy dashboard checks while keeping live PR/git signals fresh.

## v0.62.0-v0.63.0 - 2026-05-14
- Added Superplan prompt, warning-derived tasks, simple dashboard overview, cleaner first screen, badges, and collapsed technical details.

## v0.61.0 - 2026-05-14
- Added planning gate and exposed planning mode in Dashboard Auto Pilot.

## v0.60.0 - 2026-05-14
- Added Feature-Only Default: feature prompts now auto-handle budget, experts, tests, guardrails, and dashboard evidence unless a real user decision is needed.

## v0.59.0 - 2026-05-14
- Added Auto Pilot next-action decisions and dashboard panel.

## v0.58.0 - 2026-05-13
- Added `scripts/expert_feedback.py` for local used/ignored expert feedback.
- Added dashboard feedback buttons and Maintenance Advisor awareness of expert feedback trends.

## v0.57.0 - 2026-05-13
- Added per-project Context Guardrails from large files and wired them into prompts, Action Pack, memory, dashboard, and advisor.

## v0.56.0 - 2026-05-13

- Added `scripts/maintenance_advisor.py` to recommend next improvements from event log and project memory evidence.
- Wired Maintenance Advisor into the dashboard and smoke test.

## v0.55.0 - 2026-05-13

- Added event deduplication/throttling to `scripts/event_log.py` with `DEFAULT_DEDUP_SECONDS`.
- Dashboard now reports emitted vs deduplicated events for the current refresh.

## v0.54.0 - 2026-05-13

- Added event log rotation in `scripts/event_log.py` with `MAX_EVENT_LINES`.
- Added compact dashboard JSON output by default, with `--pretty-json` for full readable output.
- Added a dashboard smoke-test size guard for generated JSON.

## v0.53.0 - 2026-05-13

- Extracted local Codex session parsing and analytics into `scripts/dashboard_sessions.py`.
- Further reduced `generate_dashboard.py` by moving session confidence, command summaries, and discovered project session logic out.

## v0.52.0 - 2026-05-13

- Started dashboard refactor by extracting `scripts/dashboard_components.py` for HTML helpers/CSS.
- Extracted `scripts/dashboard_projects.py` for config, project detection, and auto-selection.
- Kept `generate_dashboard.py` behavior stable while reducing duplicated responsibilities.

## v0.51.0 - 2026-05-13

- Added `scripts/action_pack.py` for ready-to-use analysis, full-stack, review, and priority-expert prompts.
- Wired Action Pack and expert prompt table into the dashboard.
- Improved auto project selection to avoid choosing the skill source repo as the monitored app.

## v0.50.0 - 2026-05-13
- Added event log, project memory, fixture/smoke tests, overview sections, collapsed raw logs, and ignored runtime artifacts.

## v0.47.0-v0.49.0 - 2026-05-13
- Added browser project selection, non-skill auto project discovery, Project Copilot, Agent / Expert Analytics, and optional project pinning.

## v0.45.0-v0.46.0 - 2026-05-13
- Added PR readiness, dashboard config, local start/stop scripts, project targeting, and handoff prompt.

## v0.44.0 - 2026-05-13
- Added project docs audit, mature existing-docs preset, token-risk guidance, bootstrap command, and dashboard/local-command wiring.

## v0.41.0-v0.43.0 - 2026-05-13
- Added sync/context/external skill checks, dashboard visibility, security docs, non-destructive bootstrap, and mature existing-docs mapping.

## v0.36.0-v0.40.0 - 2026-05-13
- Added Tool Output Budget, Cheap Skill Review, external skill intake, remote-agent handoff, portable `AGENTS.md`, self-test, dashboard/server, command guide, and CT note.

## v0.19.0-v0.35.0 - 2026-04-29 to 2026-05-01
- Added agent logs/handoffs, response economy, UI consistency, gates, cost checkpoints, Playwright/browser checks, and filtered handoffs.

## v0.1.0-v0.18.0 - 2026-04-29
- Initial coordinator, budgets, routing, app blueprint, response economy, memory, roles, gates, loading, maintenance, handoffs, QA/Test, specialists, self-check, Red Team, validation, and compression.
