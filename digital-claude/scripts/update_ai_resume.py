#!/usr/bin/env python3
"""Update a compact AI_RESUME.md for cheap new-chat orientation."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path


MAX_STATUS_ITEMS = 18
MAX_COMMITS = 5


def run_git(root: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def git_line(root: Path, args: list[str], fallback: str = "n/d") -> str:
    code, output = run_git(root, args)
    if code != 0 or not output:
        return fallback
    return output.splitlines()[0].strip()


def git_lines(root: Path, args: list[str], limit: int) -> list[str]:
    code, output = run_git(root, args)
    if code != 0 or not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()][:limit]


def read_section(path: Path, heading: str, max_lines: int = 8) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    capture = False
    result: list[str] = []
    for line in lines:
        if line.strip().lower() == heading.lower():
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip():
            result.append(line.rstrip())
        if len(result) >= max_lines:
            break
    return result


def status_summary(root: Path) -> tuple[str, list[str]]:
    lines = git_lines(root, ["status", "--short"], MAX_STATUS_ITEMS + 1)
    if not lines:
        return "clean", []
    visible = lines[:MAX_STATUS_ITEMS]
    if len(lines) > MAX_STATUS_ITEMS:
        visible.append(f"... plus altri elementi non mostrati")
    return f"{len(lines)} elementi modificati/non tracciati", visible


def build_resume(root: Path, goal: str, next_step: str) -> str:
    branch = git_line(root, ["branch", "--show-current"], "non-git")
    last_commit = git_line(root, ["log", "-1", "--oneline"], "nessun commit")
    commits = git_lines(root, ["log", "--oneline", f"-{MAX_COMMITS}"], MAX_COMMITS)
    state, status_items = status_summary(root)
    handoff_state = read_section(root / "AI_HANDOFF.md", "## State", 6)
    handoff_next = read_section(root / "AI_HANDOFF.md", "## Next Step", 4)
    context_pending = read_section(root / "AI_CONTEXT.md", "## Pending Work", 8)
    effective_next = next_step or (handoff_next[0] if handoff_next else "")
    if not effective_next:
        effective_next = "Leggi `AI_CONTEXT.md`, poi apri solo i file collegati alla richiesta utente."
    latest_work = handoff_state or context_pending or ["Nessun handoff recente registrato."]
    status_block = status_items or ["Working tree pulito al momento dell'aggiornamento."]
    commit_block = commits or [last_commit]
    return "\n".join(
        [
            "# AI Resume",
            "",
            f"Last updated: {datetime.now().isoformat(timespec='seconds')}",
            f"Project: {root}",
            "",
            "## Current State",
            "",
            f"- Goal: {goal or 'non specificato'}",
            f"- Branch: {branch}",
            f"- Git state: {state}",
            f"- Last commit: {last_commit}",
            "",
            "## Latest Work",
            "",
            *[f"- {item.lstrip('- ').strip()}" for item in latest_work[:8]],
            "",
            "## Changed Or Untracked Files",
            "",
            *[f"- `{item}`" for item in status_block],
            "",
            "## Recent Commits",
            "",
            *[f"- `{item}`" for item in commit_block],
            "",
            "## Next Step",
            "",
            f"- {effective_next}",
            "",
            "## Read Next Only If Needed",
            "",
            "- `AI_CONTEXT.md` for routing and project docs.",
            "- `AI_HANDOFF.md` only when continuing active work.",
            "- `AI_DECISIONS.md` when architecture, data, auth, deployment, or prior tradeoffs matter.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--goal", default="")
    parser.add_argument("--next", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    content = build_resume(root, args.goal, args.next)
    target = root / "AI_RESUME.md"
    if args.dry_run:
        print(content)
    else:
        target.write_text(content, encoding="utf-8")
        print(f"Wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
