# AI Resume

Last updated: 2026-05-23T07:05:00
Project: /root/.codex/skills/cost-aware-app-coordinator

## Current State

- Goal: Lavagna come centro operativo semplice e potente
- Branch: master
- Git state: modifiche locali doc-only su Homelab/reference ops; output generati non tracciati in `reports/`
- Last commit: 45695e1 render generated frontend preview client side

## Latest Work

- Done: Lavagna orientata ad azioni con view model `blueprint-view-v1`.
- Done: filtri scanner per ridurre rumore da controlli interni dashboard.
- Done: dashboard divisa in tab Home, Lavagna, Azioni, Automazione, Diagnostica.
- Done: renderer legacy rimosso e sezioni dashboard duplicate ripulite.
- Done in current step: primo pannello Lavagna reso operativo con prossimo task, contatori, comandi diretti; wizard/screenshot spostati sotto Strumenti lavagna; React Flow ha barra Prossima azione.
- Done in current step: scanner Lavagna ora crea nodi distinti per bottoni UI e grafici, collega i figli al componente padre, e passa sotto-nodi/descrizioni precise al dettaglio React Flow.
- Done in current step: Playwright installato/configurato; Lavagna ha controlli canvas `Apri tutti`/`Chiudi tutti` e toggle sui nodi componente per mostrare/nascondere figli UI.
- Done in current step: quando un componente viene espanso, bottoni/grafici figli vengono posizionati accanto al padre; Playwright controlla anche questa relazione spaziale.
- Done in current step: Lavagna split-view con preview frontend laterale; fallback generato direttamente in React dai nodi scanner per evitare 404; selezionare un nodo UI evidenzia l'elemento corrispondente nella preview.
- Done in current step: Homelab aggiornato con procedura Codex Skill per build Lavagna/React Flow, rigenerazione dashboard e troubleshooting preview/404.

## Changed Or Untracked Files

- `M references/homelab-ops.md`
- `M AI_RESUME.md`
- external: `/root/Progetti/homelab/HOMELAB.md`
- untracked generated/output: `reports/`, `../.system/`

## Recent Commits

- `45695e1 render generated frontend preview client side`
- `3309a6d add blueprint frontend preview pane`
- `ba6819f make blueprint nodes show UI structure`
- `969727a make board first panel action focused`
- `84ee003 split dashboard diagnostics renderer`
- `e73b104 split dashboard actions renderer`

## Next Step

- Commit/push eventuale della nota Homelab se vuoi versionarla nella skill. Prossimo step naturale: supporto piu guidato per `frontend_preview_url`/dev server live e mapping DOM reale -> nodi Lavagna.

## Read Next Only If Needed

- `AI_CONTEXT.md` for routing and project docs.
- `AI_HANDOFF.md` only when continuing active work.
- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.
