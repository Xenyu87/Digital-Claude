# Coordination Sedimentation

Schema e regole per il log strutturato di ogni task chiuso dalla skill.

## Scopo

Ogni task non banale viene serializzato in un file JSONL locale, poi consumato dalla dashboard per analisi di pattern storici (categoria vs costo, modelli usati, tasso di successo). Permette auto-curriculum e drain settimanali senza dipendere da una sessione interattiva.

## Posizione file

```
~/.claude/projects/<proj-slug>/memory/coordination-log.jsonl
```

Il `<proj-slug>` è il path del progetto codificato come fa Claude Code: caratteri non alfanumerici sostituiti con `-` (es. `-root-Progetti-digital-claude-dashboard`).

## Schema JSONL (una riga per task chiuso)

```json
{
  "ts": "2026-05-22T19:30:00Z",
  "task_id": "uuid-v4",
  "project": "digital-claude-dashboard",
  "category": "modifica",
  "trigger_keywords": ["bug", "fix"],
  "agents_used": ["code-implementer"],
  "models": ["sonnet"],
  "tokens": {
    "input": 12000,
    "output": 3000,
    "cache_read": 40000,
    "cache_creation": 2000
  },
  "cost_usd": 0.42,
  "duration_s": 180,
  "outcome": "ok",
  "files_touched": 5,
  "lesson": "opzionale — stringa breve se c'è una lezione emergente"
}
```

Campi obbligatori: `ts`, `task_id`, `project`, `category`, `outcome`.
Campi opzionali: tutti gli altri (mai omettere la chiave, usa `null`).

## Chi scrive

`scripts/log_coordination.py` — chiamato dall'hook Stop (vedi `scripts/hooks/coordination_log.py`). Fa append atomico (write + rename) per evitare corruzioni.

## Chi legge

- Dashboard via `GET /api/coordination-log?category=X&limit=N`
- `scripts/drain.py` per auto-curriculum e compaction
- `scripts/run_pipeline.py` per log step-by-step

## Regole di privacy

- **Nessun PII nei campi loggati**: `lesson` e `trigger_keywords` non devono contenere nomi, email, credenziali, contenuto di messaggi utente.
- Il campo `lesson` accetta solo pattern tecnici astratti (es. "opus usato su task modifica banale").
- Il campo `trigger_keywords` è estratto dal tipo di task, non dal testo verbatim del prompt.
- Il file JSONL resta locale (`~/.claude/`): non è mai pushato al repo del progetto.

## Rotazione

Quando il file supera 5000 righe, `drain.py` archivia le righe oltre 90 giorni in `coordination-log-archive-<YYYY-MM>.jsonl` nella stessa directory.

## Dashboard: endpoint e tabella

- Tabella Supabase: `coordination_log` (migration in `supabase/migrations/`)
- POST `/api/coordination-log`: riceve una riga e la inserisce
- GET `/api/coordination-log?category=X&limit=N`: query con filtri
- Pagina analisi: `/economy/patterns`
