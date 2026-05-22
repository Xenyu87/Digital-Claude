#!/usr/bin/env python3
"""Runner per pipeline YAML di subagent con DAG delle dipendenze.

Uso:
    python scripts/run_pipeline.py \\
        --pipeline recipes/pipelines/feature-with-tests.yml \\
        --var brief="aggiungi colonna email alla tabella users"

Il runner:
1. Parsa il YAML
2. Costruisce il DAG (toposort)
3. Spawna ogni step via claude CLI rispettando le dipendenze
4. Passa output degli step precedenti come template nel prompt
5. Logga ogni step in coordination-log.jsonl

Fail-safe: exit 0 anche su errore singolo step (lo marca come failed).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("run_pipeline: yaml non installato. Installa con: pip install pyyaml", file=sys.stderr)
    sys.exit(0)

SKILL_DIR = Path(__file__).resolve().parent.parent


# ── Template engine minimale ───────────────────────────────────────────────────

def _apply_filter(value: str, filter_name: str) -> str:
    """Applica un filtro semplice al valore."""
    if filter_name == "files_list":
        # Estrae path da testo libero (righe che sembrano path)
        lines = [l.strip() for l in value.splitlines() if l.strip() and ("/" in l or "." in l)]
        return "\n".join(lines) if lines else value
    if filter_name == "first_200":
        return value[:200]
    return value


def render_template(template: str, context: dict[str, str]) -> str:
    """Sostituisce {{step.key}} e {{step.key | filter}} nel template."""
    def replace_match(m: re.Match) -> str:
        expr = m.group(1).strip()
        if "|" in expr:
            key_part, filter_part = expr.split("|", 1)
            key = key_part.strip()
            flt = filter_part.strip()
        else:
            key = expr
            flt = ""
        value = context.get(key, "")
        if flt:
            value = _apply_filter(value, flt)
        return value

    return re.sub(r"\{\{(.+?)\}\}", replace_match, template)


# ── DAG toposort ───────────────────────────────────────────────────────────────

def toposort(steps: list[dict]) -> list[dict]:
    """Ordina gli step per dipendenze (Kahn's algorithm)."""
    id_to_step = {s["id"]: s for s in steps}
    in_degree: dict[str, int] = {s["id"]: 0 for s in steps}
    dependents: dict[str, list[str]] = defaultdict(list)

    for step in steps:
        for dep in step.get("needs", []):
            if dep not in id_to_step:
                raise ValueError(f"Dipendenza '{dep}' non trovata nel pipeline.")
            in_degree[step["id"]] += 1
            dependents[dep].append(step["id"])

    queue = deque(s_id for s_id, deg in in_degree.items() if deg == 0)
    ordered: list[dict] = []

    while queue:
        s_id = queue.popleft()
        ordered.append(id_to_step[s_id])
        for dep_id in dependents[s_id]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)

    if len(ordered) != len(steps):
        raise ValueError("Dipendenza circolare rilevata nel pipeline.")

    return ordered


# ── Esecuzione step ────────────────────────────────────────────────────────────

