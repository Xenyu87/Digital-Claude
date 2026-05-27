# Role Profiles

Profili di ruolo. Attivati come prompt/sotto-task. Non sono agenti separati a meno che Claude Code non offra un `subagent_type` dedicato.

## Frontend
- Focus: UI, componenti, accessibilità, stato client
- Output: diff componenti + nota su test manuale browser
- Skip: logica server, schema DB

## Backend
- Focus: API, modelli, business logic, validazione input
- Output: diff + esempio chiamata
- Skip: pixel UI

## Full-stack
- Solo quando un task tocca davvero entrambi i lati. Default: separa.

## QA / Test
- Vedi `qa-test-agent.md`

## Security / Auth
- Focus: autenticazione, autorizzazione, segreti, OWASP top 10
- Gate: ogni modifica a flow auth è Massima sicurezza
- Output: finding + fix proposto + riferimento OWASP se applicabile

## UX / Product
- Focus: flussi utente, naming, microcopy, gerarchia informazione
- Output: proposta breve + alternativa
- Skip: implementazione dettagliata

## Data / Migration
- Focus: schema, migrazioni, integrità referenziale, backup
- Gate: ogni migrazione su dati esistenti è gate hard
- Output: piano migrazione + rollback

## DevOps / Release
- Focus: CI/CD, build, deploy, configurazione ambienti
- Gate: modifiche a pipeline produzione sono gate hard
- Output: diff config + checklist rollout

## Performance
- Focus: latenza, throughput, memoria, query DB lente
- Output: misura prima / misura dopo. Niente claim senza numeri.

## Review / Audit
- Solo lettura. Nessuna modifica.
- In Claude Code: usa il subagent `code-reviewer` quando disponibile.
- Output: finding con severità (alta/media/bassa), file:riga, fix proposto

## Skill maintenance
- Modifica skill, prompt, configurazione harness
- Esegui `scripts/validate_skill.py` prima di chiudere
- Aggiorna `improvement-log.md` e `release-notes.md`

## Quando NON attivare un ruolo

- task piccolo che il main agent chiude in 2 turni
- ruolo non riduce rischio o tempo significativamente
- task non chiaro: prima chiarisci, poi attiva

## Combinazioni utili

- Backend + QA: nuova API con test
- Security + Review/Audit: code review focalizzata su auth
- Data/Migration + DevOps: rollout migrazione produzione
