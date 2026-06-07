# Skill Sync

Procedura per modificare questa skill o sincronizzarla tra installazione globale e di progetto.

## Posizioni

- Globale (utente): `~/.claude/skills/digital-claude/`
- Progetto: `.claude/skills/digital-claude/`

Su Windows l'equivalente di `~` è `%USERPROFILE%`. Il path tipico è `C:\Users\<utente>\.claude\skills\digital-claude\`.

Su Linux/LXC `dev` (Debian) il path reale è `/root/.claude/skills/digital-claude/`, accessibile anche via symlink `/root/Progetti/_claude-skills/digital-claude/`.

## Quando aggiornare globale vs progetto

- Modifica con valore generale → globale
- Modifica specifica di un progetto (es. regole di test particolari) → progetto, sotto forma di override o estensione

## Procedura di modifica

1. Apri `SKILL.md` o la reference da modificare.
2. Applica la modifica con cambi minimi.
3. Aggiorna `improvement-log.md` con una riga.
4. Se la modifica cambia il comportamento osservabile, aggiorna `release-notes.md`.
5. Esegui `python3 scripts/validate_skill.py` (`python` su Windows).
6. Se OK, committa.

## Vincoli da rispettare

- `SKILL.md` < 450 righe (best-practice Anthropic: < 500)
- ogni reference < 120 righe
- progressive loading map in `SKILL.md` deve citare ogni file in `references/`
- ogni file in `references/` deve essere citato da `SKILL.md`
- ogni asset citato da `SKILL.md` deve esistere in `assets/`

## Sincronizzazione globale ↔ progetto

Quando una modifica fatta in versione globale deve arrivare al progetto (o viceversa):

1. Identifica la versione canonica (di solito la globale).
2. Sync automatico: `python scripts/sync_skill.py` copia `SKILL.md`, `references/`, `assets/`, `scripts/` verso `~/.claude/skills/digital-claude/`. Usa `--dry-run` per anteprima e `--dest <path>` per destinazioni custom.
3. Esegui validator in destinazione.
4. Aggiorna `improvement-log.md` solo nella canonica.

## Anti-pattern

- modificare la versione di progetto e dimenticare la globale (drift)
- copiare l'intera cartella ogni volta (perdi modifiche locali al progetto)
- saltare il validator
