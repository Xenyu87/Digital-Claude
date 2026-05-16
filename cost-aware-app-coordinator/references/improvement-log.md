# Improvement Log

Purpose: record only useful approved improvements. Do not load this file during normal app work.

## Rules

- Add entries only for behavior changes.
- Keep entries short.
- Compress old entries by theme when the log becomes noisy.
- Preserve user approval and current behavior.

## Current Behavior Summary

Approved on 2026-04-29:

- v0.1-v0.18: coordinator-first app workflow, budget/model policy, routing, app blueprint, response economy, structure memory, roles, gates, progressive loading, maintenance, skill sync, decisions, QA/Test, specialist triggers, self-check, Red Team, validation, compression.
- v0.19-v0.26: event-based `AI_AGENT_LOG.md`, `AI_HANDOFF.md`, tighter response economy, silent routine updates, local UI consistency, screenshot/mockup handling.
- v0.27-v0.35: universal gates, domain questions, cost checkpoints, plan contracts, final acceptance, conditional Playwright checks, bounded auto-improvement, memory hygiene, Design Intent Brief, Backend Contract Gate, targeted Browser Check, filtered handoffs.
- v0.36-v0.40: tool output budget, cheap skill review, external skill intake, remote-agent handoff, portable `AGENTS.md`, self-test, dashboard generator/server, local command guide.
- v0.41-v0.43: sync/context/external skill scripts, security docs, bootstrap script, minimal existing-docs mode, mapped AI context routing.
- v0.44-v0.77: project docs audit, PR readiness, selectable dashboard, Project Copilot, expert analytics, event log, memory, smoke tests, Action Pack, maintenance advisor, dashboard refactor, compact JSON, Context Guardrails, expert feedback, auto-pilot decisions, feature-only default, planning gate, Superplan, warning tasks, cleaner dashboard, smart cache, cache visibility, Blueprint Board POC, domains/tags, Doctor drift signals, metadata-only Auto-Update, visual panel, smarter import, new-app seed, one-command test runner, dashboard Blueprint confirmation, node descriptions, graph board, and Proxmox service setup.

## Latest Entries
Status: done
Date: 2026-05-16
Problema osservato: Moving Codex work to the Proxmox LXC needs a dashboard service on the same machine as Codex logs.
Miglioramento proposto: Add Linux service install/manage scripts, `--host`, and a Proxmox setup guide.
Motivazione: Supports one remote Codex workstation reachable from any PC.
Impatto token: basso
Decisione utente: wants Codex directly on the server

Status: done
Date: 2026-05-16
Problema osservato: Blueprint cards were readable but still not a real board with visible relationships.
Miglioramento proposto: Add a larger SVG Blueprint graph with lines, lanes, more nodes, and descriptions.
Motivazione: Makes the dashboard useful as a visual planning board, not just a list.
Impatto token: basso-medio
Decisione utente: requested many more blueprints, lines, and descriptions

Status: done
Date: 2026-05-16
Problema osservato: Blueprint cards showed node names but not enough meaning for user confirmation.
Miglioramento proposto: Add readable node descriptions from free text, files, Doctor reason, and next action.
Motivazione: Lets the user understand proposed nodes before confirming them.
Impatto token: basso
Decisione utente: requested descriptions for nodes

Status: done
Date: 2026-05-16
Problema osservato: Blueprint discovery still required terminal commands to persist nodes.
Miglioramento proposto: Add dashboard buttons to scan nodes read-only and explicitly confirm `app-blueprint.json` import; bound session text scanning.
Motivazione: Fits the desired flow and prevents dashboard memory spikes on large local logs.
Impatto token: basso
Decisione utente: requested dashboard scan/confirm workflow

Status: done
Date: 2026-05-15
Problema osservato: Full skill verification required remembering several separate commands.
Miglioramento proposto: Add `scripts/test_all.py` to run validation, fixtures, Blueprint, and dashboard smoke.
Motivazione: Makes maintenance safer and easier before syncing or committing.
Impatto token: basso
Decisione utente: proceed

Status: done
Date: 2026-05-15
Problema osservato: New apps still needed manual Blueprint node setup from a free idea.
Miglioramento proposto: Add `blueprint_board.py seed` to generate first nodes from a description.
Motivazione: Starts projects with a useful plan while avoiding direct code generation.
Impatto token: basso
Decisione utente: proceed

Status: done
Date: 2026-05-15
Problema osservato: Existing-project import created mostly generic Frontend/Backend nodes.
Miglioramento proposto: Infer feature-like nodes from pages, components, routes, services, and tests.
Motivazione: Gives the Blueprint a better starting map without requiring manual node entry.
Impatto token: basso-medio
Decisione utente: proceed

Status: done
Date: 2026-05-15
Problema osservato: Doctor reported drift but did not persist useful node evidence.
Miglioramento proposto: Add prudent Blueprint Auto-Update with suggestions and optional metadata-only writes.
Motivazione: Moves toward automation without changing project code or silently marking work done.
Impatto token: basso
Decisione utente: proceed

Status: done
Date: 2026-05-15
Problema osservato: Blueprint nodes did not yet show if intent matched real project files.
Miglioramento proposto: Add read-only Blueprint Doctor for health, related files, tests, and next focus.
Motivazione: Detects drift before building a heavier visual board or auto-sync layer.
Impatto token: basso-medio
Decisione utente: proceed

Status: done
Date: 2026-05-14
Problema osservato: Dashboard refresh repeated heavy checks and slowed skill observability.
Miglioramento proposto: Add short-lived smart cache while keeping live project state fresh.
Motivazione: Improves skill feedback loop without wasting time on repeated scans.
Impatto token: basso
Decisione utente: approved cache as skill-function improvement

Status: done
Date: 2026-05-14
Problema osservato: The dashboard first screen was useful but still looked too technical and dense.
Miglioramento proposto: Redesign the first screen with clearer hierarchy and collapsed technical details.
Motivazione: Makes daily use easier while keeping full logs available.
Impatto token: basso
Decisione utente: requested a simpler and better-looking dashboard

Status: done
Date: 2026-05-14
Problema osservato: The dashboard had the right signals but still needed simpler daily actions.
Miglioramento proposto: Add Superplan prompt, warning-derived tasks, and simple dashboard overview.
Motivazione: Turns evidence into clear next actions without manual configuration.
Impatto token: basso
Decisione utente: requested all three next refinements

Older entries compacted into Current Behavior Summary.
