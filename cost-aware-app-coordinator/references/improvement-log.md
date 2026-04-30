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
- v0.20: shorter routine output; precision reserved for user actions, risks, choices, and blockers.
- v0.21: `AI_HANDOFF.md` bridge for Codex, Claude Code, and other agents on the same project.
- v0.22: silent-by-default progress updates; extra detail only on request, risk, blocker, or user action.

## Latest Entries

Status: done
Date: 2026-04-30
Problema osservato: Gli update durante il lavoro consumavano troppi token e davano informazioni aggiuntive non richieste.
Miglioramento proposto: Rendere gli update silenziosi di default con gate esplicito per parlare solo se serve.
Motivazione: Riduce rumore e token mantenendo precisione su blocchi, rischi e azioni utente.
Impatto token: basso
Decisione utente: approvato con feedback diretto del 2026-04-30

Status: done
Date: 2026-04-29
Problema osservato: L'utente vuole lavorare sulla stessa app con Codex e Claude Code senza incasinare contesto, decisioni e prossimo passo.
Miglioramento proposto: Aggiungere cross-agent handoff con `AI_HANDOFF.md` e template dedicato.
Motivazione: Permette passaggio controllato tra agenti usando file condivisi, senza memoria nascosta o diario.
Impatto token: basso
Decisione utente: approvato con richiesta diretta del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: Durante test reali sulla app, gli output erano ancora troppo lunghi e spiegavano routine fix come "ho sistemato X perche Y".
Miglioramento proposto: Rendere default il formato fatto/verifica e usare dettaglio solo per azioni utente, rischi, scelte o blocchi.
Motivazione: Riduce token e rumore senza perdere precisione dove serve davvero.
Impatto token: basso
Decisione utente: approvato con feedback diretto del 2026-04-29

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

Older entries compacted into Current Behavior Summary.
