# Agent Handoff

Come passare lo stato tra agenti diversi (Claude Code, altri assistenti AI, sviluppatori umani).

## Principio

Comunicazione tramite file versionati nella repo. Nessuna memoria nascosta, nessun assunto su sessione precedente.

## File coinvolti

- `AI_CONTEXT.md` — contesto stabile (cos'è il progetto, stack, scopi)
- `AI_STRUCTURE.md` — mappa stabile di moduli, contratti, file critici
- `AI_DECISIONS.md` — decisioni durevoli (append-only)
- `AI_AGENT_LOG.md` — errori, sprechi, lezioni di processo
- `AI_HANDOFF.md` — stato corrente, sostituibile turno per turno
- `AGENTS.md` — regole condivise per qualsiasi agente
- `CLAUDE.md` — regole specifiche di Claude Code

## All'inizio del turno

Se subentri dopo un altro agente, leggi in ordine:

1. `AI_HANDOFF.md` (priorità)
2. `AI_CONTEXT.md` (se ti manca contesto base)
3. `AGENTS.md`, `CLAUDE.md` (regole vincolanti)
4. `AI_DECISIONS.md` (solo se la decisione corrente le tocca)

Non leggere `AI_AGENT_LOG.md` salvo task di skill maintenance o se sospetti pattern già visto.

## Durante il turno

- Aggiorna `AI_HANDOFF.md` solo se la modifica è non banale.
- Decisioni durevoli → vanno promosse in `AI_DECISIONS.md` con data e motivazione.
- Cambiamenti di struttura → aggiornano `AI_STRUCTURE.md`.
- Errori ripetibili → riga in `AI_AGENT_LOG.md`.

## Fine turno

Lascia `AI_HANDOFF.md` in stato pulito:

- è subito leggibile in <30 secondi
- contiene solo lo stato attuale, non la storia
- punta a file specifici e prossimo passo concreto

## Cosa NON mettere in AI_HANDOFF.md

- diari ("oggi ho fatto…")
- commenti sulle scelte fatte: vanno in `AI_DECISIONS.md`
- output di test: vanno nel terminale o in CI
- segreti, chiavi, credenziali
- considerazioni filosofiche

## Conflitti

Se `AI_HANDOFF.md` contraddice il codice: il codice vince. Aggiorna handoff.
Se `AI_DECISIONS.md` contraddice una richiesta utente nuova: chiedi se la decisione precedente va revocata, e marcala revocata.

## Comunicazione tra sub-agent (stesso coordinator)

I sub-agent **non si parlano direttamente**. Il coordinator fa da router. Tre pattern:

**A — Handoff via coordinator (default per task brevi):**

1. Lancia sub-agent A con un prompt autocontenuto.
2. Ricevi il suo risultato.
3. Lancia sub-agent B passando nel prompt **solo le parti utili** del risultato di A (non tutto).

Niente chat libera fra A e B; il coordinator filtra cosa serve a chi.

**B — Handoff via file (per task lunghi, multi-turno, o quando A e B operano in tempi diversi):**

1. Sub-agent A scrive lo stato in `AI_HANDOFF.md` (volatile) e/o promuove decisioni durevoli in `AI_DECISIONS.md`.
2. Sub-agent B riceve nel prompt l'istruzione "leggi `AI_HANDOFF.md` come primo passo".
3. B parte già informato senza che il coordinator debba ripetere tutto.

Usa questo modo quando il payload è grosso o cambia spesso, o quando vuoi tracciabilità nel repo.

**C — Riprendere un sub-agent attivo (`SendMessage`):**

Se un sub-agent è già stato lanciato in questa sessione e serve continuare, usa `SendMessage` con il suo ID. Riprende con il contesto già caricato (più efficiente di un nuovo `Agent`).

**Anti-pattern:**

- A → scrive 200 righe → B legge tutto: filtra prima.
- Loop di handoff infinito: il coordinator decide quando si chiude.
- Far chiedere a un sub-agent di lanciarne un altro: la regia resta al coordinator.
