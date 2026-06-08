# Jarvis Guardrails — Fase 1

Piano in 2 fasi per evolvere la skill verso un assistente "Jarvis": autonomo e proattivo, ma blindato su budget e sicurezza.

## Fase 1 (implementata 2026-06-07): Safety

### 1A — Circuit Breaker Finanziario

**Problema:** Oggi il costo di un task si conosce solo *post-mortem* (`auto_log_task.py` parsa il JSONL a fine turno). Nessun subprocess veniva terminato al superamento del budget — i loop infiniti di debug bruciavano tutto il wallet.

**Soluzione:** `scripts/budget_guard.py` — tripla difesa per ogni subprocess `claude`:
1. `--max-budget-usd` → hard kill **nativo** della CLI al superamento del budget in USD
2. `--max-turns` → limite turni (nessuno spawn lo passava in precedenza)
3. `timeout` wall-clock → fallback estremo

Ogni subprocess spawnato dalla skill usa `run_guarded()`:
- `drain.py → resolve_tbd_lessons`: budget 10¢, max_turns 4, timeout 120s
- `supreme_court.py → call_agent`: budget 5¢ per giudice (cap totale corte ~15¢), max_turns 3
- Futuri demone/pipeline: aggiungere `run_guarded()` ad ogni spawn `claude`

Al breach: log in `reports/circuit-breaker.jsonl` + alert via `/api/skill-feedback` (visibile a SessionStart via `inject_lessons.py`).

**Limite dichiarato:** funziona solo per subprocess spawnati dalla skill. La sessione interattiva del main agent non è uccidibile da qui — quella è protetta da `budget_aware_router.py` (forza haiku sotto 20k token residui) e dai budget per categoria in `route_hint.py`. Questo limite è architetturale (Claude Code CLI non espone un hook di kill per la sessione corrente) — documentato per non creare false aspettative.

**Correzione architetturale vs proposta originale:** la feature è stata proposta con framing "Vercel serverless". È sbagliato: killare un processo in corsa richiede subprocess e controllo live del processo — incompatibile con funzioni serverless stateless. Gira sul host persistente (LXC Claude Code runtime) come tutti gli altri script della skill.

### 1B — Sandbox Patching (Linter Coercitivo)

**Problema:** Gli agenti modificano direttamente i file di produzione. Un errore TS/lint nel diff finisce in produzione senza filtro.

**Soluzione:** Worktree isolato (`Agent(isolation:"worktree")`) + `scripts/validate_patch.py`. Solo le patch che superano i gate deterministici vengono mergate. Dettagli del protocollo: `references/sandbox-patching.md`.

---

## Fase 2 (da pianificare): Autonomia

Le 2 idee genuine rimanenti richiedono un processo demone persistente. Host da decidere (LXC 147 vs macchina dedicata) quando si attiva questa fase.

### 2A — Inbox di Approvazione
Jarvis lavora in background e posta proposte in una "inbox" (tabella DB analoga a `ai_news`/`ai_plans` già esistente). L'utente approva/rifiuta con un click — zero token in chiacchiere. Il backend esegue l'azione approvata via `actions/run` allowlist (`execFile`, no shell injection).

### 2B — Ingestione Event-Driven
Webhook Git / alert di log / eventi di sistema → filtro regex locale (zero LLM) → inject nel contesto della prossima sessione via `inject_lessons.py` (canale già attivo). Richiede un piccolo HTTP server sul LXC per ricevere i webhook.

---

## Idee della lista originale scartate (e perché)

| Idea | Perché scartata |
|---|---|
| Dialetto esoterico inter-agente (`⚡R[path]`) | Claude non è addestrato su simboli custom; risparmio token <1%; aggiunge fragilità |
| Auto-evizione messaggi dalla history | Impossibile con Claude Code CLI: non si può modificare il `messages[]` array di una sessione attiva |
| S²-MAD self-exclusion per affinità | Paradosso: calcolare l'affinità richiede chiamare un LLM — costa più del task stesso. `route_hint.py` fa già il 90% deterministicamente |
| Sessione Future Simulator | Sessioni di sviluppo guidate da sorprese, non da pattern prevedibili — poco credibile |

---

## Files

- `scripts/budget_guard.py` — circuit breaker (importabile + CLI test)
- `scripts/validate_patch.py` — gate deterministici su worktree
- `references/sandbox-patching.md` — protocollo sandbox
- `references/jarvis-guardrails.md` — questo file (visione + stato)
