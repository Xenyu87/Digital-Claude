#!/usr/bin/env python3
"""Track dashboard-guided learning signals for the skill."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from event_log import emit_event, read_events


LEARNING_EVENTS = {
    "learning_unknown",
    "learning_feedback",
    "scanner_uncertain_edge",
    "scanner_gap",
    "scanner_extra_code",
    "lesson_proposed",
    "lesson_confirmed",
}

OUTCOME_LABELS = {
    "confusing": "Non e' chiaro per un utente non tecnico.",
    "wrong": "Sembra sbagliato o non affidabile.",
    "useful": "Utile e comprensibile.",
    "ignore": "Da ignorare per ora.",
    "confirm_edge": "Collegamento confermato dall'utente.",
    "ignore_edge": "Collegamento ignorato come falso positivo.",
}


def record_learning(project: str, item_id: str, outcome: str, note: str = "", area: str = "blueprint-board") -> dict[str, object]:
    label = OUTCOME_LABELS.get(outcome, outcome)
    return emit_event(
        "learning_feedback",
        project,
        "warning" if outcome in {"confusing", "wrong", "ignore_edge"} else "info",
        f"{item_id}: {label}",
        {"area": area, "item_id": item_id, "outcome": outcome, "note": note, "fix_status": "open"},
        dedup_seconds=0,
    )


def summarize_learning(project: str = "", limit: int = 500) -> dict[str, object]:
    rows = []
    for item in read_events(limit):
        if str(item.get("event", "")) not in LEARNING_EVENTS:
            continue
        if project and Path(str(item.get("project", ""))).resolve() != Path(project).resolve():
            continue
        rows.append(item)

    by_event = collections.Counter(str(item.get("event", "")) for item in rows)
    by_outcome = collections.Counter()
    open_items = []
    lessons = []
    for item in rows:
        data = item.get("data", {}) if isinstance(item.get("data"), dict) else {}
        outcome = str(data.get("outcome", ""))
        if outcome:
            by_outcome[outcome] += 1
        if str(data.get("fix_status", "open")) == "open":
            open_items.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "event": item.get("event", ""),
                    "severity": item.get("severity", ""),
                    "item_id": data.get("item_id", ""),
                    "summary": item.get("message", ""),
                    "simple_action": simple_action(str(item.get("event", "")), outcome),
                }
            )
        if str(item.get("event", "")) in {"lesson_proposed", "lesson_confirmed"}:
            lessons.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "status": str(item.get("event", "")).replace("lesson_", ""),
                    "lesson": item.get("message", ""),
                }
            )
    return {
        "project": project,
        "events_read": len(rows),
        "open_count": len(open_items),
        "by_event": [{"name": key, "count": value} for key, value in by_event.most_common()],
        "by_outcome": [{"name": key, "count": value} for key, value in by_outcome.most_common()],
        "open_items": open_items[:12],
        "lessons": lessons[:8],
    }


def simple_action(event: str, outcome: str) -> str:
    if outcome == "confusing":
        return "Chiedi alla skill di riscriverlo in parole semplici."
    if outcome == "wrong":
        return "Chiedi alla skill di cercare evidenza prima di fidarsi."
    if event == "scanner_uncertain_edge":
        return "Lascia come suggerimento finche non c'e' una prova."
    if event == "scanner_gap":
        return "Decidi se manca davvero codice o se il design va corretto."
    if event == "scanner_extra_code":
        return "Valuta se e' codice utile non ancora previsto dal design."
    return "Rivedi quando lavori su questa parte."


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    mark = sub.add_parser("mark")
    mark.add_argument("--project", required=True)
    mark.add_argument("--item-id", required=True)
    mark.add_argument("--outcome", choices=sorted(OUTCOME_LABELS), required=True)
    mark.add_argument("--note", default="")
    summary = sub.add_parser("summary")
    summary.add_argument("--project", default="")
    summary.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.cmd == "mark":
        print(json.dumps(record_learning(args.project, args.item_id, args.outcome, args.note), indent=2))
        return 0
    result = summarize_learning(args.project if args.cmd == "summary" else "")
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Learning events: {result['events_read']}")
        print(f"Open: {result['open_count']}")
        for item in result["open_items"]:
            print(f"- {item['summary']}: {item['simple_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
