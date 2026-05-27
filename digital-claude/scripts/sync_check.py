#!/usr/bin/env python3
"""Compare a source skill folder with the installed Codex skill copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INSTALLED = Path.home() / ".codex" / "skills" / ROOT.name
INCLUDED_DIRS = {"agents", "references", "scripts"}
INCLUDED_REPORTS = {".md"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        first = rel.split("/", 1)[0]
        if rel == "SKILL.md" or first in INCLUDED_DIRS:
            files[rel] = digest(path)
        elif first == "reports" and path.suffix.lower() in INCLUDED_REPORTS:
            files[rel] = digest(path)
    return files


def compare(source: Path, installed: Path) -> dict[str, object]:
    source = source.resolve()
    installed = installed.resolve()
    if source == installed:
        return {
            "status": "same-path",
            "source": str(source),
            "installed": str(installed),
            "different": [],
            "missing_in_installed": [],
            "extra_in_installed": [],
        }
    source_files = tracked_files(source)
    installed_files = tracked_files(installed) if installed.exists() else {}
    source_keys = set(source_files)
    installed_keys = set(installed_files)
    common = source_keys & installed_keys
    return {
        "status": "in-sync"
        if source_files and source_files == installed_files
        else "differs",
        "source": str(source),
        "installed": str(installed),
        "different": sorted(rel for rel in common if source_files[rel] != installed_files[rel]),
        "missing_in_installed": sorted(source_keys - installed_keys),
        "extra_in_installed": sorted(installed_keys - source_keys),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(ROOT))
    parser.add_argument("--installed", default=str(DEFAULT_INSTALLED))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = compare(Path(args.source), Path(args.installed))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result['status']}")
        print(f"Source: {result['source']}")
        print(f"Installed: {result['installed']}")
        for key in ["different", "missing_in_installed", "extra_in_installed"]:
            values = result[key]
            if values:
                print(f"{key}:")
                for value in values:
                    print(f"- {value}")
    return 0 if result["status"] in {"in-sync", "same-path"} else 1


if __name__ == "__main__":
    sys.exit(main())
