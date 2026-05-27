# Template: AI_DECISIONS.md

Memoria a lungo termine di decisioni durevoli. Append-only.

File copiabile pronto: `assets/templates/AI_DECISIONS.md`. Esempio di voce ben compilata:

```markdown
## 2026-04-29 — Postgres su SQLite
- Decisione: usare Postgres anche in locale via Docker.
- Motivo: parità con prod, evitare divergenze sulle date.
- Implicazioni: dev richiede Docker. Test integrazione contro Postgres reale.
- Alternative scartate: SQLite (driver diverso), Postgres su CI ma SQLite locale (rischio drift).
```

## Regole

- Una voce per decisione, non per task.
- Una voce contiene: data, decisione, motivo, implicazioni, alternative scartate.
- Niente voci senza motivazione.
- Una decisione revocata non viene cancellata: marcata `~~revocata~~` e si aggiunge la nuova.
- Niente decisioni triviali (naming variabile, ordine import).

## Quando promuovere da `AI_HANDOFF.md`

- la scelta vincola decisioni future
- è costoso tornare indietro
- altri agenti rischiano di re-litigarla

## Quando NON registrare

- preferenze personali
- scelte derivabili dalla documentazione del framework
- micro-ottimizzazioni locali
