# AI_STRUCTURE

## Top-level
- `src/` — codice applicativo
- `tests/` — test
- `scripts/` — utility CLI
- `docs/` — documentazione utente
- `infra/` — configurazione infra

## Moduli principali
### src/api
- contratti REST/GraphQL
- entry: `src/api/index.ts`

### src/db
- schema, migrazioni, client
- file critico: `src/db/schema.ts`

### src/ui
- componenti pubblici e pagine

## Contratti pubblici
- `POST /login` → vedi `src/api/auth.ts`
- evento `user.created` → vedi `src/events/user.ts`

## File critici
File per cui ogni modifica richiede budget Bilanciato o superiore:

- `src/db/schema.ts`
- `src/api/auth.ts`
- `infra/deploy.yaml`

## Convenzioni di posizionamento
- nuovi endpoint → `src/api/<area>/`
- nuovi componenti → `src/ui/components/`
- nuove migrazioni → `src/db/migrations/<timestamp>_<nome>.sql`
