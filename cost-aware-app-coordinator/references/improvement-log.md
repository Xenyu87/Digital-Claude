# Improvement Log

Purpose: record only useful approved improvements. Do not load this file during normal app work.

## Rules

- Add entries only for behavior changes.
- Keep entries short.
- Compress old entries by theme when the log becomes noisy.
- Preserve user approval and current behavior.

## Current Behavior Summary

Approved on 2026-04-29:

- v0.1-v0.3: coordinator-first workflow, budget modes, task routing, working loop, definition of done, sub-agent dispatch, and approval-based improvement loop.
- v0.4: app creation blueprint with frontend/backend/data/security contracts and first usable slice.
- v0.5: response economy protocol for shorter updates, plans, final answers, and audit reports.
- v0.6: structure memory with `AI_STRUCTURE.md` to reduce repeated project scans.
- v0.7: internal role profiles for frontend, backend, full-stack, review/audit, and skill maintenance.
- v0.8: decision, risk, and quality gates for acting, asking, planning, delegating, stopping, and verifying.
- v0.9: progressive loading so references are read only when triggered.
- v0.10: maintenance and compaction rules to prevent prompt debt.
- v0.11: skill sync protocol to avoid drift between repo source and installed copies.
- v0.19: event-based `AI_AGENT_LOG.md` for real mistakes and token waste, loaded only when useful.

## Latest Entries

Status: done
Date: 2026-04-29
Problema osservato: Mancava un autolog operativo per capire quando coordinator o agenti sprecano token, rileggono troppo, scelgono agenti sbagliati o ricevono correzioni ripetute.
Miglioramento proposto: Aggiungere `AI_AGENT_LOG.md` event-based con template compatto e trigger stretti.
Motivazione: Permette miglioramento empirico senza creare diario o costo fisso.
Impatto token: basso
Decisione utente: approvato con richiesta "fallo e pusha" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Caveman e skills.sh evidenziano valore in compressione aggressiva, ma serve evitare perdita di contesto critico.
Miglioramento proposto: Aggiungere compression pass sicura con preserve rules per sicurezza, breaking change, migrazioni, auth, deploy e debug futuro.
Motivazione: Riduce token su output/handoff/docs senza sacrificare informazioni che evitano errori costosi.
Impatto token: basso
Decisione utente: approvato con richiesta su Caveman e skills.sh del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Gli autotest erano manuali e ripetuti in shell, quindi facili da dimenticare o variare.
Miglioramento proposto: Aggiungere `scripts/validate_skill.py` per validare frontmatter, reference, progressive loading, heading duplicati, sezioni obbligatorie e line limit.
Motivazione: Repo GitHub di skill utili usano validazione deterministica per mantenere qualita e coerenza.
Impatto token: basso
Decisione utente: approvato con richiesta di ricerca GitHub approfondita del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Il coordinator puo sbagliare classificazione, specialisti, contesto o verifiche.
Miglioramento proposto: Aggiungere self-check gate, decision confidence e Red Team opzionale per rischio alto/bassa confidenza; poi comprimere core e role profiles.
Motivazione: Riduce errori costosi senza attivare agenti extra per default e abbassa il costo fisso della skill.
Impatto token: basso di default, medio solo quando Red Team viene attivato
Decisione utente: approvato se non mangia token, 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Alcuni rischi importanti erano ancora impliciti invece di avere specialisti opzionali con trigger chiari.
Miglioramento proposto: Aggiungere specialisti Security/Auth, UX/Product, Data/Migration, DevOps/Release e Performance con regole di attivazione strette.
Motivazione: Il coordinator puo usarli solo quando servono, evitando costo fisso ma coprendo rischi costosi.
Impatto token: medio quando attivati, basso quando non attivati
Decisione utente: approvato con richiesta di avere tutti gli specialisti se usati bene dal coordinator del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: QA era implicito in review/verification, ma mancava un ruolo tester dedicato.
Miglioramento proposto: Aggiungere QA/Test agent opzionale con trigger, checklist e output compatto.
Motivazione: Le app full-stack hanno bisogno di una passata specifica su flussi, stati UI, contratti API, auth e regressioni.
Impatto token: basso
Decisione utente: approvato con richiesta "procedi" sul tester del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: L'utente voleva che gli agenti sotto parlassero tra loro, ma senza perdere il controllo del coordinator.
Miglioramento proposto: Aggiungere handoff strutturati tra sub-agent, mediati dal coordinator, con template e regole anti-loop.
Motivazione: Permette coordinamento reale tra slice frontend/backend/data/review senza chat libera costosa o conflittuale.
Impatto token: basso
Decisione utente: approvato con richiesta "voglio che gli agenti sotto parlino tra di loro" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill poteva diventare costosa da usare se tutte le reference venivano lette a ogni task.
Miglioramento proposto: Progressive loading con trigger espliciti per ogni reference.
Motivazione: Mantiene il core disponibile e carica dettagli solo quando servono.
Impatto token: basso
Decisione utente: approvato con "continua" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill rischiava prompt debt dopo molte iterazioni.
Miglioramento proposto: Maintenance and compaction con criteri di keep, move, compress, merge e stop.
Motivazione: Mantiene la skill sostenibile e limita nuove regole inutili.
Impatto token: basso
Decisione utente: approvato con "continua fino a quando pensi di essere arrivata al limite" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La repo source poteva divergere dalla copia installata.
Miglioramento proposto: Skill sync protocol.
Motivazione: Evita false certezze sulla versione usata in sessioni future.
Impatto token: basso
Decisione utente: approvato con "continua fino a quando pensi di essere arrivata al limite" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Autotest locale e ricerca GitHub hanno evidenziato log lungo, heading duplicato, dettagli duplicati e bisogno di memoria decisionale durevole.
Miglioramento proposto: Compattare log, template e core; aggiungere second brain `AI_DECISIONS.md` come reference modulare; chiarire piccole incoerenze.
Motivazione: Riduce token e ambiguita, mantiene le decisioni approvate e segue il pattern GitHub di SKILL.md snello con reference on-demand.
Impatto token: basso
Decisione utente: approvato con richiesta di autotest del 2026-04-29
