# Background Drain

Processo notturno che esegue manutenzione automatica su un progetto: compila TBD, propone lezioni, compatta doc, valida drift skill, apre PR.

## Cosa fa

Gira ogni notte alle 03:00 locali (systemd timer). Su ogni run:

1. **complete_tbd_entries** — compila le righe `<TBD ...>` in `AI_AGENT_LOG.md` da git log/diff.
2. **analyze_tool_errors** — raggruppa errori ricorrenti dal coordination-log (30gg) e propone lezioni in `improvement-log.md` con tag `<auto-proposed>`.
3. **run_compaction** — se un file `AI_*.md` supera 500 righe, applica `compression-pass.md` (non promuove senza approvazione umana).
4. **validate_skill_drift** — esegue `validate_skill.py` e `check_handoff_drift.py`, allega output al PR.
5. **summarize_changes** — genera body PR markdown con riepilogo delle modifiche.

6. **security_audit** *(solo domenica)* — lancia `security-hardener` sul server: porte aperte, aggiornamenti sicurezza pendenti, fail2ban status, certificati in scadenza (<30 giorni), LXC unprivileged check. Output append in `HOMELAB_PENDING.md` se trova anomalie. Non blocca il drain se fallisce.

Alla fine: commit + push su branch `drain/YYYY-MM-DD` + apertura PR con label `drain`.

## Garanzie di safety

- Lavora **solo su un branch dedicato** (`drain/YYYY-MM-DD`), mai su master/main direttamente.
- **Mai write su DB prod**: le operazioni sono solo su file locali e git.
- Se una sub-attivita' fallisce, viene loggata e saltata: le altre proseguono.
- Il PR aperto richiede **revisione umana** prima del merge: niente auto-merge.
- Il drain **non si attiva** se il progetto ha modifiche non committed (dirty working tree).

## Log esecuzioni

```
~/.claude/projects/<proj-slug>/memory/drain-log.jsonl
```

Ogni run appende una riga con: timestamp, progetto, sub-attivita' eseguite, esito, link PR.

## Attivazione

Per dettagli su drain e auto-curriculum: `references/background-drain.md` (questa pagina).
Script principale: `scripts/drain.py`.
Timer: `assets/scripts/drain.timer` + `assets/scripts/drain.service`.

Per attivare il timer systemd utente:

```bash
# Copia i file in ~/.config/systemd/user/
cp assets/scripts/drain.timer ~/.config/systemd/user/
cp assets/scripts/drain.service ~/.config/systemd/user/
# Attiva e avvia
systemctl --user enable --now drain.timer
# Verifica
systemctl --user status drain.timer
```

Il timer gira alle 03:00 ora locale ogni giorno. Modifica `OnCalendar` nel `.timer` per cambiare orario.

## Dashboard

La pagina `/drain` della dashboard mostra le esecuzioni recenti e i link ai PR aperti con label `drain`.
