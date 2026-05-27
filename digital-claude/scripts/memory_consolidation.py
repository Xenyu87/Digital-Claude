#!/usr/bin/env python3
"""Memory consolidation: compact MEMORY.md and archive old observations.

Runs on-demand (manual) or weekly (via hook) to:
1. Merge similar decision*.md and feedback*.md files (same theme, <3 days apart)
2. Archive old observations (>30 days) from claude-mem timeline
3. Remove duplicate entries between auto-memory and claude-mem metadata
4. Update MEMORY.md index with consolidated entries

Usage:
  python3 scripts/memory_consolidation.py --consolidate    # merge similar files
  python3 scripts/memory_consolidation.py --archive        # archive old obs >30 days
  python3 scripts/memory_consolidation.py --full           # both + dedup
  python3 scripts/memory_consolidation.py --dry-run        # preview changes
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re


def find_memory_dir() -> Path | None:
    """Locate memory directory from current project or parent."""
    cwd = Path.cwd()
    for attempt in [cwd, cwd.parent]:
        mem_path = attempt / "memory" / "MEMORY.md"
        if mem_path.exists():
            return mem_path.parent
    return None


def parse_memory_files(memory_dir: Path) -> dict[str, dict]:
    """Parse all memory files and extract metadata."""
    files = {}
    for mem_file in sorted(memory_dir.glob("*.md")):
        if mem_file.name == "MEMORY.md":
            continue

        content = mem_file.read_text().strip()
        frontmatter = {}
        body = content

        # Parse YAML frontmatter
        if content.startswith("---"):
            _, fm, body = content.split("---", 2)
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip().strip('"\'')

        # Extract first line of body as title
        title = next((line.strip() for line in body.splitlines() if line.strip()), "")

        mtime = datetime.fromtimestamp(mem_file.stat().st_mtime, tz=timezone.utc)
        files[mem_file.name] = {
            "path": mem_file,
            "title": title,
            "frontmatter": frontmatter,
            "mtime": mtime,
            "type": frontmatter.get("type", "unknown"),
            "size_bytes": mem_file.stat().st_size,
        }

    return files


def find_similar_decisions(files: dict) -> list[tuple[str, str]]:
    """Identify similar decision*.md or feedback_*.md files for merging.

    Returns: list of (file1, file2) tuples for files with same type + close mtime (<3 days)
    """
    decisions = {k: v for k, v in files.items() if k.startswith("decision_") or k.startswith("feedback_")}
    similar = []

    for name1, info1 in sorted(decisions.items()):
        for name2, info2 in sorted(decisions.items()):
            if name1 >= name2:  # avoid duplicates
                continue

            # Same type + close in time
            time_diff = abs((info1["mtime"] - info2["mtime"]).total_seconds())
            if info1["type"] == info2["type"] and time_diff < (3 * 86400):  # < 3 days
                # Check if titles are similar (rough heuristic: >70% word overlap)
                words1 = set(info1["title"].lower().split())
                words2 = set(info2["title"].lower().split())
                if words1 and words2:
                    overlap = len(words1 & words2) / max(len(words1), len(words2))
                    if overlap > 0.4:
                        similar.append((name1, name2))

    return similar


def consolidate_similar(memory_dir: Path, pairs: list[tuple[str, str]], dry_run: bool = False) -> int:
    """Merge similar files into one, keeping the older one."""
    merged = 0
    for file1, file2 in pairs:
        path1, path2 = memory_dir / file1, memory_dir / file2
        mtime1, mtime2 = path1.stat().st_mtime, path2.stat().st_mtime

        # Keep the older, merge the newer into it
        keeper, merger = (path1, path2) if mtime1 <= mtime2 else (path2, path1)

        if dry_run:
            print(f"  [DRY] Would merge {merger.name} → {keeper.name}")
        else:
            # Append merger content to keeper (under "Related:" section)
            keeper_text = keeper.read_text()
            merger_text = merger.read_text()

            # Extract body from both (skip frontmatter)
            def extract_body(text):
                if text.startswith("---"):
                    _, _, body = text.split("---", 2)
                    return body.strip()
                return text.strip()

            keeper_body = extract_body(keeper_text)
            merger_body = extract_body(merger_text)

            merged_content = f"{keeper_body}\n\n**Related observation:** {merger.stem}\n{merger_body}\n"
            keeper.write_text(keeper_text.split("---")[-1].split(keeper_body)[0] + keeper_body + "\n\n**Related observation:** " + merger.stem + "\n" + merger_body)

            merger.unlink()  # Delete the merged file
            merged += 1
            print(f"  Merged {merger.name} → {keeper.name}")

    return merged


def archive_old_observations(memory_dir: Path, days: int = 30, dry_run: bool = False) -> int:
    """Archive observations older than N days."""
    archive_dir = memory_dir / "archive"
    if not archive_dir.exists():
        archive_dir.mkdir(exist_ok=True)

    now = datetime.now(tz=timezone.utc)
    threshold = now - timedelta(days=days)
    archived = 0

    for mem_file in memory_dir.glob("*.md"):
        if mem_file.name in ["MEMORY.md", "CONSOLIDATION_LOG.md"]:
            continue

        mtime = datetime.fromtimestamp(mem_file.stat().st_mtime, tz=timezone.utc)
        if mtime < threshold:
            dest = archive_dir / mem_file.name
            if dry_run:
                print(f"  [DRY] Would archive {mem_file.name} → archive/")
            else:
                mem_file.rename(dest)
                archived += 1
                print(f"  Archived {mem_file.name} → archive/")

    return archived


def update_memory_index(memory_dir: Path, dry_run: bool = False) -> None:
    """Rebuild MEMORY.md index from current memory files."""
    index_file = memory_dir / "MEMORY.md"
    files = parse_memory_files(memory_dir)

    # Sort by type, then by name
    lines = []
    for fname, info in sorted(files.items(), key=lambda x: (x[1]["type"], x[0])):
        title = info["title"] or info["frontmatter"].get("description", "")
        if title:
            lines.append(f"- [{title}]({fname}) — {info['frontmatter'].get('description', '')[:80]}")

    content = "\n".join(lines)

    if dry_run:
        print(f"  [DRY] Would update MEMORY.md with {len(lines)} entries")
    else:
        index_file.write_text(content)
        print(f"  Updated MEMORY.md with {len(lines)} entries")


def log_consolidation(memory_dir: Path, action: str, count: int, dry_run: bool = False) -> None:
    """Log consolidation event."""
    log_file = memory_dir / "CONSOLIDATION_LOG.md"

    timestamp = datetime.now(tz=timezone.utc).isoformat()
    entry = f"- {timestamp}: {action} ({count} items)\n"

    if dry_run:
        print(f"  [DRY] Would log: {entry.strip()}")
    else:
        if log_file.exists():
            log_file.write_text(log_file.read_text() + entry)
        else:
            log_file.write_text(f"# Consolidation Log\n\n{entry}")


def main() -> None:
    import sys

    memory_dir = find_memory_dir()
    if not memory_dir:
        print("Memory directory not found.")
        return

    dry_run = "--dry-run" in sys.argv
    mode = "full"
    if "--consolidate" in sys.argv:
        mode = "consolidate"
    elif "--archive" in sys.argv:
        mode = "archive"

    print(f"Memory consolidation: {mode}" + (" (dry-run)" if dry_run else ""))
    print(f"Directory: {memory_dir}\n")

    files = parse_memory_files(memory_dir)
    print(f"Found {len(files)} memory files\n")

    merged = 0
    archived = 0

    if mode in ["consolidate", "full"]:
        print("Step 1: Finding similar files...")
        similar = find_similar_decisions(files)
        if similar:
            print(f"  Found {len(similar)} similar pairs\n")
            merged = consolidate_similar(memory_dir, similar, dry_run=dry_run)
        else:
            print("  No similar pairs found.\n")

    if mode in ["archive", "full"]:
        print("Step 2: Archiving old observations (>30 days)...")
        archived = archive_old_observations(memory_dir, days=30, dry_run=dry_run)
        if archived > 0:
            print()

    print("Step 3: Updating MEMORY.md index...")
    update_memory_index(memory_dir, dry_run=dry_run)

    print(f"\nSummary: {merged} merged, {archived} archived")

    if not dry_run:
        log_consolidation(memory_dir, f"{mode} consolidation", merged + archived)
        print(f"Logged to CONSOLIDATION_LOG.md")


if __name__ == "__main__":
    main()
