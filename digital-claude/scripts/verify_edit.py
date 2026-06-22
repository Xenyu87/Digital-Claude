#!/usr/bin/env python3
"""PostToolUse hook: validazione statica su Edit/Write.

Riceve il tool_input su stdin (JSON da Claude Code).
Controlla: SKILL.md line count, JSON syntax, Python syntax.
Exit 0 sempre. Output su stdout = messaggio visibile nel contesto.

Install in ~/.claude/settings.json PostToolUse Edit|Write|MultiEdit:
  {"type": "command", "command": "python3 /root/.claude/skills/digital-claude/scripts/verify_edit.py"}
"""
from __future__ import annotations

import json
import py_compile
import sys
import tempfile
from pathlib import Path


SKILL_LINE_LIMIT = 450
WARN_EMOJI = "⚠️"
OK_EMOJI = "✅"


def _check_skill_md(path: Path) -> str | None:
    """Verifica line count SKILL.md."""
    try:
        lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        if lines > SKILL_LINE_LIMIT:
            return f"{WARN_EMOJI} SKILL.md ha {lines} righe (max {SKILL_LINE_LIMIT}). Rimuovere {lines - SKILL_LINE_LIMIT} righe prima del prossimo drain."
    except Exception:
        pass
    return None


def _check_json(path: Path) -> str | None:
    """Verifica JSON syntax."""
    try:
        json.loads(path.read_bytes())
    except json.JSONDecodeError as e:
        return f"{WARN_EMOJI} JSON non valido in {path.name}: {e}"
    except Exception:
        pass
    return None


def _check_python(path: Path, new_content: str | None = None) -> str | None:
    """Verifica Python syntax."""
    try:
        if new_content is not None:
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
                f.write(new_content)
                tmp = f.name
            py_compile.compile(tmp, doraise=True)
        else:
            py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        return f"{WARN_EMOJI} Syntax error Python in {path.name}: {e}"
    except Exception:
        pass
    return None


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
        # Claude Code hook: {"tool_name": "Edit", "tool_input": {...}}
        tool_input = data.get("tool_input") or data.get("input") or {}
        file_path_str = (
            tool_input.get("file_path")
            or tool_input.get("notebook_path")
            or ""
        )
        if not file_path_str:
            return 0

        path = Path(file_path_str)
        new_content: str | None = tool_input.get("new_string") or tool_input.get("content")

        issues: list[str] = []

        name_lower = path.name.lower()

        if name_lower == "skill.md":
            msg = _check_skill_md(path)
            if msg:
                issues.append(msg)

        elif name_lower.endswith(".json") or name_lower.endswith(".jsonl"):
            # Solo se il file esiste già (non un nuovo file Write parziale)
            if path.exists():
                msg = _check_json(path)
                if msg:
                    issues.append(msg)

        elif name_lower.endswith(".py"):
            msg = _check_python(path, new_content=new_content if tool_input.get("content") else None)
            if msg:
                issues.append(msg)

        if issues:
            print("\n".join(issues))

    except Exception as e:
        # Fail-safe: non bloccare mai l'agent
        print(f"verify_edit: errore interno ({e}), skip.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
