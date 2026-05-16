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


REQUIRED_MARKERS = {
    "SKILL.md": [
        "Before noisy commands",
        "cheap review path",
        "external skills, plugins, MCP servers, and remote agents",
        "External skill or remote-agent setup",
        "AGENTS.md` portable",
    ],
    "references/response-economy.md": [
        "Tool Output Budget",
        "recursive dumps",
    ],
    "references/maintenance-compaction.md": [
        "Cheap Skill Review",
    ],
    "references/agent-handoff.md": [
        "Remote Agent Handoff",
        "acceptance criteria",
        "do-not-touch",
    ],
    "references/skill-sync.md": [
        "External Skill Intake",
        "Treat stars and popularity as discovery signals",
        "self_test.py",
        "serve_dashboard.py",
        "test_all.py",
    ],
    "references/project-context-template.md": [
        "portable across Codex",
        "GitHub agents",
        "untrusted until reviewed",
    ],
    "references/release-notes.md": [
        "v0.77.0",
    ],
    "references/improvement-log.md": [
        "v0.77",
    ],
    "SKILL.md": [
        "Feature-Only Default And Planning Gate",
        "treat the feature request as sufficient input",
        "Superplan before implementation",
        "Keep manual controls optional",
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
        "Action Pack",
        "dashboard_components",
        "render_blueprint_cards",
        "render_blueprint_graph",
        "dashboard_projects",
        "dashboard_sessions",
        "compact_report",
        "--pretty-json",
        "deduplicated_this_refresh",
        "maintenance_advisor.py",
        "Maintenance Advisor",
        "Context Guardrails",
        "expert_feedback.py",
        "Expert Feedback Loop",
        "auto_pilot.py",
        "Pilota Automatico",
        "Vista Semplice",
        "Task Automatici Dai Warning",
        "Dettagli Tecnici",
        "dashboard-cache.json",
        "cached_run_json",
        "DEFAULT_CACHE_SECONDS",
        "cache_summary",
        "cached_count",
        "blueprint_board.py",
        "Blueprint Board",
        "Blueprint Doctor",
        "Prossimo focus Blueprint",
        "Scansiona nodi",
        "Conferma e salva Blueprint",
        "Lavagna Blueprint",
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
        "render_expert_feedback",
        "blueprint-panel",
        "blueprint-map",
        "node-card",
        "node-desc",
    ],
    "scripts/dashboard_projects.py": [
        "recent_project_from_logs",
        "is_skill_workspace",
        "project_root",
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
    "scripts/project_memory.py": [
        "update_memory",
        "projects-state.json",
        "suggested_experts",
        "context_guardrails",
    ],
    "scripts/dashboard_smoke_test.py": [
        "Project Memory",
        "Skill Event Log",
        "Dashboard smoke-test passed",
        "MAX_COMPACT_JSON_BYTES",
        "Maintenance Advisor",
        "Expert Feedback Loop",
        "Pilota Automatico",
        "Vista Semplice",
        "Task Automatici Dai Warning",
        "Dettagli Tecnici",
        "Blueprint Board",
        "Auto-Update Proposto",
        "Scansiona nodi",
        "Conferma e salva Blueprint",
        "Prossimo passo:",
        "Lavagna Blueprint",
        "Blueprint graph",
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
        "seed_titles",
        "Project Overview",
        "doctor",
        "node_doctor",
        "auto_update",
        "update_suggestion",
        "suggested_status",
        "health_counts",
        "auto-update",
        "import-project",
        "add-node",
        "superplan",
        "validate_blueprint",
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
        "/blueprint-scan",
        "/blueprint-import",
        "clear_dashboard_cache",
        "/expert-feedback",
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
        "systemctl enable",
        "serve_dashboard.py --host",
    ],
    "scripts/manage_dashboard.sh": [
        "start|stop|restart|status",
        "journalctl",
        "test_all.py",
        "url",
    ],
    "reports/proxmox-codex-dashboard.md": [
        "LXC dev",
        "/root/.codex/skills/cost-aware-app-coordinator",
        "codex-skill-dashboard.service",
        "192.168.1.148:8765",
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
        if count > MAX_REFERENCE_LINES:
            add_error(
                errors,
                f"references/{ref.name} has {count} lines; max is {MAX_REFERENCE_LINES}",
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
