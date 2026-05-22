# AI Resume

Last updated: 2026-05-22T19:40:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali in corso su UX Lavagna
- Last commit: 84ee003 split dashboard diagnostics renderer

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- In progress: split incrementale di `render_html()` in helper di sezione.
- Done in current step: primo pannello Lavagna reso operativo con prossimo task, contatori, comandi diretti; wizard/screenshot spostati sotto Strumenti lavagna; React Flow ha barra Prossima azione.

## Changed Or Untracked Files

- `M AI_RESUME.md`
- `M AI_HANDOFF.md`
- `M scripts/generate_dashboard.py`

## Recent Commits

- `84ee003 split dashboard diagnostics renderer`
- `e73b104 split dashboard actions renderer`
- `db42462 split dashboard board renderer`
- `99ab40b split dashboard automation renderer`

## Next Step

- Valutare test visuale/manuale della Lavagna e poi migliorare copia task/empty states se il primo pannello risulta ancora troppo tecnico.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
