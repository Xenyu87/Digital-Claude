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
    load_config,
    project_root,
    save_config,
)
from dashboard_sessions import codex_sessions
from event_log import emit_event, summarize_events
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


def cache_key(name: str, project: Path, cmd: list[str]) -> str:
    return "|".join([name, str(project.resolve()), " ".join(cmd)])


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
    selected_project = str(monitored_project.resolve())
    if not any(str(item.get("path")) == selected_project for item in discovered_projects):
        discovered_projects.insert(
            0,
            {
                "name": monitored_project.name,
                "path": selected_project,
                "sessions": 0,
                "last_seen": "",
                "has_ai_context": (monitored_project / "AI_CONTEXT.md").exists(),
                "has_agents": (monitored_project / "AGENTS.md").exists(),
                "is_git": (monitored_project / ".git").exists(),
            },
        )
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
            "auto_pilot": auto_pilot_json,
            "handoff_prompt": build_handoff_prompt(monitored_project, docs_audit_json, pr_readiness_json),
        },
        "auto_pilot": auto_pilot_json,
        "project_memory": {"path": str(ROOT / "reports" / "projects-state.json"), "projects": memory_table(memory)},
        "expert_feedback": expert_feedback_json or {},
        "blueprint_board": blueprint_board_json or {},
        "event_log": event_summary,
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
    blueprint["doctor"] = doctor
    blueprint["preview_nodes"] = (blueprint.get("preview_nodes") or [])[:12]
    return {
        "generated_at": report.get("generated_at"),
        "root": report.get("root"),
        "monitored_project": report.get("monitored_project"),
        "config": report.get("config"),
        "project_audit": {**(report.get("project_audit") or {}), "blueprint_board": blueprint},
        "blueprint_board": blueprint,
        "auto_pilot": report.get("auto_pilot"),
        "project_memory": report.get("project_memory"),
        "expert_feedback": report.get("expert_feedback"),
        "event_log": report.get("event_log"),
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
    auto_pilot_json = report.get("auto_pilot") or project_audit.get("auto_pilot") or {}
    project_memory = report["project_memory"]
    event_log = report["event_log"]
    files = report["files"]
    git = report["git"]
    refresh_tag = f'<meta http-equiv="refresh" content="{refresh_seconds}">' if refresh_seconds else ""
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  {refresh_tag}
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
    <h2>Vista Semplice</h2>
    <section class="simple-view">
      <div class="hero-card">
        <div class="hero-label">Cosa fare ora</div>
        <div class="hero-action">{esc(auto_pilot_json.get("next_action", "n/d"))}</div>
        <div class="hero-reason">{esc(auto_pilot_json.get("why", ""))}</div>
        <div class="topline">
          <span class="badge">Esperto: {esc(auto_pilot_json.get("primary_expert", "n/d"))}</span>
          <span class="badge">Stato PR: {esc(pr_json.get("status", "n/d"))}</span>
          <span class="badge">Task: {esc(len(action_pack_json.get("warning_tasks", []) or []))}</span>
        </div>
      </div>
      <div class="quick-grid">
        <div class="quick-card"><div class="muted">Pianificazione</div><strong>{esc(auto_pilot_json.get("planning_mode", "n/d"))}</strong><div class="muted">Diretto, piano focalizzato o Superplan</div></div>
        <div class="quick-card"><div class="muted">Progetto</div><strong>{esc(Path(str(monitored_project)).name)}</strong><div class="muted">{esc(pr_json.get("pr_summary_draft", ""))}</div></div>
        <div class="quick-card"><div class="muted">Contesto</div><strong>{esc(len(copilot_json.get("context_guardrails", []) or []))}</strong><div class="muted">guardrail attivi</div></div>
        <div class="quick-card"><div class="muted">Cache</div><strong>{esc((report.get("smart_cache") or {}).get("cached_count", 0))}/{esc(((report.get("smart_cache") or {}).get("cached_count", 0)) + ((report.get("smart_cache") or {}).get("fresh_count", 0)))}</strong><div class="muted">controlli riusati, TTL {esc((report.get("smart_cache") or {}).get("ttl_seconds", 0))}s</div></div>
      </div>
    </section>

    <h2>Blueprint Board</h2>
    <section class="blueprint-panel">
      <div class="blueprint-focus">
        <div>
          <div class="hero-label">Prossimo focus Blueprint</div>
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
      <h2>Lavagna Blueprint</h2>
      {render_blueprint_graph(blueprint_json.get("doctor") or {})}
      {render_blueprint_cards(blueprint_json.get("doctor") or {})}
    </section>
    <section class="grid">
      <div class="card"><div>Nodi</div><div class="metric">{esc(blueprint_json.get("nodes", 0))}</div><div class="muted">Intent layer, non fonte unica di verita</div></div>
      <div class="card"><div>Prossimo Nodo</div><div class="metric">{esc(blueprint_json.get("next_node", "") or "n/d")}</div><div class="muted">{esc("file presente" if blueprint_json.get("exists") else "anteprima import dal progetto")}</div></div>
      <div class="card"><div>Planned</div><div class="metric">{esc(blueprint_json.get("planned", 0))}</div><div class="muted">Blocked: {esc(blueprint_json.get("blocked", 0))}</div></div>
    </section>
    {render_table(blueprint_json.get("preview_nodes", []) or [], ["id", "title", "inferred_type", "domain", "status", "confidence", "tags", "source"])}
    <h2>Blueprint Doctor</h2>
    <section class="grid">
      <div class="card"><div>Nodi Controllati</div><div class="metric">{esc((blueprint_json.get("doctor") or {}).get("nodes_checked", 0))}</div><div class="muted">File scansionati: {esc((blueprint_json.get("doctor") or {}).get("files_scanned", 0))}</div></div>
      <div class="card"><div>Prossimo Focus</div><div class="metric">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("health", "n/d"))}</div><div class="muted">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("title", ""))}</div></div>
      <div class="card"><div>Azione</div><div class="muted">{esc(((blueprint_json.get("doctor") or {}).get("next_focus") or {}).get("next_action", "n/d"))}</div></div>
    </section>
    {render_table(((blueprint_json.get("doctor") or {}).get("health_counts", []) or []), ["health", "nodes"])}
    {render_table(((blueprint_json.get("doctor") or {}).get("nodes", []) or [])[:24], ["id", "title", "description", "domain", "health", "test_signal", "next_action"])}
    <h2>Auto-Update Proposto</h2>
    {render_table(((blueprint_json.get("doctor") or {}).get("suggestions", []) or [])[:8], ["id", "title", "suggested_status", "confidence", "next_action"])}
    <h2>Domini Blueprint</h2>
    {render_table(blueprint_json.get("domains", []) or [], ["domain", "nodes"])}
    <details><summary>Superplan Blueprint</summary><pre>{esc(blueprint_json.get("superplan", ""))}</pre></details>

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

    <h2>Overview Operativa</h2>
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

    <h2>Action Pack</h2>
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

    <h2>Project Copilot</h2>
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

    <h2>Agent / Expert Analytics</h2>
    <p class="muted">{esc(agent_json.get("note", ""))}</p>
    <div class="grid">
      <div class="card"><h2>Domini Lavoro</h2>{render_table(agent_json.get("top_domains", []) or [], ["domain", "score"])}</div>
      <div class="card"><h2>Esperti Consigliati</h2>{render_table(agent_json.get("suggested_experts", []) or [], ["expert", "reason"])}</div>
      <div class="card"><h2>Progetti Recenti</h2>{render_table(agent_json.get("top_projects", []) or [], ["name", "sessions", "tokens"])}</div>
    </div>
    <h2>Expert Feedback Loop</h2>
    <p class="muted">Segna quali esperti sono stati davvero utili. La skill usa questi eventi per capire se servono altri profili o meno rumore.</p>
    {render_expert_feedback(agent_json.get("suggested_experts", []) or [], expert_feedback_json, str(monitored_project))}

    <h2>Project Memory</h2>
    <p class="muted">Memoria locale compatta dei progetti monitorati. Serve a non ripartire da zero tra una sessione e l'altra.</p>
    {render_table(project_memory.get("projects", []) or [], ["name", "app_type", "budget_mode", "pr_status", "warnings", "experts", "last_seen", "path"])}

    <h2>Skill Event Log</h2>
    <div class="grid">
      <div class="card"><h2>Eventi</h2>{render_table(event_log.get("by_event", []) or [], ["name", "count"])}</div>
      <div class="card"><h2>Severita</h2>{render_table(event_log.get("by_severity", []) or [], ["name", "count"])}</div>
      <div class="card"><h2>Progetti</h2>{render_table(event_log.get("by_project", []) or [], ["name", "count"])}</div>
    </div>
    {render_table(event_log.get("recent", []) or [], ["timestamp", "event", "severity", "project", "message"])}

    <h2>Maintenance Advisor</h2>
    <p class="muted">Consigli generati dai log locali e dalla memoria progetti.</p>
    <div class="grid">
      <div class="card"><div>Progetti Visti</div><div class="metric">{esc(maintenance_json.get("projects_seen", 0))}</div></div>
      <div class="card"><div>Eventi Letti</div><div class="metric">{esc(maintenance_json.get("events_read", 0))}</div></div>
      <div class="card"><div>Evento Dominante</div><div class="muted">{esc(maintenance_json.get("top_event", ""))}</div></div>
    </div>
    {render_table(maintenance_json.get("recommendations", []) or [], ["priority", "area", "title", "benefit"])}

    <h2>Scegli Progetto Da Monitorare</h2>
    <p class="muted">I progetti qui sotto vengono scoperti dai log locali Codex. Per un progetto nuovo mai usato, incolla il percorso una sola volta.</p>
    <form method="get" action="/select-project">
      <input type="text" name="path" value="{esc(monitored_project)}" placeholder="C:\\Percorso\\Del\\Progetto">
      <button type="submit">Monitora Questo Percorso</button>
    </form>
    {render_project_selector(discovered_projects, str(monitored_project))}

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

    <p class="muted">Nota: le stime token sono proxy locali, non costi di fatturazione.</p>
  </main>
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
