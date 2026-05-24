# In-Flight Scope Drift Monitor (v1.1.0)

Rileva divergenza fra brief e work-in-progress, ferma lo spreco di token.

## Problema

Durante l'esecuzione: utente amplia scope, subagent refactor opportunistico, bug discovery collaterale. Task brucia token su Y quando il brief era X.

## Soluzione

Check incrementale ogni 3 turni o su trigger (file +3, token >150% atteso, categoria shift).

## Drift Score

Somma pesata di deviazioni:
- **0.0–0.3**: ✅ ON_TRACK
- **0.3–0.6**: ⚠️ DRIFT_WARNING → log + chiedi conferma
- **>0.6**: 🛑 HARD_DIVERGENCE → proponi fork task

**Componenti**:
- `files_divergence` (35%): rapporto fra file attesi e toccati
- `category_shift` (25%): se categoria è cambiata
- `token_burn` (15%): burning rate >150% atteso
- `semantic_divergence` (10%): parole chiave del brief mancano
- `scope_creep_probability` (15%): trend file al completamento

## v1.1.0 Improvements

**Improvement 1 — Predictive Score**: Estrapola trend file al completamento. Se a 40% del task hai 70% dei file, accelera l'avviso.

**Improvement 2 — Auto Scope-Checkpoint**: Se brief contiene 2+ verbi separati oppure parole vaghe ("migliora", "pulisci"), attiva **debate scope automatico** (2 Haiku min vs max) all'inizio. Costo $0.01 vs. rischio scope creep $5.

**Improvement 3 — Refactor Detector**: Riconosce pattern refactor opportunistico ("cleanup", "while we're at it", "DRY", "optimize") → segnala off-scope.

## Trigger di Check

**Automatici**:
1. Ogni 3 turni di lavoro del coordinatore
2. File toccati +3 oltre stima
3. Token spending >150% atteso
4. Categoria rilevata cambia
5. Brief ha 2+ verbi separati → auto scope-checkpoint (v1.1.0)
6. Pattern refactor rilevato (v1.1.0)

## Schema coordination-log

```json
{
  "drift_check": {
    "score": 0.45,
    "severity": "warning",
    "files_expected": 2,
    "files_actual": 4,
    "scope_creep_probability": 0.65,
    "opportunistic_refactor": true,
    "refactor_pattern": "\\brefactor\\b"
  }
}
```

## Integrazione

**SKILL.md §1.5**: Auto-trigger scope-checkpoint se 2+ verbi o parole vaghe.

**SKILL.md §6.5**: In-flight check ogni 3 turni con drift score.

**Script**: `scripts/scope_drift_detector.py` — calcola score con euristica + predictive + refactor detection.

## Azioni Correttive

**DRIFT_WARNING** (0.3–0.6):
```
⚠️ Scope drift rilevato: 4 file vs 2 attesi.
Stai facendo refactor? Continuo? [y/n]
```
→ Se N: proponi fork task.

**HARD_DIVERGENCE** (>0.6):
```
🛑 Divergenza seria dal brief.
[1] Continua (token bruciati accettati)
[2] Ferma e apri nuovo task
```

## Lezione Riflettente

Se drift rilevato >5 volte in una sessione:
```
<TBD drift detection: brief ambiguo o scope creep abituale> 
→ Aggiungere scope-checkpoint protocol iniziale
```
