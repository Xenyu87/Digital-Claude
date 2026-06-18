#!/usr/bin/env python3
"""Estrae decisioni critiche da MEMORY.md e le formatta per SessionStart priming.

Legge:
- ~/Progetti/<project>/memory/MEMORY.md (indice)
- ~/Progetti/<project>/memory/*.md (decision/feedback/project/reference file)

Genera snapshot JSON:
- last_decisions: ultime N decisioni durevoli (topic + content)
- recurring_patterns: pattern ripetuti rilevati
- critical_feedback: feedback da applicare al task corrente

Output: stringa formattata per system-reminder iniettata da inject_lessons.py.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import re


def find_memory_dir() -> Path | None:
    """Ricerca MEMORY.md: prima in ~/.claude/projects/<slug>/memory/ (Claude Code standard), poi in <cwd>/memory/."""
    cwd = Path.cwd()
    # Path canonico Claude Code: ~/.claude/projects/<slug>/memory/
    slug = re.sub(r"[^a-zA-Z0-9]", "-", str(cwd)).rstrip("-")
    claude_mem = Path.home() / ".claude" / "projects" / slug / "memory" / "MEMORY.md"
    if claude_mem.exists():
        return claude_mem.parent
    # Fallback legacy: <cwd>/memory/ o <cwd.parent>/memory/
    for attempt in [cwd, cwd.parent]:
        mem_path = attempt / "memory" / "MEMORY.md"
        if mem_path.exists():
            return mem_path.parent
    return None


def parse_memory_index(memory_dir: Path) -> dict[str, str]:
    """Estrae link da MEMORY.md (formato: - [Title](file.md) — description)."""
    index_file = memory_dir / "MEMORY.md"
    if not index_file.exists():
        return {}

    links = {}
    for line in index_file.read_text().splitlines():
        match = re.match(r"- \[([^\]]+)\]\(([^)]+)\)", line)
        if match:
            title, file = match.groups()
            links[file.strip()] = title
    return links


def extract_decisions(memory_dir: Path) -> list[dict]:
    """Estrae decisioni critiche da decision_*.md e feedback_*.md."""
    decisions = []

    for mem_file in sorted(memory_dir.glob("decision_*.md")):
        content = mem_file.read_text().strip()
        # Estrai il corpo (skip frontmatter YAML)
        if "---" in content:
            _, _, body = content.split("---", 2)
            content = body.strip()

        # Prima riga = titolo decisione
        title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if title:
            decisions.append({
                "type": "decision",
                "title": title,
                "file": mem_file.name,
                "mtime": datetime.fromtimestamp(mem_file.stat().st_mtime).isoformat()
            })

    for mem_file in sorted(memory_dir.glob("feedback_*.md")):
        content = mem_file.read_text().strip()
        if "---" in content:
            _, _, body = content.split("---", 2)
            content = body.strip()

        title = next((line.strip() for line in content.splitlines() if line.strip()), "")
        if title:
            decisions.append({
                "type": "feedback",
                "title": title,
                "file": mem_file.name,
                "mtime": datetime.fromtimestamp(mem_file.stat().st_mtime).isoformat()
            })

    # Ordina per data decrescente, prendi ultime 5
    decisions.sort(key=lambda x: x["mtime"], reverse=True)
    return decisions[:5]


def extract_patterns(memory_dir: Path) -> list[str]:
    """Estrae pattern ricorrenti dalle memory files."""
    patterns = []

    # Keyword che indicano pattern important
    keywords = [
        "quando non", "evita", "non fare", "regola di", "anti-pattern",
        "always", "never", "trigger quando"
    ]

    for mem_file in memory_dir.glob("*.md"):
        if mem_file.name == "MEMORY.md":
            continue

        content = mem_file.read_text().lower()
        for keyword in keywords:
            if keyword in content:
                # Estrai la riga con il keyword
                for line in content.splitlines():
                    if keyword in line and len(line) > 20:
                        patterns.append(line.strip()[:100])
                        break

    return list(set(patterns))[:3]  # Dedup, prendi top 3


def format_snapshot(decisions: list[dict], patterns: list[str]) -> str:
    """Formatta snapshot per output system-reminder."""
    lines = ["📌 Decision Snapshot (session priming):"]

    if decisions:
        lines.append("  Decisioni critiche da ricordare:")
        for d in decisions:
            lines.append(f"    • [{d['type']}] {d['title']}")

    if patterns:
        lines.append("  Pattern ricorrenti:")
        for p in patterns:
            lines.append(f"    • {p}")

    if not decisions and not patterns:
        return ""

    return "\n".join(lines)


def main() -> None:
    memory_dir = find_memory_dir()
    if not memory_dir:
        return  # Silenzioso se non in progetto con memoria

    decisions = extract_decisions(memory_dir)
    patterns = extract_patterns(memory_dir)

    snapshot = format_snapshot(decisions, patterns)
    if snapshot:
        print(snapshot)


if __name__ == "__main__":
    main()
