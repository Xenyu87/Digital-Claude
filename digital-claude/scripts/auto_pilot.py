#!/usr/bin/env python3
"""Choose the simplest automatic next step from dashboard evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def first_expert(agent: dict[str, object]) -> str:
    experts = agent.get("suggested_experts", [])
    if isinstance(experts, list) and experts and isinstance(experts[0], dict):
        return str(experts[0].get("expert", "Context optimizer"))
    return "Context optimizer"


def decide(
    project: str,
    docs: dict[str, object],
    pr: dict[str, object],
    copilot: dict[str, object],
    agent: dict[str, object],
    maintenance: dict[str, object],
) -> dict[str, object]:
    warnings = pr.get("warnings", []) if isinstance(pr.get("warnings", []), list) else []
    docs_to_create = docs.get("recommended_create", []) if isinstance(docs.get("recommended_create", []), list) else []
    guardrails = copilot.get("context_guardrails", []) if isinstance(copilot.get("context_guardrails", []), list) else []
    recommendations = (
        maintenance.get("recommendations", []) if isinstance(maintenance.get("recommendations", []), list) else []
    )
    expert = first_expert(agent)
    mode = str(copilot.get("budget_mode") or "Economico")
    app_type = str(copilot.get("app_type", ""))
    areas = copilot.get("dominant_areas", []) if isinstance(copilot.get("dominant_areas", []), list) else []
    if docs_to_create:
        planning_mode = "Superplan"
    elif len(areas) >= 4 or "full-stack" in app_type.lower():
        planning_mode = "Piano focalizzato"
    else:
        planning_mode = "Diretto"

    if warnings:
        action = "Sistema prima i warning del progetto"
        reason = "Ci sono segnali che possono sporcare commit, PR o test. Risolverli ora evita lavoro doppio dopo."
        prompt_key = "review"
    elif docs_to_create:
        action = "Completa il contesto AI minimo"
        reason = "Mancano file di routing o contesto: crearli riduce letture inutili nelle prossime chat."
        prompt_key = "analysis"
    elif guardrails:
        action = "Lavora con Analisi Economica e guardrail attivi"
        reason = "Il progetto contiene file costosi: la skill usera rg e sezioni mirate come default."
        prompt_key = "analysis"
    elif recommendations:
        action = str(recommendations[0].get("title", "Segui il primo consiglio dell'advisor"))
        reason = str(recommendations[0].get("benefit", "E il miglior prossimo passo secondo i log locali."))
        prompt_key = "analysis"
    else:
        action = "Procedi con una vertical slice piccola"
        reason = "Non emergono blocchi forti: conviene fare una modifica completa ma stretta e testarla subito."
        prompt_key = "frontend" if "frontend" in str(copilot.get("app_type", "")).lower() else "backend"

    return {
        "auto_enabled": True,
        "project": project,
        "mode": mode,
        "planning_mode": planning_mode,
        "primary_expert": expert,
        "next_action": action,
        "why": reason,
        "prompt_key": prompt_key,
        "manual_override": "Puoi cambiare progetto o segnare feedback esperti, ma la scelta di default resta automatica.",
        "signals": [
            f"warning: {len(warnings)}",
            f"docs_da_creare: {len(docs_to_create)}",
            f"guardrail: {len(guardrails)}",
            f"advisor: {len(recommendations)}",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = decide(args.project, {}, {}, {}, {}, {})
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Auto: {result['next_action']}")
        print(f"Why: {result['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
