#!/usr/bin/env python3
"""Fixture test for Blueprint Board Core."""

from __future__ import annotations

import tempfile
from pathlib import Path

from blueprint_board import BLUEPRINT_FILE, add_node, auto_update, board_summary, doctor, import_project, load_blueprint, make_node, save_blueprint, seed_blueprint, superplan


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "DemoApp"
        (project / "frontend" / "src" / "components").mkdir(parents=True)
        (project / "backend" / "src" / "routes").mkdir(parents=True)
        (project / "backend" / "src" / "services" / "__tests__").mkdir(parents=True)
        (project / "docs").mkdir()
        (project / "backend" / "src" / "routes" / "loginRoute.js").write_text("export const login = true;\n", encoding="utf-8")
        (project / "backend" / "src" / "services" / "__tests__" / "login.test.js").write_text("test('login', () => {});\n", encoding="utf-8")
        (project / "frontend" / "src" / "components" / "AdminDashboard.jsx").write_text("export function AdminDashboard() { return null }\n", encoding="utf-8")
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
        if "doctor" not in summary:
            errors.append("summary doctor missing")
        if not doctor_report.get("suggestions"):
            errors.append("doctor suggestions missing")
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
        if errors:
            print("Blueprint Board fixture-test failed:")
            for error in errors:
                print(f"- {error}")
            return 1
    print("Blueprint Board fixture-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
