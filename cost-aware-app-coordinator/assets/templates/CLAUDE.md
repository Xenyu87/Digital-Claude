# CLAUDE.md

Regole specifiche per Claude Code in questo progetto. Estende `AGENTS.md`.

## Skill di coordinamento

Usa `cost-aware-app-coordinator` per: nuova app, modifica, audit, bug rescue, miglioramento skill. Default budget: Economico.

## Tool da preferire

- `Read`, `Edit`, `Write`, `Glob`, `Grep` invece di `Bash` per operazioni su file
- `Agent` con `subagent_type` solo se: ricerca cross-file ampia, secondo parere, slice indipendente. Mai per task <3 file.

## TodoWrite

Usa la to-do list per task multi-step (>=3 step). Mai per task banali.

## Output

- corto per default
- `Fatto: / Verifica:` come formato base
- `Da fare per te:` solo se l'utente deve agire (config, conferma, test manuale)

## Riferimenti a file

Usa link markdown cliccabili: `[file.ts:42](src/file.ts#L42)`.

## File AI_*.md

Aggiorna `AI_HANDOFF.md` dopo modifiche non banali. Promuovi decisioni durevoli in `AI_DECISIONS.md`.
