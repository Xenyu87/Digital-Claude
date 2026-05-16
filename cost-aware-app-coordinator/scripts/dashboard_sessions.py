#!/usr/bin/env python3
"""Read local Codex sessions for dashboard analytics."""

from __future__ import annotations

import collections
import json
from pathlib import Path

from dashboard_projects import SESSION_LIMIT, is_project_path, is_skill_workspace


MAX_SESSION_TEXT_CHARS = 120000


def session_confidence(raw_text: str, commands: collections.Counter[str], cwd: str | None) -> tuple[str, str]:
    strong_markers = [
        "# Cost Aware App Coordinator",
        "Tool Output Budget",
        "Budget Modes",
        "Project Context Pattern",
        "External Skill Intake",
    ]
    if any(marker in raw_text for marker in strong_markers):
        return "alta", "skill body o regole specifiche viste nella sessione"
    if any(name in commands for name in ["AI_CONTEXT.md", "AI_HANDOFF.md", "AI_STRUCTURE.md"]):
        return "media", "file contesto progetto usati"
    if "cost-aware-app-coordinator" in raw_text:
        return "bassa", "solo nome/metadata skill rilevati"
    if cwd:
        return "non rilevata", "nessun marker skill"
    return "sconosciuta", "sessione incompleta"


def short_command(command: str) -> str:
    for marker in ["AI_CONTEXT.md", "AI_HANDOFF.md", "AI_STRUCTURE.md", "AI_DECISIONS.md"]:
        if marker in command:
            return marker
    if "rg " in command or command.startswith("rg"):
        return "rg"
    if "Get-Content" in command:
        return "Get-Content"
    if "git " in command:
        return "git"
    if "npm " in command:
        return "npm"
    if "python " in command:
        return "python"
    return command[:80]


def codex_sessions(limit: int = SESSION_LIMIT) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.exists():
        return [], {}, []
    files = sorted(sessions_root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    rows: list[dict[str, object]] = []
    command_totals: collections.Counter[str] = collections.Counter()
    project_totals: collections.Counter[str] = collections.Counter()
    confidence_totals: collections.Counter[str] = collections.Counter()
    project_paths: dict[str, dict[str, object]] = {}
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for path in files:
        cwd = None
        last_usage = None
        model = None
        first_ts = None
        user_messages = 0
        tool_calls = 0
        commands: collections.Counter[str] = collections.Counter()
        raw_parts: list[str] = []
        raw_chars = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                for raw in handle:
                    if raw_chars < MAX_SESSION_TEXT_CHARS:
                        chunk = raw[:2000]
                        raw_parts.append(chunk)
                        raw_chars += len(chunk)
                    if '"type":"session_meta"' in raw or '"type":"turn_context"' in raw:
                        data = json.loads(raw)
                        payload = data.get("payload", {})
                        cwd = payload.get("cwd", cwd)
                        model = payload.get("model", model)
                        first_ts = first_ts or data.get("timestamp")
                    elif '"type":"user_message"' in raw:
                        user_messages += 1
                    elif '"type":"function_call"' in raw:
                        data = json.loads(raw)
                        payload = data.get("payload", {})
                        tool_calls += 1
                        if payload.get("name") == "shell_command":
                            try:
                                args = json.loads(payload.get("arguments") or "{}")
                                command = args.get("command", "")
                            except json.JSONDecodeError:
                                command = payload.get("arguments", "")
                            key = short_command(str(command))
                            commands[key] += 1
                            command_totals[key] += 1
                    elif '"type":"token_count"' in raw:
                        data = json.loads(raw)
                        info = data.get("payload", {}).get("info") or {}
                        if info.get("last_token_usage"):
                            last_usage = info["last_token_usage"]
                            first_ts = first_ts or data.get("timestamp")
        except (OSError, json.JSONDecodeError):
            continue
        if cwd and last_usage:
            raw_text = "\n".join(raw_parts)
            confidence, reason = session_confidence(raw_text, commands, cwd)
            confidence_totals[confidence] += 1
            project = Path(str(cwd)).name
            project_totals[project] += 1
            current_path = Path(str(cwd))
            if is_project_path(current_path) and not is_skill_workspace(current_path):
                key = str(current_path.resolve())
                existing = project_paths.setdefault(
                    key,
                    {
                        "name": current_path.name,
                        "path": key,
                        "sessions": 0,
                        "last_seen": first_ts or "",
                        "has_ai_context": (current_path / "AI_CONTEXT.md").exists(),
                        "has_agents": (current_path / "AGENTS.md").exists(),
                        "is_git": (current_path / ".git").exists(),
                    },
                )
                existing["sessions"] = int(existing["sessions"]) + 1
                existing["last_seen"] = first_ts or existing["last_seen"]
            for key in totals:
                totals[key] += int(last_usage.get(key, 0) or 0)
            rows.append(
                {
                    "timestamp": first_ts,
                    "project": project,
                    "model": model or "",
                    "skill_signal": confidence,
                    "reason": reason,
                    "input_tokens": last_usage.get("input_tokens", 0),
                    "output_tokens": last_usage.get("output_tokens", 0),
                    "total_tokens": last_usage.get("total_tokens", 0),
                    "tool_calls": tool_calls,
                    "top_tools": ", ".join(f"{k} x{v}" for k, v in commands.most_common(3)),
                    "user_messages": user_messages,
                    "session": path.name,
                }
            )
    analytics = {
        "sessions_scanned": len(files),
        "sessions_with_tokens": len(rows),
        "token_totals": totals,
        "top_commands": [{"name": k, "count": v} for k, v in command_totals.most_common(10)],
        "top_projects": [{"name": k, "count": v} for k, v in project_totals.most_common(10)],
        "skill_confidence": [{"name": k, "count": v} for k, v in confidence_totals.most_common()],
    }
    projects = sorted(project_paths.values(), key=lambda item: int(item["sessions"]), reverse=True)[:20]
    return rows[:20], analytics, projects
