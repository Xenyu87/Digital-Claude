#!/usr/bin/env python3
"""Hook Stop: chiama log_coordination.py a chiusura di ogni sessione non banale.

Questo hook viene eseguito da Claude Code come Stop hook globale.
Legge il jsonl di sessione per estrarre token/costo, poi delega a log_coordination.py.

Fail-safe: exit 0 sempre. Nessun blocco dell'agent.

Installazione in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python /root/.claude/skills/cost-aware-app-coordinator/scripts/hooks/coordination_log.py"}
        ]
      }
    ]
  }
}
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _find_latest_session_jsonl(project_path: str) -> Path | None:
    """Trova il jsonl di sessione piu' recente per il progetto."""
    # Claude Code usa slug con leading dash. Non strippare a sinistra.
    slug = re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")
    proj_dir = Path.home() / ".claude" / "projects" / slug
    if not proj_dir.exists():
        return None
    jsonls = sorted(
        proj_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Esclude coordination-log e drain-log
    for j in jsonls:
        if j.name not in ("coordination-log.jsonl", "drain-log.jsonl") and "archive" not in j.name:
            return j
    return None


def _extract_tokens(jsonl_path: Path) -> dict:
    """Aggrega token da un file jsonl di sessione Claude Code."""
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    try:
        for line in jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            usage = entry.get("usage") or entry.get("message", {}).get("usage", {})
            if not usage:
                continue
            tokens["input"]          += usage.get("input_tokens", 0)
            tokens["output"]         += usage.get("output_tokens", 0)
            tokens["cache_read"]     += usage.get("cache_read_input_tokens", 0)
            tokens["cache_creation"] += usage.get("cache_creation_input_tokens", 0)
    except Exception:
        pass
    return tokens


def _estimate_cost(tokens: dict) -> float:
    """Stima costo Sonnet 4.6 (default conservativo)."""
    prices = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_creation": 3.75}
    total = 0.0
    for k, price in prices.items():
        total += tokens.get(k, 0) * price / 1_000_000
    return round(total, 6)


def _detect_category(jsonl_path: Path) -> str:
    """Euristica: legge il primo prompt utente e classifica la categoria."""
    ops_re = re.compile(r"systemd|journalctl|ssh|lxc|porta|servizio|syncthing|deploy|riavvia|cron", re.I)
    audit_re = re.compile(r"rivedi|review|controlla|sicurezza|audit", re.I)
    bug_re = re.compile(r"non funziona|errore|crash|bug|fix|broken", re.I)
    new_app_re = re.compile(r"crea|scaffold|parti da zero|nuova app|nuovo progetto", re.I)
    skill_re = re.compile(r"skill|automiglior|aggiorna la skill", re.I)
    try:
        for line in jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = entry.get("role") or entry.get("message", {}).get("role", "")
            if role != "user":
                continue
            content = str(entry.get("content") or entry.get("message", {}).get("content", ""))
            if ops_re.search(content):
                return "ops"
            if audit_re.search(content):
                return "audit"
            if bug_re.search(content):
                return "bug_rescue"
            if new_app_re.search(content):
                return "nuova_app"
            if skill_re.search(content):
                return "miglioramento_skill"
            # primo prompt trovato, categoria default
            return "modifica"
    except Exception:
        pass
    return "modifica"


def main() -> int:
    try:
        project_path = os.getcwd()
        # Non loggare se siamo nella dir della skill stessa
        skill_marker = Path(project_path) / "SKILL.md"
        if skill_marker.exists():
            return 0

        jsonl_path = _find_latest_session_jsonl(project_path)
        if jsonl_path is None:
            return 0

        tokens = _extract_tokens(jsonl_path)
        # Salta sessioni banali (<1000 token totali)
        total = sum(tokens.values())
        if total < 1000:
            return 0

        cost = _estimate_cost(tokens)
        category = _detect_category(jsonl_path)

        script = Path(__file__).resolve().parent.parent / "log_coordination.py"
        cmd = [
            sys.executable,
            str(script),
            "--project", project_path,
            "--project-name", Path(project_path).name,
            "--category", category,
            "--outcome", "ok",
            "--cost", str(cost),
            "--input-tokens", str(tokens["input"]),
            "--output-tokens", str(tokens["output"]),
            "--cache-read", str(tokens["cache_read"]),
            "--cache-creation", str(tokens["cache_creation"]),
        ]
        subprocess.run(cmd, check=False, timeout=10)

    except Exception as e:
        print(f"coordination_log hook: errore ({e}), skip.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
