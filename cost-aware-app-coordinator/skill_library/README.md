# Skill Library

Snippet riusabili emersi da uso reale della skill. Pattern Voyager: artefatti che hanno funzionato in un task vengono catalogati per riusarli in task simili.

## Cosa va qui

- frammenti di codice testati che ricorrono (es. handler Next.js per webhook Stripe)
- prompt template per sub-agent ricorrenti (es. briefing per `code-reviewer` su PR di refactor)
- snippet di configurazione che hanno funzionato (es. `tsconfig.json` per progetti Stack A)
- regex/pattern che hanno risolto problemi non banali

## Cosa NON va qui

- snippet teorici mai usati realmente
- documentazione ufficiale ricopiata (link e basta)
- variabili di configurazione private, chiavi API
- snippet da boilerplate che chiunque genera con `create-next-app`
- "potrebbe servire" — solo cose che SONO servite

## Formato

Un file per snippet. Nome descrittivo. Header con:

```markdown
# <nome snippet>

**Quando**: <task in cui è servito>
**Stack**: <stack/framework rilevante>
**Origine**: <data + breve contesto>

## Snippet

\`\`\`<lang>
<codice>
\`\`\`

## Note d'uso

- <variabili da cambiare>
- <gotcha noti>
```

## Promozione vs cancellazione

- usato 3+ volte → considera promozione: trasformalo in ricetta in `recipes/` o in default in una reference
- usato 0 volte in 60 giorni → cancella. Lo snippet che non vive nel codice corrente è morto.

## Differenza con altri posti

| Dove | Cosa |
| --- | --- |
| `recipes/` | scheletri di app completi (Next.js+Supabase landing, bot Telegram, ecc.) |
| `assets/templates/` | file `AI_*.md`, `AGENTS.md`, `CLAUDE.md` da copiare in nuovo progetto |
| `skill_library/` | frammenti puntuali, sotto il livello di ricetta |
| `references/` | regole e protocolli, non codice |

## Stato corrente

Vuoto. Si popola con l'uso reale. Vedi `references/reflexion-loop.md` per il pattern complessivo.
