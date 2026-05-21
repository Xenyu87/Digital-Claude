# Progressive Loading

Quando affinare o verificare il caricamento delle reference. Non aprire questo file per task normali: la mappa in `SKILL.md` basta.

## Principio

`SKILL.md` è il core sempre caricato. Le `references/*.md` si aprono solo quando una regola del core lo richiama o un trigger concreto è presente. Niente "apertura per sicurezza".

## Trigger per reference

| Reference | Trigger |
| --- | --- |
| `budget-modes.md` | l'utente cambia modalità o il task è grande/ambiguo/rischioso |
| `progressive-loading.md` | stai verificando o tunando il loading stesso |
| `decision-risk-gates.md` | prossimo passo costoso, rischioso, distruttivo, esterno o ampio |
| `scope-checkpoint.md` | task vago/multi-obiettivo/utente non programmer con scelte tecniche aperte |
| `coordinator-safety.md` | confidenza media/bassa, rischio alto o serve red team |
| `response-economy.md` | output sta crescendo o serve un formato compatto |
| `compression-pass.md` | compressione sicura di prompt, handoff, doc, commit/PR |
| `role-profiles.md` | conta una lente FE/BE/full-stack/QA/security/UX/data/DevOps/perf/review |
| `qa-test-agent.md` | flusso FE+BE, cambio contratto/auth/dati, bug non banale, validazione push/PR |
| `specialist-agents.md` | scelta o briefing di un sub-agent specialista |
| `agent-handoff.md` | più sub-agent devono condividere decisioni, blocchi, contratti |
| `task-routing.md` | richiesta mista, ampia, rischio di sovra-lettura |
| `app-creation-blueprint.md` | nuova app, full-stack feature, rebuild, contratto app |
| `default-stacks.md` | nuova app senza vincoli di stack: scelta A/B/C invece di chiedere il framework |
| `deploy-paths.md` | configurazione Vercel/Netlify/Railway/Cloudflare dopo il primo dev locale |
| `visual-first-testing.md` | modifica UI o feature visibile, utente non programmer da guidare nel test |
| `mcp-integrations.md` | task che opera su SaaS esterni (GitHub/Linear/Slack/Notion/...) o briefing sub-agent che chiama tool MCP |
| `project-context-template.md` | manca sistema di contesto progetto |
| `structure-memory-template.md` | serve memoria struttura app |
| `second-brain-template.md` | servono decisioni durevoli, vincoli, trigger di revisione |
| `agent-autolog-template.md` | errore agente, spreco, correzione utente, contesto stantio |
| `cross-agent-handoff-template.md` | switch tra Claude Code e un altro agente sullo stesso progetto |
| `maintenance-compaction.md` | cleanup, consolidamento versioni, decisione di stop |
| `skill-sync.md` | install, sync, rilascio, pubblicazione, domande sulla versione futura |
| `improvement-log.md` | registrazione di un cambio di comportamento |
| `release-notes.md` | aggiornamento versione |
| `self-improvement.md` | l'utente chiede automiglioramento o audit della skill stessa |
| `reflexion-loop.md` | fine task non banale (≥5 file o utente ha corretto la skill): estrarre lezione preventiva |

## Quando NON caricare

- la decisione è già stata presa
- una regola compatta in `SKILL.md` basta
- il task è una singola modifica locale
- la reference è stata già letta nel turno corrente: riusa la comprensione

## Projected context cost (da v2.1.143)

`/plugin` ora mostra il projected context cost di ogni plugin/skill caricata. Usalo come segnale di budget:
- se una reference già caricata pesa >10% del budget residuo, evita di aprirne altre non strettamente necessarie
- se un plugin esterno (es. `wshobson/agents`) mostra costo stimato alto, valuta se il task non si chiude senza installarlo

## Tuning

Se noti che apri ripetutamente la stessa reference per task simili, valuta di promuovere la sua regola chiave dentro `SKILL.md` (e tagliare la reference). Se una reference non viene mai aperta in pratica, valuta di rimuoverla o fonderla con un'altra.
