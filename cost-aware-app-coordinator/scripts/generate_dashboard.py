#!/usr/bin/env python3
"""Generate an operational HTML dashboard for the skill."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from auto_pilot import decide as auto_pilot_decide
from background_sentinel import update_sentinel
from dashboard_components import DASHBOARD_CSS, esc, render_blueprint_cards, render_blueprint_graph, render_expert_feedback, render_project_selector, render_table, status_label
from dashboard_projects import (
    CONFIG,
    DEFAULT_CONFIG,
    REPORTS,
    REPO,
    ROOT,
    SESSION_LIMIT,
    is_project_path,
    is_skill_workspace,
    lxc_projects,
    load_config,
    merge_project_rows,
    project_row,
    project_root,
    save_config,
)
from dashboard_sessions import codex_sessions
from event_log import emit_event, summarize_events
from skill_learning import summarize_learning
from task_checkpoint import summary as task_checkpoint_summary
from persistent_runner import run_once as runner_run_once
from persistent_runner import runner_status
from project_memory import table as memory_table
from project_memory import update_memory


SMART_CACHE = REPORTS / "dashboard-cache.json"
DEFAULT_CACHE_SECONDS = 180


def load_smart_cache() -> dict[str, object]:
    if not SMART_CACHE.exists():
        return {"items": {}}
    try:
        data = json.loads(SMART_CACHE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"items": {}}
    except (OSError, json.JSONDecodeError):
        return {"items": {}}


def save_smart_cache(cache: dict[str, object]) -> None:
    SMART_CACHE.parent.mkdir(parents=True, exist_ok=True)
    SMART_CACHE.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")


def source_cache_stamp() -> str:
    roots = [ROOT / "scripts", ROOT / "frontend", ROOT / "AI_CONTEXT.md", ROOT / "docs" / "ai"]
    latest = 0.0
    for root in roots:
        if root.is_file():
            latest = max(latest, root.stat().st_mtime)
            continue
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    latest = max(latest, path.stat().st_mtime)
    return str(round(latest))


def cache_key(name: str, project: Path, cmd: list[str]) -> str:
    return "|".join([name, str(project.resolve()), " ".join(cmd), source_cache_stamp()])


def cached_run_json(
    cache: dict[str, object],
    name: str,
    project: Path,
    cmd: list[str],
    ttl_seconds: int = DEFAULT_CACHE_SECONDS,
) -> tuple[dict[str, object], dict[str, object] | None]:
    items = cache.setdefault("items", {})
    key = cache_key(name, project, cmd)
    if isinstance(items, dict) and key in items:
        item = items.get(key, {})
        if isinstance(item, dict):
            try:
                cached_at = datetime.fromisoformat(str(item.get("cached_at", "")))
                if datetime.now() - cached_at <= timedelta(seconds=ttl_seconds):
                    run_result = item.get("run", {})
                    parsed = item.get("json")
                    if isinstance(run_result, dict):
                        run_result = {**run_result, "cached": True}
                        return run_result, parsed if isinstance(parsed, dict) else None
            except ValueError:
                pass
    run_result, parsed = run_json(cmd)
    if isinstance(items, dict):
        items[key] = {
            "cached_at": datetime.now().isoformat(timespec="seconds"),
            "run": run_result,
            "json": parsed or {},
        }
    return run_result, parsed


def cached_run(
    cache: dict[str, object],
    name: str,
    project: Path,
    cmd: list[str],
    ttl_seconds: int = DEFAULT_CACHE_SECONDS,
) -> dict[str, object]:
    result, _ = cached_run_json(cache, name, project, cmd, ttl_seconds)
    return result


def cache_summary(checks: dict[str, dict[str, object]]) -> dict[str, object]:
    cached = [name for name, result in checks.items() if isinstance(result, dict) and result.get("cached")]
    fresh = [name for name, result in checks.items() if isinstance(result, dict) and not result.get("cached")]
    return {
        "status": "cache" if cached else "fresh",
        "cached_count": len(cached),
        "fresh_count": len(fresh),
        "cached_checks": cached,
        "fresh_checks": fresh,
    }


def run(cmd: list[str]) -> dict[str, object]:
    result = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_json(cmd: list[str]) -> tuple[dict[str, object], dict[str, object] | None]:
    result = run(cmd)
    try:
        parsed = json.loads(str(result.get("stdout") or "{}"))
        return result, parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return result, None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def token_estimate(text: str) -> int:
    return max(1, round(len(text) / 4))


def line_count(path: Path) -> int:
    return len(read(path).splitlines())


def latest_section(path: Path) -> str:
    lines = read(path).splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## "):
            start = index
            break
    if start is None:
        return "\n".join(lines[:20])
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def latest_improvement(path: Path) -> str:
    text = read(path)
    marker = "Status: done"
    start = text.find(marker)
    if start == -1:
        return text[:1200]
    next_start = text.find(marker, start + len(marker))
    return text[start: next_start if next_start != -1 else len(text)].strip()


def file_metrics() -> list[dict[str, object]]:
    files = [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]
    files += sorted((ROOT / "scripts").glob("*.py"))
    return [
        {
            "path": str(path.relative_to(ROOT)),
            "lines": line_count(path),
            "estimated_tokens": token_estimate(read(path)),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]


def build_handoff_prompt(project: Path, docs: dict[str, object] | None, pr: dict[str, object] | None) -> str:
    warnings = pr.get("warnings", []) if pr else []
    untracked = pr.get("untracked", []) if pr else []
    recommended = pr.get("recommended_checks", []) if pr else []
    create = docs.get("recommended_create", []) if docs else []
    do_not_create = docs.get("recommended_do_not_create_now", []) if docs else []
    return "\n".join(
        [
            "Sto lavorando su questo progetto:",
            str(project),
            "",
            "Usa AGENTS.md e AI_CONTEXT.md come routing iniziale. Non leggere file grandi interi: usa rg, heading e sezioni mirate.",
            "",
            "Controlla lo stato attuale senza modificare nulla, poi proponi il prossimo passo minimo.",
            "",
            f"Warning PR/readiness: {', '.join(warnings) if warnings else 'nessuno'}",
            f"File non tracciati da valutare: {', '.join(untracked) if untracked else 'nessuno'}",
            f"Docs AI ancora da creare secondo audit: {', '.join(create) if create else 'nessuno'}",
            f"Docs da non duplicare ora: {', '.join(do_not_create) if do_not_create else 'nessuno'}",
            f"Check consigliati: {', '.join(recommended) if recommended else 'test mirato sui file toccati'}",
            "",
            "Output richiesto: stato repo, rischi, file da toccare, test minimi, e se posso procedere.",
        ]
    )


def project_guidance(
    docs: dict[str, object],
    pr: dict[str, object],
    background: dict[str, object],
    blueprint: dict[str, object],
    warning_tasks: list[dict[str, object]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    missing_docs = [str(item) for item in docs.get("recommended_create", []) or []]
    pr_warnings = [str(item) for item in pr.get("warnings", []) or []]
    modified = [str(item) for item in pr.get("modified", []) or []]
    untracked = [str(item) for item in pr.get("untracked", []) or []]
    if untracked:
        items.append(
            {
                "kind": "File nuovi",
                "title": f"{len(untracked)} file/cartelle non tracciati",
                "where": ", ".join(untracked[:5]),
                "why": "Sono file che Git non sta ancora seguendo: potrebbero essere lavoro utile oppure output da ignorare.",
                "action": "Controlla se vanno inclusi nel progetto o aggiunti a .gitignore prima di continuare.",
            }
        )
    if missing_docs:
        items.append(
            {
                "kind": "Contesto AI",
                "title": "Mancano file guida per capire il progetto",
                "where": ", ".join(missing_docs[:5]),
                "why": "Questo puo creare confusione quando la skill o una chat AI prova a capire il progetto.",
                "action": "Crea o aggiorna questi file solo con informazioni vere: scopo app, comandi, struttura, rischi e decisioni.",
            }
        )
    elif pr_warnings:
        items.append(
            {
                "kind": "Warning progetto",
                "title": pr_warnings[0],
                "where": ", ".join(modified[:4]) or "Stato progetto",
                "why": "La dashboard ha trovato un segnale che puo sporcare commit, PR o test.",
                "action": "Risolvi questo warning prima di lavorare su feature nuove.",
            }
        )
    if modified:
        items.append(
            {
                "kind": "File modificati",
                "title": f"{len(modified)} file risultano modificati",
                "where": ", ".join(modified[:5]),
                "why": "Prima di partire conviene capire se sono modifiche tue, della skill o lavoro lasciato a meta.",
                "action": "Guarda questi file come primo controllo, poi decidi se continuare, testare o committare.",
            }
        )
    for finding in background.get("top_findings", []) or []:
        if not isinstance(finding, dict):
            continue
        items.append(
            {
                "kind": str(finding.get("kind", "Lavagna")),
                "title": str(finding.get("problem") or finding.get("title") or "Problema rilevato"),
                "where": str(finding.get("evidence") or finding.get("title") or finding.get("id") or "Nodo lavagna"),
                "why": str(finding.get("reason") or "Collegamento o nodo non abbastanza chiaro."),
                "action": str(finding.get("fix") or "Apri la Lavagna App, seleziona il nodo e controlla prove/collegamenti."),
            }
        )
        if len(items) >= 6:
            return items
    doctor = blueprint.get("doctor", {}) if isinstance(blueprint.get("doctor"), dict) else {}
    audit = doctor.get("audit", {}) if isinstance(doctor.get("audit"), dict) else {}
    for problem in audit.get("problems", []) if isinstance(audit.get("problems"), list) else []:
        if not isinstance(problem, dict):
            continue
        items.append(
            {
                "kind": "Lavagna",
                "title": str(problem.get("problem") or problem.get("title") or "Nodo da chiarire"),
                "where": str(problem.get("evidence") or problem.get("title") or "Nodo lavagna"),
                "why": str(problem.get("reason") or "La skill non ha abbastanza prove per essere sicura."),
                "action": str(problem.get("fix") or "Apri la lavagna e controlla questo nodo."),
            }
        )
        if len(items) >= 6:
            return items
    for task in warning_tasks:
        if not isinstance(task, dict):
            continue
        items.append(
            {
                "kind": f"Task {task.get('priority', '')}".strip(),
                "title": str(task.get("task") or "Task consigliato"),
                "where": "Dashboard progetto",
                "why": str(task.get("why") or "Riduce errori prima di continuare."),
                "action": str(task.get("prompt") or "Usa questo task come prossimo passo."),
            }
        )
        if len(items) >= 6:
            return items
    if not items:
        items.append(
            {
                "kind": "Prossimo passo",
                "title": "Nessun problema prioritario trovato",
                "where": "Progetto selezionato",
                "why": "La dashboard non vede warning bloccanti in questo momento.",
                "action": "Apri la Lavagna App per capire struttura e collegamenti, oppure avvia una nuova scansione.",
            }
        )
    return items[:6]


def build_report(project_override: str | None = None, save_project: bool = False) -> dict[str, object]:
    config = load_config(project_override)
    if save_project:
        save_config(config)
    monitored_project = project_root(config)
    smart_cache = load_smart_cache()
    validate = cached_run(smart_cache, "validate_skill", ROOT, [sys.executable, str(ROOT / "scripts" / "validate_skill.py")])
    self_test = cached_run(smart_cache, "self_test", ROOT, [sys.executable, str(ROOT / "scripts" / "self_test.py")])
    sync_check = cached_run(smart_cache, "sync_check", ROOT, [sys.executable, str(ROOT / "scripts" / "sync_check.py")])
    context_scan = cached_run(
        smart_cache,
        "context_budget_scan",
        monitored_project,
        [
            sys.executable,
            str(ROOT / "scripts" / "context_budget_scan.py"),
            str(monitored_project),
            "--max-files",
            "8",
        ],
    )
    skill_intake = cached_run(
        smart_cache,
        "external_skill_intake",
        ROOT,
        [sys.executable, str(ROOT / "scripts" / "external_skill_intake.py"), str(ROOT)],
    )
    bootstrap_preview = cached_run(
        smart_cache,
        "bootstrap_project_context",
        monitored_project,
        [
            sys.executable,
            str(ROOT / "scripts" / "bootstrap_project_context.py"),
            str(monitored_project),
            "--dry-run",
        ],
    )
    docs_audit, docs_audit_json = cached_run_json(
        smart_cache,
        "project_docs_audit",
        monitored_project,
        [sys.executable, str(ROOT / "scripts" / "project_docs_audit.py"), str(monitored_project), "--json"],
    )
    pr_readiness, pr_readiness_json = run_json(
        [sys.executable, str(ROOT / "scripts" / "pr_readiness_check.py"), str(monitored_project), "--json"]
    )
    project_copilot, project_copilot_json = cached_run_json(
        smart_cache,
        "project_copilot",
        monitored_project,
        [sys.executable, str(ROOT / "scripts" / "project_copilot.py"), str(monitored_project), "--json"],
    )
    agent_activity, agent_activity_json = cached_run_json(
        smart_cache,
        "agent_activity",
        monitored_project,
        [
            sys.executable,
            str(ROOT / "scripts" / "agent_activity_analyzer.py"),
            "--project",
            str(monitored_project),
            "--limit",
            "40",
            "--json",
        ],
    )
    action_pack, action_pack_json = cached_run_json(
        smart_cache,
        "action_pack",
        monitored_project,
        [sys.executable, str(ROOT / "scripts" / "action_pack.py"), str(monitored_project), "--json"],
    )
    maintenance_advisor, maintenance_advisor_json = cached_run_json(
        smart_cache,
        "maintenance_advisor",
        ROOT,
        [sys.executable, str(ROOT / "scripts" / "maintenance_advisor.py"), "--json"],
    )
    expert_feedback, expert_feedback_json = cached_run_json(
        smart_cache,
        "expert_feedback",
        monitored_project,
        [
            sys.executable,
            str(ROOT / "scripts" / "expert_feedback.py"),
            "summary",
            "--project",
            str(monitored_project),
            "--json",
        ],
        ttl_seconds=60,
    )
    blueprint_board, blueprint_board_json = cached_run_json(
        smart_cache,
        "blueprint_board",
        monitored_project,
        [
            sys.executable,
            str(ROOT / "scripts" / "blueprint_board.py"),
            "summary",
            str(monitored_project),
            "--json",
        ],
    )
    background_status = update_sentinel(
        str(monitored_project),
        str(config.get("background_mode") or "safe"),
        blueprint_board_json or {},
        int(config.get("refresh_seconds") or 15),
    )
    persistent_runner = runner_status()
    if persistent_runner.get("state") == "running":
        runner_tick = runner_run_once()
        persistent_runner = runner_tick.get("status", persistent_runner) if isinstance(runner_tick, dict) else runner_status()
        if isinstance(runner_tick, dict):
            persistent_runner["last_tick"] = {
                "ok": runner_tick.get("ok"),
                "reason": runner_tick.get("reason", ""),
                "processed": runner_tick.get("processed", 0),
            }
    active_task = task_checkpoint_summary()
    save_smart_cache(smart_cache)
    memory = update_memory(
        monitored_project,
        docs_audit_json or {},
        pr_readiness_json or {},
        project_copilot_json or {},
        agent_activity_json or {},
    )
    auto_pilot_json = auto_pilot_decide(
        str(monitored_project),
        docs_audit_json or {},
        pr_readiness_json or {},
        project_copilot_json or {},
        agent_activity_json or {},
        maintenance_advisor_json or {},
    )
    pr_warnings = (pr_readiness_json or {}).get("warnings", [])
    large_files = (project_copilot_json or {}).get("large_text_files", [])
    experts = (agent_activity_json or {}).get("suggested_experts", [])
    emitted_events = []
    emitted_events.append(emit_event(
        "dashboard_generated",
        str(monitored_project),
        "info",
        "Dashboard refreshed.",
        {"project": str(monitored_project)},
    ))
    if pr_warnings:
        emitted_events.append(emit_event(
            "pr_readiness_warn",
            str(monitored_project),
            "warn",
            "; ".join(str(item) for item in pr_warnings),
            {"warnings": pr_warnings},
        ))
    if large_files:
        emitted_events.append(emit_event(
            "large_file_detected",
            str(monitored_project),
            "warn",
            f"{len(large_files)} large text files detected.",
            {"files": large_files[:5]},
        ))
    if experts:
        emitted_events.append(emit_event(
            "expert_suggested",
            str(monitored_project),
            "info",
            ", ".join(str(item.get("expert", "")) for item in experts[:3] if isinstance(item, dict)),
            {"experts": experts[:5]},
        ))
    doctor_nodes = ((blueprint_board_json or {}).get("doctor") or {}).get("nodes", [])
    has_design_nodes = any(isinstance(item, dict) and item.get("origin") == "design" for item in doctor_nodes) if isinstance(doctor_nodes, list) else False
    doctor_by_id = {str(item.get("id", "")): item for item in doctor_nodes if isinstance(item, dict)} if isinstance(doctor_nodes, list) else {}
    uncertain_logged = 0
    for item in doctor_nodes[:90] if isinstance(doctor_nodes, list) else []:
        if not isinstance(item, dict):
            continue
        gap_status = str(item.get("gap_status") or "")
        if gap_status == "missing_code":
            emitted_events.append(emit_event(
                "scanner_gap",
                str(monitored_project),
                "warn",
                f"{item.get('title', '')}: design senza codice rilevato",
                {"area": "blueprint-board", "item_id": item.get("id", ""), "fix_status": "open"},
                dedup_seconds=86400,
            ))
        elif gap_status == "extra_code" and has_design_nodes:
            emitted_events.append(emit_event(
                "scanner_extra_code",
                str(monitored_project),
                "info",
                f"{item.get('title', '')}: codice rilevato non ancora nel design",
                {"area": "blueprint-board", "item_id": item.get("id", ""), "fix_status": "open"},
                dedup_seconds=86400,
            ))
        audit_problem = str(item.get("audit_problem") or "")
        if audit_problem:
            emitted_events.append(emit_event(
                "scanner_audit_problem",
                str(monitored_project),
                "warn" if item.get("audit_status") == "rotto" else "info",
                f"{item.get('title', '')}: {item.get('audit_reason', '')}",
                {"area": "blueprint-board", "item_id": item.get("id", ""), "problem": audit_problem, "fix_status": "open", "fix": item.get("audit_fix", "")},
                dedup_seconds=86400,
            ))
        for rel in item.get("plain_relations", []) if isinstance(item.get("plain_relations"), list) else []:
            if isinstance(rel, dict) and rel.get("state") == "proposed" and uncertain_logged < 12:
                target = doctor_by_id.get(str(rel.get("id", "")), {})
                if item.get("kind") == "action" and target.get("kind") == "action":
                    continue
                if str(target.get("title", "")).startswith("Script:"):
                    continue
                uncertain_logged += 1
                emitted_events.append(emit_event(
                    "scanner_uncertain_edge",
                    str(monitored_project),
                    "warn",
                    f"{item.get('title', '')} -> {rel.get('title', '')}: collegamento suggerito",
                    {"area": "blueprint-board", "item_id": f"{item.get('id', '')}->{rel.get('id', '')}", "fix_status": "open", "reason": rel.get("reason", "")},
                    dedup_seconds=86400,
                ))
    learning_summary = summarize_learning(str(monitored_project))
    event_summary = summarize_events()
    event_summary["emitted_this_refresh"] = len([item for item in emitted_events if not item.get("deduplicated")])
    event_summary["deduplicated_this_refresh"] = len([item for item in emitted_events if item.get("deduplicated")])
    git_status = run(["git", "status", "--short"])
    git_diff = run(["git", "--no-pager", "diff", "--stat"])
    metrics = file_metrics()
    skill_tokens = next(item["estimated_tokens"] for item in metrics if item["path"] == "SKILL.md")
    reference_tokens = sum(
        int(item["estimated_tokens"]) for item in metrics if str(item["path"]).startswith("references/")
    )
    sessions, session_analytics, discovered_projects = codex_sessions()
    discovered_projects = merge_project_rows(lxc_projects(), discovered_projects)
    selected_project = str(monitored_project.resolve())
    if not any(str(item.get("path")) == selected_project for item in discovered_projects):
        discovered_projects = merge_project_rows([project_row(monitored_project, source="progetto attivo")], discovered_projects)
    checks = {
        "validate_skill": validate,
        "self_test": self_test,
        "sync_check": sync_check,
        "context_budget_scan": context_scan,
        "external_skill_intake": skill_intake,
        "bootstrap_project_context": bootstrap_preview,
        "project_docs_audit": docs_audit,
        "pr_readiness_check": pr_readiness,
        "project_copilot": project_copilot,
        "agent_activity": agent_activity,
        "action_pack": action_pack,
        "maintenance_advisor": maintenance_advisor,
        "expert_feedback": expert_feedback,
        "blueprint_board": blueprint_board,
    }
    cache_info = cache_summary(checks)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "config": config,
        "monitored_project": str(monitored_project),
        "checks": checks,
        "project_audit": {
            "docs": docs_audit_json or {},
            "pr_readiness": pr_readiness_json or {},
            "project_copilot": project_copilot_json or {},
            "agent_activity": agent_activity_json or {},
            "action_pack": action_pack_json or {},
            "maintenance_advisor": maintenance_advisor_json or {},
            "expert_feedback": expert_feedback_json or {},
            "blueprint_board": blueprint_board_json or {},
            "background_sentinel": background_status,
            "persistent_runner": persistent_runner,
            "active_task": active_task,
            "auto_pilot": auto_pilot_json,
            "handoff_prompt": build_handoff_prompt(monitored_project, docs_audit_json, pr_readiness_json),
        },
        "auto_pilot": auto_pilot_json,
        "project_memory": {"path": str(ROOT / "reports" / "projects-state.json"), "projects": memory_table(memory)},
        "expert_feedback": expert_feedback_json or {},
        "blueprint_board": blueprint_board_json or {},
        "background_sentinel": background_status,
        "persistent_runner": persistent_runner,
        "active_task": active_task,
        "event_log": event_summary,
        "skill_learning": learning_summary,
        "smart_cache": {"path": str(SMART_CACHE), "ttl_seconds": DEFAULT_CACHE_SECONDS, **cache_info},
        "git": {
            "status": git_status,
            "diff_stat": git_diff,
        },
        "token_estimates": {
            "skill_md_loaded_on_trigger": skill_tokens,
            "all_references_if_loaded": reference_tokens,
            "note": "Local estimate only: characters / 4, not billing.",
        },
        "files": metrics,
        "recent_codex_sessions": sessions,
        "discovered_projects": discovered_projects,
        "session_analytics": session_analytics,
        "latest_release": latest_section(ROOT / "references" / "release-notes.md"),
        "latest_improvement": latest_improvement(ROOT / "references" / "improvement-log.md"),
    }


def compact_report(report: dict[str, object]) -> dict[str, object]:
    blueprint = dict(report.get("blueprint_board") or {})
    doctor = dict(blueprint.get("doctor") or {})
    doctor["nodes"] = (doctor.get("nodes") or [])[:12]
    doctor["suggestions"] = (doctor.get("suggestions") or [])[:12]
    if isinstance(doctor.get("flows"), dict):
        doctor["flows"] = {**doctor["flows"], "items": (doctor["flows"].get("items") or [])[:8]}
    if isinstance(doctor.get("audit"), dict):
        doctor["audit"] = {
            **doctor["audit"],
            "problems": (doctor["audit"].get("problems") or [])[:8],
            "fix_plan": (doctor["audit"].get("fix_plan") or [])[:8],
        }
    blueprint["doctor"] = doctor
    blueprint["preview_nodes"] = (blueprint.get("preview_nodes") or [])[:12]
    project_audit = report.get("project_audit") or {}
    compact_project_audit = {
        "docs": (project_audit.get("docs") or {}),
        "pr_readiness": (project_audit.get("pr_readiness") or {}),
        "auto_pilot": report.get("auto_pilot"),
        "background_sentinel": report.get("background_sentinel"),
        "persistent_runner": report.get("persistent_runner"),
        "active_task": report.get("active_task"),
        "handoff_prompt": project_audit.get("handoff_prompt", ""),
    }
    event_log = dict(report.get("event_log") or {})
    event_log["recent"] = (event_log.get("recent") or [])[:12]
    learning = dict(report.get("skill_learning") or {})
    learning["open_items"] = (learning.get("open_items") or [])[:12]
    return {
        "generated_at": report.get("generated_at"),
        "root": report.get("root"),
        "monitored_project": report.get("monitored_project"),
        "config": report.get("config"),
        "project_audit": compact_project_audit,
        "blueprint_board": blueprint,
        "background_sentinel": report.get("background_sentinel"),
        "persistent_runner": report.get("persistent_runner"),
        "active_task": report.get("active_task"),
        "auto_pilot": report.get("auto_pilot"),
        "project_memory": report.get("project_memory"),
        "expert_feedback": report.get("expert_feedback"),
        "event_log": event_log,
        "skill_learning": learning,
        "smart_cache": report.get("smart_cache"),
        "token_estimates": report.get("token_estimates"),
        "recent_codex_sessions": report.get("recent_codex_sessions", [])[:10],
        "discovered_projects": report.get("discovered_projects"),
        "session_analytics": report.get("session_analytics"),
        "latest_release": report.get("latest_release"),
        "latest_improvement": report.get("latest_improvement"),
    }


def render_html(report: dict[str, object], refresh_seconds: int | None = None) -> str:
    checks = report["checks"]
    validate = checks["validate_skill"]
    self_test = checks["self_test"]
    sync_check = checks["sync_check"]
    context_scan = checks["context_budget_scan"]
    skill_intake = checks["external_skill_intake"]
    bootstrap_preview = checks["bootstrap_project_context"]
    docs_audit = checks["project_docs_audit"]
    pr_readiness = checks["pr_readiness_check"]
    estimates = report["token_estimates"]
    sessions = report["recent_codex_sessions"]
    analytics = report["session_analytics"]
    discovered_projects = report["discovered_projects"]
    project_audit = report["project_audit"]
    monitored_project = report["monitored_project"]
    docs_json = project_audit.get("docs") or {}
    pr_json = project_audit.get("pr_readiness") or {}
    copilot_json = project_audit.get("project_copilot") or {}
    agent_json = project_audit.get("agent_activity") or {}
    action_pack_json = project_audit.get("action_pack") or {}
    maintenance_json = project_audit.get("maintenance_advisor") or {}
    expert_feedback_json = project_audit.get("expert_feedback") or {}
    blueprint_json = project_audit.get("blueprint_board") or report.get("blueprint_board") or {}
    background_json = report.get("background_sentinel") or project_audit.get("background_sentinel") or {}
    runner_json = report.get("persistent_runner") or project_audit.get("persistent_runner") or {}
    runner_config = runner_json.get("runner_config", {}) if isinstance(runner_json.get("runner_config"), dict) else {}
    active_task = report.get("active_task") or project_audit.get("active_task") or {}
    auto_pilot_json = report.get("auto_pilot") or project_audit.get("auto_pilot") or {}
    project_memory = report["project_memory"]
    event_log = report["event_log"]
    skill_learning = report.get("skill_learning") or {}
    files = report["files"]
    git = report["git"]
    warning_tasks = action_pack_json.get("warning_tasks", []) or []
    doctor = blueprint_json.get("doctor") or {}
    findings_count = background_json.get("findings_count", 0)
    new_count = background_json.get("new_count", 0)
    nodes_checked = doctor.get("nodes_checked", 0)
    guidance_items = project_guidance(docs_json, pr_json, background_json, blueprint_json, warning_tasks)
    guidance_html = "".join(
        "<article class='issue-card'>"
        f"<div class='section-label'>{esc(item.get('kind', 'Problema'))}</div>"
        f"<div class='issue-title'>{esc(item.get('title', ''))}</div>"
        f"<div class='issue-row'><strong>Dove guardare:</strong> {esc(item.get('where', ''))}</div>"
        f"<div class='issue-row'><strong>Perche conta:</strong> {esc(item.get('why', ''))}</div>"
        f"<div class='issue-row'><strong>Cosa fare:</strong> {esc(item.get('action', ''))}</div>"
        "</article>"
        for item in guidance_items
    )
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cost-Aware App Coordinator Dashboard</title>
  <style>
{DASHBOARD_CSS}
  </style>
</head>
<body>
  <header>
    <h1>Cost-Aware App Coordinator</h1>
    <div class="muted">Vista semplice per decidere il prossimo passo senza leggere tutti i dettagli tecnici.</div>
    <div class="topline">
      <span class="badge">Generata: {esc(report["generated_at"])}</span>
      <span class="badge">Progetto: {esc(Path(str(monitored_project)).name)}</span>
      <span class="badge">Pianificazione: {esc(auto_pilot_json.get("planning_mode", "n/d"))}</span>
      <span class="badge">Modalita: {esc(auto_pilot_json.get("mode", "n/d"))}</span>
      <span class="badge">Cache: {esc((report.get("smart_cache") or {}).get("cached_count", 0))} usati</span>
    </div>
  </header>
  <main>
    <nav class="dashboard-tabs" aria-label="Sezioni dashboard">
      <button class="tab-button is-active" type="button" data-dashboard-tab="home">Home</button>
      <button class="tab-button" type="button" data-dashboard-tab="lavagna">Lavagna</button>
      <button class="tab-button" type="button" data-dashboard-tab="azioni">Azioni</button>
      <button class="tab-button" type="button" data-dashboard-tab="automazione">Automazione</button>
      <button class="tab-button" type="button" data-dashboard-tab="diagnostica">Diagnostica</button>
    </nav>
    <section class="dashboard-section is-active" data-dashboard-section="home">
    <section class="project-switcher">
      <div>
        <h2>Scegli Progetto Da Monitorare</h2>
        <p class="muted">Seleziona dal menu i progetti rilevati, oppure incolla un percorso nuovo. Attuale: {esc(monitored_project)}</p>
      </div>
      {render_project_selector(discovered_projects, str(monitored_project))}
    </section>

    <h2 id="home-progetto">Home Progetto</h2>
    <section class="simple-view">
      <div class="hero-card">
        <div class="section-label">Riguarda il progetto selezionato</div>
        <div class="hero-label">Cosa fare ora</div>
        <div class="hero-action">{esc(auto_pilot_json.get("next_action", "n/d"))}</div>
        <div class="hero-reason">{esc(auto_pilot_json.get("why", ""))}</div>
        <div class="topline">
          <span class="badge">Esperto: {esc(auto_pilot_json.get("primary_expert", "n/d"))}</span>
          <span class="badge">Stato PR: {esc(pr_json.get("status", "n/d"))}</span>
          <span class="badge">Task: {esc(len(warning_tasks))}</span>
        </div>
        <div class="home-actions">
          <a class="button-link" href="#lavagna-app">Apri Lavagna App</a>
          <form method="get" action="/blueprint-scan"><input type="hidden" name="project" value="{esc(str(monitored_project))}"><button type="submit">Scansiona Progetto</button></form>
          <a class="button-link secondary" href="#automazione">Controllo Automatico</a>
          <a class="button-link secondary" href="#diagnostica">Diagnostica Tecnica</a>
        </div>
      </div>
      <div class="quick-grid">
        <div class="quick-card"><div class="section-label">Progetto</div><div class="muted">Problemi rilevati</div><strong>{esc(findings_count)}</strong><div class="muted">{esc(new_count)} nuovi dall'ultima scansione</div></div>
        <div class="quick-card"><div class="section-label">Progetto</div><div class="muted">Task aperti</div><strong>{esc(len(warning_tasks))}</strong><div class="muted">Azioni create dai warning</div></div>
        <div class="quick-card"><div class="section-label">Lavagna</div><div class="muted">Nodi capiti</div><strong>{esc(nodes_checked)}</strong><div class="muted">Schermate, backend, dati, test e runtime</div></div>
        <div class="quick-card"><div class="section-label">Dashboard</div><div class="muted">Progetto attivo</div><strong>{esc(Path(str(monitored_project)).name)}</strong><div class="muted">Cambia progetto dal selettore in alto</div></div>
      </div>
    </section>
    <section>
      <h2>Cosa devo fare in questo progetto</h2>
      <p class="muted">Questa lista traduce warning, errori e nodi incerti in passaggi pratici. Parti dal primo riquadro: dice dove guardare e perche.</p>
      <div class="guidance-board">{guidance_html}</div>
    </section>

    </section>
    <section class="dashboard-section" data-dashboard-section="automazione">
    <h2 id="automazione">Controllo Automatico</h2>
    <p class="section-kicker">Controlli operativi e runner restano separati dalla Home: qui si gestiscono scansioni, coda, limiti e guardrail.</p>
    <section class="grid">
      <div class="card">
        <div class="section-label">Dashboard</div>
        <div class="metric">{esc(background_json.get("mode_label", "Automatico sicuro"))}</div>
        <div class="muted">Stato: {esc("attivo" if background_json.get("active") else "manuale/pausa")}</div>
        <div class="muted">Ultima scansione: {esc(background_json.get("last_scan_at", "n/d"))}</div>
      </div>
      <div class="card">
        <div class="section-label">Progetto</div>
        <div class="metric">{esc(background_json.get("new_count", 0))}</div>
        <div class="muted">Nuovi problemi | Attuali: {esc(background_json.get("findings_count", 0))} | Spariti: {esc(background_json.get("resolved_count", 0))}</div>
      </div>
      <div class="card">
        <div class="button-row">
          <form method="get" action="/background-scan"><button type="submit">Scansiona ora</button></form>
        </div>
        <div class="muted">{esc(background_json.get("safe_write_scope", ""))}</div>
        <details class="inline-details">
          <summary>Modalita avanzate controllo automatico</summary>
          <div class="button-row">
            <form method="get" action="/background-mode"><input type="hidden" name="mode" value="manual"><button type="submit">Manuale</button></form>
            <form method="get" action="/background-mode"><input type="hidden" name="mode" value="safe"><button type="submit">Automatico sicuro</button></form>
            <form method="get" action="/background-mode"><input type="hidden" name="mode" value="assist"><button type="submit">Proposte assistite</button></form>
          </div>
        </details>
      </div>
    </section>

    <h2>Automazione Runner</h2>
    <section class="grid">
      <div class="card">
        <div class="section-label">Dashboard</div>
        <div class="metric">{esc(runner_json.get("label", "Fermo"))}</div>
        <div class="muted">AI autonoma: {esc("attiva" if runner_json.get("ai_enabled") else "disattivata")} | Budget token: {esc(runner_json.get("token_budget_limit", 0))}</div>
        <div class="muted">Heartbeat: {esc(runner_json.get("heartbeat_at", "n/d"))}</div>
      </div>
      <div class="card">
        <div class="section-label">Dashboard</div>
        <div class="metric">{esc(runner_json.get("queued_jobs", 0))}</div>
        <div class="muted">Job in coda | Eseguiti: {esc(runner_json.get("jobs_processed", 0))}</div>
        <div class="muted">{esc(runner_json.get("last_result", ""))}</div>
      </div>
      <div class="card">
        <div class="button-row">
          <form method="get" action="/runner-stop"><button type="submit">Ferma</button></form>
        </div>
        <div class="muted">{esc(runner_json.get("safe_scope", ""))}</div>
        <details class="inline-details">
          <summary>Controlli runner avanzati</summary>
          <div class="button-row">
            <form method="get" action="/runner-start"><button type="submit">Avvia runner</button></form>
            <form method="get" action="/runner-pause"><button type="submit">Pausa</button></form>
            <form method="get" action="/runner-run-once"><button type="submit">Esegui un ciclo</button></form>
            <form method="get" action="/runner-enqueue"><input type="hidden" name="kind" value="scan"><button type="submit">Accoda scan</button></form>
          </div>
        </details>
      </div>
    </section>
    <details>
      <summary>Impostazioni avanzate runner</summary>
      <section class="grid">
        <div class="card">
          <h2>Sicurezza</h2>
          <div class="metric">{esc(runner_config.get("safety_label", "Preparato, AI spenta"))}</div>
          <div class="muted">Modo: {esc(runner_config.get("execution_mode", "off"))} | Routing: {esc(runner_config.get("routing_policy", "manual"))}</div>
          <div class="muted">Cloud: {esc(runner_config.get("cloud_access", "codex_cli_session"))} | Modello: {esc(runner_config.get("cloud_model", "") or runner_config.get("model", "") or "non configurato")}</div>
          <div class="muted">Locale: {esc(runner_config.get("local_llm_mode", "optional"))} | Endpoint: {esc(runner_config.get("local_endpoint", "") or "non configurato")} | Modello: {esc(runner_config.get("local_model", "") or "non configurato")}</div>
          <div class="muted">Approvazioni: dashboard | Autonomia: {esc(runner_config.get("autonomy_level", "safe_reports"))}</div>
          <div class="muted">RAM server: {esc(runner_config.get("server_total_ram_gb", 32))} GB | RAM LXC dev: {esc(runner_config.get("dev_lxc_ram_gb", 4))} GB</div>
          <div class="muted">Scritture codice: {esc("no" if not runner_config.get("allow_code_edits") else "si")} | Shell: {esc("no" if not runner_config.get("allow_shell_commands") else "si")} | Network: {esc("no" if not runner_config.get("allow_network") else "si")}</div>
        </div>
        <div class="card">
          <h2>Limiti</h2>
          <div class="muted">Token massimi: {esc(runner_config.get("token_budget_limit", 0))}</div>
          <div class="muted">Step massimi: {esc(runner_config.get("max_steps_per_task", 0))}</div>
          <div class="muted">Durata massima: {esc(runner_config.get("max_runtime_seconds", 30))} secondi</div>
          <div class="muted">Policy scrittura: {esc(runner_config.get("write_policy", "approval_required"))}</div>
        </div>
        <div class="card">
          <h2>Configura limiti futuri</h2>
          <form method="get" action="/runner-config" class="design-form">
            <div><label>Modo esecuzione</label><select name="execution_mode">
              <option value="off" {"selected" if runner_config.get("execution_mode") == "off" else ""}>spento</option>
              <option value="local_only" {"selected" if runner_config.get("execution_mode") == "local_only" else ""}>solo locale</option>
              <option value="cloud_only" {"selected" if runner_config.get("execution_mode") == "cloud_only" else ""}>solo cloud</option>
              <option value="hybrid" {"selected" if runner_config.get("execution_mode") == "hybrid" else ""}>ibrido</option>
            </select></div>
            <div><label>Routing</label><select name="routing_policy">
              <option value="manual" {"selected" if runner_config.get("routing_policy") == "manual" else ""}>manuale</option>
              <option value="cheap_first" {"selected" if runner_config.get("routing_policy") == "cheap_first" else ""}>locale prima</option>
              <option value="quality_first" {"selected" if runner_config.get("routing_policy") == "quality_first" else ""}>qualita prima</option>
            </select></div>
            <div><label>Provider cloud</label><input type="text" name="provider" value="{esc(runner_config.get("provider", ""))}" placeholder="openai / altro"></div>
            <div><label>Modello cloud</label><input type="text" name="cloud_model" value="{esc(runner_config.get("cloud_model", "") or runner_config.get("model", ""))}" placeholder="da decidere"></div>
            <div><label>Endpoint locale</label><input type="text" name="local_endpoint" value="{esc(runner_config.get("local_endpoint", ""))}" placeholder="http://127.0.0.1:11434"></div>
            <div><label>Modello locale</label><input type="text" name="local_model" value="{esc(runner_config.get("local_model", ""))}" placeholder="piccolo, da decidere"></div>
            <div><label>LLM locale</label><select name="local_llm_mode">
              <option value="disabled" {"selected" if runner_config.get("local_llm_mode") == "disabled" else ""}>non usarlo</option>
              <option value="optional" {"selected" if runner_config.get("local_llm_mode") == "optional" else ""}>solo se conviene</option>
              <option value="enabled" {"selected" if runner_config.get("local_llm_mode") == "enabled" else ""}>abilitabile</option>
            </select></div>
            <div><label>Accesso cloud</label><input type="text" name="cloud_access" value="{esc(runner_config.get("cloud_access", "codex_cli_session"))}" placeholder="codex_cli_session"></div>
            <div><label>Autonomia</label><select name="autonomy_level">
              <option value="suggest_only" {"selected" if runner_config.get("autonomy_level") == "suggest_only" else ""}>solo suggerimenti</option>
              <option value="safe_reports" {"selected" if runner_config.get("autonomy_level") == "safe_reports" else ""}>report/check sicuri</option>
              <option value="safe_edits_with_checkpoint" {"selected" if runner_config.get("autonomy_level") == "safe_edits_with_checkpoint" else ""}>edit sicuri con checkpoint</option>
            </select></div>
            <div><label>RAM server GB</label><input type="number" name="server_total_ram_gb" min="1" max="1024" value="{esc(runner_config.get("server_total_ram_gb", 32))}"></div>
            <div><label>RAM LXC dev GB</label><input type="number" name="dev_lxc_ram_gb" min="1" max="1024" value="{esc(runner_config.get("dev_lxc_ram_gb", 4))}"></div>
            <input type="hidden" name="model" value="{esc(runner_config.get("cloud_model", "") or runner_config.get("model", ""))}">
            <div><label>Budget token</label><input type="number" name="token_budget_limit" min="0" max="200000" value="{esc(runner_config.get("token_budget_limit", 0))}"></div>
            <div><label>Max step</label><input type="number" name="max_steps_per_task" min="0" max="50" value="{esc(runner_config.get("max_steps_per_task", 0))}"></div>
            <div><label>Max secondi</label><input type="number" name="max_runtime_seconds" min="10" max="7200" value="{esc(runner_config.get("max_runtime_seconds", 30))}"></div>
            <div><label>Scrittura</label><select name="write_policy">
              <option value="approval_required" {"selected" if runner_config.get("write_policy") == "approval_required" else ""}>solo con approvazione</option>
              <option value="no_write" {"selected" if runner_config.get("write_policy") == "no_write" else ""}>mai scrivere codice</option>
              <option value="reports_only" {"selected" if runner_config.get("write_policy") == "reports_only" else ""}>solo report</option>
            </select></div>
            <div class="wide"><label>Note</label><input type="text" name="notes" value="{esc(runner_config.get("notes", ""))}" placeholder="regole o vincoli da ricordare"></div>
            <div class="wide"><button type="submit">Salva contratto runner</button></div>
          </form>
          <div class="muted">Questo non abilita AI autonoma: prepara solo limiti e regole verificabili.</div>
        </div>
      </section>
    </details>

    </section>
    <section class="dashboard-section" data-dashboard-section="azioni">
    <h2>Ripresa Lavoro</h2>
    <p class="section-kicker">Prompt, checkpoint e azioni operative per continuare il lavoro senza rileggere tutto il progetto.</p>
    <section class="grid">
      <div class="card">
        <div class="metric">{esc(active_task.get("status", "none"))}</div>
        <div class="muted">{esc(active_task.get("goal", "Nessun task attivo registrato."))}</div>
        <div class="muted">Aggiornato: {esc(active_task.get("updated_at", "n/d"))}</div>
      </div>
      <div class="card">
        <h2>Prossimo passo salvato</h2>
        <div class="muted">{esc(active_task.get("next_step", "Nessun checkpoint disponibile."))}</div>
      </div>
      <div class="card">
        <h2>Stato ripresa</h2>
        <div class="muted">Fatti: {esc(active_task.get("done_count", 0))} | Rischi: {esc(active_task.get("risk_count", 0))}</div>
        <div class="muted">File: {esc(", ".join(active_task.get("changed_files", [])[:4]) if isinstance(active_task.get("changed_files"), list) else "")}</div>
      </div>
    </section>
    <details><summary>Prompt di ripresa task</summary><pre>{esc(active_task.get("resume_prompt", ""))}</pre></details>

    </section>
    <section class="dashboard-section" data-dashboard-section="lavagna">
    <h2 id="lavagna-app">Lavagna App</h2>
    <p class="section-kicker">Area principale per capire il progetto come flussi: React Flow, nodi, relazioni, audit e piano fix.</p>
    <section class="blueprint-panel">
      <div class="blueprint-focus">
        <div>
          <div class="hero-label">Prossimo focus lavagna</div>
          <div class="blueprint-title">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("title", blueprint_json.get("next_node", "") or "n/d"))}</div>
          <p class="muted">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("next_action", "Usa il Blueprint come intent layer prima di implementare."))}</p>
        </div>
        <div>
          <div class="chip-row">
            <span class="chip">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("health", "n/d"))}</span>
            <span class="chip">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("domain", "n/d"))}</span>
            <span class="chip warn">{esc((blueprint_json.get("doctor") or {}).get("nodes_checked", 0))} nodi</span>
          </div>
          <div class="muted" style="margin-top:10px;">Auto-update: proposte visibili qui, scrittura solo con comando esplicito.</div>
          <div class="topline">
            <form method="get" action="/blueprint-scan"><input type="hidden" name="project" value="{esc(str(monitored_project))}"><button type="submit">Scansiona nodi</button></form>
            <form method="get" action="/blueprint-import"><input type="hidden" name="project" value="{esc(str(monitored_project))}"><button type="submit">Conferma e salva Blueprint</button></form>
          </div>
        </div>
      </div>
      <h2>Lavagna App</h2>
      <p class="muted">Ogni card traduce il nodo in parole semplici: cosa fa, con chi parla e perche il collegamento esiste. Le frecce mostrano il flusso principale tra UI, backend, dati, test, runtime e documentazione.</p>
      <details>
        <summary>Wizard Design App</summary>
        <p class="muted">Compila solo quello che sai. La skill crea nodi design umani e poi mostra cosa manca rispetto al codice rilevato.</p>
        <form method="post" action="/blueprint-design" class="design-form" data-design-wizard>
          <input type="hidden" name="project" value="{esc(str(monitored_project))}">
          <div class="wide"><label>Template app</label><select name="template" data-design-template>
            <option value="custom">Custom</option>
            <option value="gestionale">Gestionale</option>
            <option value="ecommerce">Ecommerce</option>
            <option value="dashboard">Dashboard/report</option>
            <option value="booking">Booking/prenotazioni</option>
            <option value="community">Community/social</option>
            <option value="game">Gioco</option>
          </select></div>
          <div class="wide"><label>Che app vuoi creare?</label><textarea name="goal" placeholder="Esempio: gestionale ordini per piccoli negozi con login e dashboard"></textarea></div>
          <div><label>Chi la usa?</label><textarea name="users" placeholder="Cliente&#10;Admin&#10;Operatore"></textarea></div>
          <div><label>Schermate principali</label><textarea name="screens" placeholder="Home&#10;Login&#10;Dashboard&#10;Ordini"></textarea></div>
          <div><label>Azioni utente</label><textarea name="actions" placeholder="fare login&#10;creare ordine&#10;cercare cliente"></textarea></div>
          <div><label>Dati da salvare/leggere</label><textarea name="data" placeholder="Utente&#10;Ordine&#10;Cliente"></textarea></div>
          <div><label>Login, ruoli, regole</label><textarea name="auth" placeholder="Solo admin puo cancellare; utenti normali vedono solo i propri dati"></textarea></div>
          <div><label>Cosa va testato</label><textarea name="tests" placeholder="login valido&#10;creazione ordine&#10;permessi admin"></textarea></div>
          <div class="wide design-preview" data-design-preview></div>
          <div class="wide"><button type="submit">Crea design nella lavagna</button></div>
        </form>
        <script>
        (function () {{
          const form = document.querySelector('[data-design-wizard]');
          if (!form) return;
          const templates = {{
            custom: {{ goal: '', users: '', screens: '', actions: '', data: '', auth: '', tests: '' }},
            gestionale: {{ goal: 'Gestionale operativo con login, dashboard e gestione dati principali.', users: 'Admin\\nOperatore', screens: 'Login\\nDashboard\\nClienti\\nOrdini\\nImpostazioni', actions: 'fare login\\ncreare cliente\\ncreare ordine\\ncercare ordine\\naggiornare stato ordine', data: 'Utente\\nCliente\\nOrdine\\nRiga ordine', auth: 'Admin gestisce tutto; operatore vede e modifica solo le aree operative.', tests: 'login valido\\ncreazione ordine\\npermessi admin' }},
            ecommerce: {{ goal: 'Ecommerce con catalogo, carrello, checkout e gestione ordini.', users: 'Cliente\\nAdmin', screens: 'Home\\nCatalogo\\nDettaglio prodotto\\nCarrello\\nCheckout\\nArea admin', actions: 'cercare prodotto\\naggiungere al carrello\\nfare checkout\\npagare ordine\\ngestire prodotti', data: 'Utente\\nProdotto\\nCarrello\\nOrdine\\nPagamento', auth: 'Cliente compra e vede i propri ordini; admin gestisce catalogo e ordini.', tests: 'aggiunta al carrello\\ncheckout riuscito\\npermessi admin' }},
            dashboard: {{ goal: 'Dashboard/report per monitorare metriche, filtri e stato operativo.', users: 'Admin\\nAnalista\\nOperatore', screens: 'Dashboard\\nReport\\nDettaglio metrica\\nFiltri\\nEsportazione', actions: 'filtrare report\\naprire dettaglio\\nesportare dati\\naggiornare dashboard', data: 'Metrica\\nReport\\nFiltro\\nEvento', auth: 'Admin vede tutto; altri ruoli vedono solo report autorizzati.', tests: 'filtri corretti\\nexport dati\\ncaricamento dashboard' }},
            booking: {{ goal: 'App prenotazioni con disponibilita, calendario e gestione appuntamenti.', users: 'Cliente\\nStaff\\nAdmin', screens: 'Home\\nCalendario\\nPrenotazione\\nLe mie prenotazioni\\nAdmin', actions: 'vedere disponibilita\\ncreare prenotazione\\nannullare prenotazione\\nconfermare appuntamento', data: 'Utente\\nDisponibilita\\nPrenotazione\\nServizio', auth: 'Cliente gestisce le proprie prenotazioni; staff conferma appuntamenti.', tests: 'creazione prenotazione\\nannullamento\\nconflitto orario' }},
            community: {{ goal: 'Community con profili, post, commenti e moderazione.', users: 'Utente\\nModeratore\\nAdmin', screens: 'Feed\\nProfilo\\nPost\\nNotifiche\\nModerazione', actions: 'creare post\\ncommentare\\nseguire utente\\nsegnalare contenuto\\nmoderare post', data: 'Utente\\nPost\\nCommento\\nSegnalazione\\nNotifica', auth: 'Utente gestisce i propri contenuti; moderatore rimuove contenuti segnalati.', tests: 'creazione post\\ncommento\\npermessi moderatore' }},
            game: {{ goal: 'Gioco con menu, partita, progressi e punteggi.', users: 'Giocatore\\nAdmin', screens: 'Menu\\nPartita\\nClassifica\\nProfilo\\nImpostazioni', actions: 'iniziare partita\\nsalvare punteggio\\nvedere classifica\\naggiornare profilo', data: 'Giocatore\\nPartita\\nPunteggio\\nLivello', auth: 'Giocatore vede i propri progressi; admin gestisce configurazioni.', tests: 'inizio partita\\nsalvataggio punteggio\\nclassifica' }}
          }};
          function field(name) {{ return form.querySelector(`[name="${{name}}"]`); }}
          function lines(name) {{ return (field(name).value || '').split(/\\n|,|;/).map(item => item.trim()).filter(Boolean); }}
          function renderList(title, items) {{ return `<div><strong>${{title}}</strong><ul>${{(items.length ? items : ['Da chiarire']).map(item => `<li>${{item}}</li>`).join('')}}</ul></div>`; }}
          function updatePreview() {{
            const preview = form.querySelector('[data-design-preview]');
            preview.innerHTML = '<h3>Anteprima design che verra creato</h3><div class="design-preview-grid">' +
              renderList('Schermate', lines('screens')) +
              renderList('Azioni', lines('actions')) +
              renderList('API previste', lines('actions').map(item => '/' + item.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40))) +
              renderList('Dati', lines('data')) +
              renderList('Test', lines('tests')) +
              '</div>';
          }}
          field('template').addEventListener('change', event => {{
            const item = templates[event.target.value] || templates.custom;
            Object.entries(item).forEach(([key, value]) => {{ if (field(key)) field(key).value = value; }});
            updatePreview();
          }});
          Array.from(form.querySelectorAll('textarea')).forEach(item => item.addEventListener('input', updatePreview));
          updatePreview();
        }})();
        </script>
      </details>
      <div class="screenshot-drop" tabindex="0" data-screenshot-drop>
        <strong>Incolla screenshot qui</strong>
        <div class="muted">Clicca questo riquadro e premi Ctrl+V dopo aver fatto lo screenshot. Lo salvo nel server della dashboard e posso leggerlo da li.</div>
        <div class="screenshot-status" data-screenshot-status>In attesa di immagine.</div>
      </div>
      <script>
      (function () {{
        const box = document.querySelector('[data-screenshot-drop]');
        const status = document.querySelector('[data-screenshot-status]');
        if (!box || !status) return;
        box.addEventListener('paste', async (event) => {{
          const items = Array.from((event.clipboardData || {{}}).items || []);
          const imageItem = items.find(item => item.type && item.type.startsWith('image/'));
          if (!imageItem) {{
            status.textContent = 'Nessuna immagine trovata negli appunti.';
            return;
          }}
          const file = imageItem.getAsFile();
          if (!file) return;
          status.textContent = 'Caricamento screenshot...';
          try {{
            const response = await fetch('/upload-screenshot', {{
              method: 'POST',
              headers: {{ 'Content-Type': file.type || 'image/png' }},
              body: file
            }});
            const payload = await response.json();
            status.textContent = payload.ok ? `Salvato: ${{payload.path}}` : 'Upload non riuscito.';
          }} catch (error) {{
            status.textContent = 'Upload non riuscito.';
          }}
        }});
      }})();
      </script>
      {render_blueprint_graph(blueprint_json.get("doctor") or {})}
      <div class="muted">Fonti / Prove disponibili nella sidebar della lavagna quando selezioni un nodo o un collegamento.</div>
      <details>
        <summary>Dettagli tecnici lavagna</summary>
      {render_blueprint_cards(blueprint_json.get("doctor") or {})}
    <section class="grid">
      <div class="card"><div>Nodi</div><div class="metric">{esc(blueprint_json.get("nodes", 0))}</div><div class="muted">Intent layer, non fonte unica di verita</div></div>
      <div class="card"><div>Prossimo Nodo</div><div class="metric">{esc(blueprint_json.get("next_node", "") or "n/d")}</div><div class="muted">{esc("file presente" if blueprint_json.get("exists") else "anteprima import dal progetto")}</div></div>
      <div class="card"><div>Planned</div><div class="metric">{esc(blueprint_json.get("planned", 0))}</div><div class="muted">Blocked: {esc(blueprint_json.get("blocked", 0))}</div></div>
    </section>
    {render_table(blueprint_json.get("preview_nodes", []) or [], ["id", "title", "inferred_type", "domain", "status", "confidence", "tags", "source"])}
    <h2>Controllo Lavagna</h2>
    <section class="grid">
      <div class="card"><div>Nodi Controllati</div><div class="metric">{esc((blueprint_json.get("doctor") or {}).get("nodes_checked", 0))}</div><div class="muted">File scansionati: {esc((blueprint_json.get("doctor") or {}).get("files_scanned", 0))}</div></div>
      <div class="card"><div>Prossimo Focus</div><div class="metric">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("health", "n/d"))}</div><div class="muted">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("title", ""))}</div></div>
      <div class="card"><div>Azione</div><div class="muted">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("next_action", "n/d"))}</div></div>
    </section>
    <h2>Audit Precisione</h2>
    {render_table((((blueprint_json.get("doctor") or {}).get("audit") or {}).get("counts", []) or []), ["status", "nodes"])}
    {render_table((((blueprint_json.get("doctor") or {}).get("audit") or {}).get("problems", []) or [])[:12], ["title", "status", "problem", "reason", "fix", "evidence"])}
    <h2>Piano Fix Dalla Lavagna</h2>
    {render_table((((blueprint_json.get("doctor") or {}).get("audit") or {}).get("fix_plan", []) or [])[:10], ["priority", "node", "problem", "action", "why", "check"])}
    <h2>Flow Trace</h2>
    {render_table((((blueprint_json.get("doctor") or {}).get("flows") or {}).get("counts", []) or []), ["status", "flows"])}
    {render_table((((blueprint_json.get("doctor") or {}).get("flows") or {}).get("items", []) or [])[:12], ["title", "status", "problem", "chain", "next_step"])}
    {render_table(((blueprint_json.get("doctor") or {}).get("health_counts", []) or []), ["health", "nodes"])}
    {render_table(((blueprint_json.get("doctor") or {}).get("nodes", []) or [])[:24], ["id", "title", "description", "domain", "health", "test_signal", "next_action"])}
    <h2>Auto-Update Proposto</h2>
    {render_table(((blueprint_json.get("doctor") or {}).get("suggestions", []) or [])[:8], ["id", "title", "suggested_status", "confidence", "next_action"])}
    <h2>Domini Blueprint</h2>
    {render_table(blueprint_json.get("domains", []) or [], ["domain", "nodes"])}
    <details><summary>Superplan Blueprint</summary><pre>{esc(blueprint_json.get("superplan", ""))}</pre></details>
      </details>
    </section>

    </section>
    <section class="dashboard-section" data-dashboard-section="azioni">
    <h2>Azioni Progetto</h2>
    <p class="section-kicker">Task dai warning, prompt pronti, analisi progetto ed esperti consigliati.</p>
    <details open>
      <summary>Strumenti azioni progetto</summary>
    <h2>Task Automatici Dai Warning</h2>
    <div class="task-table">
      {render_table(action_pack_json.get("warning_tasks", []) or [], ["priority", "task", "why", "prompt"])}
    </div>

    <details>
      <summary>Dettagli Tecnici</summary>
      <section class="grid">
        <div class="card"><div>Validatore</div><div class="{esc(status_label(validate["returncode"]).lower())} metric">{esc(status_label(validate["returncode"]))}</div></div>
        <div class="card"><div>Self-test</div><div class="{esc(status_label(self_test["returncode"]).lower())} metric">{esc(status_label(self_test["returncode"]))}</div></div>
        <div class="card"><div>Sync installata</div><div class="{esc(status_label(sync_check["returncode"]).lower())} metric">{esc(status_label(sync_check["returncode"]))}</div></div>
        <div class="card"><div>Sessioni scansionate</div><div class="metric">{esc(analytics.get("sessions_scanned", 0))}</div><div class="muted">ultimi log locali Codex</div></div>
        <div class="card"><div>Cache Dashboard</div><div class="metric">{esc((report.get("smart_cache") or {}).get("cached_count", 0))}</div><div class="muted">Freschi: {esc((report.get("smart_cache") or {}).get("fresh_count", 0))}</div></div>
      </section>
    </details>

    <details>
      <summary>Riepilogo automatico avanzato</summary>
    <section class="grid">
      <div class="card">
        <h2>Controllo automatico</h2>
        <div class="metric">{esc(background_json.get("mode_label", "Automatico sicuro"))}</div>
        <div class="muted">Stato: {esc("attivo" if background_json.get("active") else "manuale/pausa")}</div>
        <div class="muted">Ultima scansione: {esc(background_json.get("last_scan_at", "n/d"))}</div>
        <div class="muted">Prossima: {esc(background_json.get("next_scan_hint", "n/d"))}</div>
      </div>
      <div class="card">
        <h2>Novita controllo</h2>
        <div class="metric">{esc(background_json.get("new_count", 0))}</div>
        <div class="muted">Problemi attuali: {esc(background_json.get("findings_count", 0))} | Spariti: {esc(background_json.get("resolved_count", 0))}</div>
        <div class="muted">{esc(background_json.get("safe_write_scope", ""))}</div>
      </div>
      <div class="card">
        <h2>Modalita controllo</h2>
        <div class="button-row">
          <form method="get" action="/background-mode"><input type="hidden" name="mode" value="manual"><button type="submit">Manuale</button></form>
          <form method="get" action="/background-mode"><input type="hidden" name="mode" value="safe"><button type="submit">Automatico sicuro</button></form>
          <form method="get" action="/background-mode"><input type="hidden" name="mode" value="assist"><button type="submit">Proposte assistite</button></form>
          <form method="get" action="/background-scan"><button type="submit">Scansiona ora</button></form>
        </div>
      </div>
    </section>
    </details>
    <details><summary>Controllo: nuovi problemi</summary>{render_table(background_json.get("new_findings", []) or [], ["kind", "title", "status", "problem", "reason", "fix"])}</details>
    <details><summary>Controllo: problemi spariti</summary>{render_table(background_json.get("resolved_findings", []) or [], ["kind", "title", "status", "problem", "reason"])}</details>
    <div class="card">
      <h2>Pilota Automatico</h2>
      <div class="metric">{esc(auto_pilot_json.get("next_action", "n/d"))}</div>
      <p>{esc(auto_pilot_json.get("why", ""))}</p>
      <div class="muted">Calcolato da auto_pilot.py</div>
      <div class="muted">Pianificazione: {esc(auto_pilot_json.get("planning_mode", "n/d"))} | Modalita: {esc(auto_pilot_json.get("mode", "n/d"))} | Esperto: {esc(auto_pilot_json.get("primary_expert", "n/d"))}</div>
      <div class="muted">{esc(auto_pilot_json.get("manual_override", ""))}</div>
    </div>
    <div class="grid">
      <div class="card"><div>Azione Consigliata</div><div class="muted">{esc(next(iter(pr_json.get("warnings", []) or []), "Continua con prompt operativo o test mirato."))}</div></div>
      <div class="card"><div>Modalita</div><div class="metric">{esc(copilot_json.get("budget_mode", "n/d"))}</div><div class="muted">Scelta dal Project Copilot</div></div>
      <div class="card"><div>Esperto Prioritario</div><div class="muted">{esc(((agent_json.get("suggested_experts", []) or [{}])[0] or {}).get("expert", "n/d"))}</div></div>
      <div class="card"><div>Eventi Recenti</div><div class="metric">{esc(event_log.get("events_read", 0))}</div><div class="muted">Nuovi: {esc(event_log.get("emitted_this_refresh", 0))} | Dedupe: {esc(event_log.get("deduplicated_this_refresh", 0))}</div></div>
    </div>

    <h2>Prompt pronti</h2>
    <p class="muted">Prompt pronti per lavorare con meno contesto e qualita controllata.</p>
    <div class="grid">
      {''.join(f'<div class="card"><h2>{esc(item.get("name", ""))}</h2><div class="muted">{esc(item.get("when", ""))}</div><pre>{esc(item.get("prompt", ""))}</pre></div>' for item in (action_pack_json.get("actions", []) or []))}
    </div>
    <details><summary>Prompt Esperti</summary>
      {render_table(action_pack_json.get("expert_prompts", []) or [], ["expert", "reason", "prompt"])}
    </details>

    <h2>Prossima Azione Sul Progetto</h2>
    <div class="grid">
      <div class="card"><div>Docs Audit</div><div class="metric">{esc(docs_json.get("recommended_preset", "n/d"))}</div><div class="muted">Da creare: {esc(", ".join(docs_json.get("recommended_create", []) or []) or "niente")}</div></div>
      <div class="card"><div>PR Readiness</div><div class="metric">{esc(pr_json.get("status", "n/d"))}</div><div class="muted">{esc(pr_json.get("pr_summary_draft", ""))}</div></div>
      <div class="card"><div>Warning</div><div class="metric">{esc(len(pr_json.get("warnings", []) or []))}</div><div class="muted">{esc("; ".join(pr_json.get("warnings", []) or []) or "nessuno")}</div></div>
    </div>

    <h2>Analisi progetto</h2>
    <div class="grid">
      <div class="card"><div>Tipo App</div><div class="metric">{esc(copilot_json.get("app_type", "n/d"))}</div><div class="muted">Modo consigliato: {esc(copilot_json.get("budget_mode", "n/d"))}</div></div>
      <div class="card"><div>Stack</div><div class="muted">{esc(", ".join(copilot_json.get("stack", []) or []) or "n/d")}</div></div>
      <div class="card"><div>Rischi Contesto</div><div class="muted">{esc("; ".join(copilot_json.get("context_risks", []) or []) or "nessuno")}</div></div>
    </div>
    <h2>Aree Dominanti</h2>
    {render_table(copilot_json.get("dominant_areas", []) or [], ["area", "files"])}
    <h2>Context Guardrails</h2>
    <p class="muted">File e pattern costosi da trattare con rg, heading o sezioni mirate prima di spendere contesto.</p>
    {render_table(copilot_json.get("context_guardrails", []) or [], ["target", "estimated_tokens", "rule"])}
    <h2>Workflow Consigliato</h2>
    <pre>{esc(chr(10).join("- " + item for item in (copilot_json.get("recommended_workflow", []) or [])))}</pre>
    <h2>Prompt Operativi</h2>
    <div class="grid">
      <div class="card"><h2>Analisi</h2><pre>{esc((copilot_json.get("prompts", {}) or {}).get("analysis", ""))}</pre></div>
      <div class="card"><h2>Frontend</h2><pre>{esc((copilot_json.get("prompts", {}) or {}).get("frontend", ""))}</pre></div>
      <div class="card"><h2>Backend</h2><pre>{esc((copilot_json.get("prompts", {}) or {}).get("backend", ""))}</pre></div>
      <div class="card"><h2>Review</h2><pre>{esc((copilot_json.get("prompts", {}) or {}).get("review", ""))}</pre></div>
    </div>

    <h2>Esperti consigliati</h2>
    <p class="muted">{esc(agent_json.get("note", ""))}</p>
    <div class="grid">
      <div class="card"><h2>Domini Lavoro</h2>{render_table(agent_json.get("top_domains", []) or [], ["domain", "score"])}</div>
      <div class="card"><h2>Esperti Consigliati</h2>{render_table(agent_json.get("suggested_experts", []) or [], ["expert", "reason"])}</div>
      <div class="card"><h2>Progetti Recenti</h2>{render_table(agent_json.get("top_projects", []) or [], ["name", "sessions", "tokens"])}</div>
    </div>
    <h2>Expert Feedback Loop</h2>
    <p class="muted">Segna quali esperti sono stati davvero utili. La skill usa questi eventi per capire se servono altri profili o meno rumore.</p>
    {render_expert_feedback(agent_json.get("suggested_experts", []) or [], expert_feedback_json, str(monitored_project))}
    </details>

    </section>
    <section class="dashboard-section" data-dashboard-section="diagnostica">
    <h2 id="diagnostica">Diagnostica</h2>
    <p class="section-kicker">Stato tecnico, memoria, log, consumo stimato e controlli raw. Da usare quando serve debug o audit.</p>
    <h2>Memoria progetti</h2>
    <p class="muted">Memoria locale compatta dei progetti monitorati. Serve a non ripartire da zero tra una sessione e l'altra.</p>
    {render_table(project_memory.get("projects", []) or [], ["name", "app_type", "budget_mode", "pr_status", "warnings", "experts", "last_seen", "path"])}

    <h2>Dubbi e correzioni skill</h2>
    <p class="muted">Qui la skill raccoglie dubbi, parti poco chiare e possibili errori senza chiederti di giudicare codice tecnico. Puoi segnare cosa e' confuso o sembra sbagliato: la skill lo usera come memoria di miglioramento.</p>
    <div class="grid">
      <div class="card"><div>Elementi Aperti</div><div class="metric">{esc(skill_learning.get("open_count", 0))}</div><div class="muted">Da chiarire o verificare</div></div>
      <div class="card"><h2>Tipi</h2>{render_table(skill_learning.get("by_event", []) or [], ["name", "count"])}</div>
      <div class="card"><h2>Feedback</h2>{render_table(skill_learning.get("by_outcome", []) or [], ["name", "count"])}</div>
    </div>
    {render_table(skill_learning.get("open_items", []) or [], ["timestamp", "event", "severity", "item_id", "summary", "simple_action"])}
    <details><summary>Lezioni Skill</summary>{render_table(skill_learning.get("lessons", []) or [], ["timestamp", "status", "lesson"])}</details>

    <h2>Log interni skill</h2>
    <div class="grid">
      <div class="card"><h2>Eventi</h2>{render_table(event_log.get("by_event", []) or [], ["name", "count"])}</div>
      <div class="card"><h2>Severita</h2>{render_table(event_log.get("by_severity", []) or [], ["name", "count"])}</div>
      <div class="card"><h2>Progetti</h2>{render_table(event_log.get("by_project", []) or [], ["name", "count"])}</div>
    </div>
    {render_table(event_log.get("recent", []) or [], ["timestamp", "event", "severity", "project", "message"])}

    <h2>Consigli manutenzione</h2>
    <p class="muted">Consigli generati dai log locali e dalla memoria progetti.</p>
    <div class="grid">
      <div class="card"><div>Progetti Visti</div><div class="metric">{esc(maintenance_json.get("projects_seen", 0))}</div></div>
      <div class="card"><div>Eventi Letti</div><div class="metric">{esc(maintenance_json.get("events_read", 0))}</div></div>
      <div class="card"><div>Evento Dominante</div><div class="muted">{esc(maintenance_json.get("top_event", ""))}</div></div>
    </div>
    {render_table(maintenance_json.get("recommendations", []) or [], ["priority", "area", "title", "benefit"])}
    <details open>
      <summary>Diagnostica tecnica</summary>
    <h2>Prompt Pronto Per L'Altra Chat</h2>
    <pre>{esc(project_audit.get("handoff_prompt", ""))}</pre>

    <h2>Stato Git</h2>
    <pre>{esc(git["status"]["stdout"] or "Working tree clean")}</pre>
    <pre>{esc(git["diff_stat"]["stdout"] or "No diff")}</pre>

    <h2>File E Consumo Stimato</h2>
    {render_table(files, ["path", "lines", "estimated_tokens", "bytes"])}

    <h2>Uso Skill E Sessioni Recenti</h2>
    <p class="muted">Il segnale skill e inferito dai log locali: alta = corpo/regole skill viste, media = file contesto usati, bassa = solo metadata/nome skill.</p>
    {render_table(sessions, ["timestamp", "project", "model", "skill_signal", "reason", "input_tokens", "output_tokens", "total_tokens", "tool_calls", "top_tools"]) if sessions else "<p class='muted'>Nessun dato token recente trovato nei log locali.</p>"}

    <h2>Cosa Viene Usato Di Piu</h2>
    <div class="grid">
      <div class="card"><h2>Comandi</h2>{render_table(analytics.get("top_commands", []), ["name", "count"])}</div>
      <div class="card"><h2>Progetti</h2>{render_table(analytics.get("top_projects", []), ["name", "count"])}</div>
      <div class="card"><h2>Segnale Skill</h2>{render_table(analytics.get("skill_confidence", []), ["name", "count"])}</div>
    </div>

    <h2>Log Test</h2>
    <details><summary>Validatore</summary><pre>{esc(validate["stdout"])}{chr(10)}{esc(validate["stderr"])}</pre></details>
    <details><summary>Self-test</summary><pre>{esc(self_test["stdout"])}{chr(10)}{esc(self_test["stderr"])}</pre></details>
    <details><summary>Sync Check</summary><pre>{esc(sync_check["stdout"])}{chr(10)}{esc(sync_check["stderr"])}</pre></details>

    <h2>Audit Operativi</h2>
    <details><summary>Context Budget Scan</summary><pre>{esc(context_scan["stdout"])}{chr(10)}{esc(context_scan["stderr"])}</pre></details>
    <details><summary>External Skill Intake</summary><pre>{esc(skill_intake["stdout"])}{chr(10)}{esc(skill_intake["stderr"])}</pre></details>
    <details><summary>Project Context Bootstrap Preview</summary><pre>{esc(bootstrap_preview["stdout"])}{chr(10)}{esc(bootstrap_preview["stderr"])}</pre></details>
    <details><summary>Project Docs Audit</summary><pre>{esc(docs_audit["stdout"])}{chr(10)}{esc(docs_audit["stderr"])}</pre></details>
    <details><summary>PR Readiness</summary><pre>{esc(pr_readiness["stdout"])}{chr(10)}{esc(pr_readiness["stderr"])}</pre></details>
    <details><summary>Project Copilot Raw</summary><pre>{esc(checks["project_copilot"]["stdout"])}{chr(10)}{esc(checks["project_copilot"]["stderr"])}</pre></details>
    <details><summary>Agent Activity Raw</summary><pre>{esc(checks["agent_activity"]["stdout"])}{chr(10)}{esc(checks["agent_activity"]["stderr"])}</pre></details>
    <details><summary>Action Pack Raw</summary><pre>{esc(checks["action_pack"]["stdout"])}{chr(10)}{esc(checks["action_pack"]["stderr"])}</pre></details>
    <details><summary>Maintenance Advisor Raw</summary><pre>{esc(checks["maintenance_advisor"]["stdout"])}{chr(10)}{esc(checks["maintenance_advisor"]["stderr"])}</pre></details>
    <details><summary>Expert Feedback Raw</summary><pre>{esc(checks["expert_feedback"]["stdout"])}{chr(10)}{esc(checks["expert_feedback"]["stderr"])}</pre></details>

    <h2>Ultima Release</h2>
    <pre>{esc(report["latest_release"])}</pre>

    <h2>Ultimo Miglioramento</h2>
    <pre>{esc(report["latest_improvement"])}</pre>
    </details>
    </section>

    <p class="muted">Nota: le stime token sono proxy locali, non costi di fatturazione.</p>
  </main>
  <script>
    (() => {{
      const buttons = [...document.querySelectorAll('[data-dashboard-tab]')];
      const sections = [...document.querySelectorAll('[data-dashboard-section]')];
      const aliases = {{
        'lavagna-app': 'lavagna',
        'automazione': 'automazione',
        'diagnostica': 'diagnostica',
        'home-progetto': 'home'
      }};
      function activate(name, updateHash = true) {{
        const target = name || 'home';
        buttons.forEach((button) => button.classList.toggle('is-active', button.dataset.dashboardTab === target));
        sections.forEach((section) => section.classList.toggle('is-active', section.dataset.dashboardSection === target));
        if (updateHash) {{
          history.replaceState(null, '', `#${{target}}`);
        }}
      }}
      buttons.forEach((button) => button.addEventListener('click', () => activate(button.dataset.dashboardTab)));
      document.querySelectorAll('a[href^="#"]').forEach((link) => {{
        link.addEventListener('click', () => {{
          const key = link.getAttribute('href').slice(1);
          if (aliases[key]) activate(aliases[key]);
        }});
      }});
      const initial = location.hash.slice(1);
      activate(aliases[initial] || initial || 'home', false);
    }})();
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(REPORTS / "skill-dashboard.html"))
    parser.add_argument("--json", default=str(REPORTS / "skill-dashboard.json"))
    parser.add_argument("--refresh", type=int, default=0, help="Add browser auto-refresh in seconds.")
    parser.add_argument("--project", help="Project path to monitor in operational checks.")
    parser.add_argument("--save-config", action="store_true", help="Persist --project into reports/dashboard-config.json.")
    parser.add_argument("--pretty-json", action="store_true", help="Write pretty full JSON instead of compact dashboard JSON.")
    args = parser.parse_args()

    report = build_report(args.project, args.save_config)
    output = Path(args.output)
    json_output = Path(args.json)
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(report, args.refresh or None), encoding="utf-8")
    json_data = report if args.pretty_json else compact_report(report)
    if args.pretty_json:
        json_output.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    else:
        json_output.write_text(json.dumps(json_data, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {json_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
