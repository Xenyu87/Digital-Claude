#!/usr/bin/env python3
"""
Reflexion loop on failure patterns.
Triggers when 5+ tool errors are detected consecutively.

Important: Reflexion is WRITTEN EXPLICITLY by coordinator, not auto-generated.
Prevents degeneration-of-thought (ArXiv 2512.20845).
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

def detect_failure_pattern(
    tool_errors: List[Dict],
    threshold_count: int = 5,
    threshold_same: int = 3
) -> Tuple[bool, str]:
    """
    Detects failure pattern from tool error history.

    Args:
        tool_errors: list of {timestamp, tool, error_type, result}
        threshold_count: trigger if >= N errors
        threshold_same: trigger if same error type N times in a row

    Returns: (should_trigger: bool, reason: str)
    """

    if not tool_errors:
        return False, ""

    # Check total count
    if len(tool_errors) >= threshold_count:
        return True, f"consecutive_failures:{len(tool_errors)}"

    # Check for same error repeated
    if len(tool_errors) >= 3:
        recent_errors = tool_errors[-threshold_same:]
        error_types = [e.get("error_type", "unknown") for e in recent_errors]
        if len(set(error_types)) == 1 and error_types[0] != "unknown":
            return True, f"repeated_error:{error_types[0]}"

    return False, ""

def write_reflection(
    brief_original: str,
    failed_actions: List[str],
    error_summary: str,
    current_context: str = ""
) -> str:
    """
    Writes structured reflection on what's going wrong.

    NOT auto-generated — coordinator WRITES this explicitly.
    Prevents degeneration of thought.

    Args:
        brief_original: original task brief
        failed_actions: what tried and failed
        error_summary: concatenated error messages
        current_context: what's happening now

    Returns: structured reflection text
    """

    reflection_parts = [
        "[REFLEXION — Failure Analysis]",
        f"\nBrief originale: {brief_original[:100]}...",
        f"\nHo provato:",
        *[f"  - {action}" for action in failed_actions[-3:]],  # last 3 attempts
        f"\nErrori rilevati: {error_summary[:200]}...",
        f"\nCosa non sta funzionando:",
        f"  Il mio approccio attuale non è riuscito perché [COORDINATOR COMPLETA]:",
        f"  └─ [Inserire causa vera, non auto-generate]",
        f"\nProssimo approccio (SCEGLI UNO):",
        f"  1. Cambio strumento/tool (es. uso read() invece di grep)",
        f"  2. Cambio strategia (es. top-down → bottom-up)",
        f"  3. Chiedo aiuto (richiedo verifier agent o specialista)",
        f"  4. Accetto il limite (questo non è fattibile in questa sessione)",
    ]

    return "\n".join(reflection_parts)

def should_activate_reflexion(
    session_tool_errors: int,
    consecutive_same_error: bool = False
) -> bool:
    """
    Simple check: activate if tool errors >= 5 OR same error 3x in a row.
    """
    return session_tool_errors >= 5 or consecutive_same_error

def format_reflexion_output(
    reflection: str,
    coordinator_choice: Optional[str] = None
) -> str:
    """
    Formats reflexion for context injection into next turn.
    """
    output = reflection

    if coordinator_choice:
        output += f"\n\n[COORDINATOR DECISION]\nProssimo step: {coordinator_choice}"

    output += "\n\n[META] Questa reflection entra nel prompt del turno successivo, prima del brief originale."

    return output

if __name__ == "__main__":
    # Test scenario
    failed_actions = [
        "Tried to grep for function X in file Y",
        "Tried to read the API schema",
        "Attempted to run tests"
    ]
    error_summary = "FileNotFoundError: path/to/file not found. FileNotFoundError: path again. Permission denied on read."

    reflection = write_reflection(
        brief_original="Add login button and fix auth flow",
        failed_actions=failed_actions,
        error_summary=error_summary
    )

    output = format_reflexion_output(
        reflection,
        coordinator_choice="Uso code-debugger per investigare il vero path dei file"
    )

    print(output)
