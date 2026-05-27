# External Routing (opt-in)

Routing opzionale verso provider esterni (OpenRouter/DeepSeek) per categorie a basso rischio.

## DISABILITATO DI DEFAULT

`EXTERNAL_ROUTER_ENABLED=false` nell'env. Non si attiva mai senza intervento esplicito.

## Quando attivare

Solo per:
- categoria `ops` con task puramente esplorativi (nessun codice di prodotto)
- esplorazioni Haiku-equivalenti su dominio generico (non il progetto corrente)

## Quando NON attivare (assoluto)

- codice di prodotto (qualsiasi file del progetto)
- credenziali, token, segreti, env vars
- dati personali o aziendali
- task con `AI_*.md` nel contesto (contengono architettura interna)
- budget Massima sicurezza
- qualsiasi categoria: audit, bug_rescue, nuova_app, modifica, miglioramento_skill

## Caveat privacy

I dati passano da infrastruttura esterna (OpenRouter, DeepSeek). Non si applica la policy
Anthropic. Anthropic non vede queste chiamate. Il log locale marca le righe con `external_router: true`.

## Configurazione

```bash
# Nel progetto o in ~/.bashrc
export EXTERNAL_ROUTER_ENABLED=true          # solo se sai cosa stai facendo
export EXTERNAL_ROUTER_TARGET=deepseek       # o openrouter
export OPENROUTER_API_KEY=sk-or-...
```

Vedi `.env.local.example` nella skill dir per i campi completi.

## Warning di sessione

Al primo uso in sessione, `external_router.py` stampa un warning visibile e logga in `coordination-log.jsonl` con `external_router: true`. Non e' silenziabile.

## Script

`scripts/external_router.py` — classe `ExternalRouter` con metodo `route(prompt, category)`.
Se l'env non e' configurato correttamente, fallback silenzioso al router locale (Haiku).
