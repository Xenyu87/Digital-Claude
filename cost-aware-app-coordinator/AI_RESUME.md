# AI Resume

Last updated: 2026-05-22T05:30:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su `render_automation_section()`
- Last commit: 4810712 extract dashboard runner config form

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- In progress: split incrementale di `render_html()` in helper di sezione.
- Done in current step: estratta tab Automazione in `render_automation_section()`.

## Changed Or Untracked Files

- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M scripts/generate_dashboard.py`

## Recent Commits

- `4810712 extract dashboard runner config form`
- `d44b512 split dashboard home renderer`
- `58690f9 clean dashboard board renderer`
- `98a2806 make blueprint board action focused`

## Next Step

- Estrarre `render_lavagna_section()` mantenendo React Flow e wizard invariati; poi `render_actions_section()` e `render_diagnostics_section()`.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