def run_step(step: dict, context: dict[str, str], vars_: dict[str, str]) -> tuple[bool, str]:
    """Esegue un singolo step via claude CLI. Ritorna (success, output)."""
    # Merge variabili pipeline nel contesto
    full_context = {**vars_, **context}

    prompt = render_template(str(step.get("prompt", "")), full_context)
    agent = step.get("agent", "general-purpose")
    model = step.get("model", "")
    timeout = int(step.get("timeout_s", 600))

    # Costruisce il comando claude CLI
    cmd = ["claude", "--print"]
    if model:
        cmd += ["--model", model]
    # Alcune versioni CLI supportano --agent, altre no: usa il prompt diretto
    full_prompt = f"[Agente: {agent}]\n\n{prompt}"
    cmd.append(full_prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return False, result.stderr[:500]
        return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, f"timeout dopo {timeout}s"
    except FileNotFoundError:
        return False, "claude CLI non trovata — installa Claude Code"
    except Exception as e:
        return False, str(e)


def log_step(pipeline_name: str, step_id: str, agent: str, outcome: str, project: str) -> None:
    """Logga lo step in coordination-log.jsonl."""
    log_script = SKILL_DIR / "scripts" / "log_coordination.py"
    if not log_script.exists():
        return
    try:
        subprocess.run(
            [
                sys.executable, str(log_script),
                "--project", project,
                "--project-name", Path(project).name,
                "--category", "pipeline",
                "--outcome", outcome,
                "--agents", agent,
                "--keywords", pipeline_name, step_id,
            ],
            check=False,
            timeout=10,
        )
    except Exception:
        pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Runner pipeline YAML di subagent")
    ap.add_argument("--pipeline", required=True, help="Path al file YAML del pipeline")
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--var", action="append", default=[], metavar="KEY=VALUE",
                    help="Variabile da iniettare nel template (ripetibile)")
    ap.add_argument("--dry-run", action="store_true", help="Mostra il piano senza eseguire")

    try:
        args = ap.parse_args()
    except SystemExit:
        return 0

    pipeline_path = Path(args.pipeline)
    if not pipeline_path.exists():
        # Prova relativo alla skill dir
        pipeline_path = SKILL_DIR / args.pipeline
    if not pipeline_path.exists():
        print(f"run_pipeline: file non trovato: {args.pipeline}", file=sys.stderr)
        return 0

    try:
        with open(pipeline_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except Exception as e:
        print(f"run_pipeline: errore parsing YAML: {e}", file=sys.stderr)
        return 0

    # Variabili da CLI
    vars_: dict[str, str] = {}
    for v in args.var:
        if "=" in v:
            k, val = v.split("=", 1)
            vars_[k.strip()] = val.strip()

    pipeline_name = spec.get("pipeline", "unnamed")
    steps = spec.get("steps", [])

    if not steps:
        print("run_pipeline: pipeline senza step.", file=sys.stderr)
        return 0

    # Toposort
    try:
        ordered = toposort(steps)
    except ValueError as e:
        print(f"run_pipeline: {e}", file=sys.stderr)
        return 0

    print(f"\nPipeline: {pipeline_name}", file=sys.stderr)
    print(f"Step in ordine: {[s['id'] for s in ordered]}", file=sys.stderr)

    if args.dry_run:
        for step in ordered:
            prompt_preview = render_template(str(step.get("prompt", ""))[:100], vars_)
            print(f"  [{step['id']}] agent={step.get('agent')} prompt={prompt_preview!r}...", file=sys.stderr)
        return 0

    # Esecuzione
    context: dict[str, str] = {}
    results: list[dict] = []

    for step in ordered:
        step_id = step["id"]
        agent = step.get("agent", "general-purpose")
        output_key = step.get("output_key", step_id)

        print(f"\n[{step_id}] Avvio step (agent={agent})...", file=sys.stderr)

        success, output = run_step(step, context, vars_)

        # Salva output nel contesto per step successivi
        context[f"{step_id}.{output_key}"] = output
        context[output_key] = output

        outcome = "ok" if success else "failed"
        results.append({"id": step_id, "outcome": outcome, "output": output[:200]})

        print(f"[{step_id}] {outcome}: {output[:100]}...", file=sys.stderr)
        log_step(pipeline_name, step_id, agent, outcome, args.project)

        if not success:
            print(f"[{step_id}] ERRORE: {output}", file=sys.stderr)
            # Continua comunque (non bloccante)

    # Riepilogo
    print(f"\nPipeline '{pipeline_name}' completato.", file=sys.stderr)
    ok_count = sum(1 for r in results if r["outcome"] == "ok")
    print(f"Step OK: {ok_count}/{len(results)}", file=sys.stderr)

    if ok_count == len(results):
        print("\nOutput finale (ultimo step):")
        last = results[-1]
        print(context.get(last["id"] + "." + ordered[-1].get("output_key", last["id"]), ""))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"run_pipeline: errore fatale ({e}), exit 0.", file=sys.stderr)
        sys.exit(0)
