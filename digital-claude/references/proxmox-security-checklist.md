# Proxmox Security Checklist

Hardening per homelab Proxmox. Divisa in one-time (da fare una volta) e periodica (nel drain settimanale).

## One-time (esegui con homelab-admin + conferma per ogni step)

### SSH
- [ ] `PermitRootLogin no` in `/etc/ssh/sshd_config` del host Proxmox
- [ ] `PasswordAuthentication no` — solo chiavi SSH
- [ ] Porto SSH non-standard (es. 2222 invece di 22) se esposto su internet
- [ ] `AllowUsers` whitelist degli utenti abilitati

### Accesso pannello web
- [ ] 2FA abilitato (Proxmox supporta TOTP nativo: Datacenter → Permissions → Two Factor)
- [ ] Certificato Let's Encrypt invece del self-signed (Proxmox: Node → Certificates → ACME)
- [ ] Accesso pannello solo da IP LAN (firewall regola in ingress sulla porta 8006)

### Firewall Proxmox
- [ ] Firewall abilitato a livello datacenter (Datacenter → Firewall → Options → Enable)
- [ ] Policy default: DROP in ingress, ACCEPT in egress
- [ ] Whitelist esplicita: SSH (22 o custom), pannello web (8006) solo da LAN
- [ ] Regole per ogni LXC/VM: blocca traffico inter-container non necessario

### LXC containers
- [ ] Tutti i container in modalità **unprivileged** (privileged: 0 nel config)
- [ ] Nessun mount di `/` o `/etc` host dentro i container
- [ ] Risorse limitate (CPU/RAM cap) per evitare DoS accidentale

### Aggiornamenti
- [ ] `apt update && apt upgrade` sul host Proxmox (non solo sulle VM/LXC)
- [ ] Abilita notifiche aggiornamenti sicurezza: `unattended-upgrades` o cron settimanale

### Backup
- [ ] Backup cifrati abilitati (Proxmox Backup Server: encryption key configurata)
- [ ] Backup offsite o almeno su storage separato dal host

### fail2ban
- [ ] Installato e attivo sul host: `systemctl status fail2ban`
- [ ] Jail SSH attiva: `fail2ban-client status sshd`

---

## Periodica (drain domenicale — security_audit)

Comandi che `security-hardener` esegue automaticamente:

```bash
# Aggiornamenti sicurezza pendenti
apt list --upgradable 2>/dev/null | grep -i security

# Porte in ascolto (confronta con whitelist attesa)
ss -tlnp

# fail2ban attivo e ban recenti
systemctl is-active fail2ban
fail2ban-client status sshd 2>/dev/null | grep "Total banned"

# Certificati in scadenza (<30 giorni)
for cert in /etc/pve/local/pve-ssl.pem /etc/letsencrypt/live/*/cert.pem; do
  [ -f "$cert" ] && openssl x509 -enddate -noout -in "$cert" 2>/dev/null
done

# LXC privilegiati (dovrebbero essere 0)
grep -l "unprivileged: 0" /etc/pve/lxc/*.conf 2>/dev/null | wc -l
```

Se uno dei check rileva anomalie → append in `HOMELAB_PENDING.md`:
```
[SECURITY ALERT YYYY-MM-DD] <descrizione anomalia> → richiede intervento umano
```

---

## Riferimenti
- `references/homelab-ops.md` per comandi ops Proxmox
- `~/.claude/agents/security-hardener.md` per l'agente di audit
- `references/background-drain.md` per il timer notturno
