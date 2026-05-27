#!/usr/bin/env python3
"""Persist active coordinator task checkpoints for safe resume."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_FILE = ROOT / "reports" / "coordinator-task.json"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_task() -> dict[str, object]:
    if not TASK_FILE.exists():
        return {"status": "none", "checkpoints": []}
    try:
        data = json.loads(TASK_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"status": "none", "checkpoints": []}
    except (OSError, json.JSONDecodeError):
        return {"status": "none", "checkpoints": []}


def save_task(data: dict[str, object]) -> None:
    TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASK_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def normalize_list(values: list[str]) -> list[str]:
    result = []
    for value in values:
        for part in str(value).replace(";", "\n").splitlines():
            item = part.strip(" -\t")
            if item:
                result.append(item[:240])
    return result[:24]


def resume_prompt(task: dict[str, object]) -> str:
    checkpoints = [item for item in task.get("checkpoints", []) if isinstance(item, dict)]
    latest = checkpoints[-1] if checkpoints else {}
    changed = task.get("changed_files", []) if isinstance(task.get("changed_files"), list) else []
    return "\n".join(
        [
            "Riprendi questo lavoro senza ricominciare da zero.",
            "",
            f"Goal: {task.get('goal', 'n/d')}",
            f"Project: {task.get('project', 'n/d')}",
            f"Status: {task.get('status', 'active')}",
            "",
            "Fatto:",
            *[f"- {item}" for item in task.get("done", []) if isinstance(task.get("done"), list)],
            "",
            "Prossimo passo:",
            f"- {latest.get('next') or task.get('next_step') or 'Controlla lo stato e continua dal checkpoint piu recente.'}",
            "",
            "Rischi aperti:",
            *[f"- {item}" for item in task.get("risks", []) if isinstance(task.get("risks"), list)],
            "",
            "File cambiati o rilevanti:",
            *[f"- {item}" for item in changed[:18]],
            "",
            "Regola: leggi prima questo checkpoint, poi solo i file necessari. Non rifare lavoro gia indicato come fatto.",
        ]
    )


def start_task(project: str, goal: str, steps: list[str]) -> dict[str, object]:
    task = {
        "status": "active",
        "project": project,
        "goal": goal,
        "created_at": now(),
        "updated_at": now(),
        "planned_steps": normalize_list(steps),
        "done": [],
        "risks": [],
        "changed_files": [],
        "next_step": normalize_list(steps)[0] if normalize_list(steps) else "",
        "checkpoints": [],
    }
    task["resume_prompt"] = resume_prompt(task)
    save_task(task)
    return task


def add_checkpoint(done: list[str], next_step: str, risks: list[str], files: list[str]) -> dict[str, object]:
    task = load_task()
    if task.get("status") in {"none", ""}:
        task["status"] = "active"
        task["created_at"] = now()
    task["updated_at"] = now()
    existing_done = task.get("done", []) if isinstance(task.get("done"), list) else []
    existing_risks = task.get("risks", []) if isinstance(task.get("risks"), list) else []
    existing_files = task.get("changed_files", []) if isinstance(task.get("changed_files"), list) else []
    task["done"] = list(dict.fromkeys([*existing_done, *normalize_list(done)]))[:80]
    task["risks"] = list(dict.fromkeys([*existing_risks, *normalize_list(risks)]))[:40]
    task["changed_files"] = list(dict.fromkeys([*existing_files, *normalize_list(files)]))[:80]
    if next_step:
        task["next_step"] = next_step[:300]
    checkpoints = task.setdefault("checkpoints", [])
    if not isinstance(checkpoints, list):
        task["checkpoints"] = checkpoints = []
    checkpoints.append(
        {
            "timestamp": now(),
            "done": normalize_list(done),
            "next": next_step[:300],
            "risks": normalize_list(risks),
            "files": normalize_list(files),
        }
    )
    task["checkpoints"] = checkpoints[-40:]
    task["resume_prompt"] = resume_prompt(task)
    save_task(task)
    return task


def complete_task(note: str) -> dict[str, object]:
    task = load_task()
    task["status"] = "completed"
    task["completed_at"] = now()
    task["updated_at"] = now()
    if note:
        task["completion_note"] = note[:500]
    task["resume_prompt"] = resume_prompt(task)
    save_task(task)
    return task


def summary() -> dict[str, object]:
    task = load_task()
    return {
        "path": str(TASK_FILE),
        "status": task.get("status", "none"),
        "project": task.get("project", ""),
        "goal": task.get("goal", ""),
        "updated_at": task.get("updated_at", ""),
        "next_step": task.get("next_step", ""),
        "done_count": len(task.get("done", []) if isinstance(task.get("done"), list) else []),
        "risk_count": len(task.get("risks", []) if isinstance(task.get("risks"), list) else []),
        "changed_files": task.get("changed_files", []) if isinstance(task.get("changed_files"), list) else [],
        "resume_prompt": task.get("resume_prompt", resume_prompt(task)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    start = sub.add_parser("start")
    start.add_argument("--project", required=True)
    start.add_argument("--goal", required=True)
    start.add_argument("--step", action="append", default=[])
    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("--done", action="append", default=[])
    checkpoint.add_argument("--next", default="")
    checkpoint.add_argument("--risk", action="append", default=[])
    checkpoint.add_argument("--file", action="append", default=[])
    complete = sub.add_parser("complete")
    complete.add_argument("--note", default="")
    sub.add_parser("summary")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.cmd == "start":
        result = start_task(args.project, args.goal, args.step)
    elif args.cmd == "checkpoint":
        result = add_checkpoint(args.done, getattr(args, "next"), args.risk, args.file)
    elif args.cmd == "complete":
        result = complete_task(args.note)
    else:
        result = summary()
    print(json.dumps(result, indent=2) if args.json else result.get("resume_prompt") or f"Task: {result.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
