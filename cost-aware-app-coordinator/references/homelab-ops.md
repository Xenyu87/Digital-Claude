# Homelab ops — comandi e pattern ricorrenti

Reference operativo per task ops sul homelab dell'utente (Proxmox + LXC `dev`/`stable`).

## Quando caricare questa reference

Quando il task tocca: `systemd`, `journalctl`, `ssh`, `lxc`, `proxmox`, `syncthing`, `cron`, `firewall`, `nginx`, `deploy`, "porta X", "servizio X", "riavvia", "backup".

Trigger speculari nella heuristic `detect_category` (vedi `scripts/auto_log_task.py`): se la categoria classifica come `ops`, considera già caricato il know-how di questo file.

## Mappa rapida del homelab

- **Host Proxmox**: hypervisor
- **LXC `dev`** `192.168.1.148` — workstation remota, dove gira Claude Code/Codex, dashboard `dev`, Syncthing GUI su porta **3003** (non 8384), porta sync TCP **22000**
- **LXC `stable`** `192.168.1.147` — produzione (dashboard pubblica)
- **LXC `dashboard-claude-coordinator`** — dashboard di produzione Claude

Per dettagli completi → `/root/Progetti/homelab/HOMELAB.md` (indice topico in cima; **non leggerlo per intero**, usa `grep -n '^## '` + `Read offset/limit`).

## Servizi systemd noti

| Servizio | LXC | Note |
|---|---|---|
| `dashboard-claude-coordinator-dev.service` | dev | Next.js, porta 3001, `npm start` dopo `npm run build` |
| `syncthing.service` | dev | GUI 3003, sync TCP 22000, config `/root/.config/syncthing/config.xml` |

## Comandi quotidiani

```bash
# Stato + log servizio
systemctl status <nome>
systemctl restart <nome>
journalctl -u <nome> -n 50 --no-pager
journalctl -u <nome> -f          # follow live

# Verifica porte in ascolto (preferisci ss a netstat)
ss -tlnp | grep -E ':(3001|3003|22000)\s'

# Hot-reload dashboard dopo modifica sorgenti
cd /root/Progetti/dashboard-claude-coordinator
npm run build && systemctl restart dashboard-claude-coordinator-dev.service
```

## Pattern ricorrenti (lezioni)

### "Pagina dev non si vede dal browser"

Quasi sempre **cache del browser**, non server. Ordine di indagine:

1. `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001/<path>` — se 200, server OK
2. `curl -s http://localhost:3001/<path> | grep -c '<tag>'` — verifica che il contenuto atteso sia nell'HTML
3. Solo se 1+2 OK → istruisci utente **Ctrl+Shift+R** (hard refresh) o incognito

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

Cambio porta GUI Syncthing si fa nel file `~/.config/syncthing/config.xml`, tag `<gui><address>`. Dopo `systemctl restart syncthing`. Porta sync TCP 22000 resta invariata.

### "Process non parte ma porta è in LISTENING"

`netstat`/`ss` mostra il **PID che ha aperto la porta**, non sempre il processo che ti aspetti. Su Windows spesso `Code` (VS Code) forwarda porte e appare come listener.
```bash
ss -tlnp | grep :<porta>             # Linux
# PowerShell:
netstat -ano | findstr :<porta>
Get-Process -Id <pid>
```

### "Hook Stop di Claude Code"

Hook in `/root/.claude/settings.json` → array `hooks.Stop`. Comandi shell eseguiti su Stop. Tre script attivi: `propose_lesson.py`, `check_version.py`, `auto_log_task.py`. Errori negli hook non bloccano Claude Code ma logghano su stderr.

## Anti-pattern noti

- **Non cancellare** `.stversions/` o `.stfolder` di Syncthing senza capire cosa contengono.
- **Non killare `tokio-runtime-w`** manualmente: è il worker Next.js, ucciso da systemd su restart.
- **Non rinominare LXC dev senza aggiornare** `~/.ssh/config` (alias `dev`).
- **Non puntare a porta 8384** per accedere a Syncthing del LXC: oggi è **3003** (vedi `HOMELAB.md` § Syncthing).

## Riferimenti

- `/root/Progetti/homelab/HOMELAB.md` — dossier completo (indice topico in cima)
- `ops/README.md` dei singoli progetti (es. `dashboard-claude-coordinator/ops/README.md`)
- `journalctl -u <servizio>` per la verità operativa di un servizio
