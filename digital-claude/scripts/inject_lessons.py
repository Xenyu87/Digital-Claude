#!/usr/bin/env python3
"""Fetch lezioni, errori, e decision snapshot per SessionStart.

Output su stdout → iniettato come <system-reminder> tramite hook SessionStart.
Se la dashboard è down o non ci sono dati, stampa niente (silenzioso).

Scopo: la skill usa automaticamente le lezioni passate, decision snapshot, e feedback per evitare errori già visti.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
if not BASE.startswith(("http://", "https://")):
    raise SystemExit(f"SKILL_DASHBOARD_URL schema non valido (deve essere http/https): {BASE}")


def fetch(path: str) -> list[dict]:
    try:
        req = urllib.request.Request(f"{BASE.rstrip('/')}{path}")
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read().decode()).get("rows", [])
    except Exception:
        return []


def rel(iso: str) -> str:
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - t).days
        return f"{days}g fa" if days > 0 else "oggi"
    except Exception:
        return ""


def main() -> None:
    # Solo in repo git con AI_HANDOFF.md (progetti attivi con la skill)
    if not (Path.cwd() / "AI_HANDOFF.md").exists():
        return

    lines: list[str] = []

    # Pillar 1: Decision Snapshot (SessionStart priming)
    try:
        skill_dir = Path(__file__).parent.parent
        snapshot_script = skill_dir / "scripts" / "decision_snapshot_builder.py"
        if snapshot_script.exists():
            result = subprocess.run(
                ["python3", str(snapshot_script)],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.stdout.strip():
                lines.append(result.stdout.strip())
    except Exception:
        pass  # Silenzioso se fallisce

    lessons = fetch("/api/lessons?limit=8")
    errors = fetch("/api/errors?limit=5")

    if lessons:
        lines.append("📚 Lezioni dai task precedenti (evita questi errori):")
        for l in lessons:
            badge = {"spreco": "spreco", "errore": "errore", "pattern": "pattern"}.get(
                l.get("pattern_type", ""), "?"
            )
            times = l.get("occurrences", 1)
            rule = l.get("rule", "").strip()
            promoted = " ✓ in SKILL.md" if l.get("promoted_to") else ""
            times_str = f" ({times}×)" if times > 1 else ""
            lines.append(f"  • [{badge}]{times_str} {rule}{promoted}")

    if errors:
        lines.append("⚠ Errori non risolti da sessioni precedenti:")
        for e in errors:
            when = rel(e.get("created_at", ""))
            lines.append(f"  • {e.get('error_type','?')}: {e.get('message','')[:100]} ({when})")

    if lines:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
