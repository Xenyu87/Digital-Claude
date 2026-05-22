# AI Resume

Last updated: 2026-05-22T05:20:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su split Automazione
- Last commit: d44b512 split dashboard home renderer

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- In progress: split incrementale di `render_html()` in helper di sezione.
- Done in current step: estratto `render_runner_config_form()`.

## Changed Or Untracked Files

- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M scripts/generate_dashboard.py`

## Recent Commits

- `d44b512 split dashboard home renderer`
- `58690f9 clean dashboard board renderer`
- `98a2806 make blueprint board action focused`
- `53373f6 chore: sync completo skill locale -> repo (major cleanup + nuovi file)`

## Next Step

- Continuare lo split con `render_automation_section`, poi `render_lavagna_section`, `render_actions_section`, `render_diagnostics_section`.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
