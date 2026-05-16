#!/usr/bin/env python3
"""Find files and folders likely to waste agent context."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".next",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


def estimate_tokens(size_bytes: int) -> int:
    return max(1, round(size_bytes / 4))


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def scan(root: Path, max_files: int) -> dict[str, object]:
    root = root.resolve()
    files: list[dict[str, object]] = []
    skipped = Counter()
    for path in root.rglob("*"):
        if path.is_dir() and path.name in EXCLUDED_DIRS:
            skipped[path.name] += 1
            continue
        if not path.is_file() or should_skip(path.relative_to(root)):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        files.append(
            {
                "path": rel,
                "bytes": size,
                "estimated_tokens": estimate_tokens(size),
                "text_like": path.suffix.lower() in TEXT_SUFFIXES,
            }
        )
    largest = sorted(files, key=lambda item: int(item["bytes"]), reverse=True)[:max_files]
    text_risks = [
        item
        for item in sorted(files, key=lambda item: int(item["estimated_tokens"]), reverse=True)
        if item["text_like"] and int(item["estimated_tokens"]) >= 2500
    ][:max_files]
    return {
        "root": str(root),
        "files_scanned": len(files),
        "skipped_dirs": dict(skipped),
        "largest_files": largest,
        "text_context_risks": text_risks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--max-files", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = scan(Path(args.path), args.max_files)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Root: {result['root']}")
        print(f"Files scanned: {result['files_scanned']}")
        print(f"Skipped dirs: {result['skipped_dirs']}")
        print("Largest files:")
        for item in result["largest_files"]:
            print(f"- {item['path']} | {item['bytes']} bytes | ~{item['estimated_tokens']} tokens")
        print("Text context risks:")
        for item in result["text_context_risks"]:
            print(f"- {item['path']} | ~{item['estimated_tokens']} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
