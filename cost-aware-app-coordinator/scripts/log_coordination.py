#!/usr/bin/env python3
"""Registra una riga JSONL nel coordination-log del progetto corrente.

Schema: {"ts","task_id","project","category","trigger_keywords","agents_used",
          "models","tokens","cost_usd","duration_s","outcome","files_touched","lesson"}

Uso:
    python scripts/log_coordination.py \\
        --project dashboard-claude-coordinator \\
        --category modifica \\
        --outcome ok \\
        --cost 0.42 \\
        --duration 180 \\
        --files 5

Fail-safe: exit 0 anche su errore. Tutti i log su stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _parse_share(s: str) -> dict[str, float]:
    """Parsa "haiku:0.1,sonnet:0.3,opus:0.6" in dict. Best-effort, fail-safe."""
    out: dict[str, float] = {}
    if not s:
        return out
    for tok in s.split(","):
        if ":" not in tok:
            continue
        k, v = tok.split(":", 1)
        try:
            out[k.strip()] = round(float(v), 4)
        except ValueError:
            continue
    return out


def _proj_slug(project_path: str) -> str:
    """Converte il path progetto nel formato slug usato da Claude Code."""
    import re
    # Claude Code usa slug con leading dash (es. -root-Progetti-foo). Non strippare a sinistra.
    return re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")


def _coordination_log_path(project_path: str) -> Path:
    """Ritorna il path del coordination-log.jsonl per il progetto."""
    slug = _proj_slug(project_path)
    base = Path.home() / ".claude" / "projects" / slug / "memory"
    base.mkdir(parents=True, exist_ok=True)
    return base / "coordination-log.jsonl"


def _append_line(log_path: Path, record: dict) -> None:
    """Append atomico via write+rename per evitare corruzioni."""
    line = json.dumps(record, ensure_ascii=False)
    tmp = log_path.with_suffix(".jsonl.tmp")
    # Leggi contenuto esistente se il file c'è
    existing = ""
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")
    tmp.write_text(existing + line + "\n", encoding="utf-8")
    tmp.replace(log_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Append riga coordination-log.jsonl")
    ap.add_argument("--project", default=os.getcwd(), help="path o slug progetto")
    ap.add_argument("--project-name", default="", help="nome breve del progetto")
    ap.add_argument("--category", default="modifica")
    ap.add_argument("--outcome", default="ok", choices=["ok", "partial", "failed"])
    ap.add_argument("--cost", type=float, default=0.0)
    ap.add_argument("--duration", type=int, default=0)
    ap.add_argument("--files", type=int, default=0)
    ap.add_argument("--agents", default="", help="agenti usati, separati da virgola")
    ap.add_argument("--models", default="", help="modelli usati, separati da virgola")
    ap.add_argument("--models-share", default="", help='share token per famiglia, formato "haiku:0.1,sonnet:0.3,opus:0.6"')
    ap.add_argument("--keywords", default="", help="trigger keywords, separati da virgola")
    ap.add_argument("--input-tokens", type=int, default=0)
    ap.add_argument("--output-tokens", type=int, default=0)
    ap.add_argument("--cache-read", type=int, default=0)
    ap.add_argument("--cache-creation", type=int, default=0)
    ap.add_argument("--lesson", default=None, help="lezione opzionale (no PII)")
    ap.add_argument("--task-id", default=None, help="UUID task (generato se assente)")

    try:
        args = ap.parse_args()
    except SystemExit:
        print("log_coordination: argomenti non validi, skip.", file=sys.stderr)
        return 0

    try:
        project_path = args.project
        project_name = args.project_name or Path(project_path).name

        record = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "task_id": args.task_id or str(uuid.uuid4()),
            "project": project_name,
            "category": args.category,
            "trigger_keywords": [k.strip() for k in args.keywords.split(",") if k.strip()],
            "agents_used": [a.strip() for a in args.agents.split(",") if a.strip()],
            "models": [m.strip() for m in args.models.split(",") if m.strip()],
            "models_share": _parse_share(args.models_share),
            "tokens": {
                "input": args.input_tokens,
                "output": args.output_tokens,
                "cache_read": args.cache_read,
                "cache_creation": args.cache_creation,
            },
            "cost_usd": args.cost,
            "duration_s": args.duration,
            "outcome": args.outcome,
            "files_touched": args.files,
            "lesson": args.lesson,
        }

        log_path = _coordination_log_path(project_path)
        _append_line(log_path, record)
        print(f"log_coordination: registrato in {log_path}", file=sys.stderr)

    except Exception as e:
        print(f"log_coordination: errore ({e}), skip.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
