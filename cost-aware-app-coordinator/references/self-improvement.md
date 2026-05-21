# Self-Improvement

Procedura quando l'utente chiede "automigliorati", "audita la skill", "rivedi le tue regole".

## Trigger

- "automigliorati", "self-improve", "rivedi te stessa"
- "audita la skill"
- richiesta esplicita di refactor delle reference o del SKILL.md

Categoria: **miglioramento skill**. Budget default: Bilanciato.

## Step

Copia questa checklist e spunta ogni step prima di passare al successivo:

```
Self-improvement progress:
- [ ] 1. Validator baseline: errori e warning annotati
- [ ] 2. SKILL.md e reference letti una volta sola
- [ ] 3. Gap identificati con la checklist sotto
- [ ] 4. Modifiche ampie proposte all'utente; fix mirati applicati
- [ ] 5. Modifiche minime applicate
- [ ] 6. improvement-log.md aggiornato (una riga per cambio)
- [ ] 7. release-notes.md aggiornato se il comportamento cambia
- [ ] 8. Validator finale verde
```

Comandi: `python scripts/validate_skill.py` (step 1 e 8).

## Checklist di gap

Cerca questi sintomi prima di scrivere:

- **copertura**: una richiesta utente comune non ha un flow chiaro
- **duplicazione**: due reference dicono la stessa cosa con piccole differenze
- **drift**: una reference cita file/sezioni che non esistono più
- **opacità**: SKILL.md menziona una regola senza puntare alla reference
- **spreco**: una reference > 120 righe o non citata da SKILL.md
- **rumore**: esempi che non aggiungono nulla rispetto al testo
- **anti-pattern emersi**: pattern visti in `AI_AGENT_LOG.md` non ancora codificati
- **piattaforma**: regole valide solo Unix in ambiente Windows o viceversa

## Cosa NON fare

- non riscrivere reference solide per ragioni stilistiche
- non aggiungere reference "che potrebbero servire"
- non spostare contenuto tra file solo per equilibrare le righe
- non rimuovere esempi che spiegano un caso non ovvio
- non bumpare version major senza confermare con l'utente

## Stop conditions

Ferma e chiedi se:

- la modifica richiede rinominare un file `references/*.md` (rompi link esterni)
- elimini un'intera sezione di `SKILL.md` (cambio comportamento)
- cambi un default (budget mode, lingua, soglia righe)
- la modifica supera 3 reference contemporaneamente

## Output finale

```
Fatto: <N> migliorie applicate. Validator: ok.
Verifica: python scripts/validate_skill.py
```

Se hai aggiornato `release-notes.md`, cita la nuova versione.

## Test su istanza fresca

Le modifiche alla skill vanno testate con una nuova chat (instance fresh che carica la versione aggiornata). Pattern raccomandato dalla doc Anthropic: lavora con un'istanza A per modificare la skill, poi verifica con un'istanza B che la usi su task reali. Se B fallisce o ignora una regola, ritorna ad A con l'osservazione concreta.
