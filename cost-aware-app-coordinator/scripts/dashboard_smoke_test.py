#!/usr/bin/env python3
"""Smoke-test generated dashboard artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "reports" / "skill-dashboard.html"
DATA = ROOT / "reports" / "skill-dashboard.json"
CONFIG = ROOT / "reports" / "dashboard-config.json"
REQUIRED_HTML = [
    "Analisi progetto",
    "Esperti consigliati",
    "Scegli Progetto Da Monitorare",
    "project-menu",
    "path_manual",
    "Memoria progetti",
    "Log interni skill",
    "Consigli manutenzione",
    "Context Guardrails",
    "Expert Feedback Loop",
    "Pilota Automatico",
    "Home Progetto",
    "Cosa devo fare in questo progetto",
    "Dove guardare:",
    "Perche conta:",
    "Cosa fare:",
    "Task Automatici Dai Warning",
    "Dettagli Tecnici",
    "Dashboard",
    "data-dashboard-tab=\"home\"",
    "data-dashboard-tab=\"lavagna\"",
    "data-dashboard-tab=\"azioni\"",
    "data-dashboard-tab=\"automazione\"",
    "data-dashboard-tab=\"diagnostica\"",
    "data-dashboard-section=\"home\"",
    "data-dashboard-section=\"lavagna\"",
    "data-dashboard-section=\"azioni\"",
    "data-dashboard-section=\"automazione\"",
    "data-dashboard-section=\"diagnostica\"",
    "Lavagna App",
    "Auto-Update Proposto",
    "Audit Precisione",
    "Piano Fix Dalla Lavagna",
    "Flow Trace",
    "Fonti / Prove",
    "Controllo Automatico",
    "Automazione Runner",
    "Impostazioni avanzate runner",
    "Modo esecuzione",
    "Endpoint locale",
    "Autonomia",
    "RAM server",
    "Ripresa Lavoro",
    "Prompt di ripresa task",
    "Automatico sicuro",
    "/background-mode",
    "/background-scan",
    "/runner-start",
    "/runner-stop",
    "/runner-pause",
    "/runner-run-once",
    "/runner-config",
    "Prossimo focus lavagna",
    "Scansiona nodi",
    "Conferma e salva Blueprint",
    "Prossimo passo:",
    "Lavagna App",
    "data-blueprint-flow-root",
    "Incolla screenshot qui",
    "data-screenshot-drop",
    "blueprint-flow-assets/blueprint-flow.css",
    "blueprint-flow-assets/blueprint-flow.js",
    "Lavagna React Flow",
    "Wizard Design App",
    "/blueprint-design",
    "Crea design nella lavagna",
]
REQUIRED_JSON = ["project_memory", "event_log", "project_audit", "monitored_project", "expert_feedback", "auto_pilot", "smart_cache", "blueprint_board", "background_sentinel", "persistent_runner", "active_task"]
MAX_COMPACT_JSON_BYTES = 150000


def main() -> int:
    errors: list[str] = []
    if not HTML.exists():
        errors.append("missing skill-dashboard.html")
    if not DATA.exists():
        errors.append("missing skill-dashboard.json")
    if CONFIG.exists():
        try:
            json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("dashboard-config.json is invalid")
    if HTML.exists():
        html = HTML.read_text(encoding="utf-8")
        for marker in REQUIRED_HTML:
            if marker not in html:
                errors.append(f"html missing marker: {marker}")
    if DATA.exists():
        if DATA.stat().st_size > MAX_COMPACT_JSON_BYTES:
            errors.append(f"skill-dashboard.json is larger than {MAX_COMPACT_JSON_BYTES} bytes")
        try:
            data = json.loads(DATA.read_text(encoding="utf-8"))
            for marker in REQUIRED_JSON:
                if marker not in data:
                    errors.append(f"json missing key: {marker}")
        except json.JSONDecodeError:
            errors.append("skill-dashboard.json is invalid")
    if errors:
        print("Dashboard smoke-test failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Dashboard smoke-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
