# Specialist Agents

Quando e come delegare a un sotto-agente in Claude Code.

## Strumento

In Claude Code la delega avviene tramite il tool `Agent`. I `subagent_type` tipicamente disponibili nelle installazioni Claude Code recenti:

- `Explore` — ricerca read-only nel codice
- `Plan` — disegno di un piano di implementazione
- `code-reviewer` — review indipendente di un diff
- `general-purpose` — ricerca multi-step e task open-ended
- `doc-writer` — aggiornare/creare docs e commenti per logica non ovvia
- `architect` — high-level design, scelte di libreria, struttura file
- `claude-code-guide` — domande su Claude Code/SDK/API (skill, hooks, MCP)
- `statusline-setup` — configurazione status line dell'utente
- `claude` — fallback generico quando nessun nome match
- `qa-tester` — scrive ed esegue test (pytest/Vitest), test di regressione post bugfix. Custom registrato in `~/.claude/agents/qa-tester.md`.

I nomi effettivi dipendono dall'ambiente: se non sei sicuro che un subagent type esista, non inventarlo. Default: `general-purpose`.

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

Imposta sempre il parametro `model` del tool `Agent` in base al tipo di task. Tabella decisionale (in dubbio scegli il più piccolo):

| Tipo di task del sub-agent | `model` |
| --- | --- |
| ricerca cross-file (`Explore`), summary, riformulazione, formato, lookup | `haiku` |
| code review (`code-reviewer`), implementazione singolo file, debug 2-3 file, doc-writer | `sonnet` |
| architettura (`architect`), `Plan` per task ampi, refactor cross-modulo, security/auth, audit ampio, migrazione dati | `opus` |

Se il main agent è già Opus e il sub-task è leggero, `haiku` riduce il costo senza perdere qualità.

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

Fast mode (flag `/fast` in sessione) usa Opus 4.7 by default — utile per task brevi dove vuoi output veloce senza rinunciare alla qualità Opus.

## Ecosistemi di agent esterni (plugin marketplace)

`wshobson/agents` (35k+ stelle) è un ecosistema di 185 agent domain-specific (python-pro, k8s, security-auditor, ecc.) installabili via `/plugin marketplace add wshobson/agents`. Organizzati in 80 plugin, non si sovrappongono al catalogo locale (`ops-runner`, `architect`, `code-implementer`). Utile per task fuori dal dominio corrente (es. Django, blockchain, ML pipeline) ma richiede installazione plugin separata — non integrare wholesale.

## Anti-pattern

- delegare la comprensione ("decidi tu cosa cambiare")
- spawnare subagent in cascata senza riusare quelli già attivi
- duplicare lavoro tra main e subagent
