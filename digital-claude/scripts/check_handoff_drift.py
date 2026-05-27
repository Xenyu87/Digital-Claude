#!/usr/bin/env python3
"""Rileva drift tra AI_HANDOFF.md e lo stato git recente.

Confronta i file toccati negli ultimi 3 commit con i file menzionati in
AI_HANDOFF.md. Se ci sono file significativi non menzionati, stampa un avviso.

Trigger: hook SessionStart (non-blocking — stampa solo, non blocca).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, check=False, cwd=cwd)
        return r.stdout.strip()
    except FileNotFoundError:
        return ""


def in_git_repo(cwd: Path) -> bool:
    return git("rev-parse", "--is-inside-work-tree", cwd=cwd) == "true"


def recent_files(cwd: Path, n_commits: int = 3) -> set[str]:
    out = git("diff", f"HEAD~{n_commits}", "HEAD", "--name-only", cwd=cwd)
    return {f for f in out.splitlines() if f.strip()}


def handoff_mentioned_files(handoff_path: Path) -> set[str]:
    text = handoff_path.read_text(encoding="utf-8", errors="ignore")
    # Estrae token simili a percorsi file (contengono / o . con estensione)
    tokens = re.findall(r"[\w./-]+\.(?:ts|tsx|js|mjs|py|md|json|sql|sh|css|yaml|yml|env)\b", text)
    return {t.lstrip("/") for t in tokens}


def main() -> int:
    cwd = Path.cwd()

    if not in_git_repo(cwd):
        return 0

    handoff = cwd / "AI_HANDOFF.md"
    if not handoff.exists():
        return 0

    # Controlla quanti commit ci sono (repo nuovi hanno meno di 3)
    count = git("rev-list", "--count", "HEAD", cwd=cwd)
    n = min(int(count) if count.isdigit() else 0, 3)
    if n == 0:
        return 0

    changed = recent_files(cwd, n)
    mentioned = handoff_mentioned_files(handoff)

    # File significativi toccati ma non menzionati in AI_HANDOFF.md
    # Ignora lock files, build artifacts, state files
    IGNORE = re.compile(r"(package-lock|\.lock|node_modules|\.next|dist/|build/|\.state\.json)")
    untracked = {
        f for f in changed
        if not IGNORE.search(f) and not any(m in f or f in m for m in mentioned)
    }

    if len(untracked) >= 3:
        files_str = "\n  ".join(sorted(untracked)[:8])
        more = f"\n  ... e altri {len(untracked) - 8}" if len(untracked) > 8 else ""
        print(
            f"\n⚠ Drift AI_HANDOFF.md: {len(untracked)} file toccati di recente non compaiono nel doc:\n"
            f"  {files_str}{more}\n"
            f"Considera di aggiornare AI_HANDOFF.md prima di iniziare.\n"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
