#!/usr/bin/env python3
"""Audit existing project docs and suggest AI context bootstrap scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DOC_CANDIDATES = {
    "agent_guidance": ["AGENTS.md", "docs/AI-GUIDE.md", ".github/copilot-instructions.md"],
    "context_index": ["AI_CONTEXT.md"],
    "architecture": ["AI_STRUCTURE.md", "ARCHITECTURE.md", "docs/ARCHITECTURE.md"],
    "handoff": ["AI_HANDOFF.md", "docs/AI-HANDOFF.md"],
    "decisions": ["AI_DECISIONS.md", "docs/DECISIONS.md", "docs/ADR.md"],
    "agent_log": ["AI_AGENT_LOG.md"],
    "api": ["docs/API-REFERENCE.md", "docs/API.md", "API.md"],
    "deploy": ["docs/DEPLOYMENT.md", "DEPLOYMENT.md"],
    "security": ["docs/SECURITY-RELEASE.md", "SECURITY.md"],
    "env": ["docs/SEGRETI-ENV.md", "docs/ENV.md", ".env.example"],
    "onboarding": ["docs/ONBOARDING.md", "README.md"],
    "app_contract": ["docs/ai/app-contract.md", "docs/TROVA-PEZZO-AI.md"],
}
AI_FILES = [
    "AGENTS.md",
    "AI_CONTEXT.md",
    "AI_STRUCTURE.md",
    "AI_HANDOFF.md",
    "AI_DECISIONS.md",
    "AI_AGENT_LOG.md",
    "docs/ai/app-contract.md",
]


def existing(root: Path, candidates: list[str]) -> list[str]:
    return [item for item in candidates if (root / item).exists()]


def audit(root: Path) -> dict[str, object]:
    root = root.resolve()
    docs = {key: existing(root, values) for key, values in DOC_CANDIDATES.items()}
    ai_existing = existing(root, AI_FILES)
    has_mature_docs = bool(docs["architecture"] or docs["api"] or docs["deploy"] or docs["agent_guidance"])
    missing_ai = [item for item in AI_FILES if item not in ai_existing]
    if has_mature_docs:
        recommended = ["AGENTS.md", "AI_CONTEXT.md"]
        avoid = [item for item in AI_FILES if item not in recommended]
        preset = "mature-existing-docs"
    else:
        recommended = ["AGENTS.md", "AI_CONTEXT.md", "AI_HANDOFF.md", "AI_DECISIONS.md", "docs/ai/app-contract.md"]
        avoid = ["AI_AGENT_LOG.md"]
        preset = "full"
    maps = []
    for key, values in docs.items():
        if values:
            maps.append({"purpose": key, "path": values[0]})
    return {
        "root": str(root),
        "docs_found": docs,
        "ai_files_existing": ai_existing,
        "ai_files_missing": missing_ai,
        "recommended_create": [item for item in recommended if item not in ai_existing],
        "recommended_do_not_create_now": [item for item in avoid if item not in ai_existing],
        "recommended_preset": preset,
        "maps": maps,
        "bootstrap_command": build_command(root, preset, maps),
        "token_risks": [
            "Avoid lock files, build/dist folders, generated mobile/web assets, and bundled JS.",
            "Use headings, rg, or targeted sections for large docs and source files.",
        ],
    }


def build_command(root: Path, preset: str, maps: list[dict[str, str]]) -> str:
    parts = [
        "python",
        "scripts\\bootstrap_project_context.py",
        str(root),
        "--preset",
        preset,
        "--dry-run",
    ]
    for item in maps:
        parts.extend(["--map", f"\"{item['purpose']}={item['path']}\""])
    return " ".join(parts)


def print_text(result: dict[str, object]) -> None:
    print(f"Project: {result['root']}")
    print(f"Recommended preset: {result['recommended_preset']}")
    print("Docs found:")
    for key, values in result["docs_found"].items():
        if values:
            print(f"- {key}: {', '.join(values)}")
    print("AI files existing:")
    for item in result["ai_files_existing"]:
        print(f"- {item}")
    print("Recommended create:")
    for item in result["recommended_create"]:
        print(f"- {item}")
    print("Do not create now:")
    for item in result["recommended_do_not_create_now"]:
        print(f"- {item}")
    print("Bootstrap command:")
    print(result["bootstrap_command"])
    print("Token risks:")
    for item in result["token_risks"]:
        print(f"- {item}")


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
