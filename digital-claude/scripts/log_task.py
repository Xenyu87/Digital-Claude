#!/usr/bin/env python3
"""Invia un log task all'endpoint POST /api/log della skill-dashboard.

Trigger consigliato: hook Stop di Claude Code, dopo `propose_lesson.py`.
La skill chiama questo script a chiusura di un task non banale.

Variabili ambiente:
    SKILL_DASHBOARD_URL    base URL del dashboard (default http://localhost:3001)
    SKILL_VERSION          versione skill (default: leggi da SKILL.md frontmatter)

Uso:
    python scripts/log_task.py \\
        --category modifica \\
        --status ok \\
        --summary "v0.9.0 reflexion loop"

In assenza di rete o dashboard non raggiungibile: stampa avviso, exit 0.
Mai bloccare l'agent perche' il dashboard e' giu'.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CATEGORIES = (
    "nuova_app",
    "modifica",
    "audit",
    "bug_rescue",
    "miglioramento_skill",
)
STATUSES = ("ok", "partial", "failed")


def git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False
        )
        return out.stdout.strip()
    except FileNotFoundError:
        return ""


def files_touched_in_last_commit() -> list[str]:
    out = git("diff", "HEAD~1", "HEAD", "--name-only")
    return [f for f in out.splitlines() if f.strip()]


def detect_skill_version() -> str:
    env = os.environ.get("SKILL_VERSION")
    if env:
        return env
    # cerca SKILL.md nella skill installata o nel CWD
    candidates = [
        Path.home() / ".claude/skills/cost-aware-app-coordinator/SKILL.md",
        Path.cwd() / "SKILL.md",
    ]
    for p in candidates:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        # cerca pattern come 'v0.9.0' nei primi 50 caratteri del frontmatter o sezione "Validator"
        import re
        m = re.search(r"v\d+\.\d+\.\d+", text)
        if m:
            return m.group(0)
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", choices=CATEGORIES, required=True)
    ap.add_argument("--status", choices=STATUSES, default="ok")
    ap.add_argument("--summary", default="")
    ap.add_argument("--duration", type=int, default=0)
    ap.add_argument("--tool-calls", type=int, default=0)
    ap.add_argument("--cost", type=float, default=0.0)
    ap.add_argument("--project", default=os.getcwd())
    args = ap.parse_args()

    base = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    url = base.rstrip("/") + "/api/log"

    payload = {
        "project_path": args.project,
        "category": args.category,
        "files_touched": files_touched_in_last_commit(),
        "duration_seconds": args.duration,
        "tool_calls_count": args.tool_calls,
        "cost_estimate_usd": args.cost,
        "status": args.status,
        "skill_version": detect_skill_version(),
        "summary": args.summary,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = resp.read().decode("utf-8")
            print(f"log_task: registrato ({resp.status}) {body}")
    except urllib.error.URLError as e:
        print(f"log_task: dashboard non raggiungibile a {url} ({e}). Skip.")
    except Exception as e:
        print(f"log_task: errore inatteso ({e}). Skip.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
