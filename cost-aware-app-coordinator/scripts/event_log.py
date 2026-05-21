#!/usr/bin/env python3
"""Append and summarize local skill events."""

from __future__ import annotations

import argparse
import collections
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_LOG = ROOT / "reports" / "skill-events.jsonl"
MAX_EVENT_LINES = 400
DEFAULT_DEDUP_SECONDS = 300


def rotate_events(max_lines: int = MAX_EVENT_LINES) -> None:
    if not EVENT_LOG.exists():
        return
    try:
        lines = EVENT_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    if len(lines) <= max_lines:
        return
    EVENT_LOG.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")


def should_skip_duplicate(event: str, project: str, message: str, dedup_seconds: int) -> bool:
    if dedup_seconds <= 0:
        return False
    recent = read_events(25)
    now = datetime.now()
    for item in recent:
        if item.get("event") != event or item.get("project") != project or item.get("message") != message:
            continue
        try:
            timestamp = datetime.fromisoformat(str(item.get("timestamp", "")))
        except ValueError:
            continue
        if now - timestamp <= timedelta(seconds=dedup_seconds):
            return True
    return False


def emit_event(
    event: str,
    project: str = "",
    severity: str = "info",
    message: str = "",
    data: dict[str, object] | None = None,
    dedup_seconds: int = DEFAULT_DEDUP_SECONDS,
) -> dict[str, object]:
    if should_skip_duplicate(event, project, message, dedup_seconds):
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": event,
            "project": project,
            "severity": severity,
            "message": message,
            "deduplicated": True,
            "data": data or {},
        }
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "project": project,
        "severity": severity,
        "message": message,
        "data": data or {},
    }
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    rotate_events()
    return row


def read_events(limit: int = 50) -> list[dict[str, object]]:
    if not EVENT_LOG.exists():
        return []
    rows: list[dict[str, object]] = []
    with EVENT_LOG.open("r", encoding="utf-8") as handle:
        for raw in handle:
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return rows[-limit:][::-1]


def summarize_events(limit: int = 120) -> dict[str, object]:
    events = read_events(limit)
    by_event = collections.Counter(str(item.get("event", "")) for item in events)
    by_project = collections.Counter(str(item.get("project", "")) for item in events if item.get("project"))
    by_severity = collections.Counter(str(item.get("severity", "")) for item in events)
    return {
        "path": str(EVENT_LOG),
        "events_read": len(events),
        "by_event": [{"name": key, "count": value} for key, value in by_event.most_common(10)],
        "by_project": [{"name": key, "count": value} for key, value in by_project.most_common(10)],
        "by_severity": [{"name": key, "count": value} for key, value in by_severity.most_common()],
        "recent": events[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    emit = sub.add_parser("emit")
    emit.add_argument("event")
    emit.add_argument("--project", default="")
    emit.add_argument("--severity", default="info")
    emit.add_argument("--message", default="")
    emit.add_argument("--data", default="{}")
    emit.add_argument("--dedup-seconds", type=int, default=DEFAULT_DEDUP_SECONDS)
    summary = sub.add_parser("summary")
    summary.add_argument("--limit", type=int, default=120)
    summary.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.cmd == "emit":
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            data = {"raw": args.data}
        print(json.dumps(emit_event(args.event, args.project, args.severity, args.message, data, args.dedup_seconds), indent=2))
    else:
        result = summarize_events(args.limit)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Events read: {result['events_read']}")
            for item in result["by_event"]:
                print(f"- {item['name']}: {item['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
