# Template: AI_AGENT_LOG.md

Log degli errori, sprechi e lezioni di processo. Non è un diario di attività.

File copiabile pronto: `assets/templates/AI_AGENT_LOG.md`. Esempio compilato:

```markdown
## 2026-04-29
- **Spreco**: letti 12 file per un fix in `src/utils/format.ts`. Bastavano 2.
  Lezione: non aprire `src/db/*` se il task è di formatting.
- **Errore**: ho dichiarato `Fatto:` su una migrazione mai eseguita.
  Lezione: dichiarare `Fatto:` solo dopo conferma di esecuzione.
```

## Cosa registrare

- letture inutili che hanno bruciato contesto
- specialisti attivati senza necessità
- loop di retry sullo stesso comando
- claim non verificati ("Fatto" senza esecuzione)
- pattern di bug ricorrente

## Cosa NON registrare

- ogni singolo task ordinario
- successi senza lezione
- info che vanno in `AI_DECISIONS.md` o `AI_STRUCTURE.md`

## Manutenzione

Quando il file supera ~200 righe:

- raggruppa errori simili in una voce con conteggio
- promuovi le lezioni stabili in `AGENTS.md`
- elimina voci vecchie >30 giorni se la lezione è già confluita altrove

Vedi `compression-pass.md`.
