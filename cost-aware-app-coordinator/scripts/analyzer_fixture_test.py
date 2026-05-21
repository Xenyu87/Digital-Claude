#!/usr/bin/env python3
"""Fixture tests for project analyzers without depending on real user projects."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from project_copilot import analyze


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_full_stack(root: Path) -> None:
    write(root / "package.json", json.dumps({"dependencies": {"react": "latest", "express": "latest"}, "devDependencies": {"typescript": "latest"}}))
    write(root / "vite.config.ts", "export default {}")
    write(root / "frontend" / "src" / "components" / "App.tsx", "export function App() { return <main /> }")
    write(root / "backend" / "src" / "controllers" / "healthController.js", "export function health(req, res) { res.json({ ok: true }) }")
    write(root / "backend" / "src" / "routes" / "healthRoutes.js", "router.get('/health', health)")
    write(root / "README.md", "# Fixture")


def assert_true(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "FullStackFixture"
        make_full_stack(root)
        result = analyze(root)
        stack = set(result["stack"])
        areas = {item["area"] for item in result["dominant_areas"]}
        assert_true(result["app_type"] == "full-stack app", f"expected full-stack app, got {result['app_type']}", errors)
        assert_true("React" in stack or "React/Vite" in stack, "expected React stack marker", errors)
        assert_true("Express" in stack or "Node/Express" in stack, "expected Express stack marker", errors)
        assert_true("frontend" in areas, "expected frontend area", errors)
        assert_true("backend" in areas, "expected backend area", errors)
        assert_true(bool(result["prompts"].get("frontend")), "expected frontend prompt", errors)
        assert_true(bool(result["prompts"].get("backend")), "expected backend prompt", errors)
    if errors:
        print("Analyzer fixture-test failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Analyzer fixture-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
