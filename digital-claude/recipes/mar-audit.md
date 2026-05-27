# Ricetta: MAR Audit

Quando e come attivare il Multi-Agent Reflexion reviewer per un audit strutturato.

## Cosa fa

Spawna 3 reviewer Sonnet in parallelo (sicurezza, performance, leggibilità) + 1 aggregatore Haiku che produce un consensus. Riduce i falsi positivi rispetto a una singola review e cattura angolazioni complementari.

## Quando attivarlo

- diff tocca >5 file
- categoria=audit
- categoria=modifica AND >5 file AND budget non Economico
- pre-merge su moduli critici: auth, schema DB, API pubblica, script di deploy
- l'utente chiede "review completa" o "audit cross-modulo"

Regola rapida: se useresti `code-reviewer` ma il diff è grande o il rischio è alto, usa `mar-reviewer`.

## Costo stimato

~3 chiamate Sonnet (~50k token ciascuna) + 1 Haiku (~15k token) = ~$0.05–0.15 per audit tipico.
Confronto: ~5 minuti utente per review manuale equivalente.

## Come attivarlo

Dalla main session:

```
Agent(subagent_type="mar-reviewer", prompt="
Esegui un MAR audit sui file modificati nell'ultimo commit.
git diff HEAD~1 HEAD --name-only per la lista.
Riporta solo il consensus finale.
")
```

Oppure specificando file:

```
Agent(subagent_type="mar-reviewer", prompt="
Esegui un MAR audit su: src/app/api/auth/route.ts, src/lib/db.ts, src/middleware.ts.
Focus su: security e correttezza delle query.
")
```

## Output atteso

```
## Consensus review

### Blocking
- src/api/auth/route.ts:42 — token non validato prima dell'uso

### Should fix
- src/lib/db.ts:18 — query senza LIMIT, rischio N+1

### Nit
- src/middleware.ts:7 — nome variabile `x` non descrittivo

### Verdetto
APPROVA CON RISERVA
```

## Integrazione con pipeline

Vedi `recipes/pipelines/feature-with-tests.yml` per un esempio di MAR come step `review` finale.
