#!/usr/bin/env python3
"""Installa i git hook versionati in scripts/hooks/ dentro .git/hooks/.

Necessario perche' .git/hooks/ non e' versionato.

Uso:
    python scripts/install_hooks.py            # installa
    python scripts/install_hooks.py --check    # mostra cosa farebbe, non scrive
    python scripts/install_hooks.py --uninstall  # rimuove

Cross-platform (Windows/macOS/Linux). Su Windows il hook gira via Git Bash
incluso in Git for Windows.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "scripts" / "hooks"
TARGET_DIR = ROOT / ".git" / "hooks"
MANAGED = ["pre-commit"]


def install(check_only: bool = False) -> int:
    if not TARGET_DIR.exists():
        print(f"ERRORE: {TARGET_DIR} non esiste. Sei in un repo git?")
        return 1

    for name in MANAGED:
        src = SOURCE_DIR / name
        dst = TARGET_DIR / name
        if not src.exists():
            print(f"SKIP: {src} non trovato.")
            continue

        if check_only:
            status = "EXISTS (sovrascriverei)" if dst.exists() else "NEW"
            print(f"[check] {dst}: {status}")
            continue

        shutil.copy2(src, dst)
        # chmod +x (no-op su Windows ma chiarezza)
        try:
            os.chmod(dst, 0o755)
        except Exception:
            pass
        print(f"INSTALLATO: {dst}")

    if check_only:
        print("\n(dry-run; nessun file scritto)")
    return 0


def uninstall() -> int:
    for name in MANAGED:
        dst = TARGET_DIR / name
        if dst.exists():
            dst.unlink()
            print(f"RIMOSSO: {dst}")
        else:
            print(f"SKIP: {dst} gia' assente.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()

    if args.uninstall:
        return uninstall()
    return install(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
