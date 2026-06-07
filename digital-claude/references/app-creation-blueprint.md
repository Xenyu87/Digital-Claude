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

## Regola post-modifica (obbligatoria su app attive)

Dopo OGNI modifica al codice di un'app già in esecuzione:

1. **Build** → `npm run build` (Next.js) o equivalente
2. **Restart** → `systemctl restart <service>` o `pm2 restart`
3. **Verifica** → controlla che la pagina/endpoint risponda prima di dire "done"

Non delegare questi step all'utente. Non dichiarare il task completato prima di averli eseguiti.

## Security gate (obbligatorio prima del deploy)

Prima di ogni deploy su stable o su internet, esegui in sequenza:

1. **Secrets scan** → `Agent(subagent_type="secrets-scanner")` — blocca se trova SECRET con livello CRITICO
2. **Code security scan** → `Agent(subagent_type="code-security-scanner")` — blocca se trova VULN HIGH
3. **Dependency audit** → `Agent(subagent_type="dependency-checker")` — segnala ma non blocca (a meno di CVE critical)

Se un agente trova blocchi: non procedere col deploy, mostrare i finding all'utente e aspettare fix confermati.

Questi check **non si saltano** anche se l'utente dice "deploy veloce" — al massimo si può rimandare il dependency audit.

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
