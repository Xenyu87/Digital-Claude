# Homelab ops — comandi e pattern ricorrenti

Reference operativo per task ops sul homelab dell'utente (Proxmox + LXC `dev`/`stable`).

## Quando caricare questa reference

Quando il task tocca: `systemd`, `journalctl`, `ssh`, `lxc`, `proxmox`, `syncthing`, `cron`, `firewall`, `nginx`, `deploy`, "porta X", "servizio X", "riavvia", "backup".

Trigger speculari nella heuristic `detect_category` (vedi `scripts/auto_log_task.py`): se la categoria classifica come `ops`, considera già caricato il know-how di questo file.

## Mappa rapida del homelab

- **Proxmox host** `.136` (VMID: dev=113, stable=108, security=114) — fallback via `pct exec <VMID>`
- **LXC `dev`** `.148` — Claude Code/Codex, Syncthing GUI **3003**, sync TCP **22000**
- **LXC `stable`** `.147` — produzione app
- Per topologia completa → `HOMELAB.md` (usa `grep -n '^## '` + `Read offset/limit`)

## Servizi systemd noti

| Servizio | LXC | Note |
|---|---|---|
| `codex-skill-dashboard.service` | dev | Dashboard Codex Skill, porta 3002, serve `reports/skill-dashboard.html` |
| `digital-claude-dashboard-dev.service` | dev | Next.js, porta 3001, `npm start` dopo `npm run build` |
| `syncthing.service` | dev | GUI 3003, sync TCP 22000, config `/root/.config/syncthing/config.xml` |

## Comandi quotidiani

```bash
# Stato + log servizio
systemctl status <nome>
systemctl restart <nome>
journalctl -u <nome> -n 50 --no-pager
journalctl -u <nome> -f          # follow live

# Verifica porte in ascolto (preferisci ss a netstat)
ss -tlnp | grep -E ':(3001|3002|3003|22000)\s'

# Hot-reload dashboard dopo modifica sorgenti
cd /root/Progetti/digital-claude-dashboard
npm run build && systemctl restart digital-claude-dashboard-dev.service

# Hot-reload dashboard Codex Skill dopo modifica Lavagna/React Flow
cd /root/Progetti/codex-skill-dashboard
npm run build:blueprint-flow
python3 scripts/generate_dashboard.py --refresh 15
scripts/manage_dashboard.sh restart
```

## Pattern ricorrenti (lezioni)

### "Pagina dev non si vede dal browser"

Quasi sempre **cache del browser**, non server. Ordine di indagine:

1. `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001/<path>` — se 200, server OK
2. `curl -s http://localhost:3001/<path> | grep -c '<tag>'` — verifica che il contenuto atteso sia nell'HTML
3. Solo se 1+2 OK → istruisci utente **Ctrl+Shift+R** (hard refresh) o incognito

### "Preview/Lavagna Codex mostra 404"

Di solito il browser sta parlando con un vecchio processo o con asset React Flow non ricompilati.

Ordine di indagine:

1. `cd /root/Progetti/codex-skill-dashboard`
2. `npm run build:blueprint-flow`
3. `python3 scripts/generate_dashboard.py --refresh 15`
4. `scripts/manage_dashboard.sh restart`
5. Apri `http://192.168.1.148:3002/reports/skill-dashboard.html` e fai hard refresh.

Nota: la preview frontend generata della Lavagna non dovrebbe piu' dipendere dall'iframe `/frontend-preview`; il fallback viene renderizzato direttamente da React. L'endpoint `/frontend-preview?project=...` resta solo per compatibilita'/debug.

### "VS Code Remote-SSH forwarda porte fantasma"

VS Code auto-forwarda porte rilevate sul remote → `127.0.0.1:<porta>` sul PC mostra il **remote**, non il locale.
Sintomo: l'utente vede la stessa pagina su 127.0.0.1 e su 192.168.1.148. Soluzione: View → Ports → Stop Forwarding sulla porta in conflitto. Per Syncthing è risolto stabilmente spostando GUI LXC su 3003.

### "Editare config systemd in /etc/systemd/system/"

Dopo modifica:
```bash
systemctl daemon-reload
systemctl restart <nome>
```
Dimenticare `daemon-reload` è errore comune → il servizio riparte con la vecchia config.

### "Non si apre 8384 dopo cambio porta Syncthing"

Cambio porta GUI: `~/.config/syncthing/config.xml`, tag `<gui><address>`. Poi `systemctl restart syncthing`. Porta sync TCP 22000 invariata.

## Anti-pattern noti

- **Non cancellare** `.stversions/` o `.stfolder` di Syncthing senza capire cosa contengono.
- **Non killare `tokio-runtime-w`** manualmente: è il worker Next.js, ucciso da systemd su restart.
- **Non rinominare LXC dev senza aggiornare** `~/.ssh/config` (alias `dev`).
- **Non puntare a porta 8384** per accedere a Syncthing del LXC: oggi è **3003** (vedi `HOMELAB.md` § Syncthing).

## LXC non raggiungibile — protocollo

Se SSH su un LXC non risponde (timeout, connection refused):
1. **Non ritentare SSH in loop** — fermarsi dopo 2 tentativi
2. **Fallback via Proxmox host**: `ssh root@192.168.1.136 "pct exec <VMID> -- <comando>"` oppure `qm guest exec <VMID> -- bash -c '<comando>'` per VM
3. **VMID noti**: dev=113, stable=108, security=114, adguard=101, uptimekuma=102
4. Se anche il Proxmox host non è raggiungibile → segnala all'utente e suggerisci console grafica Proxmox

## Deploy homelab dev→stable — rollback

Se il deploy su stable fallisce dopo che i file sono già stati copiati:
1. Ferma il servizio: `systemctl stop <service>`
2. Ripristina dal backup pre-deploy (se esistente in `/opt/<app>/backup/`)
3. Se non c'è backup: `git checkout HEAD` nella directory dell'app su stable
4. Riavvia: `systemctl start <service>` e verifica con `curl -s http://localhost:<porta>`
5. Segnala all'utente con stato preciso

## Riferimenti

- `/root/Progetti/homelab/HOMELAB.md` — dossier completo (indice topico in cima)
- `ops/README.md` dei singoli progetti (es. `digital-claude-dashboard/ops/README.md`)
- `journalctl -u <servizio>` per la verità operativa di un servizio
