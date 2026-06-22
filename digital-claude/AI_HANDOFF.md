# AI Handoff

## Current Goal

Consolidare il sistema di automazione notturna (drain.py) e le fondamenta di self-improvement della skill (skillopt, verify_edit, evoskill).

## State

- Done (2026-06-22): drain.py ristrutturato in 2 fasi (parallela + sequenziale), 4 nuove funzioni: `run_morning_briefing`, `run_skillopt_lite`, `run_ace_reflector`, `run_evoskill_lite`. Helper `_run_parallel()` con ThreadPoolExecutor(max_workers=4).
- Done (2026-06-22): `scripts/verify_edit.py` (NUOVO) — hook PostToolUse command per validare SKILL.md line count, JSON syntax, Python syntax su ogni Edit/Write/MultiEdit.
- Done (2026-06-22): `scripts/hooks/coordination_log.py` arricchito con `_extract_duration()`, `_extract_agents()`, `_extract_files_count()` — popola duration_s, agents_used, files_touched per ogni log entry.
- Done (2026-06-22): `AI_EVOLUTION_PLAN.md` creato — piano L0→L3 con stato aggiornato.
- Done (2026-06-22): settings.json aggiornato con 3 nuovi hook (SessionStart cache_bundle_builder async, PostToolUse verify_edit, PostToolUse agent su SKILL.md/settings.json) e UserPromptSubmit ora locale.
- Done (2026-06-22): `references/prompt-caching.md` e `references/task-routing.md` aggiornati con nuove sezioni (non cachare output dinamici, RouteLLM).
- Done (2026-06-22): `skill-cache.md` (83KB bundle SKILL+references) generato da `cache_bundle_builder.py` per Anthropic SDK caching.
- Done (in sessione precedente): Lavagna con blueprint-view-v1, React Flow, frontend preview side-by-side, Playwright visual tests, tab dashboard.
- In progress: evoskill_lite produce `reports/failure-patterns.jsonl` con status=frontier (da usare per future iterazioni di SKILL.md).

## Changed Files (2026-06-22)

- `scripts/drain.py`: 2-fase pipeline, 4 nuove funzioni, helper `_run_parallel()`.
- `scripts/hooks/coordination_log.py`: nuovi extractor `_extract_duration`, `_extract_agents`, `_extract_files_count`.
- `scripts/verify_edit.py` (NUOVO): PostToolUse hook per validazione SKILL.md/JSON/Python.
- `.gitignore`: aggiunti AI_SCORE.md, scripts/.score_checksum, scripts/dead-rules-cache.json, scripts/skill-assay-results.json, scripts/thresholds.json, skill-cache.md.
- `AI_EVOLUTION_PLAN.md` (NUOVO): piano progressione autonomia L0→L3.
- `references/prompt-caching.md`: sezione "Non cachare output di tool dinamici".
- `references/task-routing.md`: sezione RouteLLM.

## Open Risks

- evoskill_lite è status=frontier: legge sessioni ma non modifica ancora SKILL.md autonomamente. Da attivare solo dopo validazione pattern failure.
- skillopt_lite ha gate ≤450 righe su SKILL.md — se SKILL.md supera il limite l'edit viene saltato silenziosamente.
- verify_edit.py hook è PostToolUse command (non agent): si aspetta exit 0 per non bloccare. Se lancia eccezione uncaught, può interferire con Edit normali.
- Playwright richiede Chromium e socket permissions su ambienti ristretti.

## Next Step

1. Validare evoskill_lite su sessioni reali con outcome=failed/partial (verificare che `reports/failure-patterns.jsonl` si popoli).
2. Definire soglia minima di pattern failure per far propagare un aggiornamento a SKILL.md via skillopt.
3. Valutare se aggiungere morning_briefing a un cron separato o tenerlo dentro drain.py.

## Do Not Repeat

- Non eseguire drain.py in parallelo con test che leggono/scrivono gli stessi file in `reports/`.
- Non modificare `§0`, `§1`, `§3` di SKILL.md direttamente — sono protetti da skillopt_lite gate.
- Non aumentare max_workers oltre 4 in `_run_parallel()` senza verificare contention su SKILL.md.

## Cronologia

### 2026-06-22 — Drain 2-fase + verify_edit + evoskill_lite
- Cosa: ristrutturato drain.py in pipeline parallela/sequenziale; aggiunto hook verify_edit.py; arricchito coordination_log.py; creato AI_EVOLUTION_PLAN.md; aggiornato settings.json con 3 nuovi hook.
- Perché: ridurre latenza drain notturno, aggiungere guardrail su edit SKILL.md, iniziare raccolta failure pattern per self-improvement.
- TODO generati: validare evoskill_lite su sessioni reali, definire soglia propagazione failure→SKILL.md.
