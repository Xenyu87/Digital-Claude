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
DEFAULT_CONFIG = {
    "project_path": "",
    "refresh_seconds": 15,
    "port": 3002,
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
        or (resolved / "cost-aware-app-coordinator" / "SKILL.md").exists()
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
