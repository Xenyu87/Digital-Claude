#!/usr/bin/env python3
"""Validate the cost-aware app coordinator skill.

Checks are intentionally lightweight and dependency-free so they can run before
commits without loading every reference into the model context.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
REFERENCES = ROOT / "references"
PROGRESSIVE = REFERENCES / "progressive-loading.md"

MAX_LINES = {
    "SKILL.md": 350,
}
DEFAULT_MAX_REFERENCE_LINES = 120


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    if not SKILL.exists():
        fail(errors, "Missing SKILL.md")
        return report(errors)

    skill_text = read(SKILL)
    progressive_text = read(PROGRESSIVE) if PROGRESSIVE.exists() else ""

    if not skill_text.startswith("---\n"):
        fail(errors, "SKILL.md must start with YAML frontmatter")
    if "name: cost-aware-app-coordinator" not in skill_text:
        fail(errors, "SKILL.md frontmatter missing expected name")
    if "description:" not in skill_text:
        fail(errors, "SKILL.md frontmatter missing description")

    reference_files = sorted(REFERENCES.glob("*.md"))
    skill_refs = set(re.findall(r"references/[^`:\s]+\.md", skill_text))
    progressive_refs = {
        f"references/{match}"
        for match in re.findall(r"`([^`]+\.md)`", progressive_text)
        if match != "SKILL.md"
    }

    for ref in reference_files:
        rel = f"references/{ref.name}"
        if rel not in skill_refs:
            fail(errors, f"{rel} exists but is not referenced from SKILL.md")

    for rel in skill_refs:
        if not (ROOT / rel).exists():
            fail(errors, f"{rel} is referenced from SKILL.md but does not exist")
        if rel not in progressive_refs:
            fail(errors, f"{rel} is missing from progressive-loading.md")

    for md in [SKILL, *reference_files]:
        headings = [
            line.strip()
            for line in read(md).splitlines()
            if re.match(r"^#{1,3}\s+", line)
        ]
        for heading, count in Counter(headings).items():
            if count > 1:
                fail(errors, f"{md.relative_to(ROOT)} has duplicate heading: {heading}")

    for md in [SKILL, *reference_files]:
        max_lines = MAX_LINES.get(md.name, DEFAULT_MAX_REFERENCE_LINES)
        count = line_count(md)
        if count > max_lines:
            fail(errors, f"{md.relative_to(ROOT)} has {count} lines; max is {max_lines}")

    required_sections = [
        "Start Protocol",
        "Progressive Loading",
        "Decision And Risk Gates",
        "Coordinator Rules",
        "Definition Of Done",
        "References",
    ]
    for section in required_sections:
        if not re.search(rf"^##\s+{re.escape(section)}$", skill_text, re.MULTILINE):
            fail(errors, f"SKILL.md missing section: {section}")

    return report(errors)


def report(errors: list[str]) -> int:
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
