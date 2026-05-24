#!/usr/bin/env python3
"""
Budget-aware model routing.
Selects model based on tokens remaining in budget, not just task type.
"""

import os
from typing import Dict, Optional
from difficulty_estimator import difficulty_to_model

def get_tokens_budget() -> tuple:
    """
    Get budget info from environment or coordination-log.

    Returns: (tokens_budget_max, tokens_spent)
    """
    # Try env first
    budget_max = int(os.getenv("TOKENS_BUDGET_MAX", "200000"))
    tokens_spent = int(os.getenv("TOKENS_SPENT", "0"))

    return budget_max, tokens_spent

def get_tokens_residui(budget_max: int = None, tokens_spent: int = None) -> int:
    """Calculate tokens remaining in budget."""
    if budget_max is None or tokens_spent is None:
        budget_max, tokens_spent = get_tokens_budget()

    return max(0, budget_max - tokens_spent)

def suggest_model_by_budget(
    tokens_residui: int,
    difficulty_score: float = 0.5,
    task_type: str = "modifica"
) -> Dict[str, any]:
    """
    Suggests model based on budget constraint + difficulty.

    Priority: **Budget constraint > Difficulty > Task type**

    Args:
        tokens_residui: tokens remaining in budget
        difficulty_score: from difficulty_estimator, 0-1
        task_type: "audit", "modifica", "ops", etc. (fallback only)

    Returns:
        {
            model: "haiku"|"sonnet"|"opus",
            reason: str,
            force: bool,  # True if budget forced the choice
            residui: int,
            burn_rate: float
        }
    """

    reasons = []
    force = False

    # Tier 1: Budget constraint (hard override)
    if tokens_residui < 20000:
        model = "haiku"
        reason = f"budget critical: {tokens_residui} < 20k → force haiku"
        force = True
    elif tokens_residui < 100000:
        # Medium budget: prefer sonnet, but haiku if easy
        if difficulty_score < 0.3:
            model = "haiku"
            reason = f"budget constrained {tokens_residui}/200k, easy task → haiku"
        else:
            model = "sonnet"
            reason = f"budget constrained {tokens_residui}/200k → sonnet (safe mid-tier)"
    else:
        # Plenty of budget: use difficulty + task_type
        model = difficulty_to_model(difficulty_score)
        reason = f"budget adequate {tokens_residui}/200k → {model} (by difficulty {difficulty_score:.2f})"

    burn_rate = 0.0 if tokens_residui == 0 else (1.0 - (tokens_residui / 200000))

    return {
        "model": model,
        "reason": reason,
        "force": force,
        "residui": tokens_residui,
        "burn_rate": round(burn_rate, 2),
    }

def estimate_task_cost(task_type: str = "modifica") -> int:
    """Estimates token cost for a task type (rough)."""
    costs = {
        "ops": 20000,
        "modifica": 50000,
        "bug_rescue": 75000,
        "audit": 100000,
        "nuova_app": 150000,
    }
    return costs.get(task_type, 50000)

def can_afford_task(task_type: str, tokens_residui: int, safety_factor: float = 1.5) -> bool:
    """
    Checks if budget can afford the task.

    Args:
        task_type: category
        tokens_residui: tokens left
        safety_factor: multiply estimate by this (1.5 = 50% buffer)

    Returns: bool
    """
    estimated_cost = estimate_task_cost(task_type) * safety_factor
    return tokens_residui > estimated_cost

if __name__ == "__main__":
    # Test scenarios
    scenarios = [
        (10000, 0.5, "modifica", "emergency mode"),
        (50000, 0.7, "audit", "constrained"),
        (200000, 0.8, "nuova_app", "plenty"),
    ]

    for residui, difficulty, task_type, desc in scenarios:
        os.environ["TOKENS_SPENT"] = str(200000 - residui)
        result = suggest_model_by_budget(residui, difficulty, task_type)
        affordable = can_afford_task(task_type, residui)
        print(f"\n{desc.upper()} (residui={residui})")
        print(f"  Model: {result['model']} (force={result['force']})")
        print(f"  Reason: {result['reason']}")
        print(f"  Affordable: {affordable}")
