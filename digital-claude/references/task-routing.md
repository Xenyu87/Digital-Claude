# Task Routing

Come classificare la richiesta e instradarla.

## Classi

### nuova app
Trigger: "crea", "scaffold", "parti da zero", repo vuota.
Routing: blueprint completo. Vedi `app-creation-blueprint.md`.
Budget default: Bilanciato.

### modifica app
Trigger: "aggiungi", "cambia", "refactor", "sposta", su repo esistente.
Routing: leggi `AI_HANDOFF.md` o `AI_CONTEXT.md`, identifica file impattati.
Budget default: Economico.

### audit
Trigger: "rivedi", "fai una review", "controlla sicurezza", "audit".
Routing: solo lettura. Output strutturato per severità.
Budget default: Bilanciato. Se è auth/dati/segreti → Massima sicurezza.

### bug rescue
Trigger: "non funziona", "errore", "crash", "test fallisce".
Routing: riproduci con minime letture, isola, proponi fix prima di applicarlo se la causa non è ovvia.
Budget default: Economico, con escalation se la superficie è ampia.

### miglioramento skill
Trigger: "modifica la skill", "aggiungi al SKILL.md", "aggiorna le regole".
Routing: usa `skill-sync.md`, esegui validator.
Budget default: Bilanciato.

## Quando il task è ambiguo

Esegui un singolo turno di chiarimento mirato. Niente questionari lunghi:

```
Per partire: <X> o <Y>?
```

Se l'utente non risponde alla domanda chiave, fai la scelta più conservativa e dichiarala.

## Combo

- "audit + fix" → prima audit, poi piano di fix, poi conferma, poi modifica
- "nuova app con feature X" → prima blueprint minimo, poi feature
- "bug rescue con cambio architetturale" → escalation a Massima sicurezza

## Anti-pattern

- partire a scrivere codice senza classificare
- trattare un audit come modifica e cambiare file
- partire da zero quando esiste già un progetto (leggi sempre prima)
