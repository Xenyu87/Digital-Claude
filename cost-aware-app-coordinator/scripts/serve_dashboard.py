#!/usr/bin/env python3
"""Serve an auto-refreshing local dashboard for the skill."""

from __future__ import annotations

import argparse
import html
import json
import http.server
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

from expert_feedback import record_feedback
from skill_learning import record_learning
from blueprint_board import apply_design_wizard, doctor as blueprint_doctor
from persistent_runner import enqueue_job, pause_runner, run_once as runner_run_once, start_runner, stop_runner, update_runner_config


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "skill-dashboard.html"
CONFIG = ROOT / "reports" / "dashboard-config.json"
CACHE = ROOT / "reports" / "dashboard-cache.json"
UPLOADS = ROOT / "reports" / "uploads"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
DEFAULT_CONFIG = {"project_path": "", "refresh_seconds": 15, "port": 3002, "host": "127.0.0.1", "background_mode": "safe"}


def load_config() -> dict[str, object]:
    config = dict(DEFAULT_CONFIG)
    if CONFIG.exists():
        try:
            loaded = json.loads(CONFIG.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update({key: value for key, value in loaded.items() if value not in (None, "")})
        except (OSError, json.JSONDecodeError):
            pass
    return config


def save_config(config: dict[str, object]) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")


def generate_once(interval: int, project: str | None = None, save: bool = False) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "generate_dashboard.py"),
        "--refresh",
        str(interval),
    ]
    if project:
        command.extend(["--project", project])
    if save:
        command.append("--save-config")
    subprocess.run(command, cwd=ROOT.parent, check=False)


def clear_dashboard_cache() -> None:
    try:
        CACHE.unlink(missing_ok=True)
    except OSError:
        pass


def upload_extension(content_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get(content_type.split(";")[0].strip().lower(), "")


def blueprint_import(project: str, write: bool) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "blueprint_board.py"),
        "import-project",
        project,
    ]
    if write:
        command.append("--write")
    subprocess.run(command, cwd=ROOT, check=False)


