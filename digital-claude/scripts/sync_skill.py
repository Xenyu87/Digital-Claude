#!/usr/bin/env python3
"""Sync della skill dalla sorgente alla copia installata in `~/.claude/skills/digital-claude`.

Esegui dalla root della skill sorgente:
    python scripts/sync_skill.py            # sync verso il default
    python scripts/sync_skill.py --dry-run  # mostra cosa farebbe
    python scripts/sync_skill.py --dest <path>   # sync verso path custom

Copia: SKILL.md, references/*.md, assets/**/*, scripts/*.py.
Non tocca file estranei nella destinazione.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEST = Path.home() / ".claude" / "skills" / "digital-claude"

ITEMS = [
    "SKILL.md",
    "references",
    "assets",
    "recipes",
    "skill_library",
    "scripts",
    "tests",
]


def copy_item(src: Path, dst: Path, dry: bool) -> int:
    if not src.exists():
        return 0
    n = 0
    if src.is_file():
        if dry:
            print(f"WOULD COPY  {src} -> {dst}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"COPY        {src.name}")
        return 1
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        target = dst / rel
        if dry:
            print(f"WOULD COPY  {p} -> {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            print(f"COPY        {rel.as_posix()}")
        n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not (ROOT / "SKILL.md").exists():
        print(f"ERRORE: SKILL.md non trovato in {ROOT}", file=sys.stderr)
        return 1

    dest: Path = args.dest
    print(f"Sorgente: {ROOT}")
    print(f"Destinazione: {dest}")
    if not dest.exists() and not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    total = 0
    for item in ITEMS:
        total += copy_item(ROOT / item, dest / item, args.dry_run)

    print()
    print(f"{'WOULD COPY' if args.dry_run else 'Copiati'}: {total} file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
