# Maintenance Compaction

Compaction dei file `AI_*.md` per evitare drift e crescita non controllata.

## Trigger

Esegui (o proponi) compaction quando una soglia di `compression-pass.md` è superata, o quando l'utente lo chiede esplicitamente. Le soglie esatte stanno in `compression-pass.md` come fonte unica.

## Cadenza consigliata

Non automatica. Compaction manuale o offerta a fine settimana / fine sprint.

## Procedura

1. Leggi il file da compattare.
2. Identifica contenuto promovibile in `AI_DECISIONS.md`, `AI_STRUCTURE.md`, `AGENTS.md`.
3. Promuovi.
4. Comprimi residui (raggruppa, accorcia, rimuovi voci scadute).
5. Diff e commit separato `chore: compaction memorie AI`.

## Cosa preservare sempre

- decisioni durevoli e loro motivazione
- file marcati critici
- regole condivise tra agenti

## Cosa è sicuro rimuovere

- voci di log >30 giorni la cui lezione è confluita altrove
- stato di task chiusi
- output di test
- riferimenti a branch o PR già mergeate

## Baseline modelli — revisione periodica

Ad ogni minor della CLI Claude Code (es. v2.1.x → v2.2.x), rivisita la nota "Baseline" in `SKILL.md` §3. Verifica:
- `grep -rn "Opus 4\.\|Sonnet 4\.\|Haiku 4\." SKILL.md references/` → nessun modello hardcoded obsoleto
- prezzi in §18 ancora allineati con la pricing page Anthropic

## Context Editing (API beta — alternativa alla compaction manuale)

Per sessioni agentic lunghe con molte tool call (file read, search, screenshot): invece di compattare manualmente i file AI_*.md, si può abilitare **context editing** a livello API. Rimuove automaticamente tool call e risultati obsoleti dal context window prima di raggiungere il limite.

- **Risparmio**: 84% token su sessioni 100+ turni con tool use; +29% performance agenti
- **Come attivare**: parametro nella chiamata SDK (vedi docs Anthropic `context-editing`)
- **Quando preferirla alla compaction manuale**: sessioni pure-API o script automatizzati (drain, schedule); per sessioni Claude Code interattive, la compaction automatica del runtime già gestisce questo

## Anti-pattern

- compaction durante una feature attiva (rischia di perdere stato)
- compaction "aggressiva" che riduce le righe ma perde contesto
- compaction senza commit precedente (impossibile rivedere)

## Output

```
Fatto: compaction AI_HANDOFF.md (84 → 22), AI_AGENT_LOG.md (210 → 65).
Promosso in AI_DECISIONS.md: scelta DB, scelta auth.
Verifica: git diff
```
