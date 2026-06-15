# Specialist Agents

Quando e come delegare a un sotto-agente in Claude Code.

## Catalogo completo locale (~/.claude/agents/, 27 agenti)

| Subagent | Model | Use for |
|---|---|---|
| `Explore` (built-in) | haiku | grep/glob, "where is X", fast file read |
| `ops-runner` | haiku | systemctl/journalctl/cron/ss/df, no decisions |
| `dependency-checker` | haiku | npm/pip audit: CVE, obsolete, unmaintained — read-only |
| `secrets-scanner` | haiku | hardcoded keys/tokens/.env — pre-commit |
| `pentest-agent` | haiku | scan esterno (nmap/nikto/nuclei) homelab |
| `drain-analyst` | haiku | analisi log overnight drain |
| `session-analyst` | haiku | metriche sessioni coordination-log |
| `classifier-tuner` | haiku | tuning regole classificazione log |
| `homelab-admin` | sonnet | config LXC/Proxmox/network/deploy workflow |
| `homelab-syncer` | sonnet | sync note homelab → HOMELAB.md |
| `security-hardener` | sonnet | infra security SSH/firewall/LXC — read-only |
| `code-security-scanner` | sonnet | OWASP scan + secrets + pentest report — pre-deploy |
| `bypass-guardian` | sonnet | review pre-azione rischiosa in bypass-permissions |
| `db-migrator` | sonnet | migrazioni SQL con rollback |
| `disaster-recovery` | sonnet | recovery dopo perdita ambiente |
| `code-implementer` | sonnet | edit 1-5 file scope deciso |
| `qa-tester` | sonnet | scrittura/esecuzione test, regressioni |
| `code-debugger` | sonnet | bug rescue: riproduci → isola → fix → verifica |
| `doc-writer` | sonnet | AI_*.md / README / handoff |
| `code-reviewer` | sonnet | review pre-commit diff singolo |
| `handoff-syncer` | sonnet | sync AI_HANDOFF.md / AI_CONTEXT.md |
| `intent-checker` | sonnet | verifica allineamento brief↔output parziale |
| `release-manager` | sonnet | readiness check pre-release |
| `cost-governor` | sonnet | audit budget token/costo sessione |
| `preflight-validator` | sonnet/opus | validazione piano prima di esecuzione rischiosa |
| `guida` | sonnet | orchestrazione multi-dominio per utente non tecnico |
| `architect` | opus | new feature, stack choice, data model |
| `mar-reviewer` | opus | cross-module audit, 3 reviewer + aggregatore |

## Strumento

In Claude Code la delega avviene tramite il tool `Agent`. Oltre al catalogo locale sopra, built-in disponibili: `Plan`, `general-purpose` (fallback default), `claude-code-guide`, `statusline-setup`, `claude` (fallback generico). Se non sei sicuro che un subagent type esista, non inventarlo — usa `general-purpose`.

## Quando attivare

Solo se almeno una è vera:

- la ricerca attraversa molti file e tornerebbe troppo contesto al main
- serve un secondo parere indipendente (review, audit)
- il task è chiaramente fuori scope dal main agent corrente
- richiesta esplicita dell'utente

## Quando NON attivare

- task di <3 step che il main agent chiude rapido
- editing localizzato su 1-3 file noti
- ogni volta che il task è "thorough" o "multi-angolo": gestiscilo inline

## Briefing del subagent

Il subagent parte freddo. Il prompt deve essere autocontenuto:

- obiettivo del task
- contesto necessario (path, file, vincoli)
- cosa hai già escluso
- formato di risposta atteso (es. "report sotto 200 parole")

Niente "fai del tuo meglio". Niente "in base ai risultati, implementa X" — la sintesi resta al main agent.

## Modello del subagent

Imposta sempre `model` in base al catalogo sopra. Default Haiku, scala su fallimento (vedi SKILL.md §3). Se il main agent è già Opus e il sub-task è leggero, `haiku` riduce il costo senza perdere qualità.

## Background vs foreground

- Foreground: quando ti serve il risultato per il prossimo passo
- Background: solo se hai lavoro indipendente realmente parallelo

Default: foreground.

## Verifica

Il summary del subagent dice cosa ha provato a fare. Quando un subagent scrive codice, controlla i diff effettivi prima di dichiarare fatto.

## Flag per subagent dispatched (Claude Code)

I subagent accettano flag diretti per override puntuale:

```bash
# ops-runner in read-only: niente scrittura accidentale
claude agents run ops-runner --model haiku --permission-mode read-only "tail -50 /var/log/app.log"

# architect con permesso pieno e priorità alta
claude agents run architect --model opus "disegna lo schema dati per feature X"
```

Fast mode (flag `/fast` in sessione) usa Opus 4.8 by default — output 2.5x più veloce e 3x più economico rispetto al fast mode di Opus 4.7. Utile per task brevi dove vuoi velocità senza rinunciare alla qualità Opus.

## Ecosistemi di agent esterni (plugin marketplace)

`wshobson/agents` (35k+ stelle) è un ecosistema di 185 agent domain-specific (python-pro, k8s, security-auditor, ecc.) installabili via `/plugin marketplace add wshobson/agents`. Organizzati in 80 plugin, non si sovrappongono al catalogo locale (`ops-runner`, `architect`, `code-implementer`). Utile per task fuori dal dominio corrente (es. Django, blockchain, ML pipeline) ma richiede installazione plugin separata — non integrare wholesale.

## Trigger automatico MAR

Preferisci `mar-reviewer` a `code-reviewer` quando:
- categoria=audit, oppure
- categoria=modifica AND >5 file AND budget diverso da Economico

`mar-reviewer` spawna 3 sub-review Sonnet (sicurezza/performance/leggibilità) + aggregatore Haiku. Ricetta: `recipes/mar-audit.md`.

## Dynamic Workflows (Opus 4.8 — research preview)

Tier sopra il parallel swarm: fino a 1.000 agenti (16 concurrent), multi-giorno, codebase-wide (1k+ file), zero context pollution (script fuori context window) — vs parallel swarm (2-3 agenti, <1 sessione, <5 file).

**Attivazione**: auto mode o effort `xhigh` (ultracode), non parametro API — Claude scrive lo script di orchestrazione. Richiede Claude Code v2.1.154+, piano Max/Team/Enterprise. Costo alto, conferma sempre con utente. Quirk: early stopping, file deletion aggressiva su ops distruttive. Non usare per: <20 file, task sequenziali, latency-sensitive.

## Anti-pattern

- delegare la comprensione ("decidi tu cosa cambiare")
- spawnare subagent in cascata senza riusare quelli già attivi
- duplicare lavoro tra main e subagent
