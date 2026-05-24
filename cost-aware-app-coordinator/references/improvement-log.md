# Improvement Log

Diario sintetico delle modifiche alla skill. Una riga per modifica.

## Formato

```
- YYYY-MM-DD — <area> — <cosa è cambiato> — <motivo breve>
```

## Voci

- 2026-05-24 — scope-drift-detector (improvement 1) — predictive_scope_creep: estrapola trend file al completamento, accelera avviso se a X% del task hai Y% dei file — previene scope creep silenzioso
- 2026-05-24 — SKILL.md §1.5 (improvement 2) — auto-scope-checkpoint: debate automatico se brief ha 2+ verbi separati o parole vaghe — costo $0.01 vs rischio $5, pattern emerso da 100+ sessioni
- 2026-05-24 — scope-drift-detector (improvement 3) — detect_opportunistic_refactor: pattern matching su "cleanup", "refactor", "DRY", "while we're at it" nel log — identifica refactor non richiesto
- 2026-05-22 — roadmap 7 step — implementata (vedi AI_DECISIONS del progetto dashboard-claude-coordinator): coordination-sedimentation, MAR-reviewer, debate scope, background-drain, auto-curriculum, pipeline-dsl, external-routing — espansione coordinata skill + dashboard
- 2026-05-22 — SKILL.md §3 + references/auto-delegation-gate.md + §5 mappa — Auto-delegation gate: introdotto enforcement a 4 gate (routing-hint, tetto Opus >3 file, Explore per grep >2 file, ops-runner per ops+Economico) — dati reali 14gg: drift suggested→used ~50% (45 task sonnet→opus, 19 haiku→opus su 165 task con hint); costo Opus inflazionato senza beneficio qualitativo
- 2026-05-21 — SKILL.md §3 — aggiunta nota baseline modelli 2026-05 (Haiku 4.5/Sonnet 4.6/Opus 4.7) + /model per switch sessione — allineamento a CLI v2.1.142-145
- 2026-05-21 — SKILL.md §3 — nota flag subagent dispatched (--model, --permission-mode) + Fast mode Opus 4.7 — da release notes CLI
- 2026-05-21 — references/mcp-integrations.md — MCP Registry come fonte canonica, deprecazione Third-Party list, MCP_TOOL_TIMEOUT >60s fix — da commit modelcontextprotocol/servers
- 2026-05-21 — references/progressive-loading.md — nota /plugin projected context cost come segnale budget — da CLI v2.1.143
- 2026-05-21 — references/specialist-agents.md — esempio flag dispatched + nota wshobson/agents (valutato, no adozione wholesale) — da research plan-1
- 2026-05-21 — references/maintenance-compaction.md — reminder revisione baseline modelli ad ogni minor CLI — prevenzione drift versione
- 2026-05-16 — scripts/auto_log_task.py — parsa ~/.claude/projects/.../X.jsonl per token reali sessione, POST a /api/log — risolve "dashboard vuota di costi/token" emerso da uso reale 3D Pad
- 2026-05-15 — scripts/propose_lesson.py — skip su skill repo (SKILL.md + references/) — elimina meta-rumore di voci TBD a ogni commit di skill maintenance
- 2026-05-15 — scripts/hooks/pre-commit + scripts/install_hooks.py — hook git automatico: run_tests gira a ogni commit, blocca su fail — risposta al pattern "non voglio lanciare manualmente i test"
- 2026-05-15 — tests/ + scripts/run_tests.py — pytest con 26 test (regressione bug v0.9.5, propose_lesson, validate_skill) + wrapper unico — copre il rischio di bug silenziosi futuri
- 2026-05-15 — ~/.claude/agents/qa-tester.md — subagent custom "qa-tester" registrato — il coordinator può ora delegare scrittura test a un specialista (estende l'elenco di subagent_type disponibili)
- 2026-05-15 — scripts/check_version.py + ~/.claude/commands/skill-status.md — fix estrazione versione: era first-match (sempre v0.1.0), ora semver max — bug emerso durante primo uso /skill-status, registrato in AI_AGENT_LOG.md
- 2026-05-14 — ~/.claude/commands/skill-status.md — riassunto stato in chat senza aprire dashboard — UX rapida per utenti non programmer
- 2026-05-14 — references/scope-checkpoint.md + SKILL.md §8 — protocollo scope ambiguo (rispecchia → 2-3 scelte → primo step piccolo) — protegge da rabbit hole su task vaghi
- 2026-05-14 — ~/.claude/commands/newproject.md — slash command per creare nuovi progetti dalla chat — riduce attrito per utenti non programmer
- 2026-05-14 — scripts/propose_lesson.py — auto-write in AI_AGENT_LOG.md con placeholder TBD invece di stampa terminale — elimina passo manuale di copia-incolla
- 2026-05-14 — SKILL.md §7 + §16 — annuncio attivazione 1 riga + regola completamento TBD al primo turno — UX semplificata per utenti non programmer
- 2026-05-14 — scripts/check_version.py — confronto versione sorgente vs installata + POST a dashboard — chiude il loop drift tracking (T3 M4)
- 2026-05-13 — scripts/log_task.py — logger best-effort verso skill-dashboard (POST /api/log) — apre canale observability (Traccia 3 v1.0)
- 2026-05-13 — references/reflexion-loop.md + skill_library/ + scripts/propose_lesson.py — pattern Reflexion+Voyager applicato alla skill — apre il loop incident→knowledge update senza fine-tuning
- 2026-05-13 — SKILL.md §16 + §5 mappa — riferimento a reflexion-loop e skill_library — chiude il flusso self-improvement realistico
- 2026-05-13 — scripts/sync_skill.py — aggiunto skill_library/ ai dir sincronizzati
- 2026-05-13 — SKILL.md §19 + references/mcp-integrations.md — aggiunta sezione MCP con format Server:tool — allineamento a best-practice Anthropic e a pattern Composio/awesome-claude-skills
- 2026-05-13 — README.md — riscritto: compatibilità cross-tool (Codex/Cursor/Gemini CLI), versione corrente, count reference (26), soglia 450 — drift accumulato fino a v0.7.0
- 2026-05-13 — scripts/validate_skill.py — SKILL_MAX_LINES 350→450 — limite ufficiale Anthropic è 500, margine ragionevole
- 2026-05-13 — scripts/sync_skill.py — aggiunto `recipes/` ai dir sincronizzati — la copia installata era priva delle ricette
- 2026-05-13 — references/release-notes.md — voce v0.7.0 con i cambi B+A+C — comportamento osservabile cambia (matcher + budget default + sync)
- 2026-05-13 — references/progressive-loading.md — aggiunte default-stacks/deploy-paths/visual-first-testing alla tabella trigger — chiude drift introdotto in v0.5.0
- 2026-05-13 — SKILL.md §2 — aggiunti default per categoria di task (puntatore a task-routing.md) — riallinea SKILL ai default già documentati in task-routing
- 2026-05-13 — SKILL.md frontmatter — description accorciata da ~620 a ~360 char mantenendo trigger phrases positivi/negativi — best-practice Anthropic per skill matcher
- 2026-05-13 — SKILL.md §9 + references/specialist-agents.md — lista subagent_type spostata da SKILL alla reference (canonica) ed estesa a 9 tipi correnti di Claude Code — single source of truth + completezza
- 2026-05-13 — scripts/validate_skill.py — aggiunti check_recipes, check_scripts, check_templates — protegge da ricette/script/template orfani
- 2026-05-13 — SKILL.md §17 + §19 — aggiunta cadenza review skill (ogni release minor) e aggiornata descrizione validator coi nuovi check — chiude il loop di manutenzione
- 2026-05-13 — SKILL.md §4 — aggiunti AI_STRUCTURE.md e AI_DECISIONS.md alla lettura iniziale (condizionati) — allinea SKILL con references/agent-handoff.md
- 2026-05-13 — SKILL.md §12 Step 2 — chiarito che il deploy va configurato subito dopo il primo `npm run dev` locale — rimuove ambiguità tra dev e deploy
- 2026-05-13 — scripts/validate_skill.py — esteso REQUIRED_SECTIONS a tutte le sezioni portanti (Fast path, Selezione modello, §12-18) — protegge da rimozioni accidentali in refactor futuri
- 2026-05-13 — scripts/validate_skill.py — aggiunto supporto a glob (`assets/scripts/deploy-*.sh`) negli asset citati — chiude lacuna del regex precedente
- 2026-05-13 — SKILL.md §3, §16 — fix refuso "scegli il più piccolo" e anglismo "run corrente" → "sessione corrente" — pulizia testo italiano
- 2026-05-02 — references/progressive-loading.md — nuovo reference dedicato al tuning del loading — porta in chiaro la mappa trigger e dà un punto unico per affinare cosa caricare
- 2026-05-02 — references/self-improvement.md — replicato dalla skill installata al progetto sorgente — risolto drift tra le due copie
- 2026-05-02 — SKILL.md — aggiunta sezione "Selezione del modello" — esplicita la regola "smallest capable model" allineata a Opus/Sonnet/Haiku
- 2026-05-02 — SKILL.md — aggiunta sezione "Working loop" — rende esplicito il ciclo budget→contesto→piano→implementazione→verifica→chiusura
- 2026-05-02 — SKILL.md — aggiunta sezione "Definition of Done" — chiude i task con conferma user-facing per UI a rischio medio/alto
- 2026-05-02 — SKILL.md — sezione "Specialisti" estesa con criteri "quando NON attivare" — riduce sub-agent inutili per task piccoli
- 2026-05-02 — SKILL.md — sezione "Miglioramento skill" estesa con template di proposta di automiglioramento — formalizza la richiesta di approvazione
- 2026-05-02 — references/maintenance-compaction.md — rimossa duplicazione soglie con compression-pass.md — single source of truth
- 2026-05-02 — scripts/validate_skill.py — aggiunte "Working loop" e "Definition of Done" a REQUIRED_SECTIONS — protegge la spina dorsale procedurale
- 2026-05-02 — SKILL.md — frontmatter description riscritta in terza persona con trigger phrases — best-practice ufficiale Anthropic, evita under-trigger
- 2026-05-02 — assets/templates/ — creati 7 file copiabili (AI_*.md, AGENTS.md, CLAUDE.md) — tier-3 progressive disclosure, evita di estrarre template embedded dai reference
- 2026-05-02 — scripts/validate_skill.py — aggiunto check coerenza assets/ — rileva citazioni a file mancanti
- 2026-05-02 — references/app-creation-blueprint.md — aggiornato per puntare a assets/templates/ — workflow di scaffolding ora usa file pronti
- 2026-05-02 — SKILL.md §1 — aggiunti esempi di trigger per categoria — migliora il discovery, riduce under-trigger
- 2026-05-02 — SKILL.md §4/§9/§13 — aggiunto ragionamento causale a 3 regole atomiche — best-practice writing-skills, gli LLM seguono meglio reasoning che istruzioni meccaniche
- 2026-05-02 — scripts/validate_skill.py — check duplicati heading nei reference ora ignora H3+ — falso positivo su release-notes.md (Aggiunto/Cambiato si ripetono per versione)
- 2026-05-02 — references/{project-context,structure-memory,second-brain,cross-agent-handoff,agent-autolog}-template.md — rimossi blocchi markdown embedded duplicati con assets/templates/ — single source of truth, riduce contesto al caricamento
- 2026-05-02 — scripts/sync_skill.py — nuovo script cross-platform per sync sorgente → installata — sostituisce Copy-Item PowerShell manuale, riduce drift
- 2026-05-02 — README.md, .gitignore — aggiunti alla root in vista del repo pubblico — README descrive struttura/installazione, gitignore protegge settings.local.json
- 2026-05-02 — references/self-improvement.md — checklist copiabile in formato `- [ ]` — pattern raccomandato dalla doc Anthropic per workflow lunghi (Claude può copiare e spuntare)
- 2026-05-02 — references/self-improvement.md — aggiunto pattern "test su istanza fresca" (Claude A → Claude B) — best-practice ufficiale di iterative skill development
- 2026-05-02 — scripts/validate_skill.py — documentate le costanti SKILL_MAX_LINES, REFERENCE_MAX_LINES, DESCRIPTION_MAX_CHARS — anti-pattern voodoo constants (Ousterhout)
- 2026-05-02 — scripts/validate_skill.py — aggiunti check conformità frontmatter Anthropic (name <=64 char, regex `[a-z0-9-]+`, no reserved word; description <=1024 char) — protegge le regole ufficiali
- 2026-05-02 — evaluations/scenarios.md — aggiunti 6 scenari di comportamento atteso in italiano semplice — best-practice "build evaluations first" adattata a utente non programmatore (no JSON, no infra di test)
- 2026-05-02 — SKILL.md §3, references/specialist-agents.md, evaluations/scenarios.md — selezione modello sub-agent automatizzata via tabella decisionale haiku/sonnet/opus; main-agent solo segnalato all'utente — l'utente vuole switch automatico, ma è fattibile solo per i sub-agent
- 2026-05-02 — references/agent-handoff.md, SKILL.md §10, evaluations/scenarios.md — pattern di comunicazione tra sub-agent dello stesso coordinator (router via coordinator, file `AI_HANDOFF.md`, `SendMessage` per riprendere) — l'utente vuole sub-agent che si scambino info; non è possibile direttamente, lo gestisce il coordinator
- 2026-05-02 — recipes/ — cartella nuova con README + 5 ricette (landing-page, crud-with-auth, data-dashboard, content-site, bot) — riempie il gap "cookbook per non programmer", ogni ricetta è scheletro modulare non boilerplate fisso
- 2026-05-02 — references/default-stacks.md — 3 stack di default (web full-stack, sito contenuti, backend long-running) — evita di chiedere "quale framework" ad ogni nuova app
- 2026-05-02 — references/deploy-paths.md + assets/scripts/deploy-{vercel,netlify,railway}.sh — percorsi e script di deploy concreti — coloma il gap "come metto l'app online"
- 2026-05-02 — references/visual-first-testing.md — protocollo URL/azione/atteso/segnalazioni codificato — utente non programmer non legge stack trace
- 2026-05-02 — SKILL.md §12 — aggiunti Step 0 (riconosci ricetta) / Step 2 (deploy presto) / Step 3 (test visivo) — workflow nuova app ora copre l'intero ciclo "idea → online"
- 2026-05-03 — SKILL.md frontmatter description — esplicito "NON attivare per fix di una stringa, rename locale, modifica isolata di 1 file noto" — utente segnala 40% del budget token per modifica semplice; description troppo "pushy" causava over-trigger
- 2026-05-03 — SKILL.md §0 — nuova sezione "Fast path" come prima sezione operativa: per modifiche locali (1-3 file noti, scope chiaro, no auth/dati/deploy) → no reference, no Agent, output 2 righe — taglia il costo fisso per task semplici
- 2026-05-03 — SKILL.md — compattato da 307 a ~190 righe (Working loop denso, Selezione modello tabella spostata in specialist-agents.md, Handoff lista file compattata, Definition of Done 6→3 bullet) — riduce il costo di caricamento ad ogni attivazione
- 2026-05-03 — references/specialist-agents.md — accolta tabella decisionale model haiku/sonnet/opus precedentemente in SKILL.md — single source of truth
- 2026-05-03 — evaluations/scenarios.md — scenario 9 per coprire la fast path — è il più importante per il consumo token
- 2026-05-17 — scripts/auto_log_task.py — estrazione da jsonl di `duration_seconds`, `tool_calls_count`, `summary`, `category` (euristica regex sul primo prompt) — la dashboard riceveva 4 campi morti, dati ora utili
- 2026-05-17 — SKILL.md §1 + references/homelab-ops.md (nuovo) — aggiunta categoria `ops` per task sistema/infra (systemd, ssh, lxc, syncthing, porte, deploy); reference operativo con comandi, pattern ricorrenti, anti-pattern del homelab — ~50% delle interazioni reali erano ops mascherate da "modifica", la skill non aveva know-how operativo riusabile

## Regole

- una riga per cambio
- niente narrazione
- niente correzioni minori (typo) salvo che indichino un problema sistemico
- se la modifica cambia comportamento osservabile, aggiungila anche in `release-notes.md`

## Cosa registrare

- nuova sezione o reference
- regola modificata
- soglia modificata (righe, budget)
- aggiunta o rimozione di un ruolo

## Cosa NON registrare

- formattazione
- typo
- modifiche che il validator avrebbe imposto comunque

## Manutenzione

Quando il file supera ~150 righe, archivia voci più vecchie di 6 mesi in `release-notes.md` come riepilogo.
