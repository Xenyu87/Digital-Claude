#!/usr/bin/env python3
"""Persist compact per-project dashboard memory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEMORY_PATH = ROOT / "reports" / "projects-state.json"


def load_memory() -> dict[str, object]:
    if not MEMORY_PATH.exists():
        return {"projects": {}}
    try:
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"projects": {}}
    except (OSError, json.JSONDecodeError):
        return {"projects": {}}


def save_memory(memory: dict[str, object]) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def update_memory(
    project: Path,
    docs: dict[str, object],
    pr: dict[str, object],
    copilot: dict[str, object],
    agent: dict[str, object],
) -> dict[str, object]:
    memory = load_memory()
    projects = memory.setdefault("projects", {})
    key = str(project.resolve())
    previous = projects.get(key, {}) if isinstance(projects, dict) else {}
    entry = {
        "name": project.name,
        "path": key,
        "first_seen": previous.get("first_seen") or datetime.now().isoformat(timespec="seconds"),
        "last_seen": datetime.now().isoformat(timespec="seconds"),
        "app_type": copilot.get("app_type", ""),
        "stack": copilot.get("stack", []),
        "budget_mode": copilot.get("budget_mode", ""),
        "dominant_areas": copilot.get("dominant_areas", []),
        "context_risks": copilot.get("context_risks", []),
        "large_text_files": copilot.get("large_text_files", [])[:8],
        "context_guardrails": copilot.get("context_guardrails", [])[:8],
        "docs_preset": docs.get("recommended_preset", ""),
        "docs_to_create": docs.get("recommended_create", []),
        "pr_status": pr.get("status", ""),
        "warnings": pr.get("warnings", []),
        "recommended_checks": pr.get("recommended_checks", []),
        "suggested_experts": agent.get("suggested_experts", []),
        "top_domains": agent.get("top_domains", []),
    }
    projects[key] = entry
    memory["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_memory(memory)
    return memory


def table(memory: dict[str, object]) -> list[dict[str, object]]:
    projects = memory.get("projects", {})
    if not isinstance(projects, dict):
        return []
    rows = []
    for item in projects.values():
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "name": item.get("name", ""),
                "app_type": item.get("app_type", ""),
                "budget_mode": item.get("budget_mode", ""),
                "pr_status": item.get("pr_status", ""),
                "warnings": len(item.get("warnings", []) or []),
                "experts": ", ".join(e.get("expert", "") for e in item.get("suggested_experts", [])[:3] if isinstance(e, dict)),
                "last_seen": item.get("last_seen", ""),
                "path": item.get("path", ""),
            }
        )
    return sorted(rows, key=lambda row: str(row["last_seen"]), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    memory = load_memory()
    result = {"path": str(MEMORY_PATH), "updated_at": memory.get("updated_at", ""), "projects": table(memory)}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Project memory: {result['path']}")
        for item in result["projects"]:
            print(f"- {item['name']} | {item['app_type']} | {item['pr_status']} | {item['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
