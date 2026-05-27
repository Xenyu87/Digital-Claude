# Reflexion Loop

Pattern per far imparare il coordinator dai propri errori senza fine-tuning. Realistico in skill markdown: l'agente scrive testo, non aggiorna pesi.

## Pattern Reflexion in 4 fasi

1. **Trigger**: a fine task non banale (≥30 min, ≥5 file toccati, oppure utente ha corretto la skill).
2. **Estrazione lezione**: 1-3 lezioni preventive, ognuna in una riga, con format `errore/spreco → regola futura`.
3. **Log**: append in `AI_AGENT_LOG.md` (file di progetto). Vedi `assets/templates/AI_AGENT_LOG.md` e `agent-autolog-template.md`.
4. **Promozione**: dopo 3 occorrenze dello stesso pattern, promuovi la regola in `AGENTS.md` (vincolante per tutti gli agent del progetto).

## Quando estrarre una lezione

Sì:
- ho letto N file e ne sono serviti M<<N
- ho spawnato un sub-agent senza gate; il main bastava
- ho riscritto invece di cercare un pattern già nel repo
- ho dichiarato `Fatto:` senza verificare l'esecuzione
- l'utente ha corretto un comportamento mio (es. "non rinominare i vars unused")

No:
- task ordinario riuscito al primo colpo (nessuna lezione)
- successo banale ("ho aggiunto un punto e virgola")
- supposizione sul futuro ("forse un giorno servirà X")

## Format della lezione

```
- YYYY-MM-DD — Spreco — letti 12 file in src/db/ per fix in src/utils/format.ts (servivano 2)
  Lezione: non aprire src/db/ se il task è formatting
```

Lunghezza: 2 righe per voce. Mai 5. Se serve di più, va in `AI_DECISIONS.md`.

## Loop incident → knowledge update (per la skill stessa)

Quando l'utente corregge il comportamento della skill (es. "non riscrivere il file intero, usa Edit"):

1. Applica la correzione subito.
2. **Aggiungi voce** in `references/improvement-log.md` (cosa è cambiato, perché).
3. **Aggiungi pattern** in `AI_AGENT_LOG.md` del progetto sorgente della skill (lezione preventiva).
4. Se è la 3ª occorrenza del pattern: **promuovi** la regola in `SKILL.md` o nella reference rilevante.

Il loop si chiude solo a step 4 — finché il pattern resta in `AI_AGENT_LOG.md`, è solo "memoria episodica"; la promozione lo trasforma in regola.

## Skill library (Voyager pattern)

Dove finiscono snippet riusabili emersi da task ricorrenti (es. stub Next.js route, schema Zod per form contatti). Vedi `skill_library/README.md`.

Differenza:
- **Lessons** = regole anti-pattern (NON fare X). Vivono in `AI_AGENT_LOG.md`.
- **Library** = snippet positivi (fai X così). Vivono in `skill_library/<nome>.{md,ts,py}`.

## Helper: `scripts/propose_lesson.py`

Script che legge il diff dell'ultimo commit, conta file toccati, e propone un template di lezione se ≥5 file. Non scrive automaticamente; stampa il blocco da copiare in `AI_AGENT_LOG.md`.

```bash
python scripts/propose_lesson.py
```

Uso suggerito: hook `Stop` di Claude Code in `settings.json` per esecuzione automatica a fine sessione. Vedi skill `update-config`.

## Anti-pattern

- estrarre lezioni da ogni task (rumore: bruci tempo e bruci il file)
- promuovere regole dopo 1 sola occorrenza (potrebbe essere caso isolato)
- mettere lezioni in `AI_HANDOFF.md` (è stato corrente, non memoria)
- riscrivere `AI_AGENT_LOG.md` per "pulirlo": è append-only fino a compaction (vedi `compression-pass.md`)
