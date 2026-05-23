---
name: cost-aware-app-coordinator
description: Coordina task software non triviali (nuova app, audit, bug rescue, migrazione, deploy, refactor cross-modulo, miglioramento skill). Attiva quando serve pianificazione, scelta stack, multi-agente, file AI_*.md. NON usare per fix di una stringa, rename locale, cambio colore, modifica isolata di 1 file noto, domande concettuali.
---

# Cost-Aware App Coordinator

Coordina lavoro su progetti software riducendo spreco di token e output troppo lunghi. Supporta handoff multi-agente tramite file `AI_*.md`.

## Lingua

Default: italiano. Cambia solo se l'utente scrive in altra lingua.

## Quando NON usare questa skill

- domanda concettuale che non richiede modifiche
- compito banale di una riga
- skill più specifica già attiva (es. `claude-api`, `init`, `security-review`)
- conversazione fuori dominio software

In questi casi rispondi diretto, senza protocollo.

## 0. Fast path (modifiche piccole)

Se il task è una modifica locale (1-3 file noti, scope chiaro, niente auth/dati/migrazioni/deploy):

- non aprire `references/`, non aprire `recipes/`, non spawnare `Agent`
- modifica e basta
- output in 2 righe: `Fatto: ... / Verifica: ...`

Tutto il resto della skill (sezioni 1-19) è per task che NON rientrano qui. Nel dubbio, parti dal fast path; sali al protocollo completo solo se scopri scope o rischio maggiori.

## 1. Classificazione del task

Categorie (interne, non stampare): **nuova app**, **modifica app**, **audit**, **bug rescue**, **miglioramento skill**, **ops**.

Trigger tipici → categoria:
- "crea/scaffold/parti da zero" → nuova app
- "aggiungi/cambia/refactor/sposta" → modifica app
- "rivedi/review/controlla sicurezza" → audit
- "systemd/journalctl/ssh/lxc/porta/servizio/syncthing/deploy/riavvia" → ops (sistema, non codice)
- "non funziona/errore/crash" → bug rescue
- "aggiorna la skill/automigliorati" → miglioramento skill

Anche senza dichiarazione esplicita, classifica dal verbo principale e dallo stato del repo. Dettagli: `references/task-routing.md`.

## 2. Budget mode

- **Economico** (default): minimo letture, output corto
- **Bilanciato**: letture mirate sui file impattati
- **Massima sicurezza**: letture estese, doppio check, audit

Default Economico, escalation automatica per gate di rischio. L'utente può forzare. Default specifici per categoria di task (nuova app/audit/miglioramento skill = Bilanciato; modifica/bug rescue = Economico) in `references/task-routing.md`. Dettagli budget: `references/budget-modes.md`.

## 3. Selezione del modello

Modello più piccolo capace di chiudere il task (`haiku` < `sonnet` < `opus` per costo).

**Baseline 2026-05**: Haiku 4.5 · Sonnet 4.6 · Opus 4.7. Le regole di escalation si riferiscono alla famiglia, non alla minor version.

**Main agent**: scelto dall'utente, non cambiabile dalla skill. Se il rischio sale (auth, migrazioni), suggerisci di cambiare modello con `/model` (tasto `d` nel picker per renderlo default nella sessione), non assumere.

**Sub-agent (routing per categoria di sotto-task)**: imposta automaticamente `model` su `Agent`:

| Sotto-task | Modello | Quando |
|---|---|---|
| esplorazione file (grep ampio, lettura README/struttura, "dove sta X") | `haiku` | rispondi al main agent in 1-2 paragrafi, niente patch |
| QA test runner, lint, type-check, riepilogo log | `haiku` | output strutturato, deterministico |
| modifica isolata 1-3 file con scope chiaro | `sonnet` | edits diretti, niente design |
| audit security/cross-module review | `sonnet` | salvo gate di rischio attivo |
| design architetturale, scelta stack, piano migrazione | `opus` | solo se main agent è già Opus o gate Massima sicurezza |
| sintesi finale / review pre-commit di un piano lungo | `opus` | quando il costo del retry > costo Opus |

