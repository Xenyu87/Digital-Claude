# Compression Pass

Procedura per ridurre file `AI_*.md` quando crescono troppo o si ripetono.

## Quando eseguire

- `AI_HANDOFF.md` > 80 righe
- `AI_AGENT_LOG.md` > 200 righe
- `AI_CONTEXT.md` > 300 righe
- l'utente chiede "compatta", "ripulisci", "riassumi memoria"

## Cosa NON comprimere

- `AI_DECISIONS.md`: si tagliano solo decisioni revocate (con marker `~~revocata~~`)
- `AI_STRUCTURE.md`: si aggiorna 1:1 con la struttura, non si comprime

## Strategia per file

### AI_HANDOFF.md
Tieni solo lo stato corrente. Se contiene storia, sposta in `AI_AGENT_LOG.md` come voce sintetica e svuota.

### AI_AGENT_LOG.md
- Raggruppa errori simili in una voce con conteggio
- Rimuovi voci più vecchie di 30 giorni se la lezione è già confluita in `AI_DECISIONS.md` o in `AGENTS.md`
- Mantieni solo lezioni con valore preventivo

### AI_CONTEXT.md
- Elimina sezioni superate dai file dedicati (struttura → `AI_STRUCTURE.md`, decisioni → `AI_DECISIONS.md`)
- Tieni: scopo del progetto, stack, convenzioni di alto livello, contatti / proprietari

## Output del compression pass

Dopo la compattazione:

```
Fatto: compattati AI_HANDOFF.md (<old> → <new> righe), AI_AGENT_LOG.md (<old> → <new>).
Verifica: git diff AI_HANDOFF.md AI_AGENT_LOG.md
```

## Anti-pattern

- riscrivere da zero perdendo decisioni durevoli
- comprimere durante una feature attiva (rischia di perdere stato)
- comprimere senza commit precedente

## Trigger automatico

Se durante un task ti accorgi che un file `AI_*.md` è oltre soglia, **non comprimere automaticamente**. Segnala in chiusura turno:

```
Da fare per te:
- AI_AGENT_LOG.md è a 240 righe. Vuoi che lo compatti?
```
