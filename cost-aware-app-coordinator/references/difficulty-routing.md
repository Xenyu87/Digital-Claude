# Difficulty-Based Routing

Estima la difficoltà del task dal brief e suggerisce il modello appropriato.

## Logica

```
Difficulty Score (0.0-1.0)
  ├─ 0.0-0.3: EASY → Haiku (fix bug, add button, update text)
  ├─ 0.3-0.6: MEDIUM → Sonnet (add feature, refactor local, new endpoint)
  └─ 0.6-1.0: HARD → Opus (redesign architecture, migrate DB schema)
```

## Keyword Scoring

**Hard** (+0.3 ciascuno):
- refactor, architecture, migrate, redesign, microservices, oauth, rearchitect, data model, schema

**Medium** (+0.15 ciascuno):
- add feature, new endpoint, new component, auth, implement, integrate, api, database

**Easy** (-0.15 ciascuno):
- fix typo, add button, update text, change color, fix bug, small fix

**Vagueness** (+0.2):
- Parole senza contesto: "migliora", "rendi", "ottimizza", "pulisci" su brief corto (<100 char)

Base score: 0.5 (neutrale)

## Integration con Budget-Aware Routing

Precedenza: **Budget** > **Difficulty**

```python
if budget_residui < 20k:
    model = "haiku"  # force cheap, ignora difficulty
else:
    model = difficulty_to_model(difficulty_score, budget_residui)
```

Se budget è normale (>100k): usa solo difficulty.

## Esempio

Brief: "Refactor auth architecture and migrate to OAuth"
- Keywords: refactor (+0.3), architecture (+0.3), migrate (+0.3), oauth (+0.3)
- Score: 0.5 + 1.2 = 1.7 → capped 1.0
- Routing: **Opus**

Brief: "Add button logout"
- Keywords: add button (-0.15)
- Score: 0.5 - 0.15 = 0.35
- Routing: **Sonnet** (actually easy, but with medium buffer)

Brief: "Improve performance"
- Keywords: none (vague)
- Score: 0.5 + 0.2 (vagueness) = 0.7
- Routing: **Opus** (conservative estimate)

## Script

`scripts/difficulty_estimator.py`
- `estimate_difficulty(brief: str) → {score, routing, reasons}`
- `difficulty_to_model(score, budget_residui=None) → "haiku"|"sonnet"|"opus"`