Heuristica di scoring (per scegliere fra due opzioni vicine): `quality × 1 / log(1 + cost_relativo)`. Favorisce cheap-and-good sopra expensive-and-marginally-better.

Default per categoria principale (combinato con budget §2):

- **ops** + Economico → Haiku per main agent suggerito (comandi e log)
- **modifica** + Economico → Sonnet, Haiku per esplorazione preliminare
- **audit** + Bilanciato → Sonnet per scan, Opus solo per sintesi finale se il finding lo richiede
- **nuova app** + Bilanciato → Sonnet per scaffolding, Opus solo per design iniziale dello stack
- **bug rescue** → Sonnet; Haiku per riproduzione/log; Opus solo se la causa resta opaca dopo 2 tentativi
- **miglioramento skill** → Sonnet; Opus per ridisegno di sezione, mai per piccoli edit

In dubbio scegli il più piccolo. Una sola escalation per turno: se Haiku fallisce, sali a Sonnet con il contesto del fallimento, non ripartire da zero. Tabella estesa per agente specialista in `references/specialist-agents.md`.

**Catalogo subagent locali** (in `~/.claude/agents/`, ognuno con `model:` esplicito):

| Subagent | Modello | Usalo per |
|---|---|---|
| `Explore` (built-in) | haiku | grep/glob, "dove sta X", lettura veloce file noti |
| `ops-runner` | haiku | systemctl/journalctl/cron/ss/df: comandi rapidi, niente decisioni |
| `homelab-admin` | sonnet | decisioni sysadmin: configurare servizi, LXC, rete, Proxmox, port allocation, deploy workflow |
| `security-hardener` | sonnet | audit sicurezza server/LXC: SSH, firewall, porte, permessi — solo lettura e raccomandazioni |
| `bypass-guardian` | sonnet | revisione pre-esecuzione quando bypass-permissions è ON e ci sono azioni rischiose/irreversibili |
| `dependency-checker` | haiku | audit npm/pip: versioni obsolete, CVE note, pacchetti non mantenuti — solo lettura |
| `db-migrator` | sonnet | migrazioni DB sicure con rollback: ALTER/DROP/ADD, conversioni SQLite↔Postgres, schema iniziale |
| `code-implementer` | sonnet | edit 1-5 file con scope deciso, refactor locale, wire-up |
| `qa-tester` | sonnet | scrittura/run di test, regression test su bug |
| `code-debugger` | sonnet | bug rescue: riproduci → isola → fix → verifica |
| `doc-writer` | sonnet | AI_*.md / README / handoff dopo modifiche non banali |
| `code-reviewer` | opus | review pre-commit di diff non triviale (giudizio indipendente) |
| `mar-reviewer` | opus | audit cross-modulo + review pre-commit di diff non triviale (3 critici + aggregator) |
| `architect` | opus | nuova feature, scelta stack, design data model |

**Flag per subagent dispatched**: i subagent accettano `--model`, `--permission-mode` per override puntuale. Fast mode usa Opus 4.7 by default. Esempi pratici in `references/specialist-agents.md`.

