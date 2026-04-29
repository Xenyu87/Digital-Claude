# Improvement Log

Purpose: record only useful, approved, or pending improvements to this skill. Do not load this file during normal app work.

## Rules

- Add an entry only when it changes future behavior or prevents repeated waste.
- Keep entries short.
- Mark entries as `pending`, `approved`, `rejected`, or `done`.
- Remove or compress obsolete entries during maintenance.

## Proposal Template

```text
Status: pending
Date:
Problema osservato:
Miglioramento proposto:
Motivazione:
Pro:
Contro:
Impatto token: basso|medio|alto
File della skill da modificare:
Decisione utente:
```

## Entries

Status: done
Date: 2026-04-29
Problema osservato: La skill deve nascere con un processo di miglioramento controllato.
Miglioramento proposto: Richiedere sempre approvazione prima di modificare la skill e registrare solo lezioni utili.
Motivazione: Permette evoluzione reale senza perdere controllo o aumentare rumore.
Pro: Migliora nel tempo; resta comprensibile; protegge dai cambi automatici.
Contro: Richiede una conferma quando si vuole cambiare comportamento.
Impatto token: basso
File della skill da modificare: SKILL.md, references/improvement-log.md
Decisione utente: approvato nella v0.1.0

Status: done
Date: 2026-04-29
Problema osservato: La skill controllava budget e sub-agent, ma non decideva il modello in base al tipo di lavoro.
Miglioramento proposto: Aggiungere un protocollo di selezione modello per task semplici, lavoro normale, coding pesante e rischi alti.
Motivazione: Riduce costi sui task semplici e migliora sicurezza quando il lavoro e ambiguo o rischioso.
Pro: Scelta piu economica per default; upgrade motivato; migliore uso dei sub-agent.
Contro: Dipende dai modelli esposti dal runtime; non sempre il coordinator attivo puo cambiare modello.
Impatto token: basso
File della skill da modificare: SKILL.md, references/budget-modes.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill spiegava bene l'avvio, ma guidava meno bene il lavoro dopo la classificazione iniziale.
Miglioramento proposto: Aggiungere routing operativo, working loop, definition of done, dispatch sub-agent piu esplicito e una reference compatta per task comuni.
Motivazione: Riduce letture inutili, migliora continuita operativa e rende piu chiaro quando un task e davvero finito.
Pro: Meno domande superflue; verifiche piu mirate; finali piu utili; migliore gestione di richieste miste; sub-agent piu economici e controllabili.
Contro: Aggiunge qualche regola da mantenere.
Impatto token: basso
File della skill da modificare: SKILL.md, references/task-routing.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta "studiati e migliorati ora" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill coordinava bene il processo, ma per creare app non obbligava abbastanza a definire il contratto tra frontend, backend, dati, sicurezza e verifiche.
Miglioramento proposto: Aggiungere un app creation blueprint, un riferimento dedicato, un template `app-contract.md` e campi nel project context template per il first usable slice.
Motivazione: Le app falliscono spesso quando UI, API, dati e stati di errore vengono progettati separatamente o troppo tardi.
Pro: Migliore coerenza full-stack; meno feature placeholder; verifiche piu vicine al flusso reale; migliore gestione di auth, dati e stati UI.
Contro: Richiede qualche decisione iniziale in piu nei progetti nuovi.
Impatto token: medio
File della skill da modificare: SKILL.md, references/app-creation-blueprint.md, references/task-routing.md, references/project-context-template.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta su frontend e backend del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill poteva ancora spendere troppi token in aggiornamenti, finali, riepiloghi di output e spiegazioni non richieste.
Miglioramento proposto: Aggiungere un response economy protocol, template di risposta breve e regole anti-verbosita.
Motivazione: Le fonti consultate raccomandano istruzioni chiare su formato, lunghezza, vincoli e rimozione di dettagli irrilevanti.
Pro: Risposte piu corte; meno ripetizioni; finali piu leggibili; costo token piu basso.
Contro: Richiede espansione consapevole nei task ad alto rischio o didattici.
Impatto token: basso
File della skill da modificare: SKILL.md, references/response-economy.md, references/budget-modes.md, references/task-routing.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta di ridurre token e cercare online soluzioni migliori del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill poteva rileggere spesso la struttura dell'app per orientarsi tra route, moduli, backend, dati e test.
Miglioramento proposto: Aggiungere un protocollo di structure memory e un template `AI_STRUCTURE.md` compatto.
Motivazione: Una mappa aggiornata riduce token e tempo, ma deve restare un indice e non sostituire la lettura del codice quando serve.
Pro: Meno scansioni ripetute; orientamento piu rapido; migliore memoria di flow e invarianti; aggiornabile quando cambia l'architettura.
Contro: Rischio di mappa stantia se non aggiornata; richiede fiducia limitata e controllo contro il codice.
Impatto token: basso
File della skill da modificare: SKILL.md, references/project-context-template.md, references/structure-memory-template.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta di procedere sui miglioramenti del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill non definiva profili di ruolo mirati per frontend, backend, full-stack, review e manutenzione skill.
Miglioramento proposto: Aggiungere role profiles interni e una reference compatta.
Motivazione: Un ruolo mirato aiuta a prendere decisioni migliori senza ripetere formule generiche come "programmatore esperto".
Pro: Migliori checklist mentali per UI, API, dati, sicurezza e review; poco rumore nelle risposte.
Contro: Va usato come guida interna, non come testo da ripetere.
Impatto token: basso
File della skill da modificare: SKILL.md, references/role-profiles.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato con "procedi" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill aveva buoni protocolli separati, ma mancava un controllo centrale per decidere quando agire, chiedere, pianificare, delegare, fermarsi o verificare di piu.
Miglioramento proposto: Aggiungere decision gate, risk gate, quality gate e una reference operativa dedicata.
Motivazione: Riduce errori di autonomia, evita domande inutili, aumenta sicurezza sui lavori ad alto rischio e collega meglio budget, ruoli, modelli e verifiche.
Pro: Decisioni piu coerenti; meno spreco token; migliore sicurezza; controlli piu proporzionati al rischio.
Contro: Aggiunge un passaggio mentale in piu prima dei lavori grandi.
Impatto token: basso
File della skill da modificare: SKILL.md, references/decision-risk-gates.md, references/task-routing.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato nella richiesta "ragionamento intenso, massima forza per migliorarti" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill accumulava reference utili, ma poteva diventare costosa se lette tutte a ogni task.
Miglioramento proposto: Aggiungere progressive loading con trigger espliciti per ogni reference.
Motivazione: Mantiene la skill scalabile: core sempre disponibile, dettagli caricati solo quando servono.
Pro: Meno token; meno distrazione; migliore manutenzione; reference piu modulari.
Contro: Se un trigger viene ignorato, una reference utile potrebbe non essere letta.
Impatto token: basso
File della skill da modificare: SKILL.md, references/progressive-loading.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato con "continua" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill stava migliorando rapidamente, ma rischiava prompt debt: troppe regole, log lunghi e versioni difficili da mantenere.
Miglioramento proposto: Aggiungere un protocollo di maintenance and compaction con criteri per tenere, spostare, comprimere, unire o fermarsi.
Motivazione: Una skill cost-aware deve anche limitare la propria crescita e restare leggibile.
Pro: Migliore sostenibilita; meno duplicazioni future; stop criteria chiari; manutenzione piu sicura.
Contro: Richiede disciplina quando si fanno molte iterazioni di miglioramento.
Impatto token: basso
File della skill da modificare: SKILL.md, references/maintenance-compaction.md, references/progressive-loading.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato con "continua fino a quando pensi di essere arrivata al limite" del 2026-04-29

Status: done
Date: 2026-04-29
Problema osservato: La skill poteva essere modificata nel repo ma caricata in futuro da una copia installata diversa.
Miglioramento proposto: Aggiungere un protocollo di skill sync con regole per controllare path, segnalare divergenza e non sovrascrivere senza approvazione.
Motivazione: Evita falsa sicurezza sulle versioni usate nelle sessioni future.
Pro: Versioni piu chiare; meno drift; protezione delle copie installate; release piu affidabili.
Contro: Aggiunge un controllo quando si prepara una release o sincronizzazione.
Impatto token: basso
File della skill da modificare: SKILL.md, references/skill-sync.md, references/progressive-loading.md, references/release-notes.md, references/improvement-log.md
Decisione utente: approvato con "continua fino a quando pensi di essere arrivata al limite" del 2026-04-29
