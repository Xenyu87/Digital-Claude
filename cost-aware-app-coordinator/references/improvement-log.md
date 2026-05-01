# Improvement Log

Purpose: record only useful approved improvements. Do not load this file during normal app work.

## Rules

- Add entries only for behavior changes.
- Keep entries short.
- Compress old entries by theme when the log becomes noisy.
- Preserve user approval and current behavior.

## Current Behavior Summary

Approved on 2026-04-29:

- v0.1-v0.3: coordinator-first workflow, budget modes, task routing, working loop, definition of done, sub-agent dispatch, and approval-based improvement loop.
- v0.4: app creation blueprint with frontend/backend/data/security contracts and first usable slice.
- v0.5: response economy protocol for shorter updates, plans, final answers, and audit reports.
- v0.6: structure memory with `AI_STRUCTURE.md` to reduce repeated project scans.
- v0.7: internal role profiles for frontend, backend, full-stack, review/audit, and skill maintenance.
- v0.8: decision, risk, and quality gates for acting, asking, planning, delegating, stopping, and verifying.
- v0.9: progressive loading so references are read only when triggered.
- v0.10: maintenance and compaction rules to prevent prompt debt.
- v0.11: skill sync protocol to avoid drift between repo source and installed copies.
- v0.19: event-based `AI_AGENT_LOG.md` for real mistakes and token waste, loaded only when useful.
- v0.20: shorter routine output; precision reserved for user actions, risks, choices, and blockers.
- v0.21: `AI_HANDOFF.md` bridge for Codex, Claude Code, and other agents on the same project.
- v0.22: silent-by-default progress updates; extra detail only on request, risk, blocker, or user action.
- v0.23: suppress skill/mode/role/design/file/check/commit narration unless the user must decide.
- v0.24: progress updates only for agents used, errors, blockers, risks, status requests, and user actions.
- v0.25: flexible local UI consistency check for new screens and redesigns across any app.
- v0.26: plan-first questions for ambiguous/high-impact work and stronger visual fidelity handling for screenshots/mockups.
- v0.27: universal plan gates, domain question bank, and cost checkpoints for non-UI work too.
- v0.28: plain-language plan contract and final visual/functional acceptance feedback with autolog on missed intent.
- v0.29: conditional Playwright UI checks with cost checkpoint before expensive browser setup.
- v0.30: bounded auto-improvement runs and plain `Come provarlo` steps for user-facing changes.
- v0.31: memory hygiene write filters for decisions and agent logs.
- v0.32: Design Intent Brief for important UI work.
- v0.33: Backend Contract Gate for risky backend/API/data-facing work.
- v0.34: concrete targeted Playwright Browser Check.

## Latest Entries

Status: done
Date: 2026-05-01
Problema osservato: La regola Playwright era utile ma ancora generica su cosa controllare concretamente.
Miglioramento proposto: Aggiungere Browser Check mirato: screenshot, console, workflow principale, stati toccati e artifact utili.
Motivazione: Aumenta sicurezza UI senza trasformare ogni task in E2E ampio.
Impatto token: basso-medio
Decisione utente: approvato con richiesta di arrivare fino a v0.35

Status: done
Date: 2026-05-01
Problema osservato: Backend e database falliscono spesso per contratti impliciti: input, output, permessi, dati esistenti o errori non chiariti.
Miglioramento proposto: Aggiungere Backend Contract Gate prima di API/RPC/server action/job rischiosi.
Motivazione: Riduce regressioni e rende verificabile il comportamento anche da UI.
Impatto token: basso
Decisione utente: approvato con richiesta di arrivare fino a v0.35

Status: done
Date: 2026-05-01
Problema osservato: Le migliori skill design distinguono prima l'intento visivo, altrimenti l'agente puo oscillare tra fedelta, coerenza locale e redesign creativo.
Miglioramento proposto: Aggiungere Design Intent Brief compatto per UI medie o rischiose.
Motivazione: Riduce rework e rende il risultato valutabile anche senza leggere codice.
Impatto token: basso
Decisione utente: approvato con richiesta di arrivare fino a v0.35

Status: done
Date: 2026-05-01
Problema osservato: Le ricerche su memoria agentica evidenziano rischio di drift, memoria rumorosa e salvataggio di contenuti non verificati.
Miglioramento proposto: Aggiungere filtro di scrittura per memorie: verificate, durevoli, azionabili e sicure.
Motivazione: Migliora memoria senza aumentare contesto fisso.
Impatto token: basso
Decisione utente: approvato con richiesta di arrivare fino a v0.35

Older entries compacted into Current Behavior Summary.
