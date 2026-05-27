#!/usr/bin/env python3
"""Persistent runner control plane with hard safety defaults.

The runner starts as an orchestration shell only: it can track state and process
small local jobs, but autonomous AI execution is disabled until an explicit
budget/provider layer is added.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STATUS_FILE = REPORTS / "runner-status.json"
QUEUE_FILE = REPORTS / "runner-queue.json"
CONFIG_FILE = REPORTS / "runner-config.json"
ALLOWED_STATES = {"running", "paused", "stopped"}
ALLOWED_JOBS = {"scan", "checkpoint", "refresh"}
WRITE_POLICIES = {"no_write", "approval_required", "reports_only"}
EXECUTION_MODES = {"off", "local_only", "cloud_only", "hybrid"}
ROUTING_POLICIES = {"manual", "cheap_first", "quality_first"}
AUTONOMY_LEVELS = {"suggest_only", "safe_reports", "safe_edits_with_checkpoint"}
LOCAL_LLM_MODES = {"disabled", "optional", "enabled"}
DEFAULT_GUARDRAILS = {
    "ai_enabled": False,
    "token_budget_limit": 0,
    "max_jobs_per_cycle": 2,
    "max_runtime_seconds": 30,
    "loop_guard_max_same_job": 3,
}
DEFAULT_CONFIG = {
    "ai_enabled": False,
    "provider": "",
    "model": "",
    "execution_mode": "off",
    "routing_policy": "manual",
    "local_endpoint": "http://127.0.0.1:11434",
    "local_model": "",
    "local_llm_mode": "optional",
    "cloud_model": "",
    "cloud_access": "codex_cli_session",
    "approval_channel": "dashboard",
    "autonomy_level": "safe_reports",
    "server_total_ram_gb": 32,
    "dev_lxc_ram_gb": 4,
    "token_budget_limit": 0,
    "max_steps_per_task": 0,
    "max_runtime_seconds": 30,
    "write_policy": "approval_required",
    "approval_required": True,
    "allow_code_edits": False,
    "allow_shell_commands": False,
    "allow_network": False,
    "allowed_job_kinds": sorted(ALLOWED_JOBS),
    "notes": "AI autonoma non collegata. Configurazione preparatoria solo per budget e regole.",
}


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


def default_status() -> dict[str, object]:
    return {
        "state": "stopped",
        "label": "Fermo",
        "project": "",
        "heartbeat_at": "",
        "last_started_at": "",
        "last_stopped_at": "",
        "last_paused_at": "",
        "jobs_processed": 0,
        "last_job": "",
        "same_job_count": 0,
        "last_result": "Runner non avviato.",
        "safe_scope": "Controlla coda e metadata dashboard; AI autonoma disattivata.",
    }


def clamp_int(value: object, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = minimum
    return max(minimum, min(maximum, parsed))


def runner_config() -> dict[str, object]:
    config = dict(DEFAULT_CONFIG)
    config.update(load_json(CONFIG_FILE, {}))
    for stale_key in ["telegram_enabled", "telegram_bot_token_env", "telegram_chat_id", "telegram_secret_file"]:
        config.pop(stale_key, None)
    config["ai_enabled"] = False
    config["token_budget_limit"] = clamp_int(config.get("token_budget_limit"), 0, 200000)
    config["max_steps_per_task"] = clamp_int(config.get("max_steps_per_task"), 0, 50)
    config["max_runtime_seconds"] = clamp_int(config.get("max_runtime_seconds"), 10, 7200)
    config["write_policy"] = str(config.get("write_policy") or "approval_required")
    if config["write_policy"] not in WRITE_POLICIES:
        config["write_policy"] = "approval_required"
    config["execution_mode"] = str(config.get("execution_mode") or "off")
    if config["execution_mode"] not in EXECUTION_MODES:
        config["execution_mode"] = "off"
    config["routing_policy"] = str(config.get("routing_policy") or "manual")
    if config["routing_policy"] not in ROUTING_POLICIES:
        config["routing_policy"] = "manual"
    config["approval_channel"] = "dashboard"
    config["autonomy_level"] = str(config.get("autonomy_level") or "safe_reports")
    if config["autonomy_level"] not in AUTONOMY_LEVELS:
        config["autonomy_level"] = "safe_reports"
    config["local_llm_mode"] = str(config.get("local_llm_mode") or "optional")
    if config["local_llm_mode"] not in LOCAL_LLM_MODES:
        config["local_llm_mode"] = "optional"
    config["server_total_ram_gb"] = clamp_int(config.get("server_total_ram_gb"), 1, 1024)
    config["dev_lxc_ram_gb"] = clamp_int(config.get("dev_lxc_ram_gb"), 1, 1024)
    config["approval_required"] = True
    config["allow_code_edits"] = False
    config["allow_shell_commands"] = False
    config["allow_network"] = False
    config["config_path"] = str(CONFIG_FILE)
    config["safety_label"] = "Preparato, AI spenta"
    return config


def update_runner_config(updates: dict[str, object]) -> dict[str, object]:
    config = runner_config()
    for key in ["provider", "model", "local_endpoint", "local_model", "cloud_model", "cloud_access", "notes"]:
        if key in updates:
            config[key] = str(updates.get(key) or "")[:240]
    if "server_total_ram_gb" in updates:
        config["server_total_ram_gb"] = clamp_int(updates.get("server_total_ram_gb"), 1, 1024)
    if "dev_lxc_ram_gb" in updates:
        config["dev_lxc_ram_gb"] = clamp_int(updates.get("dev_lxc_ram_gb"), 1, 1024)
    if "token_budget_limit" in updates:
        config["token_budget_limit"] = clamp_int(updates.get("token_budget_limit"), 0, 200000)
    if "max_steps_per_task" in updates:
        config["max_steps_per_task"] = clamp_int(updates.get("max_steps_per_task"), 0, 50)
    if "max_runtime_seconds" in updates:
        config["max_runtime_seconds"] = clamp_int(updates.get("max_runtime_seconds"), 10, 7200)
    if str(updates.get("write_policy") or "") in WRITE_POLICIES:
        config["write_policy"] = str(updates.get("write_policy"))
    if str(updates.get("execution_mode") or "") in EXECUTION_MODES:
        config["execution_mode"] = str(updates.get("execution_mode"))
    if str(updates.get("routing_policy") or "") in ROUTING_POLICIES:
        config["routing_policy"] = str(updates.get("routing_policy"))
    config["approval_channel"] = "dashboard"
    if str(updates.get("autonomy_level") or "") in AUTONOMY_LEVELS:
        config["autonomy_level"] = str(updates.get("autonomy_level"))
    if str(updates.get("local_llm_mode") or "") in LOCAL_LLM_MODES:
        config["local_llm_mode"] = str(updates.get("local_llm_mode"))
    config["ai_enabled"] = False
    config["approval_required"] = True
    config["allow_code_edits"] = False
    config["allow_shell_commands"] = False
    config["allow_network"] = False
    config["updated_at"] = now()
    to_save = {key: value for key, value in config.items() if key not in {"config_path", "safety_label"}}
    save_json(CONFIG_FILE, to_save)
    return runner_config()


def load_queue() -> dict[str, object]:
    queue = load_json(QUEUE_FILE, {"items": []})
    if not isinstance(queue.get("items"), list):
        queue["items"] = []
    return queue


def save_queue(queue: dict[str, object]) -> None:
    save_json(QUEUE_FILE, queue)


def runner_status() -> dict[str, object]:
    status = default_status()
    status.update(load_json(STATUS_FILE, {}))
    config = runner_config()
    if status.get("state") not in ALLOWED_STATES:
        status["state"] = "stopped"
    status.update(DEFAULT_GUARDRAILS)
    status.update(
        {
            "ai_enabled": config.get("ai_enabled"),
            "token_budget_limit": config.get("token_budget_limit"),
            "max_runtime_seconds": config.get("max_runtime_seconds"),
            "max_steps_per_task": config.get("max_steps_per_task"),
            "approval_required": config.get("approval_required"),
            "write_policy": config.get("write_policy"),
            "provider": config.get("provider", ""),
            "model": config.get("model", ""),
            "execution_mode": config.get("execution_mode", "off"),
            "routing_policy": config.get("routing_policy", "manual"),
            "local_endpoint": config.get("local_endpoint", ""),
            "local_model": config.get("local_model", ""),
            "local_llm_mode": config.get("local_llm_mode", "optional"),
            "cloud_model": config.get("cloud_model", ""),
            "cloud_access": config.get("cloud_access", "codex_cli_session"),
            "approval_channel": config.get("approval_channel", "dashboard"),
            "autonomy_level": config.get("autonomy_level", "safe_reports"),
            "runner_config": config,
        }
    )
    queue = load_queue()
    status["queued_jobs"] = len([item for item in queue.get("items", []) if isinstance(item, dict)])
    status["queue_path"] = str(QUEUE_FILE)
    status["status_path"] = str(STATUS_FILE)
    status["label"] = {"running": "In esecuzione", "paused": "In pausa", "stopped": "Fermo"}.get(str(status.get("state")), "Fermo")
    return status


def write_status(updates: dict[str, object]) -> dict[str, object]:
    status = runner_status()
    status.update(updates)
    status["updated_at"] = now()
    status["label"] = {"running": "In esecuzione", "paused": "In pausa", "stopped": "Fermo"}.get(str(status.get("state")), "Fermo")
    save_json(STATUS_FILE, status)
    return runner_status()


def start_runner(project: str = "") -> dict[str, object]:
    return write_status(
        {
            "state": "running",
            "project": project,
            "last_started_at": now(),
            "heartbeat_at": now(),
            "last_result": "Runner avviato in modalita sicura. AI autonoma disattivata.",
        }
    )


def stop_runner() -> dict[str, object]:
    return write_status(
        {
            "state": "stopped",
            "last_stopped_at": now(),
            "last_result": "Runner fermato. Nessun job verra eseguito.",
        }
    )


def pause_runner() -> dict[str, object]:
    return write_status(
        {
            "state": "paused",
            "last_paused_at": now(),
            "last_result": "Runner in pausa. La coda resta salvata.",
        }
    )


def enqueue_job(kind: str, project: str = "", reason: str = "") -> dict[str, object]:
    if kind not in ALLOWED_JOBS:
        return {"ok": False, "error": f"Job non consentito: {kind}", "status": runner_status()}
    queue = load_queue()
    items = [item for item in queue.get("items", []) if isinstance(item, dict)]
    job = {
        "id": f"{kind}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(items) + 1}",
        "kind": kind,
        "project": project,
        "reason": reason,
        "created_at": now(),
    }
    items.append(job)
    queue["items"] = items[:100]
    queue["updated_at"] = now()
    save_queue(queue)
    status = runner_status()
    return {"ok": True, "job": job, "status": status}


def process_job(job: dict[str, object]) -> dict[str, object]:
    kind = str(job.get("kind") or "")
    if kind == "scan":
        return {"ok": True, "message": "Scan accodato come refresh dashboard sicuro.", "spent_tokens": 0}
    if kind == "checkpoint":
        return {"ok": True, "message": "Checkpoint conservato; nessuna AI avviata.", "spent_tokens": 0}
    if kind == "refresh":
        return {"ok": True, "message": "Refresh dashboard richiesto.", "spent_tokens": 0}
    return {"ok": False, "message": "Job ignorato: tipo non riconosciuto.", "spent_tokens": 0}


def run_once() -> dict[str, object]:
    status = runner_status()
    if status.get("state") != "running":
        return {"ok": False, "reason": f"Runner {status.get('label', 'fermo')}", "processed": 0, "status": status}
    if status.get("ai_enabled") is not False:
        stopped = stop_runner()
        stopped["last_result"] = "Guardrail attivato: configurazione AI non sicura."
        save_json(STATUS_FILE, stopped)
        return {"ok": False, "reason": "Guardrail AI", "processed": 0, "status": runner_status()}

    queue = load_queue()
    items = [item for item in queue.get("items", []) if isinstance(item, dict)]
    max_jobs = max(1, int(status.get("max_jobs_per_cycle") or 1))
    processed: list[dict[str, object]] = []
    remaining = list(items)
    last_job = str(status.get("last_job") or "")
    same_job_count = int(status.get("same_job_count") or 0)
    total_processed = int(status.get("jobs_processed") or 0)

    for job in items[:max_jobs]:
        key = str(job.get("kind") or "")
        if key == last_job:
            same_job_count += 1
        else:
            same_job_count = 1
        if same_job_count > int(status.get("loop_guard_max_same_job") or 3):
            stopped = stop_runner()
            stopped["last_result"] = f"Runner fermato dal loop guard sul job: {key}"
            save_json(STATUS_FILE, stopped)
            return {"ok": False, "reason": "loop_guard", "processed": len(processed), "status": runner_status()}
        result = process_job(job)
        processed.append({"job": job, "result": result})
        remaining.pop(0)
        last_job = key
        total_processed += 1

    queue["items"] = remaining
    queue["updated_at"] = now()
    save_queue(queue)
    message = "Nessun job in coda." if not processed else f"Eseguiti {len(processed)} job sicuri."
    status = write_status(
        {
            "heartbeat_at": now(),
            "jobs_processed": total_processed,
            "last_job": last_job,
            "same_job_count": same_job_count if processed else 0,
            "last_result": message,
        }
    )
    return {"ok": True, "processed": len(processed), "jobs": processed, "status": status}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    start = sub.add_parser("start")
    start.add_argument("--project", default="")
    sub.add_parser("stop")
    sub.add_parser("pause")
    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("--kind", choices=sorted(ALLOWED_JOBS), required=True)
    enqueue.add_argument("--project", default="")
    enqueue.add_argument("--reason", default="")
    configure = sub.add_parser("configure")
    configure.add_argument("--provider", default=None)
    configure.add_argument("--model", default=None)
    configure.add_argument("--execution-mode", choices=sorted(EXECUTION_MODES), default=None)
    configure.add_argument("--routing-policy", choices=sorted(ROUTING_POLICIES), default=None)
    configure.add_argument("--local-endpoint", default=None)
    configure.add_argument("--local-model", default=None)
    configure.add_argument("--local-llm-mode", choices=sorted(LOCAL_LLM_MODES), default=None)
    configure.add_argument("--cloud-model", default=None)
    configure.add_argument("--cloud-access", default=None)
    configure.add_argument("--autonomy-level", choices=sorted(AUTONOMY_LEVELS), default=None)
    configure.add_argument("--server-total-ram-gb", type=int, default=None)
    configure.add_argument("--dev-lxc-ram-gb", type=int, default=None)
    configure.add_argument("--token-budget", type=int, default=None)
    configure.add_argument("--max-steps", type=int, default=None)
    configure.add_argument("--max-runtime", type=int, default=None)
    configure.add_argument("--write-policy", choices=sorted(WRITE_POLICIES), default=None)
    configure.add_argument("--notes", default=None)
    sub.add_parser("run-once")
    args = parser.parse_args()

    if args.command == "start":
        result = start_runner(args.project)
    elif args.command == "stop":
        result = stop_runner()
    elif args.command == "pause":
        result = pause_runner()
    elif args.command == "enqueue":
        result = enqueue_job(args.kind, args.project, args.reason)
    elif args.command == "configure":
        updates = {
            "provider": args.provider,
            "model": args.model,
            "execution_mode": args.execution_mode,
            "routing_policy": args.routing_policy,
            "local_endpoint": args.local_endpoint,
            "local_model": args.local_model,
            "local_llm_mode": args.local_llm_mode,
            "cloud_model": args.cloud_model,
            "cloud_access": args.cloud_access,
            "autonomy_level": args.autonomy_level,
            "server_total_ram_gb": args.server_total_ram_gb,
            "dev_lxc_ram_gb": args.dev_lxc_ram_gb,
            "token_budget_limit": args.token_budget,
            "max_steps_per_task": args.max_steps,
            "max_runtime_seconds": args.max_runtime,
            "write_policy": args.write_policy,
            "notes": args.notes,
        }
        result = update_runner_config({key: value for key, value in updates.items() if value is not None})
    elif args.command == "run-once":
        result = run_once()
    else:
        result = runner_status()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f"Persistent Runner: {result.get('label', result.get('state', 'stopped'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
