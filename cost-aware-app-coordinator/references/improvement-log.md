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
- v0.23: suppress skill/mode/role/design/file/check/commit narration unless the user must decide.
- v0.24: progress updates only for agents used, errors, blockers, risks, status requests, and user actions.
- v0.25: flexible local UI consistency check for new screens and redesigns across any app.
- v0.26: plan-first questions for ambiguous/high-impact work and stronger visual fidelity handling for screenshots/mockups.
- v0.27: universal plan gates, domain question bank, and cost checkpoints for non-UI work too.

## Latest Entries

Status: done
Date: 2026-05-01
Problema osservato: Il plan era utile ma troppo generico fuori dalla UI e non fermava sempre le fasi costose prima di broad read, agenti, test larghi, dati o deploy.
Miglioramento proposto: Aggiungere plan gate universale, domande mirate per dominio e checkpoint costo prima di passi costosi.
Motivazione: Riduce errori e token anche su backend, dati, auth, deploy, refactor, bug e nuove app.
Impatto token: basso
Decisione utente: approvato con richiesta "procedi con tutte e 3" del 2026-05-01

Status: done
Date: 2026-05-01
Problema osservato: Su task visuali o di prodotto con piu strade valide, procedere subito puo creare rework e non riflettere bene l'idea dell'utente.
Miglioramento proposto: Aggiungere mini-plan con 1-3 domande precise e una regola per screenshot/mockup ad alta fedelta con verifica visuale e sub-agenti quando portano valore.
Motivazione: Riduce errori prima del codice e mantiene flessibilita per qualunque app.
Impatto token: basso-medio
Decisione utente: approvato con richiesta "ok procedi con tutto" del 2026-05-01

Status: done
Date: 2026-05-01
Problema osservato: Una nuova pagina UI puo funzionare ma sembrare scollegata dal prodotto se non confrontata con il design locale.
Miglioramento proposto: Richiedere un controllo generale di coerenza UI contro 2-4 schermate/componenti esistenti della stessa app.
Motivazione: Ogni app ha linguaggio visivo diverso; la skill deve imparare quello locale, non imporre regole specifiche di X Manager.
Impatto token: basso
Decisione utente: approvato con richiesta "procedi, pusha e attiva" del 2026-05-01

Status: done
Date: 2026-04-30
Problema osservato: L'utente vuole vedere solo uso agenti, errori e cose importanti da fare, non stati intermedi.
Miglioramento proposto: Limitare gli update a agenti usati, errori, blocchi, rischi, status richiesto e azioni utente.
Motivazione: Riduce token e mostra solo informazioni operative importanti.
Impatto token: basso
Decisione utente: approvato con feedback diretto del 2026-04-30

Status: done
Date: 2026-04-30
Problema osservato: Screenshot reale mostra ancora update troppo lunghi: skill/mode, cappello UX/UI, scelta struttura, file intent, doc update, controlli e commit preparation.
Miglioramento proposto: Vietare esplicitamente queste routine updates e tenere skill, mode, role, model, intent e checks interni.
Motivazione: Taglia token durante il lavoro senza ridurre precisione su blocchi o azioni utente.
Impatto token: basso
Decisione utente: approvato con screenshot e feedback del 2026-04-30

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

Older entries compacted into Current Behavior Summary.
