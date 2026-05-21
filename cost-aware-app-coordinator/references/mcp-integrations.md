# MCP Integrations

Quando un task richiede di operare su SaaS esterni (issue tracker, chat, docs, code host), usa server MCP invece di scrivere wrapper bash o curl. Format ufficiale dei tool: `ServerName:tool_name`.

## Quando attivare un server MCP

- handoff cross-tool reale (aprire issue, notificare canale, aggiornare board)
- letture autoritative (PR review, status incident, doc operativa)
- azioni di chiusura turno (es. commento su PR a fine task non banale)

NON attivare per: scraping web generico (usa `WebFetch`), lookup veloce di una pagina nota.

## Server raccomandati (Anthropic + community 2026)

| Server | Tool tipici | Quando |
| --- | --- | --- |
| `GitHub` | `GitHub:create_issue`, `GitHub:get_pr`, `GitHub:list_workflow_runs` | apertura issue, lettura PR, controllo CI |
| `Linear` | `Linear:create_issue`, `Linear:update_issue`, `Linear:get_issue` | task tracking. Remote HTTP da feb 2026 (no più STDIO) |
| `Slack` | `Slack:post_message`, `Slack:search_messages` | notifiche team, recupero contesto da canali |
| `Notion` | `Notion:search`, `Notion:get_page`, `Notion:append_block` | doc operativa, runbook, scheda progetto |
| `Filesystem` | `Filesystem:read`, `Filesystem:write` | path fuori dal repo corrente (rare, conferma prima) |

Server addizionali utili a seconda del progetto: `Sentry` (incident), `Atlassian` (Jira+Confluence; SSE deprecato 30 giu 2026, usare Streamable HTTP), `Stripe` (read-only su pagamenti).

## Gate di rischio per MCP

I tool che **scrivono** su sistemi esterni sono gate hard (vedi `decision-risk-gates.md`):

- creazione/chiusura issue, commenti su PR, merge
- post su canali team
- modifica doc condivise

I tool **read-only** (`get_*`, `search_*`, `list_*`) sono safe — usali liberamente.

## Briefing al sub-agent con tool MCP

Quando deleghi a un `Agent` un task che usa MCP:

- cita i tool esatti con format `Server:tool` nel prompt
- specifica i parametri obbligatori
- chiedi formato output strutturato (l'agente non deve raccontare la chiamata, deve riportare il risultato)

Esempio briefing:

```
Apri issue Linear nel team "PLATFORM" con title "Drift skill v0.7" e description <X>.
Tool: Linear:create_issue.
Riporta: URL dell'issue creata.
```

## Compatibilità formato

Le skill custom sono ora standard aperto: Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot supportano lo stesso formato. I riferimenti MCP `Server:tool` funzionano cross-tool. Le skill di questa repo sono quindi portabili — nessuna dipendenza specifica Claude Code.

## Anti-pattern

- `mcp__github__create_issue` (forma client-specifica): usa `GitHub:create_issue`.
- chiamare server MCP per leggere file locali del repo: usa Read/Glob/Grep.
- spawnare un sub-agent solo per fare 1 chiamata MCP: chiamala dal main.
- assumere che un server sia configurato: se non hai conferma in `AI_CONTEXT.md`, chiedi.

## Dove trovare server MCP

Usa il **MCP Registry** come fonte canonica: `https://registry.modelcontextprotocol.io/`
La lista "Third-Party Servers" nel README di `modelcontextprotocol/servers` è deprecata (rimossa a favore del Registry).

**`MCP_TOOL_TIMEOUT`**: da v2.1.142 rispetta valori >60s (fix storico). Alzalo per tool MCP lenti (fetch di pagine pesanti, chiamate git remote):
```bash
MCP_TOOL_TIMEOUT=120000  # ms — in .env.local o nell'env del processo
```

## Quando aggiungere un nuovo server al progetto

1. L'utente lo abilita in `settings.json` (vedi skill `update-config`).
2. Aggiungi nota in `AI_CONTEXT.md` su quale server è disponibile e su che ambito.
3. Non assumere che la copia installata di Claude Code abbia gli stessi server — è settaggio per workspace.
