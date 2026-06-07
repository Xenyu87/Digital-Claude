#!/usr/bin/env python3
"""Dashboard project selection and config helpers."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORTS = ROOT / "reports"
CONFIG = REPORTS / "dashboard-config.json"
SESSION_LIMIT = 80
PROJECTS_DIRS = [Path("/root/Progetti"), Path("/progetti")]
DEFAULT_CONFIG = {
    "project_path": "",
    "refresh_seconds": 15,
    "port": 3002,
    "background_mode": "safe",
}


def load_config(project_override: str | None = None) -> dict[str, object]:
    config = dict(DEFAULT_CONFIG)
    if CONFIG.exists():
        try:
            loaded = json.loads(CONFIG.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update({key: value for key, value in loaded.items() if value not in (None, "")})
        except (OSError, json.JSONDecodeError):
            config["config_warning"] = f"Cannot read {CONFIG}"
    if project_override:
        config["project_path"] = project_override
    return config


def save_config(config: dict[str, object]) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")


def is_project_path(path: Path) -> bool:
    markers = [".git", "package.json", "pyproject.toml", "README.md", "AGENTS.md", "AI_CONTEXT.md"]
    return path.exists() and any((path / marker).exists() for marker in markers)


def is_skill_workspace(path: Path) -> bool:
    resolved = path.resolve()
    return (
        resolved == ROOT.resolve()
        or resolved == REPO.resolve()
        or resolved.name == "Codex-app-coordinator-skill"
        or (resolved / "digital-claude" / "SKILL.md").exists()
    )


def project_row(
    path: Path,
    sessions: int = 0,
    last_seen: str = "",
    source: str = "cartella progetti",
    display_name: str | None = None,
    display_path: Path | None = None,
) -> dict[str, object]:
    resolved = path.resolve()
    shown_path = display_path or resolved
    return {
        "name": display_name or resolved.name,
        "path": str(shown_path),
        "sessions": sessions,
        "last_seen": last_seen,
        "has_ai_context": (resolved / "AI_CONTEXT.md").exists(),
        "has_agents": (resolved / "AGENTS.md").exists(),
        "is_git": (resolved / ".git").exists(),
        "source": source,
    }


def lxc_projects() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for root in PROJECTS_DIRS:
        if not root.exists() or not root.is_dir():
            continue
        try:
            children = sorted(root.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            continue
        for child in children:
            if child.name.startswith("."):
                continue
            try:
                if not child.is_dir():
                    continue
                resolved = child.resolve()
            except OSError:
                continue
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            source = "symlink in /root/Progetti" if child.is_symlink() else "cartella /root/Progetti"
            if is_skill_workspace(resolved):
                source = f"{source}, skill/dashboard"
            rows.append(project_row(resolved, source=source, display_name=child.name, display_path=child))
    return rows


def merge_project_rows(*groups: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for group in groups:
        for item in group:
            path = item.get("path")
            if not path:
                continue
            try:
                key = str(Path(str(path)).resolve())
            except OSError:
                key = str(path)
            existing = merged.get(key)
            if not existing:
                merged[key] = {**item, "path": key}
                continue
            existing["sessions"] = max(int(existing.get("sessions", 0) or 0), int(item.get("sessions", 0) or 0))
            existing["last_seen"] = existing.get("last_seen") or item.get("last_seen", "")
            existing["has_ai_context"] = bool(existing.get("has_ai_context")) or bool(item.get("has_ai_context"))
            existing["has_agents"] = bool(existing.get("has_agents")) or bool(item.get("has_agents"))
            existing["is_git"] = bool(existing.get("is_git")) or bool(item.get("is_git"))
            sources = {str(existing.get("source", "")), str(item.get("source", ""))}
            existing["source"] = ", ".join(sorted(source for source in sources if source))
    return sorted(
        merged.values(),
        key=lambda item: (
            0 if str(item.get("path", "")).startswith("/root/Progetti/") or str(item.get("path", "")).startswith("/progetti/") else 1,
            str(item.get("name", "")).lower(),
        ),
    )


def recent_project_from_logs() -> Path | None:
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.exists():
        return None
    files = sorted(sessions_root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    skill_repo = REPO.resolve()
    for file in files[:SESSION_LIMIT]:
        try:
            with file.open("r", encoding="utf-8") as handle:
                for raw in handle:
                    if '"type":"session_meta"' not in raw and '"type":"turn_context"' not in raw:
                        continue
                    payload = json.loads(raw).get("payload", {})
                    cwd = payload.get("cwd")
                    if not cwd:
                        continue
                    candidate = Path(str(cwd))
                    if is_project_path(candidate) and candidate.resolve() != skill_repo and not is_skill_workspace(candidate):
                        return candidate.resolve()
        except (OSError, json.JSONDecodeError):
            continue
    return None


def project_root(config: dict[str, object]) -> Path:
    if not config.get("project_path"):
        return recent_project_from_logs() or REPO.resolve()
    candidate = Path(str(config.get("project_path") or REPO))
    return candidate.resolve() if candidate.exists() else REPO.resolve()
