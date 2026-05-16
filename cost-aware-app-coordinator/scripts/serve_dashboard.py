#!/usr/bin/env python3
"""Serve an auto-refreshing local dashboard for the skill."""

from __future__ import annotations

import argparse
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


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "skill-dashboard.html"
CONFIG = ROOT / "reports" / "dashboard-config.json"
CACHE = ROOT / "reports" / "dashboard-cache.json"
DEFAULT_CONFIG = {"project_path": "", "refresh_seconds": 15, "port": 8765, "host": "127.0.0.1"}


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


def regenerate(interval: int, project: str | None, save_config: bool, stop: threading.Event) -> None:
    while not stop.is_set():
        current_project = project or str(load_config().get("project_path") or "")
        generate_once(interval, current_project or None, save_config)
        stop.wait(interval)


def handler_class(interval: int) -> type[http.server.SimpleHTTPRequestHandler]:
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/select-project":
                params = urllib.parse.parse_qs(parsed.query)
                selected = (params.get("path") or [""])[0].strip().strip('"')
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
            super().do_GET()

    return DashboardHandler


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=str(config.get("host") or "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(config.get("port") or 8765))
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
