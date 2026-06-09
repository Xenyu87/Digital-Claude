#!/usr/bin/env python3
"""skill_assay.py — Assertions deterministiche sulle trace coordination-log.

Ispirato ad AgentAssay (arxiv:2603.02601): scoring 0-100 su 5 assertion
calcolate interamente da dati locali (zero costo LLM).

Uso standalone:
    python3 skill_assay.py /path/al/progetto

Uso da drain.py (import):
    from skill_assay import run_skill_assay
    result = run_skill_assay(project_path)
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
RESULTS_PATH = SKILL_DIR / "scripts" / "skill-assay-results.json"

# Thresholds hardcoded usati se thresholds.json non esiste
_DEFAULT_THRESHOLDS = {
    "modifica": {"p90": 77.38},
    "domanda": {"p90": 9.10},
    "ops": {"p90": 0.36},
}


def _proj_slug(project_path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")


def _load_log(project_path: str) -> list[dict]:
    slug = _proj_slug(project_path)
    log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
    if not log_path.exists():
        return []
    records: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _ts_epoch(rec: dict) -> float:
    ts_str = rec.get("ts", "")
    try:
        return datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _load_thresholds() -> dict:
    thresholds_file = SKILL_DIR / "scripts" / "thresholds.json"
    if not thresholds_file.exists():
        return _DEFAULT_THRESHOLDS
    try:
        data = json.loads(thresholds_file.read_text(encoding="utf-8"))
        result: dict = {}
        for row in data.get("thresholds", []):
            cat = row.get("categoria", "")
            p90 = row.get("ceiling_p90")
            if cat and p90 is not None:
                result[cat] = {"p90": float(p90)}
        return result if result else _DEFAULT_THRESHOLDS
    except Exception:
        return _DEFAULT_THRESHOLDS


# ── Assertions ────────────────────────────────────────────────────────────────

def a1_cost_compliance(records: list[dict], thresholds: dict) -> dict:
    """A1 — % sessioni (ultime 90gg) con cost_usd ≤ threshold[category].p90."""
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - 90 * 86400

    window = [r for r in records if _ts_epoch(r) >= cutoff]
    if not window:
        return {
            "score": 50,
            "label": "Costo nei limiti",
            "detail": "nessuna sessione negli ultimi 90gg",
            "weight": 0.30,
        }

    compliant = 0
    for r in window:
        cat = r.get("category", "")
        cost = float(r.get("cost_usd") or 0)
        if cat not in thresholds:
            compliant += 1  # categoria senza soglia → conta come conforme
            continue
        if cost <= thresholds[cat]["p90"]:
            compliant += 1

    score = round((compliant / len(window)) * 100)
    return {
        "score": score,
        "label": "Costo nei limiti",
        "detail": f"{compliant}/{len(window)} sessioni sotto p90",
        "weight": 0.30,
    }


def a2_delegation_rate(records: list[dict]) -> dict:
    """A2 — % sessioni (ultime 30gg) con agents_used non vuoto."""
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - 30 * 86400

    window = [r for r in records if _ts_epoch(r) >= cutoff]
    if not window:
        return {
            "score": 0,
            "label": "Deleghe a subagent",
            "detail": "nessuna sessione negli ultimi 30gg",
            "weight": 0.25,
        }

    with_agents = sum(
        1 for r in window
        if r.get("agents_used") and len(r["agents_used"]) > 0
    )
    score = round((with_agents / len(window)) * 100)
    detail = f"{with_agents}/{len(window)} sessioni con agenti"
    if with_agents == 0:
        detail += " (fix deployato oggi)"
    return {
        "score": score,
        "label": "Deleghe a subagent",
        "detail": detail,
        "weight": 0.25,
    }


def a3_category_diversity(records: list[dict]) -> dict:
    """A3 — Shannon entropy delle categorie (ultimi 90gg), normalizzata."""
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - 90 * 86400

    window = [r for r in records if _ts_epoch(r) >= cutoff]
    if not window:
        return {
            "score": 0,
            "label": "Diversità categorie",
            "detail": "nessuna sessione negli ultimi 90gg",
            "weight": 0.20,
        }

    counts: dict[str, int] = {}
    for r in window:
        cat = r.get("category", "unknown") or "unknown"
        counts[cat] = counts.get(cat, 0) + 1

    n_cats = len(counts)
    total = len(window)

    if n_cats <= 1:
        score = 0
        entropy_str = "1 categoria"
    else:
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
        max_entropy = math.log2(n_cats)
        entropy_norm = entropy / max_entropy if max_entropy > 0 else 0
        score = round(entropy_norm * 100)
        entropy_str = f"{n_cats} categorie: {', '.join(sorted(counts))}"

    return {
        "score": score,
        "label": "Diversità categorie",
        "detail": entropy_str,
        "weight": 0.20,
    }


def a4_model_efficiency(records: list[dict]) -> dict:
    """A4 — % sessioni con almeno 1 modello 'haiku' in models."""
    # Nessun filtro temporale: usa tutto lo storico disponibile
    if not records:
        return {
            "score": 0,
            "label": "Utilizzo modelli economici",
            "detail": "nessuna sessione disponibile",
            "weight": 0.15,
        }

    with_haiku = sum(
        1 for r in records
        if any("haiku" in str(m).lower() for m in (r.get("models") or []))
    )
    score = round((with_haiku / len(records)) * 100)
    return {
        "score": score,
        "label": "Utilizzo modelli economici",
        "detail": f"haiku: {with_haiku}/{len(records)} sessioni",
        "weight": 0.15,
    }


def a5_cost_trend(records: list[dict]) -> dict:
    """A5 — Trend cost_usd categoria 'modifica': ultima settimana vs precedente."""
    now = datetime.now(timezone.utc).timestamp()
    week1_start = now - 7 * 86400
    week2_start = now - 14 * 86400

    modifica_recent = [
        float(r.get("cost_usd") or 0)
        for r in records
        if r.get("category") == "modifica" and _ts_epoch(r) >= week1_start
    ]
    modifica_prev = [
        float(r.get("cost_usd") or 0)
        for r in records
        if r.get("category") == "modifica"
        and week2_start <= _ts_epoch(r) < week1_start
    ]

    if len(modifica_recent) < 2 or len(modifica_prev) < 2:
        return {
            "score": 50,
            "label": "Trend costo",
            "detail": "dati insufficienti per il confronto settimanale",
            "weight": 0.10,
        }

    avg_recent = sum(modifica_recent) / len(modifica_recent)
    avg_prev = sum(modifica_prev) / len(modifica_prev)

    if avg_prev == 0:
        return {
            "score": 50,
            "label": "Trend costo",
            "detail": "settimana precedente a costo zero — dati insufficienti",
            "weight": 0.10,
        }

    change_pct = (avg_recent - avg_prev) / avg_prev * 100

    if change_pct < -10:
        score = 100
        detail = f"in calo ({change_pct:+.1f}%): ${avg_prev:.2f}→${avg_recent:.2f}"
    elif change_pct <= 10:
        score = 60
        detail = f"stabile questa settimana ({change_pct:+.1f}%)"
    else:
        score = 20
        detail = f"in aumento ({change_pct:+.1f}%): ${avg_prev:.2f}→${avg_recent:.2f}"

    return {
        "score": score,
        "label": "Trend costo",
        "detail": detail,
        "weight": 0.10,
    }


# ── Runner principale ─────────────────────────────────────────────────────────

def run_skill_assay(project_path: str) -> dict:
    """Calcola il punteggio assay e scrive skill-assay-results.json.

    Ritorna dict con status/detail compatibile con il formato sub-attività drain.
    """
    result = {"name": "skill_assay", "status": "skip", "detail": ""}

    try:
        records = _load_log(project_path)
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"errore lettura coordination-log: {e}"
        return result

    if not records:
        result["detail"] = "coordination-log.jsonl vuoto o non trovato"
        return result

    thresholds = _load_thresholds()

    assertions = {
        "cost_compliance": a1_cost_compliance(records, thresholds),
        "delegation_rate": a2_delegation_rate(records),
        "category_diversity": a3_category_diversity(records),
        "model_efficiency": a4_model_efficiency(records),
        "cost_trend": a5_cost_trend(records),
    }

    # Media pesata
    weighted_sum = sum(a["score"] * a["weight"] for a in assertions.values())
    total_weight = sum(a["weight"] for a in assertions.values())
    score = round(weighted_sum / total_weight) if total_weight > 0 else 0

    if score >= 80:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 40:
        grade = "C"
    else:
        grade = "D"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n_sessions = len(records)

    output = {
        "score": score,
        "grade": grade,
        "updated_at": today,
        "n_sessions": n_sessions,
        "assertions": assertions,
        "grade_scale": {"A": "≥80", "B": "60-79", "C": "40-59", "D": "<40"},
    }

    try:
        RESULTS_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"scrittura skill-assay-results.json fallita: {e}"
        return result

    result["status"] = "ok"
    result["detail"] = f"score={score} ({grade}), {n_sessions} sessioni analizzate"
    return result


# ── Entry point standalone ────────────────────────────────────────────────────

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    r = run_skill_assay(project)
    print(f"[{r['status']}] {r['detail']}")
    if r["status"] == "ok":
        data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
        print(json.dumps(data, indent=2, ensure_ascii=False))
