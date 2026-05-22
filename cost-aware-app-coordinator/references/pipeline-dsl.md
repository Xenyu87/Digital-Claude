# Pipeline DSL

Sintassi YAML per definire pipeline di subagent con dipendenze esplicite (DAG).

## Formato base

```yaml
pipeline: <nome-pipeline>
description: <descrizione breve>
steps:
  - id: <identificatore-unico>
    agent: <nome-subagent>
    model: <haiku|sonnet|opus>       # opzionale, default del subagent
    prompt: "<testo del prompt>"
    output_key: <chiave>             # nome del risultato in contesto
    needs: [<id>, ...]               # dipendenze (ometti se primo step)
    input_filter: <chiave-da-needs>  # quale output precedente usare
```

## Variabili di template

Nel campo `prompt` puoi usare `{{step_id.output_key}}` per iniettare l'output di uno step precedente:

```yaml
prompt: "Scrivi test per i file modificati: {{impl.files_changed}}"
```

Filtri disponibili:
- `{{step.output_key}}` — output grezzo dello step
- `{{step.output_key | files_list}}` — estrae lista di path da testo libero
- `{{step.output_key | first_200}}` — primi 200 caratteri (risparmio token)

## Regole DAG

- Ogni `id` deve essere unico nel pipeline.
- `needs` forma il grafo delle dipendenze; il runner fa toposort automatico.
- Step senza `needs` girano per primi (possibilmente in parallelo se indipendenti).
- Loop e dipendenze circolari causano errore immediato.

## Log e tracing

Ogni step completato viene loggato in `coordination-log.jsonl` con campo `pipeline` e `step_id`. Il runner `scripts/run_pipeline.py` gestisce il log.

## Esempi disponibili

- `recipes/pipelines/feature-with-tests.yml` — impl + test + review
- `recipes/pipelines/bugfix-locked.yml` — debug + fix + regression test

## Limitazioni

- I subagent non si parlano direttamente: il runner e' sempre il router.
- Output di uno step e' passato come testo nel prompt del successivo (niente struct).
- Timeout per step: 10 minuti (configurabile con `timeout_s` per step).
- Massimo 10 step per pipeline (anti-pattern: pipeline enormi nascondono scope ambigui).
