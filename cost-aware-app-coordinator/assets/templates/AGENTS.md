# AGENTS.md

Regole condivise per qualsiasi agente AI che lavora su questo progetto.

## Lingua

Italiano per default. Termini tecnici inglesi sono ok.

## File da consultare prima di iniziare

In ordine:

1. `AI_HANDOFF.md` — solo se subentri dopo un altro agente
2. `AI_CONTEXT.md` — contesto stabile
3. `AI_STRUCTURE.md` — layout e file critici
4. `AI_DECISIONS.md` — solo se la decisione corrente le tocca

Non leggere tutta la repo. Apri altri file solo on-demand.

## Comportamento atteso

- Output corto. Default: `Fatto: ... / Verifica: ...`.
- Niente refactor opportunistico.
- Niente test scaffolding non richiesto.
- Niente sub-agent per task <3 file.

## Gate hard (chiedere sempre)

- `git push --force`, `git reset --hard`, `git clean -fd`
- migrazioni o drop su DB
- rotazione di segreti / token
- pubblicazione package, merge su branch protetti
- invio messaggi a sistemi esterni

## Cosa scrivere e dove

- decisione durevole → `AI_DECISIONS.md`
- cambio di struttura → `AI_STRUCTURE.md`
- errore o spreco → `AI_AGENT_LOG.md`
- stato corrente del task → `AI_HANDOFF.md`

## Cosa NON committare

- segreti, chiavi, token
- file `.env` non in `.gitignore`
- output di build, dipendenze
