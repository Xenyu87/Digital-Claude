#!/usr/bin/env python3
"""Audit a local third-party skill before recommending or installing it."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RISK_PATTERNS = {
    "shell_execution": r"\b(subprocess|os\.system|Invoke-WebRequest|curl|wget|Start-Process)\b",
    "secret_access": r"\b(API_KEY|TOKEN|SECRET|PASSWORD|credential|\.env)\b",
    "network_access": r"\b(requests\.|fetch\(|http://|https://|socket)\b",
    "destructive_fs": r"\b(rm -rf|Remove-Item|shutil\.rmtree|unlink\(|delete)\b",
    "broad_scan": r"\b(rglob\(\"\\*\"|Get-ChildItem .* -Recurse|find \.)\b",
}
DEPENDENCY_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "uv.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    is_local_source = root == Path(__file__).resolve().parents[1]
    skill = root / "SKILL.md"
    scripts = sorted((root / "scripts").rglob("*")) if (root / "scripts").exists() else []
    files = [path for path in root.rglob("*") if path.is_file()]
    text = "\n".join(read_text(path)[:20000] for path in files if path.suffix.lower() in {".md", ".py", ".js", ".ts", ".json", ".yml", ".yaml", ".toml", ".txt"})
    risks = {
        name: bool(re.search(pattern, text, re.IGNORECASE))
        for name, pattern in RISK_PATTERNS.items()
    }
    dependencies = sorted(path.relative_to(root).as_posix() for path in files if path.name in DEPENDENCY_FILES)
    script_files = sorted(path.relative_to(root).as_posix() for path in scripts if path.is_file())
    frontmatter_ok = skill.exists() and read_text(skill).startswith("---\n") and "description:" in read_text(skill)
    recommendations: list[str] = []
    if not frontmatter_ok:
        recommendations.append("Do not install until SKILL.md frontmatter and description are clear.")
    if script_files or dependencies:
        recommendations.append("Read scripts and dependency files before enabling this skill.")
    if any(risks.values()):
        recommendations.append("Treat as medium/high risk; sandbox or reject unless the behavior is required and understood.")
    if is_local_source:
        recommendations.insert(
            0,
            "This is the local source skill; risk flags describe capabilities to review before publishing or sharing, not an automatic install blocker.",
        )
    if not recommendations:
        recommendations.append("Low structural risk found; still review behavior before installing.")
    return {
        "path": str(root),
        "local_source_skill": is_local_source,
        "frontmatter_ok": frontmatter_ok,
        "script_files": script_files,
        "dependency_files": dependencies,
        "risk_flags": risks,
        "recommendations": recommendations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(Path(args.path))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Path: {result['path']}")
        print(f"Frontmatter ok: {result['frontmatter_ok']}")
        print(f"Scripts: {len(result['script_files'])}")
        print(f"Dependencies: {', '.join(result['dependency_files']) or 'none'}")
        print("Risk flags:")
        for key, value in result["risk_flags"].items():
            print(f"- {key}: {value}")
        print("Recommendations:")
        for item in result["recommendations"]:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
