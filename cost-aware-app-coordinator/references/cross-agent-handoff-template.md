# Template: AI_HANDOFF.md

Stato corrente, sostituibile. Pensato per essere letto in <30 secondi dal prossimo agente.

File copiabile pronto: `assets/templates/AI_HANDOFF.md`. Esempio compilato:

```markdown
## Goal corrente
aggiungere validazione email all'endpoint login

## Stato
in corso

## File toccati
- `src/api/login.ts` — aggiunta validazione email
- `src/db/schema.ts` — nuovo campo `email_verified`

## Decisioni
- Zod invece di yup (consistenza col repo)

## Rischi aperti
- migrazione `email_verified` non ancora applicata in staging

## Prossimo passo
- applicare la migrazione in staging e rilanciare e2e
```

## Regole

- Sostituibile, non append-only. Sovrascrivi sezioni quando lo stato cambia.
- Solo stato corrente. Niente storia.
- Decisioni durevoli → promuovile in `AI_DECISIONS.md` e rimuovile da qui.
- Se stato è `rilasciato` e non c'è prossimo passo, ripulisci a uno stato vuoto coerente.

## Quando aggiornare

Dopo modifiche non banali:

- nuova feature
- refactor su >2 file
- bug fix con causa non ovvia
- cambio decisione di scope

Non aggiornare per: typo, rename locale, commento.

## Quando NON usare

- come diario
- come elenco di tutto ciò che hai fatto in giornata
- come contenitore di output di test
