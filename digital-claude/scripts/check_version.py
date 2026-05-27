#!/usr/bin/env python3
"""Confronta la versione della skill nel sorgente vs nella copia installata.

Estrae la versione dalla prima riga `## vX.Y.Z` in `references/release-notes.md`.

Trigger consigliato: hook Stop di Claude Code (insieme a propose_lesson.py e log_task.py).

Best-effort: se la dashboard e' giu', stampa avviso ed esce 0. Mai blocca.

Variabili ambiente:
    SKILL_SOURCE_PATH       default: path installato (LXC dev) o c:/Progetti/Claude-Skill-Coordinator (Windows)
    SKILL_INSTALLED_PATH    default: ~/.claude/skills/cost-aware-app-coordinator
    SKILL_DASHBOARD_URL     default: http://localhost:3001
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Aggiungi scripts/ al path per importare helper
sys.path.insert(0, str(Path(__file__).parent))
from buffering_client import post_with_fallback


def detect_source_path() -> Path:
    env = os.environ.get("SKILL_SOURCE_PATH")
    if env:
        return Path(env).expanduser()
    # Linux LXC: la copia installata e' anche la canonica.
    # Windows: clone separato in c:/Progetti/Claude-Skill-Coordinator.
    candidates = [
        Path.home() / ".claude/skills/cost-aware-app-coordinator",
        Path("c:/Progetti/Claude-Skill-Coordinator"),
        Path.home() / "Progetti/Claude-Skill-Coordinator",
        Path.home() / "src/cost-aware-app-coordinator",
    ]
    for p in candidates:
        if (p / "SKILL.md").exists():
            return p
    return candidates[0]


def detect_installed_path() -> Path:
    env = os.environ.get("SKILL_INSTALLED_PATH")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".claude" / "skills" / "cost-aware-app-coordinator"


VERSION_RE = re.compile(r"^##\s+v(\d+)\.(\d+)\.(\d+)\b", re.MULTILINE)


def extract_version(skill_root: Path) -> str:
    """Estrae la versione semver piu' alta da release-notes.md.

    Non usa il primo match: v0.1.0 e' in cima al file per ragioni storiche
    ma non e' la versione corrente. Ordina semver e prende il max.
    """
    notes = skill_root / "references" / "release-notes.md"
    if not notes.exists():
        return "unknown"
    text = notes.read_text(encoding="utf-8", errors="ignore")
    matches = VERSION_RE.findall(text)
    if not matches:
        return "unknown"
    major, minor, patch = max(matches, key=lambda v: (int(v[0]), int(v[1]), int(v[2])))
    return f"v{major}.{minor}.{patch}"


def main() -> int:
    source = detect_source_path()
    installed = detect_installed_path()

    source_version = extract_version(source)
    installed_version = extract_version(installed)

    if source_version == "unknown" and installed_version == "unknown":
        print(f"check_version: nessun release-notes.md trovato in {source} o {installed}. Skip.")
        return 0

    print(f"check_version: sorgente={source_version} installato={installed_version}")
    if source_version != installed_version:
        print(f"  DRIFT: lancia `python3 scripts/sync_skill.py` per allineare.")

    payload = {
        "source_version": source_version,
        "installed_version": installed_version,
    }
    if post_with_fallback("/api/skill-version", payload):
        print(f"check_version: ✓ registrato sulla dashboard centralizzata.")
    else:
        print(f"check_version: ⚠️  offline, dati salvati localmente per invio futuro.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
