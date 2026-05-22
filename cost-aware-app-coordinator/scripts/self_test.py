#!/usr/bin/env python3
"""Run behavioral self-tests for the cost-aware app coordinator skill.

This complements validate_skill.py: it checks that important workflow rules stay
present after maintenance, without loading the whole skill into an agent context.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
MAX_SKILL_LINES = 350
MAX_REFERENCE_LINES = 120
REFERENCE_LINE_LIMIT_OVERRIDES = {
    "release-notes.md": 200,
}


REQUIRED_MARKERS = {
    "SKILL.md": [
        "Fast path",
        "Progressive loading",
        "Definition of Done",
        "miglioramento skill",
        "AGENTS.md",
        "AI_CONTEXT.md",
    ],
    "references/response-economy.md": [
        "Response Economy",
        "Formato base routine",
        "Cosa evitare",
    ],
    "references/maintenance-compaction.md": [
        "Maintenance Compaction",
        "compression-pass.md",
    ],
    "references/agent-handoff.md": [
        "Agent Handoff",
        "Comunicazione tramite file versionati",
        "Cosa NON mettere in AI_HANDOFF.md",
    ],
    "references/skill-sync.md": [
        "Skill Sync",
        "sync_skill.py",
        "validate_skill.py",
    ],
    "references/project-context-template.md": [
        "Template: AI_CONTEXT.md",
        "assets/templates/AI_CONTEXT.md",
    ],
    "references/release-notes.md": [
        "Release Notes",
    ],
    "references/improvement-log.md": [
        "Improvement Log",
    ],
    "scripts/generate_dashboard.py": [
        "skill_signal",
        "top_commands",
        "sessions_scanned",
        "context_budget_scan.py",
        "external_skill_intake.py",
        "sync_check.py",
        "bootstrap_project_context.py",
        "project_docs_audit.py",
        "pr_readiness_check.py",
        "dashboard-config.json",
        "handoff_prompt",
        "discovered_projects",
        "render_project_selector",
        "project_copilot.py",
        "agent_activity_analyzer.py",
        "project_root",
        "event_log",
        "projects-state.json",
        "<details><summary>",
        "action_pack.py",
        "Prompt pronti",
        "dashboard_components",
        "render_blueprint_cards",
        "render_blueprint_graph",
        "dashboard_projects",
        "dashboard_sessions",
        "compact_report",
        "--pretty-json",
        "deduplicated_this_refresh",
        "maintenance_advisor.py",
        "Consigli manutenzione",
        "Context Guardrails",
        "expert_feedback.py",
        "Expert Feedback Loop",
        "auto_pilot.py",
        "Pilota Automatico",
        "Home Progetto",
        "Cosa devo fare in questo progetto",
        "project_guidance",
        "Dove guardare:",
        "Perche conta:",
        "Cosa fare:",
        "Task Automatici Dai Warning",
        "Dettagli Tecnici",
        "dashboard-cache.json",
        "cached_run_json",
        "DEFAULT_CACHE_SECONDS",
        "cache_summary",
        "cached_count",
        "blueprint_board.py",
        "Lavagna App",
        "data-dashboard-tab",
        "data-dashboard-section",
        "Controllo Lavagna",
        "Prossimo task dalla lavagna",
        "Scansiona progetto",
        "Salva Blueprint",
        "Lavagna App",
        "Audit Precisione",
        "Piano Fix Dalla Lavagna",
        "Flow Trace",
        "Fonti e prove",
        "Controllo Automatico",
        "Automazione Runner",
        "Impostazioni avanzate runner",
        "Modo esecuzione",
        "Endpoint locale",
        "Autonomia",
        "RAM server",
        "Ripresa Lavoro",
        "Prompt di ripresa task",
        "background_sentinel",
        "/background-mode",
        "/background-scan",
        "/runner-start",
        "/runner-config",
    ],
    "scripts/auto_pilot.py": [
        "auto_enabled",
        "next_action",
        "planning_mode",
        "manual_override",
        "decide",
    ],
    "scripts/maintenance_advisor.py": [
        "recommendations",
        "large_file_detected",
        "expert_suggested",
        "has_context_guardrails",
        "Review expert feedback trends",
    ],
    "scripts/dashboard_components.py": [
        "DASHBOARD_CSS",
        "hero-card",
        "simple-view",
        "render_project_selector",
        "render_table",
        "render_blueprint_cards",
        "render_blueprint_graph",
        "build_blueprint_view_model",
        "blueprint-view-v1",
        "render_expert_feedback",
        "blueprint-panel",
        "blueprint-map",
        "button-row",
        "guidance-board",
        "issue-card",
        "project-switcher",
        "project-menu",
        "node-card",
        "node-desc",
    ],
    "scripts/dashboard_projects.py": [
        "recent_project_from_logs",
        "is_skill_workspace",
        "project_root",
        "background_mode",
        "PROJECTS_DIRS",
        "lxc_projects",
        "merge_project_rows",
        "project_row",
    ],
    "scripts/background_sentinel.py": [
        "Background Sentinel",
        "update_sentinel",
        "current_findings",
        "background-status.json",
        "background-findings.json",
    ],
    "scripts/persistent_runner.py": [
        "runner-status.json",
        "runner-queue.json",
        "runner-config.json",
        "runner_config",
        "update_runner_config",
        "execution_mode",
        "routing_policy",
        "local_endpoint",
        "local_model",
        "cloud_model",
        "EXECUTION_MODES",
        "AUTONOMY_LEVELS",
        "LOCAL_LLM_MODES",
        "codex_cli_session",
        "start_runner",
        "stop_runner",
        "pause_runner",
        "run_once",
        "ai_enabled",
        "token_budget_limit",
        "loop_guard_max_same_job",
    ],
    "scripts/task_checkpoint.py": [
        "coordinator-task.json",
        "resume_prompt",
        "checkpoint",
        "start_task",
        "complete_task",
    ],
    "scripts/bootstrap_project_context.py": [
        "AI_RESUME.md",
        "cheap \"latest state\" entry point",
        "AI_RESUME",
        "MINIMAL_FILES",
    ],
    "scripts/update_ai_resume.py": [
        "AI_RESUME.md",
        "MAX_STATUS_ITEMS",
        "Recent Commits",
        "Read Next Only If Needed",
        "AI_HANDOFF.md",
    ],
    "scripts/telegram_notify.py": [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "runner-secrets.env",
        "token_configured",
        "discover_chats",
        "chats",
        "send-test",
    ],
    "scripts/dashboard_sessions.py": [
        "codex_sessions",
        "MAX_SESSION_TEXT_CHARS",
        "session_confidence",
        "short_command",
    ],
    "scripts/action_pack.py": [
        "build_actions",
        "warning_tasks",
        "superplan_prompt",
        "ACTION_PACK_SESSION_LIMIT",
        "expert_prompt",
        "Vertical Slice Full-stack",
        "Esperto Prioritario",
        "Context Guardrails",
        "Superplan",
    ],
    "scripts/event_log.py": [
        "emit_event",
        "summarize_events",
        "skill-events.jsonl",
        "rotate_events",
        "MAX_EVENT_LINES",
        "DEFAULT_DEDUP_SECONDS",
        "should_skip_duplicate",
    ],
    "scripts/skill_learning.py": [
        "record_learning",
        "summarize_learning",
        "learning_feedback",
        "scanner_uncertain_edge",
        "simple_action",
    ],
    "scripts/project_memory.py": [
        "update_memory",
        "projects-state.json",
        "suggested_experts",
        "context_guardrails",
    ],
    "scripts/dashboard_smoke_test.py": [
        "Memoria progetti",
        "Log interni skill",
        "Dashboard smoke-test passed",
        "MAX_COMPACT_JSON_BYTES",
        "Consigli manutenzione",
        "Expert Feedback Loop",
        "Pilota Automatico",
        "Home Progetto",
        "Task Automatici Dai Warning",
        "Dettagli Tecnici",
        "Lavagna App",
        "Auto-Update Proposto",
        "Scansiona progetto",
        "Salva Blueprint",
        "Prossimo passo:",
        "Lavagna App",
        "data-blueprint-flow-root",
    ],
    "frontend/blueprint-flow/src/main.jsx": [
        "Prossima azione",
        "boardPrimaryAction",
        "Strumenti mappa",
        "Trasforma in task Codex",
        "blueprintView",
        "taskPrompt",
        "Rumore noto",
    ],
    "scripts/test_all.py": [
        "Run the full local verification suite",
        "validate_skill",
        "self_test",
        "blueprint_board",
        "dashboard_smoke",
        "test-all-report.json",
        "RESULT",
    ],
    "scripts/blueprint_board.py": [
        "Blueprint Board Core",
        "app-blueprint.json",
        "SCHEMA_VERSION",
        "node_description",
        "infer_domain",
        "infer_tags",
        "implementation_steps",
        "feature_candidates",
        "human_title",
        "imported-inferred",
        "seed_blueprint",
        "apply_design_wizard",
        "origin",
        "ui_route",
        "seed_titles",
        "Project Overview",
        "doctor",
        "node_doctor",
        "auto_update",
        "update_suggestion",
        "suggested_status",
        "health_counts",
        "attach_audit_status",
        "audit_summary",
        "audit_fix_plan",
        "build_flow_traces",
        "apply_edge_feedback",
        "edge_key",
        "audit_problem",
        "auto-update",
        "import-project",
        "add-node",
        "superplan",
        "validate_blueprint",
        "INTERNAL_UI_LABELS",
        "is_internal_ui_control",
        "node_focus_rank",
    ],
    "scripts/blueprint_board_test.py": [
        "Blueprint Board fixture-test passed",
        "auth inference failed",
        "infra inference failed",
        "implementation steps missing",
        "doctor checked no nodes",
        "auto-update applied no metadata",
        "smart import missed component",
        "smart import missed route",
        "seed missed login",
        "seed missed dashboard",
    ],
    "scripts/analyzer_fixture_test.py": [
        "FullStackFixture",
        "Analyzer fixture-test passed",
        "full-stack app",
    ],
    "scripts/project_copilot.py": [
        "budget_mode",
        "dominant_areas",
        "recommended_workflow",
        "prompts",
        "context_guardrails",
    ],
    "scripts/agent_activity_analyzer.py": [
        "suggested_experts",
        "top_domains",
        "Context optimizer",
        "Inferred from local Codex logs",
    ],
    "scripts/serve_dashboard.py": [
        "ThreadingHTTPServer",
        "--host",
        "--interval",
        "/select-project",
        "path_manual",
        "/blueprint-scan",
        "/blueprint-import",
        "/blueprint-design",
        "clear_dashboard_cache",
        "/expert-feedback",
        "/learning-feedback",
        "/upload-screenshot",
        "/blueprint-layout",
        "/runner-start",
        "/runner-stop",
        "/runner-pause",
        "/runner-run-once",
        "/runner-enqueue",
        "/runner-config",
        "save_blueprint_layout",
        "MAX_UPLOAD_BYTES",
        "urllib.parse",
    ],
    "scripts/expert_feedback.py": [
        "record_feedback",
        "summarize_feedback",
        "expert_used",
        "expert_ignored",
    ],
    "scripts/start_dashboard.ps1": [
        "serve_dashboard.py",
        "dashboard-config.json",
        "auto dai log Codex",
    ],
    "scripts/stop_dashboard.ps1": [
        "serve_dashboard.py",
        "Stop-Process",
    ],
    "scripts/install_dashboard_service.sh": [
        "codex-skill-dashboard",
        "0.0.0.0",
        "PORT=\"${PORT:-3002}\"",
        "systemctl enable",
        "serve_dashboard.py --host",
    ],
    "scripts/manage_dashboard.sh": [
        "start|stop|restart|status",
        "journalctl",
        "test_all.py",
        "url",
    ],
    "scripts/sync_check.py": [
        "missing_in_installed",
        "extra_in_installed",
    ],
    "scripts/context_budget_scan.py": [
        "Text context risks",
        "EXCLUDED_DIRS",
    ],
    "scripts/external_skill_intake.py": [
        "Risk flags",
        "RISK_PATTERNS",
    ],
    "scripts/bootstrap_project_context.py": [
        "AGENTS.md",
        "AI_CONTEXT.md",
        "--dry-run",
        "--overwrite",
        "minimal-existing",
        "Additional Existing Docs",
        "mature-existing-docs",
    ],
    "scripts/project_docs_audit.py": [
        "recommended_preset",
        "mature-existing-docs",
        "bootstrap_command",
    ],
    "scripts/pr_readiness_check.py": [
        "PR readiness",
        "risky_files",
        "recommended_checks",
        "pr_summary_draft",
        "stdout.rstrip",
    ],
    "reports/local-dashboard-commands.md": [
        "Avvio In Background",
        "Fermare Il Server",
        "Proxmox",
        "Creare Contesto AI",
        "mature-existing-docs",
        "start_dashboard.ps1",
        "scoperti automaticamente",
        "Project Copilot",
        "Agent / Expert Analytics",
        "Skill Event Log",
        "Project Memory",
        "analyzer_fixture_test.py",
        "Action Pack",
    ],
    "reports/security-and-permissions.md": [
        "What The Scripts Can Do",
        "Before Sharing Or Publishing",
    ],
}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def run_validator(errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_skill.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        add_error(errors, "validate_skill.py failed:\n" + result.stdout + result.stderr)


def check_markers(errors: list[str]) -> None:
    for rel, markers in REQUIRED_MARKERS.items():
        text = read(rel)
        for marker in markers:
            if marker not in text:
                add_error(errors, f"{rel} missing marker: {marker}")


def check_line_budgets(errors: list[str]) -> None:
    skill_lines = line_count(ROOT / "SKILL.md")
    if skill_lines > MAX_SKILL_LINES:
        add_error(errors, f"SKILL.md has {skill_lines} lines; max is {MAX_SKILL_LINES}")

    for ref in sorted(REFERENCES.glob("*.md")):
        count = line_count(ref)
        limit = REFERENCE_LINE_LIMIT_OVERRIDES.get(ref.name, MAX_REFERENCE_LINES)
        if count > limit:
            add_error(
                errors,
                f"references/{ref.name} has {count} lines; max is {limit}",
            )


def check_installed_copy(warnings: list[str]) -> None:
    installed = Path.home() / ".codex" / "skills" / ROOT.name
    if not installed.exists():
        warnings.append("Installed copy not found.")
        return

    source_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    installed_skill = (installed / "SKILL.md").read_text(encoding="utf-8")
    if source_skill != installed_skill:
        warnings.append(f"Installed copy may be stale: {installed}")


def report(errors: list[str], warnings: list[str]) -> int:
    for warning in warnings:
        print(f"Warning: {warning}")
    if errors:
        print("Skill self-test failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Skill self-test passed.")
    return 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    run_validator(errors)
    check_line_budgets(errors)
    check_markers(errors)
    check_installed_copy(warnings)
    return report(errors, warnings)


if __name__ == "__main__":
    sys.exit(main())