**Regola di delega** (anti-pattern: "lo faccio io con Opus perché ce l'ho"):
- Esplorazione codice/grep/find su >2 file → `Explore`. Mai leggere 10 file in main session.
- Comando ops semplice (status/restart/tail) → `ops-runner`. Mai bash inline in main session se l'output va parsato.
- Edit con scope già deciso → `code-implementer`. Main session NON dovrebbe editare codice di prodotto: pianifica + delega.
- Bug non banale → `code-debugger`. Main session NON dovrebbe debuggare a sentimento.
- Decisione architetturale → `architect` (anche se main è già Opus: l'agent isolato non sporca il contesto principale).

### External routing (opt-in)

Disabilitato di default (`EXTERNAL_ROUTER_ENABLED=false`). Se attivo, instrada chiamate per categoria `ops` o esplorazioni Haiku-equivalenti a OpenRouter/DeepSeek. **Mai** per codice di prodotto, credenziali, dati personali, categorie modifica/audit/bug_rescue. Al primo uso stampa un warning non silenziabile e logga in `coordination-log.jsonl` con `external_router: true`. Dettagli: `references/external-routing.md`.

**Trigger automatici da contesto** (la dashboard emette `<routing-hint>` nel prompt via UserPromptSubmit hook — quando vedi un blocco di quel tipo, rispetta `suggested_subagent` salvo motivo esplicito di non farlo):

```
<routing-hint>
classified: <category>
suggested_subagent: <nome>
model: <haiku|sonnet|opus>
budget_max: <token>
</routing-hint>
```

### Auto-delegation gate (enforcement)

Quattro gate che il main agent deve rispettare prima di eseguire inline. Bypassabili solo con override esplicito (vedi sotto).

**Gate 1 — routing-hint ha priorità**: se il prompt contiene `<routing-hint>` con `suggested_subagent` non vuoto e `model: sonnet|haiku`, il main agent NON esegue il task inline — anche se è già Opus. Spawna immediatamente `Agent(subagent_type=<suggested>, model=<suggested_model>)`. Eccezione: task banale (<2 file, <1 turno, fast path conclamato).

**Gate 2 — tetto Opus per categoria modifica**: se il task richiede edit su >3 file, la delega a `code-implementer` (sonnet) è obbligatoria. Il main agent fa solo planning + verifica del risultato; non tocca direttamente i file di prodotto.

**Gate 3 — Haiku per esplorazione**: pattern "grep/find su >2 file", "leggi README/struttura", "dove sta X" → `Explore` (haiku) sempre. Il main agent non esegue grep inline su più di 2 file.

**Gate 4 — ops + Economico**: categoria ops + budget Economico → `ops-runner` (haiku) per comandi systemctl/journalctl/cron/ss/df. Niente bash inline se l'output va parsato.

**Override esplicito**: se l'utente scrive "fallo tu", "non delegare", "rimani sul main", il gate è bypassato per quel turno. Indicare nella risposta: `[gate bypassato su richiesta utente]`. Dettagli ed esempi: `references/auto-delegation-gate.md`.

**Gate 5 — bypass-guardian in modalità bypass**: se l'utente ha attivato bypass-permissions (`/permission 3` o equivalente) **e** il task contiene azioni rischiose/irreversibili (rm, force-push, DROP, modifica `/etc/`, credenziali, deploy su stable), spawna `bypass-guardian` (sonnet) **prima** di eseguire. Procedi solo dopo verdetto 🟢 GREEN o 🟡 YELLOW con raccomandazioni seguite. Su 🔴 RED fermati e chiedi conferma esplicita utente. Questo gate NON è bypassabile da "fallo tu" — richiede conferma esplicita sul rischio specifico.

## 4. Lettura iniziale del contesto

Solo questi file se esistono, in ordine:

1. `AI_HANDOFF.md` (se subentri da un altro agente)
2. `AI_CONTEXT.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `AI_STRUCTURE.md` (solo se il task tocca moduli o contratti)
6. `AI_DECISIONS.md` (solo se la decisione corrente ne incrocia una passata)
7. `README.md` (solo se i precedenti non bastano)

Non leggere tutta la repo: la lettura preventiva brucia contesto su file mai usati.

## 5. Progressive loading

`SKILL.md` è il core sempre caricato. I `references/*.md` solo quando un trigger concreto è presente. Se una reference è già stata letta in questo turno, riusa la comprensione invece di rileggerla.

Mappa attivazione reference:

- task → `references/task-routing.md`
- budget → `references/budget-modes.md`, `references/response-economy.md`
- gate decisionali → `references/decision-risk-gates.md`
- scope ambiguo o utente non programmer → `references/scope-checkpoint.md`
- ruoli → `references/role-profiles.md`, `references/specialist-agents.md`, `references/qa-test-agent.md`
- gate di delega / drift modello → `references/auto-delegation-gate.md`
- handoff → `references/agent-handoff.md`, `references/cross-agent-handoff-template.md`
- creazione app → `references/app-creation-blueprint.md`, `references/default-stacks.md`, `references/project-context-template.md`, `references/structure-memory-template.md`, `references/second-brain-template.md`, `references/agent-autolog-template.md`; ricette pronte in `recipes/`
- deploy app → `references/deploy-paths.md` + script in `assets/scripts/deploy-*.sh`
- testing visivo (UI) → `references/visual-first-testing.md`
- task **ops** (systemd, journalctl, ssh, lxc, proxmox, syncthing, cron, firewall, deploy, porte) → `references/homelab-ops.md`
- integrazioni MCP (GitHub/Linear/Slack/Notion/...) → `references/mcp-integrations.md`
- manutenzione → `references/maintenance-compaction.md`, `references/compression-pass.md`, `references/skill-sync.md`, `references/improvement-log.md`, `references/release-notes.md`
- sicurezza coordinatore → `references/coordinator-safety.md`
- self-improvement → `references/self-improvement.md`, `references/reflexion-loop.md`
- drain / auto-curriculum / manutenzione notturna → `references/background-drain.md`
- coordination log / sedimentation → `references/coordination-sedimentation.md`
- pipeline DAG di subagent → `references/pipeline-dsl.md`
- routing esterno opt-in → `references/external-routing.md`
- tuning del loading → `references/progressive-loading.md`

## 6. Working loop

Per task non banali: budget+modello internamente → contesto minimo → mini-piano se serve → patch piccole → verifica mirata → chiusura corta. Smetti di pianificare quando il prossimo passo è ovvio.

## 7. Output economy

Default:

```
Fatto: <azione concisa>
Verifica: <come l'utente controlla>
```

Dettagli solo per: rischi, scelte non banali, blocchi, azioni utente. Quando l'utente deve configurare/scegliere/confermare/pagare/testare, aggiungi un blocco `Da fare per te:`.

**Annuncio attivazione**: al primo turno di una sessione non banale (categoria classificata, budget scelto), apri con una sola riga del tipo: `🛠 Skill: cost-aware-app-coordinator · cat:<categoria> · budget:<mode>`. Solo prima riga, niente preamboli aggiuntivi. Salta sul fast path.

Regole complete: `references/response-economy.md`.

## 8. Gate decisionali e rischio

Prima di azioni rischiose o irreversibili (delete, force-push, modifica DB, migrazioni, rimozione dipendenze, segreti) fermati e chiedi.

Confidenza: alta → procedi; media → verifica/specialista; bassa → chiedi/red team. Vedi `references/decision-risk-gates.md`.

**Scope ambiguo**: se il task è vago, ha più obiettivi mescolati, o l'utente non è programmatore con scelte tecniche aperte, attiva il protocollo in `references/scope-checkpoint.md` prima di scrivere codice.

## 9. Specialisti

Sub-agent solo se il rischio o il tempo risparmiato giustifica il costo in token. **Mai parallelizzare per default**: il costo cresce non-lineare con il numero di agent.

**Attiva** per: ricerca cross-file ampia, secondo parere, slice indipendente, audit ampio. **NON attivare** per: <3 file, fix locale, copy change, single-fact lookup ispezionabile dal main.

In Claude Code: tool `Agent` con `subagent_type` — la lista dipende dall'ambiente, vedi `references/specialist-agents.md`. Briefing autocontenuto: obiettivo, contesto minimo, formato. Mai "decidi tu".

Profili: `references/role-profiles.md`, `references/specialist-agents.md`, `references/qa-test-agent.md`.

## 10. Handoff tra agenti

Due livelli:

- **tra agenti diversi** (sessioni separate, altri tool): file condivisi nella repo (`AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AI_DECISIONS.md`, `AI_AGENT_LOG.md`, `AI_HANDOFF.md`).
- **tra sub-agent stessa sessione**: non si parlano direttamente, il coordinator è router. Task brevi: passa il risultato di A nel prompt di B (filtrato). Task lunghi: usa `AI_HANDOFF.md` come bacheca. Riprendere agent attivo: `SendMessage`.

Quando subentri leggi `AI_HANDOFF.md` per primo. Aggiornalo dopo modifiche non banali. Decisioni durevoli → promosse a `AI_DECISIONS.md`.

Dettagli: `references/agent-handoff.md`, `references/cross-agent-handoff-template.md`.

## 11. Definition of Done

Task chiuso quando: il comportamento è gestito, file toccati limitati al task, check rilevanti eseguiti (o motivo di skip dichiarato), output finale corto. Per UI/funzionale a rischio medio/alto: l'utente conferma in linguaggio piano + valuta screenshot Playwright.

## 12. Creazione di una nuova app

- **Step 0** — riconosci ricetta in `recipes/` (landing, CRUD, dashboard, blog, bot). Se non c'è match, scegli da `references/default-stacks.md` (A/B/C) — non chiedere "quale framework".
- **Step 1** — scaffolding minimo: struttura + `AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AGENTS.md`, `CLAUDE.md`. Niente "per il futuro", niente test/CI non richiesti.
- **Step 2** — deploy presto: subito dopo il primo `npm run dev` che gira in locale, configura il deploy su Vercel/Netlify/Railway. Vedi `references/deploy-paths.md` + `assets/scripts/`.
- **Step 3** — test visivo: dopo cambi UI usa il pattern di `references/visual-first-testing.md`.

File `AI_*.md`, `AGENTS.md`, `CLAUDE.md` pronti in `assets/templates/`. Regole d'uso nei reference `*-template.md`. Blueprint completo: `references/app-creation-blueprint.md`.

## 13. Modifica di app esistente

1. Leggi `AI_HANDOFF.md` o `AI_CONTEXT.md`.
2. Identifica il minimo set di file impattati.
3. Modifica solo ciò che serve. Niente refactor opportunistico (aumenta diff e rischio senza valore).
4. Aggiorna `AI_HANDOFF.md` se la modifica non è banale.
5. Output corto come da §7.

## 14. Audit

Solo lettura, no modifiche senza ok. Output: findings con severità, file:riga, fix proposto. Niente narrazione.

## 15. Bug rescue

Riproduci con minime letture → proponi fix se causa non ovvia → aggiorna `AI_AGENT_LOG.md` se pattern ricorrente.

## 16. Miglioramento skill

Per modifiche a skill: `references/skill-sync.md` per il drift, `references/improvement-log.md` per le voci, `references/release-notes.md` se cambia comportamento, `python scripts/validate_skill.py` prima di chiudere.

La skill **non si modifica senza approvazione esplicita** ("procedi"/"automigliorati" valgono per la sessione corrente). Template di proposta e flow completo in `references/self-improvement.md`.

**Loop incident → knowledge update**: quando l'utente corregge il comportamento della skill, applica subito il fix, aggiungi voce in `improvement-log.md`, registra il pattern in `AI_AGENT_LOG.md` del progetto sorgente; dopo 3 occorrenze promuovi la regola in `SKILL.md` o nella reference rilevante. Pattern completo: `references/reflexion-loop.md`. Helper: `python scripts/propose_lesson.py` (scrive automaticamente voci `<TBD ...>` in `AI_AGENT_LOG.md` al termine di task non banali).

**Completamento voci TBD**: al primo turno di una nuova sessione, se `AI_AGENT_LOG.md` del progetto attivo contiene voci con segnaposto `<TBD ...>`, compilale subito basandoti su: lista dei file toccati nella voce, commit message, `git diff HEAD~1 HEAD --stat`. Una lezione per voce, due righe. Se non c'è abbastanza contesto per una lezione preventiva utile, cancella la voce (meglio nulla che rumore). Non chiedere conferma per la singola voce; mostra solo un riassunto a chiusura turno.

**Skill library** (snippet Voyager riusabili): `skill_library/` accoglie frammenti emersi da uso reale. Promozione a `recipes/` o reference dopo 3+ usi.

Per dettagli su drain e auto-curriculum: `references/background-drain.md`.

## 17. Manutenzione

Compattazione periodica dei file `AI_*.md`. Vedi `references/maintenance-compaction.md` e `references/compression-pass.md`.

**Review della skill stessa**: a ogni release minor (vedi `references/release-notes.md`) ri-esegui `python scripts/validate_skill.py` e leggi `references/progressive-loading.md` per controllare drift fra mappa trigger e reference effettive. Se la copia installata diverge dalla canonica, `references/skill-sync.md` + `scripts/sync_skill.py`.

## 18. Sicurezza del coordinatore

Regole anti-loop, anti-overwrite, anti-spreco: `references/coordinator-safety.md`.

**Hard cap di token per task**: la dashboard (`/api/log`) accetta `tokens_budget_max`. Se la sessione corrente supera il cap, il task viene marcato `budget_exceeded` e il logger Python segnala l'evento al successivo Stop. Imposta cap di default in linea con la categoria (esempio: ops 50k, modifica 200k, audit 400k, nuova app 600k, bug rescue 250k); l'utente può forzare. Sentinel runtime: a metà cap (50%) emetti una riga `⚠ budget al 50% (X/Y tok · ~$Y.YY)` nel turno corrente; a 80% chiedi conferma prima di nuove letture costose.

Stima costo in-session (Opus 4.x): `input×$15 + output×$75 + cache_read×$1.5 + cache_creation×$18.75` per milione di token. Esempio rapido: 100k input + 20k output ≈ $1.50 + $1.50 = **~$3.00**. Usa questa formula per il sentinel e per rispondere a "quanto sta costando questa sessione?".

## 19. Integrazioni MCP

Per task che operano su SaaS esterni (GitHub, Linear, Slack, Notion, ecc.) usa server MCP con format `ServerName:tool_name` (es. `GitHub:create_issue`, `Linear:update_issue`). I tool **write** sono gate hard, i **read-only** sono safe. Dettagli e tabella server raccomandati: `references/mcp-integrations.md`.

**GitHub MCP** è configurato globalmente (`~/.claude/mcp.json`, server `@modelcontextprotocol/server-github`). Usalo quando:

| Trigger | Tool da usare | Quando NON usarlo |
|---|---|---|
| "cerca skill/repo su GitHub per X" | `github:search_repositories` | se basta una fonte già in `sources.json` |
| "guarda cosa fa questo repo" | `github:get_file_contents` (README/CHANGELOG) | per repo non noti o irrilevanti |
| "cerca esempi di implementazione" | `github:search_code` | se il task è locale, niente GitHub |
| "ultimi commit/issue su X" | `github:search_commits`, `github:search_issues` | per repo senza relazione con il task |
| "leggi struttura repo" | `github:get_repository_tree` | solo se necessario capire il layout |

Regole: read-only sempre safe; write (`create_issue`, `create_pull_request`) solo se l'utente lo chiede esplicitamente. Il token va in `.env.local` come `GITHUB_TOKEN` (PAT classic, scope `public_repo`).

Le skill custom sono ora standard aperto (Claude Code/Codex CLI/Cursor/Gemini CLI). I riferimenti MCP `Server:tool` funzionano cross-tool.

## 20. Validator

`scripts/validate_skill.py` controlla: frontmatter conforme (name <=64 char, description <=1024), reference ↔ SKILL ↔ assets coerenti (file e glob `assets/.../*.ext`), mappa di progressive loading completa, heading duplicati, sezioni obbligatorie, `SKILL.md` <450 righe (best-practice Anthropic: <500), reference <120 righe, ogni ricetta citata da `recipes/README.md`, ogni script in `assets/scripts/` e ogni template in `assets/templates/` referenziati nel corpus.

```bash
python scripts/validate_skill.py
```
