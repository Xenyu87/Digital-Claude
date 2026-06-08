#!/usr/bin/env python3
"""
Validate Patch: esegue gate deterministici su un worktree isolato prima del merge.

Rileva automaticamente il tipo di progetto ed esegue i gate appropriati:
  - TypeScript/Next.js: tsc --noEmit + lint + build (se presente)
  - Python con run_tests.py: pytest runner locale
  - Skill (SKILL.md + validate_skill.py): validator della skill

Uso (da coordinator o manuale):
    python3 validate_patch.py /path/al/worktree
    python3 validate_patch.py /path/al/worktree --json-only   # solo JSON, no stdout verbose

Ritorna JSON su stdout:
    {"passed": bool, "gates": [{"gate": str, "ok": bool, "output": str}]}

Exit code: 0 se passed=True, 1 altrimenti.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: str, timeout: int = 300) -> tuple[int, str]:
    """Esegue un comando e ritorna (returncode, tail degli errori)."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        combined = (r.stdout + r.stderr).strip()
        # Ritorna solo la coda (ultime 4000 char) per non saturare il contesto nel retry
        return r.returncode, combined[-4000:] if combined else ""
    except subprocess.TimeoutExpired:
        return 1, f"timeout dopo {timeout}s"
    except FileNotFoundError as e:
        return 1, f"comando non trovato: {e}"


def validate(worktree: str, verbose: bool = True) -> dict:
    """Rileva i gate applicabili ed eseguili. Ritorna il risultato strutturato."""
    wt = Path(worktree)
    gates: list[tuple[str, list[str]]] = []

    if (wt / "package.json").exists():
        if (wt / "tsconfig.json").exists():
            gates.append(("tsc", ["npx", "--no-install", "tsc", "--noEmit"]))
        # lint solo se c'è una config ESLint esplicita (evita next lint interattivo)
        has_eslint = any(
            (wt / f).exists() for f in
            (".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json",
             ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js", "eslint.config.mjs")
        )
        if has_eslint:
            gates.append(("lint", ["npm", "run", "--if-present", "lint"]))
        if (wt / ".next").exists() or (wt / "next.config.ts").exists() or (wt / "next.config.js").exists():
            gates.append(("build", ["npm", "run", "--if-present", "build"]))

    if (wt / "scripts" / "run_tests.py").exists():
        gates.append(("pytest", ["python", "scripts/run_tests.py"]))

    if (wt / "SKILL.md").exists() and (wt / "scripts" / "validate_skill.py").exists():
        gates.append(("validate_skill", ["python", "scripts/validate_skill.py"]))

    if not gates:
        return {"passed": True, "gates": [], "note": "nessun gate rilevato per questo progetto"}

    results = []
    for name, cmd in gates:
        if verbose:
            print(f"  → {name}: {' '.join(cmd[:3])}...", flush=True)
        code, out = _run(cmd, str(wt))
        ok = (code == 0)
        results.append({"gate": name, "ok": ok, "output": out if not ok else ""})
        if verbose:
            icon = "✅" if ok else "❌"
            print(f"    {icon} {name} (exit {code})")
            if not ok and out:
                # Mostra solo le ultime 10 righe per non sommergere il log
                tail = "\n".join(out.splitlines()[-10:])
                print(f"    Errore:\n{tail}")

    passed = all(r["ok"] for r in results)
    return {"passed": passed, "gates": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Patch — gate deterministici su worktree")
    parser.add_argument("worktree", help="Path del git worktree da validare")
    parser.add_argument("--json-only", action="store_true", help="Output solo JSON su stdout, niente verbose")
    args = parser.parse_args()

    wt = Path(args.worktree)
    if not wt.exists():
        print(json.dumps({"passed": False, "gates": [], "error": f"path non trovato: {wt}"}))
        sys.exit(1)

    verbose = not args.json_only
    if verbose:
        print(f"\n🔍 Validazione worktree: {wt}")

    result = validate(str(wt), verbose=verbose)

    if args.json_only:
        print(json.dumps(result, ensure_ascii=False))
    else:
        icon = "✅ PASSA" if result["passed"] else "❌ FALLISCE"
        gates_ok = sum(1 for g in result["gates"] if g["ok"])
        gates_total = len(result["gates"])
        print(f"\n{icon} — {gates_ok}/{gates_total} gate superati")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
