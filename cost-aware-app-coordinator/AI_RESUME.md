# AI Resume

Last updated: 2026-05-22T16:05:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su `render_diagnostics_section()`
- Last commit: e73b104 split dashboard actions renderer

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- In progress: split incrementale di `render_html()` in helper di sezione.
- Done in current step: estratta tab Diagnostica in `render_diagnostics_section()` e rimossa variabile `estimates` inutilizzata da `render_html()`.

## Changed Or Untracked Files

- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M scripts/generate_dashboard.py`

## Recent Commits

- `e73b104 split dashboard actions renderer`
- `db42462 split dashboard board renderer`
- `99ab40b split dashboard automation renderer`
- `4810712 extract dashboard runner config form`

## Next Step

- Valutare uno step UX sulla Lavagna: rendere il primo pannello ancora piu operativo e ridurre i dettagli tecnici visibili di default.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
