#!/usr/bin/env python3
"""
Difficulty estimation for task routing.
Estimates task complexity on 0-1 scale using keyword-based heuristics.
"""

import re
from typing import Dict, Tuple, List

def estimate_difficulty(brief: str) -> Dict[str, any]:
    """
    Estimates task difficulty from brief text on scale 0-1.

    Scoring:
    - Hard keywords (+0.3): refactor, architecture, migrate, redesign, microservices, oauth
    - Medium keywords (+0.15): add feature, new endpoint, new component, auth
    - Easy keywords (-0.15): fix typo, add button, update text, change color
    - Vagueness penalty (+0.2): words like "migliora", "rendi", "ottimizza" without context
    - Base score: 0.5

    Returns: {score: float, routing: str, reasons: list[str]}
    """

    if not brief:
        return {
            "score": 0.5,
            "routing": "sonnet",
            "reasons": ["empty brief, assuming medium difficulty"],
        }

    brief_lower = brief.lower()
    score = 0.5  # base
    reasons = []

    # Hard keywords (+0.3 each)
    hard_keywords = [
        r'\brefactor\b', r'\barchitecture\b', r'\bmigrat\w*\b',
        r'\bredesign\b', r'\bmicroservice\w*\b', r'\boauth\b',
        r'\brearchitect\b', r'\bdata model\b', r'\bschema\b'
    ]
    hard_count = 0
    for pattern in hard_keywords:
        if re.search(pattern, brief_lower, re.IGNORECASE):
            hard_count += 1

    if hard_count > 0:
        score += hard_count * 0.3
        reasons.append(f"hard keywords detected: {hard_count}")

    # Medium keywords (+0.15 each)
    medium_keywords = [
        r'\badd feature\b', r'\bnew endpoint\b', r'\bnew component\b',
        r'\badd auth\b', r'\bimplement\b', r'\bintegrat\w*\b',
        r'\bapi\b', r'\bdatabase\b'
    ]
    medium_count = 0
    for pattern in medium_keywords:
        if re.search(pattern, brief_lower, re.IGNORECASE):
            medium_count += 1

    if medium_count > 0:
        score += medium_count * 0.15
        reasons.append(f"medium keywords detected: {medium_count}")

    # Easy keywords (-0.15 each, reduce difficulty)
    easy_keywords = [
        r'\bfix typo\b', r'\badd button\b', r'\bupdate text\b',
        r'\bchange color\b', r'\bfix bug\b', r'\bcorrect\b',
        r'\bsmall fix\b'
    ]
    easy_count = 0
    for pattern in easy_keywords:
        if re.search(pattern, brief_lower, re.IGNORECASE):
            easy_count += 1

    if easy_count > 0:
        score -= easy_count * 0.15
        reasons.append(f"easy keywords detected: {easy_count}")

    # Vagueness penalty (+0.2)
    vague_keywords = [
        r'\bmigliora\b', r'\brendi\b', r'\bottimizza\b',
        r'\bpulisci\b', r'\bimprovementX\b', r'\bmigliorare\b'
    ]
    is_vague = False
    for pattern in vague_keywords:
        if re.search(pattern, brief_lower, re.IGNORECASE):
            is_vague = True
            break

    if is_vague and len(brief) < 100:
        score += 0.2
        reasons.append("vague wording without context")

    # Normalize to 0-1
    score = max(0.0, min(1.0, score))

    # Routing decision
    if score < 0.3:
        routing = "haiku"
    elif score < 0.6:
        routing = "sonnet"
    else:
        routing = "opus"

    return {
        "score": round(score, 2),
        "routing": routing,
        "reasons": reasons,
    }

def difficulty_to_model(difficulty_score: float, budget_residui: int = None) -> str:
    """
    Maps difficulty score to model choice.
    Optionally considers budget constraint.

    Args:
        difficulty_score: 0-1, from estimate_difficulty()
        budget_residui: if < 20k, force haiku regardless

    Returns: "haiku" | "sonnet" | "opus"
    """
    # Budget override
    if budget_residui is not None and budget_residui < 20000:
        return "haiku"

    # Difficulty-based
    if difficulty_score < 0.3:
        return "haiku"
    elif difficulty_score < 0.6:
        return "sonnet"
    else:
        return "opus"

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "add button logout",
        "refactor auth architecture and migrate to OAuth",
        "fix typo in README",
        "improve performance of dashboard",
        "add feature X + modify UI + redesign database",
    ]

    for test in test_cases:
        result = estimate_difficulty(test)
        model = difficulty_to_model(result["score"])
        print(f"Brief: '{test}'")
        print(f"  Score: {result['score']} → {model}")
        print(f"  Reasons: {', '.join(result['reasons'])}\n")
