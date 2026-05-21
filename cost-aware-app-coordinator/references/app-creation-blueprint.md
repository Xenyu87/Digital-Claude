# App Creation Blueprint

Crea una nuova app con scaffolding minimo, senza file "per il futuro".

## Pre-requisiti

Prima di scrivere file:

1. Conferma con l'utente: stack, target (web/mobile/CLI), licenza, posizione su disco.
2. Se il progetto richiede package manager o runtime non installati, segnala.
3. Verifica che la cartella scelta sia vuota o crea sotto-cartella.

## Step base

1. `git init` se richiesto
2. File minimi del linguaggio scelto (es. `package.json`, `pyproject.toml`)
3. Entry point unico (es. `src/index.ts`, `app.py`)
4. `.gitignore` standard del linguaggio
5. `README.md` minimo: nome, scopo, come avviare
6. File `AI_*.md` di base (vedi sotto)

## File AI_*.md di base

Crea solo se hanno contenuto utile da subito; altrimenti rimanda al primo passo non banale. I file pronti stanno in `assets/templates/`: copiali nella root del nuovo progetto e compila i campi.

- `AI_CONTEXT.md` — copia da `assets/templates/AI_CONTEXT.md`; regole in `project-context-template.md`
- `AI_STRUCTURE.md` — copia da `assets/templates/AI_STRUCTURE.md`; regole in `structure-memory-template.md`
- `AGENTS.md` — copia da `assets/templates/AGENTS.md`
- `CLAUDE.md` — copia da `assets/templates/CLAUDE.md`

`AI_DECISIONS.md`, `AI_AGENT_LOG.md`, `AI_HANDOFF.md` si creano solo quando hai qualcosa da scrivere; usa rispettivamente `assets/templates/AI_DECISIONS.md`, `AI_AGENT_LOG.md`, `AI_HANDOFF.md`.

## Cosa NON includere by default

- test scaffolding (a meno che l'utente lo chieda)
- CI / GitHub Actions
- Docker / docker-compose
- linter / formatter completi (massimo configurazione minima)
- librerie "che potrebbero servire dopo"
- pagine demo, esempi finti
- file `LICENSE` se l'utente non ha dichiarato licenza

## Conferma a metà

Dopo lo scaffolding, ferma e mostra struttura:

```
Fatto: scaffolding minimo. Struttura:
- ...
Da fare per te:
- conferma stack e prossima feature da implementare
```

## Anti-pattern

- copiare un boilerplate gigante
- generare 20 cartelle "che servono in produzione" prima del primo run
- aggiungere autenticazione, database, deploy prima che l'utente abbia detto cosa vuole
