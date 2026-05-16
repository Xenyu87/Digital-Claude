#!/usr/bin/env python3
"""Recommend next skill/dashboard maintenance steps from local evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from event_log import summarize_events
from expert_feedback import IGNORED_EVENT, USED_EVENT
from project_memory import load_memory, table


ROOT = Path(__file__).resolve().parents[1]


def has_event(summary: dict[str, object], name: str) -> int:
    for item in summary.get("by_event", []):
        if item.get("name") == name:
            return int(item.get("count", 0))
    return 0


def has_context_guardrails(memory: dict[str, object]) -> bool:
    projects = memory.get("projects", {})
    if not isinstance(projects, dict):
        return False
    for item in projects.values():
        if isinstance(item, dict) and item.get("context_guardrails"):
            return True
    return False


def advise() -> dict[str, object]:
    events = summarize_events()
    memory = load_memory()
    projects = table(memory)
    recommendations: list[dict[str, object]] = []
    guardrails_enabled = has_context_guardrails(memory)
    if has_event(events, "large_file_detected") and not guardrails_enabled:
        recommendations.append(
            {
                "priority": "alta",
                "area": "context-cost",
                "title": "Add per-project large-file ignore hints",
                "benefit": "Reduces accidental full reads of known expensive files.",
            }
        )
    elif has_event(events, "large_file_detected"):
        recommendations.append(
            {
                "priority": "media",
                "area": "context-cost",
                "title": "Review per-project context guardrails",
                "benefit": "Keeps expensive-file rules aligned with real project usage.",
            }
        )
    if any(int(project.get("warnings", 0) or 0) for project in projects):
        recommendations.append(
            {
                "priority": "alta",
                "area": "pr-readiness",
                "title": "Turn recurring warnings into focused Action Pack tasks",
                "benefit": "Makes warning resolution faster and less manual.",
            }
        )
    feedback_count = has_event(events, USED_EVENT) + has_event(events, IGNORED_EVENT)
    if has_event(events, "expert_suggested") and not feedback_count:
        recommendations.append(
            {
                "priority": "media",
                "area": "experts",
                "title": "Track accepted vs ignored expert suggestions",
                "benefit": "Improves future expert recommendations with feedback.",
            }
        )
    elif feedback_count:
        recommendations.append(
            {
                "priority": "bassa",
                "area": "experts",
                "title": "Review expert feedback trends",
                "benefit": "Shows which expert profiles are useful enough to keep or expand.",
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "priority": "bassa",
                "area": "maintenance",
                "title": "Keep using the dashboard on real projects",
                "benefit": "More evidence is needed before adding complexity.",
            }
        )
    return {
        "projects_seen": len(projects),
        "events_read": events.get("events_read", 0),
        "top_event": (events.get("by_event", [{}]) or [{}])[0].get("name", ""),
        "recommendations": recommendations[:5],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = advise()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Projects seen: {result['projects_seen']}")
        print(f"Events read: {result['events_read']}")
        for item in result["recommendations"]:
            print(f"- {item['priority']} | {item['area']} | {item['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
