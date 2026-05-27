#!/usr/bin/env python3
"""Fixture test for Blueprint Board Core."""

from __future__ import annotations

import tempfile
from pathlib import Path

from skill_learning import record_learning
from blueprint_board import BLUEPRINT_FILE, add_node, apply_design_wizard, auto_update, board_summary, doctor, edge_key, import_project, is_internal_ui_control, load_blueprint, make_node, save_blueprint, seed_blueprint, superplan


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "DemoApp"
        (project / "frontend" / "src" / "components").mkdir(parents=True)
        (project / "backend" / "src" / "routes").mkdir(parents=True)
        (project / "backend" / "src" / "services" / "__tests__").mkdir(parents=True)
        (project / "docs").mkdir()
        (project / "backend" / "src" / "routes" / "loginRoute.js").write_text("router.post('/login', login);\n", encoding="utf-8")
        (project / "backend" / "src" / "services" / "__tests__" / "login.test.js").write_text("test('login', () => {});\n", encoding="utf-8")
        (project / "frontend" / "src" / "components" / "AdminDashboard.jsx").write_text(
            """
export function AdminDashboard() {
  fetch('/login', { method: 'POST', body: JSON.stringify({email}) })
  function saveOrder() { fetch('/orders', { method: 'POST', body: JSON.stringify({email}) }) }
  function exportCsv() { window.location.href = '/orders/export' }
  return <>
    <button onClick={saveOrder}>Salva ordine</button>
    <button onClick={() => router.push('/reports')}>Apri report</button>
    <button onClick={exportCsv}>Esporta CSV</button>
    <button onClick={() => setFilters(open)}>Filtra ordini</button>
    <RevenueChart data={orders} />
  </>
}
function RevenueChart({ data }) {
  return <LineChart data={data}><XAxis dataKey="month" /><YAxis /><Tooltip /></LineChart>
}
""",
            encoding="utf-8",
        )
        (project / "frontend" / "src" / "components" / "BoardToolbar.jsx").write_text("export function BoardToolbar() { return <><button>Zoom -</button><button>Reset vista</button><form action='/api'><button>Monitora</button></form></> }\n", encoding="utf-8")
        data = load_blueprint(project)
        login = add_node(data, make_node("Login con email e Google"))
        cache = add_node(data, make_node("Cache intelligente dashboard", "Ridurre refresh e mostrare log consumi"))
        save_blueprint(project, data)
        imported = import_project(project, write=True)
        summary = board_summary(project)
        doctor_report = doctor(project)
        dry_update = auto_update(project, write=False)
        written_update = auto_update(project, write=True)
        updated_data = load_blueprint(project)
        plan = superplan(load_blueprint(project))
        errors = []
        if not (project / BLUEPRINT_FILE).exists():
            errors.append("missing app-blueprint.json")
        if login.get("inferred_type") != "auth":
            errors.append("auth inference failed")
        if cache.get("inferred_type") != "infra":
            errors.append("infra inference failed")
        if cache.get("domain") != "devops":
            errors.append("domain inference failed")
        if "observability" not in cache.get("tags", []):
            errors.append("tag inference failed")
        if not cache.get("implementation_steps"):
            errors.append("implementation steps missing")
        if not imported.get("added"):
            errors.append("import added no nodes")
        imported_titles = {str(item.get("title", "")) for item in imported.get("added", []) if isinstance(item, dict)}
        if not any("Admin Dashboard" in title for title in imported_titles):
            errors.append("smart import missed component")
        if not any("Login Route" in title for title in imported_titles):
            errors.append("smart import missed route")
        if int(summary.get("nodes", 0)) < 2:
            errors.append("summary node count too low")
        if not summary.get("domains"):
            errors.append("domain summary missing")
        if not doctor_report.get("nodes_checked"):
            errors.append("doctor checked no nodes")
        if not doctor_report.get("health_counts"):
            errors.append("doctor health counts missing")
        if not doctor_report.get("audit", {}).get("counts"):
            errors.append("doctor audit counts missing")
        if not doctor_report.get("audit", {}).get("fix_plan"):
            errors.append("doctor audit fix plan missing")
        if not doctor_report.get("flows", {}).get("items"):
            errors.append("flow trace missing")
        if "doctor" not in summary:
            errors.append("summary doctor missing")
        if not doctor_report.get("suggestions"):
            errors.append("doctor suggestions missing")
        doctor_nodes = [item for item in doctor_report.get("nodes", []) if isinstance(item, dict)]
        doctor_titles = {str(item.get("title", "")) for item in doctor_nodes}
        if "Button: Zoom -" in doctor_titles or "Button: Reset vista" in doctor_titles or "Action: Monitora" in doctor_titles:
            errors.append("internal board controls leaked into blueprint issues")
        for title in {"Button: Salva ordine", "Button: Apri report", "Button: Esporta CSV", "Button: Filtra ordini"}:
            if title not in doctor_titles:
                errors.append(f"scanner missed UI button node {title}")
        chart_node = next((item for item in doctor_nodes if item.get("title") == "Chart: RevenueChart"), {})
        if not chart_node:
            errors.append("scanner missed chart node")
        elif not chart_node.get("subnodes"):
            errors.append("chart node missing subnodes")
        admin_node = next((item for item in doctor_nodes if item.get("title") == "Screen/Component: AdminDashboard"), {})
        if not any(item.get("title") == "Button: Salva ordine" and item.get("parent_id") == admin_node.get("id") for item in doctor_nodes):
            errors.append("button node missing component parent")
        if not any(
            item.get("title") == "Screen/Component: AdminDashboard"
            and any(rel.get("kind") == "contains_ui" for rel in item.get("plain_relations", []) if isinstance(rel, dict))
            for item in doctor_nodes
        ):
            errors.append("component missing contains_ui relation")
        next_focus_title = str((doctor_report.get("next_focus") or {}).get("title", ""))
        if next_focus_title in {"Button: Zoom -", "Button: Reset vista", "Action: Monitora"}:
            errors.append("internal board control selected as next focus")
        if is_internal_ui_control("Apri tutti") is not True or is_internal_ui_control("Chiudi tutti") is not True:
            errors.append("internal blueprint expand controls not filtered")
        if not any(item.get("plain_summary") for item in doctor_nodes):
            errors.append("doctor plain summaries missing")
        if not any("plain_relations" in item for item in doctor_nodes):
            errors.append("doctor plain relations missing")
        if not any(
            any(rel.get("kind") == "calls_api" and rel.get("confidence") == "high" for rel in item.get("plain_relations", []) if isinstance(rel, dict))
            for item in doctor_nodes
        ):
            errors.append("scanner missed high-confidence UI to API link")
        action_node = next((item for item in doctor_nodes if item.get("title") == "Action: POST /login"), {})
        relation = next((rel for rel in action_node.get("plain_relations", []) if isinstance(rel, dict) and rel.get("kind") == "calls_api"), {})
        if action_node and relation:
            record_learning(str(project), edge_key(str(action_node.get("id")), str(relation.get("id")), str(relation.get("kind"))), "ignore_edge")
            ignored_report = doctor(project)
            ignored_nodes = [item for item in ignored_report.get("nodes", []) if isinstance(item, dict)]
            ignored_action = next((item for item in ignored_nodes if item.get("title") == "Action: POST /login"), {})
            ignored_relation = next((rel for rel in ignored_action.get("plain_relations", []) if isinstance(rel, dict) and rel.get("kind") == "calls_api"), {})
            if ignored_relation.get("state") != "ignored":
                errors.append("edge ignore feedback not applied")
        if not any(
            item.get("http_method") == "POST" and item.get("contract", {}).get("input") == ["email"]
            for item in doctor_nodes
        ):
            errors.append("scanner missed method/body contract")
        if not any(item.get("scanner_evidence") for item in doctor_nodes):
            errors.append("scanner evidence missing")
        if not any(item.get("audit_status") == "certo" for item in doctor_nodes):
            errors.append("audit precision missed certain node")
        if not any(item.get("audit_problem") for item in doctor_nodes):
            errors.append("audit problems missing")
        flow_items = doctor_report.get("flows", {}).get("items", [])
        if not any("POST /login" in str(item.get("chain", "")) for item in flow_items if isinstance(item, dict)):
            errors.append("flow trace missed login chain")
        if dry_update.get("applied"):
            errors.append("dry auto-update wrote changes")
        if not written_update.get("applied"):
            errors.append("auto-update applied no metadata")
        if not any(item.get("doctor_health") for item in updated_data.get("nodes", []) if isinstance(item, dict)):
            errors.append("auto-update metadata missing")
        if "Superplan Blueprint Board" not in plan:
            errors.append("missing superplan text")
        seeded_project = Path(tmp) / "SeedApp"
        seeded_project.mkdir()
        seeded = seed_blueprint(seeded_project, "Gestionale magazzino con login, dashboard e report", write=True)
        seeded_titles = {str(item.get("title", "")) for item in seeded.get("added", []) if isinstance(item, dict)}
        if not (seeded_project / BLUEPRINT_FILE).exists():
            errors.append("seed did not write blueprint")
        if "Login e gestione accessi" not in seeded_titles:
            errors.append("seed missed login")
        if "Dashboard principale" not in seeded_titles:
            errors.append("seed missed dashboard")
        if "Report e analytics" not in seeded_titles:
            errors.append("seed missed report")
        designed_project = Path(tmp) / "DesignedApp"
        designed_project.mkdir()
        designed = apply_design_wizard(
            designed_project,
            {
                "goal": "Gestionale ordini",
                "users": "Admin\nCliente",
                "screens": "Home\nOrdini",
                "actions": "creare ordine\nfare login",
                "data": "Ordine\nUtente",
                "auth": "Solo admin cancella",
                "tests": "creazione ordine",
                "template": "gestionale",
            },
            write=True,
        )
        designed_nodes = [item for item in designed.get("blueprint", {}).get("nodes", []) if isinstance(item, dict)]
        if not any(item.get("origin") == "design" and item.get("kind") == "screen" for item in designed_nodes):
            errors.append("design wizard missed screen nodes")
        if not any(item.get("origin") == "design" and item.get("kind") == "action" and item.get("ui_route") for item in designed_nodes):
            errors.append("design wizard missed action route")
        if not any(item.get("origin") == "design" and item.get("kind") == "api" and item.get("api_route") for item in designed_nodes):
            errors.append("design wizard missed api contract node")
        if designed.get("blueprint", {}).get("design_template") != "gestionale":
            errors.append("design wizard missed template metadata")
        skill_project = Path(tmp) / "SkillProject"
        (skill_project / "references").mkdir(parents=True)
        (skill_project / "scripts").mkdir()
        (skill_project / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
        (skill_project / "scripts" / "generate_dashboard.py").write_text("print('dashboard')\n", encoding="utf-8")
        (skill_project / "scripts" / "serve_dashboard.py").write_text("print('serve')\n", encoding="utf-8")
        (skill_project / "scripts" / "validate_skill.py").write_text("print('validate')\n", encoding="utf-8")
        skill_summary = board_summary(skill_project)
        skill_titles = {str(item.get("title", "")) for item in skill_summary.get("preview_nodes", []) if isinstance(item, dict)}
        if int(skill_summary.get("nodes", 0)) < 3:
            errors.append("skill import found too few nodes")
        if "Skill Operating Rules" not in skill_titles:
            errors.append("skill import missed operating rules")
        if "Dashboard Runtime" not in skill_titles:
            errors.append("skill import missed dashboard runtime")
        if errors:
            print("Blueprint Board fixture-test failed:")
            for error in errors:
                print(f"- {error}")
            return 1
    print("Blueprint Board fixture-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
