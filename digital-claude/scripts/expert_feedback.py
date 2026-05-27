#!/usr/bin/env python3
"""Track lightweight feedback for suggested experts."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from event_log import emit_event, read_events


USED_EVENT = "expert_used"
IGNORED_EVENT = "expert_ignored"


def record_feedback(project: str, expert: str, outcome: str) -> dict[str, object]:
    event = USED_EVENT if outcome == "used" else IGNORED_EVENT
    return emit_event(
        event,
        project,
        "info",
        expert,
        {"expert": expert, "outcome": outcome},
        dedup_seconds=0,
    )


def summarize_feedback(project: str = "", limit: int = 400) -> dict[str, object]:
    rows = read_events(limit)
    used = collections.Counter()
    ignored = collections.Counter()
    last_seen: dict[str, str] = {}
    for item in rows:
        event = str(item.get("event", ""))
        if event not in {USED_EVENT, IGNORED_EVENT}:
            continue
        if project and Path(str(item.get("project", ""))).resolve() != Path(project).resolve():
            continue
        data = item.get("data", {})
        expert = str(data.get("expert") if isinstance(data, dict) else item.get("message", ""))
        if not expert:
            expert = str(item.get("message", ""))
        if not expert:
            continue
        if event == USED_EVENT:
            used[expert] += 1
        else:
            ignored[expert] += 1
        last_seen.setdefault(expert, str(item.get("timestamp", "")))
    experts = sorted(set(used) | set(ignored), key=lambda name: (used[name] - ignored[name], used[name]), reverse=True)
    rows_out = [
        {
            "expert": expert,
            "used": used[expert],
            "ignored": ignored[expert],
            "score": used[expert] - ignored[expert],
            "last_feedback": last_seen.get(expert, ""),
        }
        for expert in experts
    ]
    return {
        "project": project,
        "events_read": len(rows),
        "feedback_events": sum(item["used"] + item["ignored"] for item in rows_out),
        "experts": rows_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    mark = sub.add_parser("mark")
    mark.add_argument("--project", required=True)
    mark.add_argument("--expert", required=True)
    mark.add_argument("--outcome", choices=["used", "ignored"], required=True)
    summary = sub.add_parser("summary")
    summary.add_argument("--project", default="")
    summary.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.cmd == "mark":
        print(json.dumps(record_feedback(args.project, args.expert, args.outcome), indent=2))
        return 0
    result = summarize_feedback(args.project if args.cmd == "summary" else "")
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Feedback events: {result['feedback_events']}")
        for item in result["experts"]:
            print(f"- {item['expert']}: used={item['used']} ignored={item['ignored']} score={item['score']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
