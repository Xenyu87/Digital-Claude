# AI Resume

Last updated: 2026-05-22T15:55:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su `render_actions_section()`
- Last commit: db42462 split dashboard board renderer

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- In progress: split incrementale di `render_html()` in helper di sezione.
- Done in current step: estratta tab Azioni in `render_actions_section()` mantenendo ripresa lavoro, task, prompt e feedback esperti.

## Changed Or Untracked Files

- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M scripts/generate_dashboard.py`

## Recent Commits

- `db42462 split dashboard board renderer`
- `99ab40b split dashboard automation renderer`
- `4810712 extract dashboard runner config form`
- `d44b512 split dashboard home renderer`

## Next Step

- Estrarre `render_diagnostics_section()`; poi valutare pulizia variabili inutilizzate in `render_html()`.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
