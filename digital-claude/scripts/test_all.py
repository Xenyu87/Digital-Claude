#!/usr/bin/env python3
"""Run the full local verification suite for the coordinator skill."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "test-all-report.json"
TESTS = [
    ("validate_skill", [sys.executable, str(ROOT / "scripts" / "validate_skill.py")]),
    ("self_test", [sys.executable, str(ROOT / "scripts" / "self_test.py")]),
    ("analyzer_fixture", [sys.executable, str(ROOT / "scripts" / "analyzer_fixture_test.py")]),
    ("blueprint_board", [sys.executable, str(ROOT / "scripts" / "blueprint_board_test.py")]),
    ("generate_dashboard", [sys.executable, str(ROOT / "scripts" / "generate_dashboard.py"), "--refresh", "15"]),
    ("dashboard_smoke", [sys.executable, str(ROOT / "scripts" / "dashboard_smoke_test.py")]),
]


def run_test(name: str, command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "name": name,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "command": " ".join(command),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    results = [run_test(name, command) for name, command in TESTS]
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "status": "PASS" if all(item["returncode"] == 0 for item in results) else "FAIL",
        "tests": results,
    }
    if not args.no_write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        for item in results:
            print(f"{item['status']} {item['name']}")
        print(f"RESULT {report['status']}")
        if not args.no_write:
            print(f"REPORT {REPORT}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