def save_blueprint_layout(project: Path, payload: dict[str, object]) -> dict[str, object]:
    blueprint = project.resolve() / "app-blueprint.json"
    try:
        data = json.loads(blueprint.read_text(encoding="utf-8")) if blueprint.exists() else {
            "schema_version": "1.0",
            "project_name": project.resolve().name,
            "project_path": str(project.resolve()),
            "nodes": [],
        }
    except (OSError, json.JSONDecodeError):
        data = {"schema_version": "1.0", "project_name": project.resolve().name, "project_path": str(project.resolve()), "nodes": []}
    if not isinstance(data, dict):
        data = {"schema_version": "1.0", "project_name": project.resolve().name, "project_path": str(project.resolve()), "nodes": []}
    layout = data.setdefault("layout", {})
    if not isinstance(layout, dict):
        data["layout"] = layout = {}
    positions = layout.setdefault("positions", {})
    if not isinstance(positions, dict):
        layout["positions"] = positions = {}
    incoming = payload.get("positions", {})
    saved = 0
    if isinstance(incoming, dict):
        for node_id, position in incoming.items():
            if not isinstance(node_id, str) or not isinstance(position, dict):
                continue
            try:
                x = float(position.get("x"))
                y = float(position.get("y"))
            except (TypeError, ValueError):
                continue
            positions[node_id[:96]] = {"x": round(x, 2), "y": round(y, 2)}
            saved += 1
    layout["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    data["updated_at"] = layout["updated_at"]
    blueprint.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    return {"ok": True, "path": str(blueprint), "saved": saved}


def render_frontend_preview(project: Path) -> str:
    try:
        report = blueprint_doctor(project)
    except Exception as exc:  # pragma: no cover - defensive server fallback
        safe_error = html.escape(str(exc))
        return f"<!doctype html><meta charset='utf-8'><body><p>Preview non disponibile: {safe_error}</p></body>"
    nodes = [item for item in report.get("nodes", []) if isinstance(item, dict)]
    by_parent: dict[str, list[dict[str, object]]] = {}
    roots = []
    for node in nodes:
        if str(node.get("domain") or "") != "frontend":
            continue
        parent_id = str(node.get("parent_id") or "")
        if parent_id:
            by_parent.setdefault(parent_id, []).append(node)
        elif str(node.get("kind") or "") in {"screen", "component"} or str(node.get("title") or "").startswith("Screen/Component:"):
            roots.append(node)
    if not roots:
        roots = [item for item in nodes if str(item.get("domain") or "") == "frontend"][:6]

    def node_attr(node: dict[str, object]) -> str:
        return html.escape(str(node.get("id") or ""), quote=True)

    def node_title(node: dict[str, object]) -> str:
        return html.escape(str(node.get("title") or "Nodo UI"))

    def child_html(child: dict[str, object]) -> str:
        kind = str(child.get("kind") or "")
        title = node_title(child)
        node_id = node_attr(child)
        summary = html.escape(str(child.get("action_description") or child.get("plain_summary") or child.get("description") or "Elemento UI rilevato."))
        route = html.escape(str(child.get("ui_route") or child.get("api_route") or ""))
        if kind == "chart":
            return f"<section class='preview-chart' data-blueprint-node-id='{node_id}' tabindex='0'><strong>{title}</strong><div class='chart-bars'><i></i><i></i><i></i><i></i></div><small>{summary}</small></section>"
        return f"<button class='preview-action' type='button' data-blueprint-node-id='{node_id}'><span>{title}</span><small>{summary}</small>{f'<em>{route}</em>' if route else ''}</button>"

    sections = []
    for root in roots[:10]:
        children = by_parent.get(str(root.get("id") or ""), [])
        if not children and root not in nodes:
            continue
        child_markup = "\n".join(child_html(child) for child in children[:12]) or "<p class='muted'>Nessun elemento UI figlio rilevato.</p>"
        sections.append(
            f"<article class='preview-card' data-blueprint-node-id='{node_attr(root)}' tabindex='0'>"
            f"<header><span>Componente</span><h2>{node_title(root)}</h2></header>"
            f"<p>{html.escape(str(root.get('plain_summary') or root.get('description') or 'Componente frontend rilevato.'))}</p>"
            f"<div class='preview-grid'>{child_markup}</div>"
            "</article>"
        )
    body = "\n".join(sections) or "<p class='muted'>Nessuna UI frontend rilevata nello scan.</p>"
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{ color-scheme: light; --ink:#17212f; --muted:#5c6876; --line:#d7e1ec; --accent:#2563a8; --soft:#f4f8fc; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:Inter, Segoe UI, Arial, sans-serif; color:var(--ink); background:#eef4fa; }}
    main {{ padding:16px; display:grid; gap:14px; }}
    .preview-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; padding:14px; box-shadow:0 8px 24px rgba(23,33,47,.08); }}
    .preview-card header {{ display:flex; justify-content:space-between; gap:10px; align-items:start; border-bottom:1px solid var(--line); padding-bottom:10px; margin-bottom:10px; }}
    .preview-card span {{ color:var(--accent); font-size:12px; font-weight:900; text-transform:uppercase; }}
    h1 {{ margin:0; font-size:18px; }}
    h2 {{ margin:2px 0 0; font-size:18px; }}
    p, small {{ color:var(--muted); line-height:1.35; }}
    .preview-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:9px; }}
    .preview-action, .preview-chart {{ min-height:96px; border:1px solid var(--line); border-radius:7px; background:var(--soft); color:var(--ink); padding:10px; text-align:left; }}
    .preview-action span, .preview-chart strong {{ display:block; font-weight:900; margin-bottom:5px; }}
    .preview-action small, .preview-chart small, .preview-action em {{ display:block; font-size:12px; color:var(--muted); overflow-wrap:anywhere; }}
    .preview-action em {{ margin-top:6px; font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-style:normal; }}
    .chart-bars {{ display:flex; align-items:end; gap:7px; height:52px; margin:6px 0 8px; }}
    .chart-bars i {{ flex:1; min-width:16px; border-radius:4px 4px 0 0; background:linear-gradient(180deg,#56a0df,#2563a8); }}
    .chart-bars i:nth-child(1) {{ height:45%; }} .chart-bars i:nth-child(2) {{ height:78%; }} .chart-bars i:nth-child(3) {{ height:58%; }} .chart-bars i:nth-child(4) {{ height:92%; }}
    [data-blueprint-node-id].is-highlighted {{ outline:4px solid #f2b84b; outline-offset:3px; box-shadow:0 0 0 8px rgba(242,184,75,.22); }}
    .muted {{ color:var(--muted); }}
  </style>
</head>
<body>
  <main>
    <h1>Preview frontend generata</h1>
    {body}
  </main>
  <script>
    function selectNode(id) {{
      document.querySelectorAll('[data-blueprint-node-id]').forEach((item) => item.classList.toggle('is-highlighted', item.dataset.blueprintNodeId === id));
      const selected = document.querySelector('[data-blueprint-node-id="' + CSS.escape(id) + '"]');
      if (selected) selected.scrollIntoView({{ block: 'center', inline: 'center', behavior: 'smooth' }});
    }}
    window.addEventListener('message', (event) => {{
      if (event.data && event.data.type === 'highlight-node') selectNode(String(event.data.id || ''));
    }});
    document.addEventListener('click', (event) => {{
      const target = event.target.closest('[data-blueprint-node-id]');
      if (target) window.parent.postMessage({{ type: 'preview-node-click', id: target.dataset.blueprintNodeId }}, '*');
    }});
  </script>
</body>
</html>"""


def regenerate(interval: int, project: str | None, save_config: bool, stop: threading.Event) -> None:
    while not stop.is_set():
        current_project = project or str(load_config().get("project_path") or "")
        generate_once(interval, current_project or None, save_config)
        stop.wait(interval)


def handler_class(interval: int) -> type[http.server.SimpleHTTPRequestHandler]:
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def list_directory(self, path):
            self.send_error(404, "Directory listing disabled")
            return None

        def redirect_to_dashboard(self) -> None:
            self.send_response(303)
            self.send_header("Location", "/reports/skill-dashboard.html")
            self.end_headers()

        def do_HEAD(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in {"", "/"}:
                self.redirect_to_dashboard()
                return
            super().do_HEAD()

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in {"", "/"}:
                self.redirect_to_dashboard()
                return
            if parsed.path == "/frontend-preview":
                params = urllib.parse.parse_qs(parsed.query)
                project = (params.get("project") or [""])[0].strip().strip('"')
                target = Path(project).resolve() if project else Path(str(load_config().get("project_path") or ROOT)).resolve()
                if not target.exists():
                    self.send_error(404, "Project not found")
                    return
                content = render_frontend_preview(target).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
                return
            if parsed.path == "/select-project":
                params = urllib.parse.parse_qs(parsed.query)
                manual = (params.get("path_manual") or [""])[0].strip().strip('"')
                selected = manual or (params.get("path") or [""])[0].strip().strip('"')
                if selected and Path(selected).exists():
                    config = load_config()
                    config["project_path"] = str(Path(selected).resolve())
                    save_config(config)
                    generate_once(interval, str(config["project_path"]), False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path in {"/blueprint-scan", "/blueprint-import"}:
                params = urllib.parse.parse_qs(parsed.query)
                project = (params.get("project") or [""])[0].strip().strip('"')
                if project and Path(project).exists():
                    clear_dashboard_cache()
                    if parsed.path == "/blueprint-import":
                        blueprint_import(project, write=True)
                    generate_once(interval, project, False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path in {"/background-mode", "/background-scan"}:
                params = urllib.parse.parse_qs(parsed.query)
                config = load_config()
                project = str(config.get("project_path") or "").strip()
                if parsed.path == "/background-mode":
                    mode = (params.get("mode") or ["safe"])[0].strip()
                    if mode in {"manual", "safe", "assist"}:
                        config["background_mode"] = mode
                        save_config(config)
                clear_dashboard_cache()
                generate_once(interval, project or None, False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path in {"/runner-start", "/runner-stop", "/runner-pause", "/runner-run-once", "/runner-enqueue", "/runner-config"}:
                params = urllib.parse.parse_qs(parsed.query)
                config = load_config()
                project = str(config.get("project_path") or "").strip()
                if parsed.path == "/runner-start":
                    start_runner(project)
                elif parsed.path == "/runner-stop":
                    stop_runner()
                elif parsed.path == "/runner-pause":
                    pause_runner()
                elif parsed.path == "/runner-run-once":
                    runner_run_once()
                elif parsed.path == "/runner-enqueue":
                    kind = (params.get("kind") or ["scan"])[0].strip()
                    enqueue_job(kind, project, "Richiesto dalla dashboard")
                elif parsed.path == "/runner-config":
                    update_runner_config(
                        {
                            "provider": (params.get("provider") or [""])[0].strip(),
                            "model": (params.get("model") or [""])[0].strip(),
                            "execution_mode": (params.get("execution_mode") or ["off"])[0].strip(),
                            "routing_policy": (params.get("routing_policy") or ["manual"])[0].strip(),
                            "local_endpoint": (params.get("local_endpoint") or [""])[0].strip(),
                            "local_model": (params.get("local_model") or [""])[0].strip(),
                            "local_llm_mode": (params.get("local_llm_mode") or ["optional"])[0].strip(),
                            "cloud_model": (params.get("cloud_model") or [""])[0].strip(),
                            "cloud_access": (params.get("cloud_access") or ["codex_cli_session"])[0].strip(),
                            "autonomy_level": (params.get("autonomy_level") or ["safe_reports"])[0].strip(),
                            "server_total_ram_gb": (params.get("server_total_ram_gb") or ["32"])[0].strip(),
                            "dev_lxc_ram_gb": (params.get("dev_lxc_ram_gb") or ["4"])[0].strip(),
                            "token_budget_limit": (params.get("token_budget_limit") or ["0"])[0].strip(),
                            "max_steps_per_task": (params.get("max_steps_per_task") or ["0"])[0].strip(),
                            "max_runtime_seconds": (params.get("max_runtime_seconds") or ["30"])[0].strip(),
                            "write_policy": (params.get("write_policy") or ["approval_required"])[0].strip(),
                            "notes": (params.get("notes") or [""])[0].strip(),
                        }
                    )
                clear_dashboard_cache()
                generate_once(interval, project or None, False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path == "/expert-feedback":
                params = urllib.parse.parse_qs(parsed.query)
                project = (params.get("project") or [""])[0].strip().strip('"')
                expert = (params.get("expert") or [""])[0].strip()
                outcome = (params.get("outcome") or [""])[0].strip()
                if project and expert and outcome in {"used", "ignored"}:
                    record_feedback(project, expert, outcome)
                    generate_once(interval, project, False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path == "/learning-feedback":
                params = urllib.parse.parse_qs(parsed.query)
                project = (params.get("project") or [""])[0].strip().strip('"')
                item_id = (params.get("item") or [""])[0].strip()
                outcome = (params.get("outcome") or [""])[0].strip()
                note = (params.get("note") or [""])[0].strip()
                if project and item_id and outcome in {"confusing", "wrong", "useful", "ignore", "confirm_edge", "ignore_edge"}:
                    record_learning(project, item_id, outcome, note)
                    generate_once(interval, project, False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            super().do_GET()

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/blueprint-design":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 256 * 1024:
                    self.send_error(413, "Design payload is empty or too large")
                    return
                body = self.rfile.read(length).decode("utf-8", errors="ignore")
                params = urllib.parse.parse_qs(body)
                project_value = (params.get("project") or [""])[0].strip().strip('"')
                project = Path(project_value).resolve() if project_value else None
                if not project or not project.exists() or not project.is_dir():
                    self.send_error(400, "Invalid project")
                    return
                payload = {key: (params.get(key) or [""])[0] for key in ["template", "goal", "users", "screens", "actions", "data", "auth", "tests"]}
                apply_design_wizard(project, payload, write=True)
                clear_dashboard_cache()
                generate_once(interval, str(project), False)
                self.send_response(303)
                self.send_header("Location", "/reports/skill-dashboard.html")
                self.end_headers()
                return
            if parsed.path == "/blueprint-layout":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 1024 * 1024:
                    self.send_error(413, "Layout payload is empty or too large")
                    return
                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self.send_error(400, "Invalid JSON")
                    return
                if not isinstance(payload, dict):
                    self.send_error(400, "Invalid layout payload")
                    return
                project_value = str(payload.get("project") or "").strip()
                project = Path(project_value).resolve() if project_value else None
                if not project or not project.exists() or not project.is_dir():
                    self.send_error(400, "Invalid project")
                    return
                result = save_blueprint_layout(project, payload)
                clear_dashboard_cache()
                generate_once(interval, str(project), False)
                body = json.dumps(result)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body.encode("utf-8"))))
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
                return
            if parsed.path != "/upload-screenshot":
                self.send_error(404, "Unknown endpoint")
                return
            content_type = self.headers.get("Content-Type", "")
            extension = upload_extension(content_type)
            if not extension:
                self.send_error(415, "Only image uploads are allowed")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_UPLOAD_BYTES:
                self.send_error(413, "Image is empty or too large")
                return
            body = self.rfile.read(length)
            UPLOADS.mkdir(parents=True, exist_ok=True)
            target = UPLOADS / f"latest-screenshot{extension}"
            target.write_bytes(body)
            latest = UPLOADS / "latest-screenshot.txt"
            latest.write_text(str(target), encoding="utf-8")
            payload = json.dumps({"ok": True, "path": str(target), "bytes": len(body)})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))

    return DashboardHandler


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=str(config.get("host") or "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(config.get("port") or 3002))
    parser.add_argument("--interval", type=int, default=int(config.get("refresh_seconds") or 15))
    parser.add_argument("--project", default="")
    parser.add_argument("--save-config", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    stop = threading.Event()
    thread = threading.Thread(
        target=regenerate,
        args=(args.interval, args.project or None, args.save_config, stop),
        daemon=True,
    )
    thread.start()
    time.sleep(1)

    handler = handler_class(args.interval)
    server = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    shown_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    url = f"http://{shown_host}:{args.port}/reports/skill-dashboard.html"
    print(f"Serving {REPORT}")
    print(f"Open {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
