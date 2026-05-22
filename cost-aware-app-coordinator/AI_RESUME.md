# AI Resume

Last updated: 2026-05-22T20:02:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su expand/collapse Lavagna e Playwright
- Last commit: ba6819f make blueprint nodes show UI structure

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- Done in current step: primo pannello Lavagna reso operativo con prossimo task, contatori, comandi diretti; wizard/screenshot spostati sotto Strumenti lavagna; React Flow ha barra Prossima azione.
- Done in current step: scanner Lavagna ora crea nodi distinti per bottoni UI e grafici, collega i figli al componente padre, e passa sotto-nodi/descrizioni precise al dettaglio React Flow.
- Done in current step: Playwright installato/configurato; Lavagna ha controlli canvas `Apri tutti`/`Chiudi tutti` e toggle sui nodi componente per mostrare/nascondere figli UI.

## Changed Or Untracked Files

- `M scripts/blueprint_board.py`
- `M scripts/dashboard_components.py`
- `M frontend/blueprint-flow/src/main.jsx`
- `M frontend/blueprint-flow/src/styles.css`
- `M scripts/blueprint_board_test.py`
- `M package.json`
- `M package-lock.json`
- `A playwright.config.js`
- `A tests/visual/blueprint-board.spec.js`
- `A tests/fixtures/visual-blueprint-app/...`
- `A docs/ai/visual-testing.md`
- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M AI_CONTEXT.md`
- `M docs/ai/app-contract.md`

## Recent Commits

- `ba6819f make blueprint nodes show UI structure`
- `969727a make board first panel action focused`
- `84ee003 split dashboard diagnostics renderer`
- `e73b104 split dashboard actions renderer`

## Next Step

- Commit/push di expand/collapse + Playwright + docs. Prossimo step naturale: ridurre rumore scanner residuo e migliorare layout automatico dei figli quando un componente viene aperto.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
