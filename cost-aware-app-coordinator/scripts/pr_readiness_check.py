#!/usr/bin/env python3
"""Check whether a project is ready for commit/PR handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


RISK_PATTERNS = [
    ".env",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "dist/",
    "build/",
    "android/",
    "ios/",
]
DOC_FILES = ["AGENTS.md", "AI_CONTEXT.md"]


def run_git(root: Path, args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout.rstrip(), result.stderr.strip()


def parse_status(status: str) -> list[dict[str, str]]:
    items = []
    for line in status.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 else ""
        items.append({"code": code, "path": path})
    return items


def has_risk(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(pattern in normalized for pattern in RISK_PATTERNS)


def recommended_checks(root: Path) -> list[str]:
    checks: list[str] = []
    if (root / "frontend" / "package.json").exists():
        checks.append("frontend: npm test/build/lint if configured")
    if (root / "backend" / "package.json").exists():
        checks.append("backend: npm test/build/lint if configured")
    if (root / "package.json").exists():
        checks.append("root: npm test/build/lint if configured")
    if not checks:
        checks.append("run the narrowest project-specific test for touched files")
    return checks


def audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    branch_code, branch, branch_err = run_git(root, ["status", "--short", "--branch"])
    status_code, status, status_err = run_git(root, ["status", "--short"])
    if branch_code != 0 or status_code != 0:
        return {
            "root": str(root),
            "status": "fail",
            "errors": [branch_err or status_err or "not a git repository"],
        }
    items = parse_status(status)
    untracked = [item["path"] for item in items if item["code"] == "??"]
    modified = [item["path"] for item in items if item["code"] != "??"]
    risky = [item["path"] for item in items if has_risk(item["path"])]
    missing_docs = [doc for doc in DOC_FILES if not (root / doc).exists()]
    warnings = []
    if untracked:
        warnings.append("Review untracked files before PR.")
    if risky:
        warnings.append("Risky/generated/secret-like files are changed or untracked.")
    if missing_docs:
        warnings.append("Project AI context files are missing.")
    pr_status = "warn" if warnings else "pass"
    if not items:
        pr_status = "clean"
    summary = []
    if modified:
        summary.append(f"Modified/staged files: {len(modified)}")
    if untracked:
        summary.append(f"Untracked files: {len(untracked)}")
    if not summary:
        summary.append("No local changes detected.")
    return {
        "root": str(root),
        "status": pr_status,
        "branch": branch.splitlines()[0] if branch else "",
        "modified": modified,
        "untracked": untracked,
        "risky_files": risky,
        "missing_ai_docs": missing_docs,
        "warnings": warnings,
        "recommended_checks": recommended_checks(root),
        "pr_summary_draft": "; ".join(summary),
    }


def print_text(result: dict[str, object]) -> None:
    print(f"Project: {result['root']}")
    print(f"PR readiness: {result['status']}")
    if result.get("branch"):
        print(result["branch"])
    for key in ["modified", "untracked", "risky_files", "missing_ai_docs", "warnings", "recommended_checks"]:
        values = result.get(key) or []
        print(f"{key}:")
        for value in values:
            print(f"- {value}")
    print("PR summary draft:")
    print(result.get("pr_summary_draft", ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(Path(args.path))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
