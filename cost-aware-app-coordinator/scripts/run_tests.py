#!/usr/bin/env python3
"""Lancia validator + pytest in un comando solo.

Uso:
    python scripts/run_tests.py

Exit code 0 se tutto verde; non-zero se anche solo uno fallisce.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], label: str) -> int:
    print(f"\n=== {label} ===")
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main() -> int:
    rc_validate = run(["python", "scripts/validate_skill.py"], "validate_skill")
    rc_pytest = run(["python", "-m", "pytest", "-v", "--tb=short"], "pytest")

    print()
    print("=" * 50)
    if rc_validate == 0 and rc_pytest == 0:
        print("Risultato finale: tutto verde [OK]")
        return 0
    print("Risultato finale: qualche test fallito [FAIL]")
    print(f"  validate_skill: {'ok' if rc_validate == 0 else 'FAIL'}")
    print(f"  pytest:         {'ok' if rc_pytest == 0 else 'FAIL'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
