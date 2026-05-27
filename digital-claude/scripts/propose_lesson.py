#!/usr/bin/env python3
"""Scrive una voce TBD in AI_AGENT_LOG.md del progetto corrente quando il diff
dell'ultimo commit coinvolge >=5 file (task non banale), oppure quando rileva
correzioni esplicite dell'utente nel jsonl della sessione (reflexion loop).

La voce e' un *placeholder*: contiene metadata (data, commit, lista file) e
2 segnaposto `<TBD ...>` che la skill compila al primo turno della prossima
sessione (vedi regola in SKILL.md sezione "Loop incident -> knowledge update").

Se vengono rilevate correzioni, la voce include anche il testo della correzione
come contesto per facilitare la compilazione automatica.

Cosi' l'utente non deve mai copiare/incollare nulla: la skill gestisce tutto.

Trigger consigliato: hook Stop di Claude Code (gia' configurato in
~/.claude/settings.json).

Comportamento:
- non scrive se non e' in un git repo
- non scrive se il diff coinvolge <5 file (soglia "task non banale")
- non scrive se l'ultima voce TBD non e' ancora stata compilata (evita rumore)
- crea AI_AGENT_LOG.md se manca

Uso (manuale):
    python scripts/propose_lesson.py              # ultimo commit
    python scripts/propose_lesson.py --staged     # diff staged
    python scripts/propose_lesson.py --threshold 3
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path


TBD_MARKER = "<TBD"
LOG_FILENAME = "AI_AGENT_LOG.md"

# Pattern che indicano una correzione esplicita dell'utente
CORRECTION_PATTERNS = re.compile(
    r"\b(no[,!.]|non farlo|non fare|stop|sbagliato|hai sbagliato|"
    r"non così|non voglio|evita|non usare|non aggiungere|"
    r"don'?t|wrong|stop doing|avoid|don'?t do that)\b",
    re.IGNORECASE,
)


def find_session_jsonl() -> Path | None:
    """Trova il jsonl della sessione corrente leggendo CLAUDE_CONVERSATION_FILE o cercando il più recente."""
    env_path = os.environ.get("CLAUDE_CONVERSATION_FILE") or os.environ.get("CLAUDE_SESSION_FILE")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    # Fallback: jsonl più recente in ~/.claude/conversations/
    claude_home = Path.home() / ".claude"
    conv_dirs = [claude_home / "conversations", claude_home / "projects"]
    candidates: list[Path] = []
    for d in conv_dirs:
        if d.is_dir():
            candidates.extend(d.rglob("*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def detect_corrections(jsonl_path: Path) -> list[str]:
    """Estrae testi di messaggi utente con pattern di correzione (ultimi 200 messaggi)."""
    corrections: list[str] = []
    try:
        lines = jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines[-200:]:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Supporta sia il formato {role, content} che {type, content}
            role = obj.get("role") or obj.get("type", "")
            if role not in ("human", "user"):
                continue
            content = obj.get("content", "")
            if isinstance(content, list):
                text = " ".join(
                    c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"
                )
            elif isinstance(content, str):
                text = content
            else:
                continue
            if CORRECTION_PATTERNS.search(text):
                snippet = text.strip()[:200].replace("\n", " ")
                corrections.append(snippet)
    except Exception:
        pass
    return corrections


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return ""


def in_git_repo(cwd: Path) -> bool:
    out = git("rev-parse", "--is-inside-work-tree", cwd=cwd)
    return out == "true"


def is_skill_repo(cwd: Path) -> bool:
    """True se cwd e' il repo di una skill (ha SKILL.md alla root + references/).

    Le skill hanno il loro improvement-log.md / release-notes.md per la storia;
    il loop Reflexion in AI_AGENT_LOG.md serve per task utente, non per
    skill maintenance.
    """
    return (cwd / "SKILL.md").is_file() and (cwd / "references").is_dir()


def files_changed(staged: bool, cwd: Path) -> list[str]:
    if staged:
        out = git("diff", "--cached", "--name-only", cwd=cwd)
    else:
        out = git("diff", "HEAD~1", "HEAD", "--name-only", cwd=cwd)
    return [f for f in out.splitlines() if f.strip()]


def last_entry_is_tbd(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    # se l'ultimo header `##` ha sotto un TBD non compilato, evita di accodare un altro placeholder
    sections = text.split("\n## ")
    if len(sections) < 2:
        return False
    last = sections[-1]
    return TBD_MARKER in last


def append_tbd_entry(
    log_path: Path,
    files: list[str],
    commit_msg: str,
    today: str,
    corrections: list[str] | None = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header_block = ""
    if not log_path.exists():
        header_block = (
            "# AI_AGENT_LOG\n\n"
            "> Solo errori, sprechi, lezioni. Niente attivita' ordinaria.\n"
            "> Le voci con `<TBD ...>` vengono compilate automaticamente dalla skill al turno successivo.\n\n"
        )

    sample = "\n".join(f"  - {f}" for f in files[:10])
    more = f"\n  - ... e altri {len(files) - 10} file" if len(files) > 10 else ""

    correction_block = ""
    if corrections:
        snippets = "\n".join(f'  > "{c}"' for c in corrections[:3])
        correction_block = f"\n  Correzioni rilevate nella sessione:\n{snippets}\n"

    entry = (
        f"## {today}\n"
        f"- **<TBD pattern_type>**: <TBD descrizione dello spreco/errore nel task "
        f"'{commit_msg}' ({len(files)} file toccati)>\n"
        f"  Lezione: <TBD regola futura, una riga>\n"
        f"  File toccati:\n{sample}{more}\n"
        f"{correction_block}\n"
    )

    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8", errors="ignore")
        new_content = existing.rstrip() + "\n\n" + entry
    else:
        new_content = header_block + entry

    log_path.write_text(new_content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true", help="diff staged invece di ultimo commit")
    ap.add_argument("--threshold", type=int, default=5, help="numero minimo di file per proporre")
    args = ap.parse_args()

    cwd = Path.cwd()

    if not in_git_repo(cwd):
        return 0

    if is_skill_repo(cwd):
        return 0

    # Rilevamento correzioni dalla sessione (reflexion loop)
    corrections: list[str] = []
    jsonl = find_session_jsonl()
    if jsonl:
        corrections = detect_corrections(jsonl)
        if corrections:
            print(f"propose_lesson: rilevate {len(corrections)} correzione/i utente nella sessione.")

    files = files_changed(args.staged, cwd)
    n = len(files)

    # Scrivi voce se: abbastanza file toccati OPPURE correzioni rilevate
    if n < args.threshold and not corrections:
        return 0

    log_path = cwd / LOG_FILENAME
    if last_entry_is_tbd(log_path):
        print(f"propose_lesson: ultima voce gia' TBD in {LOG_FILENAME}, non accodo (evito rumore).")
        return 0

    today = dt.date.today().isoformat()
    commit_msg = (
        git("log", "-1", "--pretty=%s", cwd=cwd) if not args.staged else "(staged)"
    )

    append_tbd_entry(log_path, files, commit_msg, today, corrections=corrections or None)
    reason = []
    if n >= args.threshold:
        reason.append(f"{n} file toccati")
    if corrections:
        reason.append(f"{len(corrections)} correzioni utente")
    print(
        f"propose_lesson: scritta voce TBD in {log_path} ({', '.join(reason)}). "
        f"La skill la compilera' al prossimo turno."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
