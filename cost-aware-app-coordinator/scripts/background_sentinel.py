#!/usr/bin/env python3
"""Safe background sentinel state for the dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STATUS_FILE = REPORTS / "background-status.json"
FINDINGS_FILE = REPORTS / "background-findings.json"
MODES = {"manual", "safe", "assist"}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_json(path: Path, fallback: dict[str, object]) -> dict[str, object]:
    if not path.exists():
        return dict(fallback)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else dict(fallback)
    except (OSError, json.JSONDecodeError):
        return dict(fallback)


def save_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def finding_key(item: dict[str, object]) -> str:
    return "|".join(
        [
            str(item.get("id") or ""),
            str(item.get("problem") or item.get("status") or ""),
            str(item.get("title") or ""),
        ]
    )


def current_findings(blueprint_summary: dict[str, object]) -> list[dict[str, object]]:
    doctor = blueprint_summary.get("doctor", {}) if isinstance(blueprint_summary.get("doctor"), dict) else {}
    audit = doctor.get("audit", {}) if isinstance(doctor.get("audit"), dict) else {}
    flows = doctor.get("flows", {}) if isinstance(doctor.get("flows"), dict) else {}
    findings: list[dict[str, object]] = []
    for item in audit.get("problems", []) if isinstance(audit.get("problems"), list) else []:
        if not isinstance(item, dict):
            continue
        findings.append(
            {
                "kind": "node",
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "status": item.get("status", ""),
                "problem": item.get("problem", ""),
                "reason": item.get("reason", ""),
                "fix": item.get("fix", ""),
                "evidence": item.get("evidence", ""),
            }
        )
    for item in flows.get("items", []) if isinstance(flows.get("items"), list) else []:
        if not isinstance(item, dict) or item.get("status") == "completo":
            continue
        findings.append(
            {
                "kind": "flow",
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "status": item.get("status", ""),
                "problem": item.get("problem", ""),
                "reason": item.get("chain", ""),
                "fix": item.get("next_step", ""),
                "evidence": item.get("start", ""),
            }
        )
    return findings[:80]


def update_sentinel(project: str, mode: str, blueprint_summary: dict[str, object], refresh_seconds: int) -> dict[str, object]:
    mode = mode if mode in MODES else "safe"
    previous = load_json(FINDINGS_FILE, {"findings": []})
    previous_items = [item for item in previous.get("findings", []) if isinstance(item, dict)]
    previous_by_key = {finding_key(item): item for item in previous_items}
    findings = current_findings(blueprint_summary)
    current_by_key = {finding_key(item): item for item in findings}
    new_items = [item for key, item in current_by_key.items() if key not in previous_by_key]
    resolved_items = [item for key, item in previous_by_key.items() if key not in current_by_key]

    status = {
        "mode": mode,
        "mode_label": {
            "manual": "Manuale",
            "safe": "Automatico sicuro",
            "assist": "Proposte assistite",
        }.get(mode, mode),
        "project": project,
        "last_scan_at": now(),
        "next_scan_hint": "solo quando clicchi" if mode == "manual" else f"circa ogni {refresh_seconds} secondi mentre il servizio e' attivo",
        "active": mode in {"safe", "assist"},
        "safe_write_scope": "reports e metadata dashboard; non modifica codice app o SKILL.md",
        "findings_count": len(findings),
        "new_count": len(new_items),
        "resolved_count": len(resolved_items),
        "top_findings": findings[:12],
        "new_findings": new_items[:12],
        "resolved_findings": resolved_items[:12],
    }
    save_json(FINDINGS_FILE, {"project": project, "updated_at": status["last_scan_at"], "findings": findings})
    save_json(STATUS_FILE, status)
    return status


def load_status() -> dict[str, object]:
    return load_json(STATUS_FILE, {"mode": "safe", "active": False, "findings_count": 0, "new_count": 0, "resolved_count": 0})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = load_status()
    print(json.dumps(result, indent=2) if args.json or args.status else f"Background Sentinel: {result.get('mode', 'safe')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
