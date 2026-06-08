#!/usr/bin/env python3
"""
Budget Guard: spawna claude con hard-cap finanziario nativo + guardie secondarie.

Tripla difesa contro loop infiniti:
  1. --max-budget-usd   → hard kill nativo della CLI al superamento del budget
  2. --max-turns        → limite turni (nessuno spawn lo passava in precedenza)
  3. timeout wall-clock → fallback estremo

LIMITE DICHIARATO: funziona solo per subprocess spawnati dalla skill.
La sessione interattiva del main agent non è uccidibile da qui;
quella è protetta da budget_aware_router.py (forza haiku sotto 20k token residui).

Uso da codice:
    from budget_guard import run_guarded
    result = run_guarded("fai X", model="haiku", budget_cents=10)
    if result["killed"]:
        notify_breach("nome_task", 10, result["cost_usd"], result["reason"])

Uso CLI (test/dry-run):
    python3 budget_guard.py --prompt "ciao" --model haiku --budget-cents 1 --dry-run
    python3 budget_guard.py --prompt "dimmi il meteo" --model haiku --budget-cents 50
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Prezzi USD/Mtok — allineati a coordination_log.py (aggiornare entrambi se cambiano).
_PRICING = {
    "haiku":  {"input": 0.80, "output":  4.00, "cache_read": 0.08, "cache_creation": 1.00},
    "sonnet": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_creation": 3.75},
    "opus":   {"input": 15.0, "output": 75.00, "cache_read": 1.50, "cache_creation": 18.75},
}


def _family(model: str) -> str:
    m = (model or "").lower()
    if "haiku" in m: return "haiku"
    if "opus"  in m: return "opus"
    return "sonnet"


def _tokens_to_usd(usage: dict, model: str) -> float:
    p = _PRICING[_family(model)]
    return round(
        (usage.get("input_tokens", 0) * p["input"] +
         usage.get("output_tokens", 0) * p["output"] +
         usage.get("cache_read_input_tokens", 0) * p["cache_read"] +
         usage.get("cache_creation_input_tokens", 0) * p["cache_creation"]) / 1_000_000, 6
    )


def run_guarded(
    prompt: str,
    model: str = "haiku",
    budget_cents: int = 15,
    max_turns: int = 8,
    cwd: str | None = None,
    timeout: int = 180,
    dry_run: bool = False,
) -> dict:
    """Spawna claude con budget nativo + guardie secondarie.

    Ritorna dict:
        text       : output dell'agente
        killed     : True se terminato prima del completamento
        reason     : 'ok' | 'budget' | 'timeout' | 'turns' | 'error_N'
        cost_usd   : costo stimato (float se disponibile nell'output JSON, altrimenti None)
        exit_code  : return code del processo
    """
    if dry_run:
        return {
            "text": f"[DRY RUN] budget={budget_cents}¢ model={model} max_turns={max_turns}",
            "killed": False, "reason": "ok", "cost_usd": 0.0, "exit_code": 0,
        }

    budget_usd = round(budget_cents / 100.0, 4)
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--permission-mode", "default",
        "--model", model,
        "--max-turns", str(max_turns),
        "--max-budget-usd", str(budget_usd),
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"text": "", "killed": True, "reason": "timeout", "cost_usd": None, "exit_code": -1}
    except Exception as e:
        return {"text": "", "killed": True, "reason": f"error: {e}", "cost_usd": None, "exit_code": -2}

    raw = result.stdout.strip()
    text = raw
    cost_usd = None

    # Parsa JSON output (include total_cost_usd / usage quando disponibile)
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            text = data.get("result", raw)
            cost_usd = data.get("total_cost_usd") or data.get("cost_usd")
            if cost_usd is None and data.get("usage"):
                cost_usd = _tokens_to_usd(data["usage"], model)
        except Exception:
            pass

    killed = result.returncode != 0
    reason = "ok"
    if killed:
        combined = (result.stderr + raw).lower()
        if any(kw in combined for kw in ("budget", "cost limit", "max-budget", "spending limit")):
            reason = "budget"
        elif any(kw in combined for kw in ("max turns", "max-turns", "turn limit")):
            reason = "turns"
        else:
            reason = f"exit_{result.returncode}"

    return {
        "text": text,
        "killed": killed,
        "reason": reason,
        "cost_usd": cost_usd,
        "exit_code": result.returncode,
    }


def notify_breach(task_name: str, budget_cents: int, cost_usd: float | None, reason: str) -> None:
    """Notifica il breach: log locale + best-effort POST alla dashboard."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "circuit_breaker",
        "task": task_name,
        "budget_cents": budget_cents,
        "cost_usd": cost_usd,
        "reason": reason,
    }

    # Log locale in reports/circuit-breaker.jsonl (sempre disponibile, anche offline)
    skill_dir = Path(__file__).parent.parent
    log_path = skill_dir / "reports" / "circuit-breaker.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # POST dashboard via buffering_client (degrade offline automatico)
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from buffering_client import post_with_fallback  # type: ignore
        post_with_fallback("/api/skill-feedback", {
            "kind": "efficacy_alert",
            "title": f"⚡ Circuit breaker: {task_name}",
            "detail": f"Budget {budget_cents}¢ esaurito. Motivo: {reason}. Costo stimato: {cost_usd}$",
            "source": "budget_guard",
        })
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Budget Guard — test CLI")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--budget-cents", type=int, default=15)
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_guarded(
        args.prompt,
        model=args.model,
        budget_cents=args.budget_cents,
        max_turns=args.max_turns,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    icon = "⚡ KILLATO" if result["killed"] else "✅ Completato"
    print(f"\n{icon} — motivo: {result['reason']}")
    print(f"Exit code : {result['exit_code']}")
    print(f"Cost      : {result['cost_usd']}$")
    print(f"\nOutput:\n{str(result['text'])[:500]}")
    sys.exit(1 if result["killed"] else 0)


if __name__ == "__main__":
    main()
