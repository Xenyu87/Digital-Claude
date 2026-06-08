#!/usr/bin/env python3
"""Aggrega i token della sessione Claude Code corrente e li invia alla dashboard.

Trigger: hook Stop di Claude Code (configurato in ~/.claude/settings.json).

Best-effort: timeout breve, mai blocca. Skip silenzioso se:
- cwd e' un repo di skill (no meta-tracking)
- cwd non e' un repo git
- nessun file jsonl trovato per la sessione
- la dashboard e' giu'

Dati raccolti:
- input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens
- duration_seconds (delta primo/ultimo timestamp nel jsonl)
- tool_calls_count (entry con content type 'tool_use')
- summary (primo prompt utente, troncato 160 char)
- category (euristica sul verbo principale del primo prompt)
- files_touched (da ultimo commit, se presente)
- skill_version (da release-notes.md)

Dati NON raccolti (limite Claude Code):
- cost in USD (lo stima la dashboard dai token)
- status (sempre "ok": l'hook scatta su Stop normale; failure non triggerano Stop)

Uso (manuale):
    python scripts/auto_log_task.py
    python scripts/auto_log_task.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Aggiungi scripts/ al path per importare helper
sys.path.insert(0, str(Path(__file__).parent))
from buffering_client import post_with_fallback, flush_queue
from dashboard_client import discover_dashboard_url


CLAUDE_HOME = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_HOME / "projects"


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=False, cwd=cwd
        )
        return out.stdout.strip()
    except FileNotFoundError:
        return ""


def in_git_repo(cwd: Path) -> bool:
    return git("rev-parse", "--is-inside-work-tree", cwd=cwd) == "true"


def is_skill_repo(cwd: Path) -> bool:
    return (cwd / "SKILL.md").is_file() and (cwd / "references").is_dir()


def files_touched(cwd: Path) -> list[str]:
    out = git("diff", "HEAD~1", "HEAD", "--name-only", cwd=cwd)
    return [f for f in out.splitlines() if f.strip()]


def files_touched_from_jsonl(jsonl_path: Path, cwd: Path) -> list[str]:
    """Estrae i file modificati dalle entry tool_use Edit/Write/MultiEdit/NotebookEdit nel jsonl.

    Affidabile anche se l'utente non committa: legge cio' che Claude ha
    effettivamente toccato durante la sessione.
    """
    edit_tools = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
    files: set[str] = set()
    try:
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict) or c.get("type") != "tool_use":
                        continue
                    if c.get("name") not in edit_tools:
                        continue
                    inp = c.get("input")
                    if not isinstance(inp, dict):
                        continue
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    if isinstance(fp, str) and fp.strip():
                        # rendi relativo al cwd se possibile
                        try:
                            rel = str(Path(fp).resolve().relative_to(cwd.resolve()))
                            files.add(rel)
                        except (ValueError, OSError):
                            files.add(fp)
    except OSError:
        pass
    return sorted(files)


def encode_cwd(cwd: Path) -> str:
    """Replica il naming che Claude Code usa per la dir in ~/.claude/projects/.

    Pattern osservato: ogni carattere non alfanumerico (es. ':', '\\', '/', ' ')
    diventa un trattino singolo. `c:\\Progetti\\3D Pad` -> `c--Progetti-3D-Pad`.
    """
    s = str(cwd)
    s = re.sub(r"[^A-Za-z0-9]", "-", s)
    return s


def find_session_jsonl(cwd: Path) -> Path | None:
    encoded = encode_cwd(cwd)
    if not PROJECTS_DIR.exists():
        return None
    # match case-insensitive
    for d in PROJECTS_DIR.iterdir():
        if d.name.lower() == encoded.lower() and d.is_dir():
            jsonl_files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            return jsonl_files[0] if jsonl_files else None
    return None


def aggregate_usage(jsonl_path: Path) -> dict:
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
    models: dict[str, int] = {}
    try:
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = obj.get("message")
                if not isinstance(msg, dict):
                    continue
                mdl = msg.get("model")
                if isinstance(mdl, str) and mdl:
                    models[mdl] = models.get(mdl, 0) + 1
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                for k in totals:
                    val = usage.get(k, 0)
                    if isinstance(val, (int, float)):
                        totals[k] += int(val)
    except OSError:
        pass
    # model_used: il piu' frequente (l'orchestratore puo' fare hop fra modelli,
    # qui ci interessa il "principale" della sessione).
    model_used = max(models.items(), key=lambda x: x[1])[0] if models else None
    totals["model_used"] = model_used
    return totals


def parse_session_meta(jsonl_path: Path) -> dict:
    """Estrae duration, tool_calls_count, summary, first_user_text dal jsonl."""
    ts_min = None
    ts_max = None
    tool_calls = 0
    tool_errors = 0
    agents_used: list[str] = []
    agent_models: list[str] = []
    # Manteniamo l'ULTIMO prompt reale (non il primo): il jsonl accumula
    # sessioni resume su resume, quindi il "primo" e' sempre lo stesso
    # messaggio storico. L'ultimo prompt utente prima dello Stop e' il
    # vero trigger del turno corrente.
    last_user_text: str | None = None
    try:
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = obj.get("timestamp")
                if isinstance(ts, str):
                    if ts_min is None or ts < ts_min:
                        ts_min = ts
                    if ts_max is None or ts > ts_max:
                        ts_max = ts
                msg = obj.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict):
                            if c.get("type") == "tool_use":
                                tool_calls += 1
                                if c.get("name") == "Agent":
                                    inp = c.get("input") or {}
                                    st = inp.get("subagent_type")
                                    if st and st not in agents_used:
                                        agents_used.append(st)
                                    am = inp.get("model")
                                    if am and am not in agent_models:
                                        agent_models.append(am)
                            elif c.get("type") == "tool_result" and c.get("is_error") is True:
                                tool_errors += 1
                if obj.get("type") == "user" and msg.get("role") == "user":
                    text = None
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                text = c.get("text", "")
                                break
                    if not text:
                        continue
                    stripped = text.strip()
                    # filtra wrapper di sistema / tool_result / resume markers
                    if (
                        stripped.startswith("<")
                        or stripped.startswith("[Request")
                        or stripped.startswith("Caveat:")
                        or "Continue from where you left off" in stripped
                        or "This session is being continued" in stripped
                    ):
                        continue
                    last_user_text = stripped
    except OSError:
        pass
    first_user_text = last_user_text

    duration = 0
    if ts_min and ts_max:
        # ISO 8601 con suffisso Z; per evitare dipendenze, parse minimale
        from datetime import datetime
        try:
            t0 = datetime.fromisoformat(ts_min.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(ts_max.replace("Z", "+00:00"))
            duration = max(0, int((t1 - t0).total_seconds()))
        except ValueError:
            duration = 0

    summary = None
    if first_user_text:
        summary = first_user_text[:160]

    return {
        "duration_seconds": duration,
        "tool_calls_count": tool_calls,
        "tool_errors_count": tool_errors,
        "summary": summary,
        "first_user_text": first_user_text or "",
        "agents_used": agents_used,
        "agent_models": agent_models,
    }


_CATEGORY_PATTERNS = [
    # ops ha priorità: parole chiave sistema/infra prima delle altre per
    # evitare di classificare "configura porta del servizio" come modifica.
    ("ops",                r"\b(systemd|journalctl|syncthing|ssh|sshd|lxc|proxmox|cron(tab)?|firewall|iptables|nginx|deploy(o|are)?|servizio|service|porta\s*\d+|reboot|riavvia(re)?|backup|monta(re)?|mount)\b"),
    ("miglioramento_skill", r"\b(aggiorna(re)? la skill|automigliorati|migliora(re)? la skill|miglioramento skill|usa la skill (sulla|su) ?(s)?kill)\b"),
    ("nuova_app",          r"\b(crea(re)?|scaffold|parti(re)? da zero|nuovo progetto|nuova app|inizia(re)? un)\b"),
    ("audit",              r"\b(rivedi|review|audit|valuta|controlla|analizza|cosa possiamo migliorare)\b"),
    ("bug_rescue",         r"\b(non funziona|errore|crash|bug|rotto|fix|risolvi|debug)\b"),
]


def detect_category(first_user_text: str) -> str:
    t = (first_user_text or "").lower()
    if not t:
        return "modifica"
    for cat, pat in _CATEGORY_PATTERNS:
        if re.search(pat, t):
            return cat
    return "modifica"


def parse_lessons_from_log(cwd: Path) -> list[dict]:
    """Legge AI_AGENT_LOG.md ed estrae voci compilate (senza marcatori TBD)."""
    log_path = cwd / "AI_AGENT_LOG.md"
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    sections = re.split(r"\n## ", text)
    lessons = []
    for section in sections[1:]:
        if "<TBD" in section:
            continue
        # Estrae tipo e descrizione dalla voce "- **tipo**: descrizione"
        m = re.search(r"-\s+\*\*(\w+)\*\*:\s*(.+?)(?:\n|$)", section)
        if not m:
            continue
        raw_type = m.group(1).lower()
        description = m.group(2).strip()
        pattern_type = (
            "spreco" if "spreco" in raw_type
            else "errore" if raw_type in ("errore", "error", "bug")
            else "pattern"
        )
        # Estrae regola dalla riga "Lezione: ..."
        rule_m = re.search(r"Lezione:\s*(.+?)(?:\n|$)", section)
        if not rule_m:
            continue
        rule = rule_m.group(1).strip()
        if not rule or "<TBD" in rule:
            continue
        lessons.append({"pattern_type": pattern_type, "description": description, "rule": rule})
    return lessons


def post_errors(meta: dict, task_id: str | None, base: str, dry_run: bool) -> None:
    """Invia un errore alla dashboard se la sessione ha avuto tool_errors significativi."""
    errs = meta.get("tool_errors_count", 0) or 0
    calls = meta.get("tool_calls_count", 0) or 0
    if errs < 3 and not (calls > 0 and errs / calls > 0.20):
        return
    summary = meta.get("summary", "")[:120]
    payload = [{
        "error_type": "tool_errors",
        "message": f"{errs} tool call fallite su {calls} ({summary})",
        "task_id": task_id,
    }]
    if dry_run:
        print(f"auto_log_task [dry-run]: errore tool_errors ({errs}/{calls}) da inviare")
        return
    url = base.rstrip("/") + "/api/errors"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        pass


def post_lessons(lessons: list[dict], task_id: str | None, dry_run: bool = False) -> None:
    if not lessons:
        return
    for l in lessons:
        l["task_id"] = task_id
    if dry_run:
        print(f"auto_log_task [dry-run]: {len(lessons)} lezioni da AI_AGENT_LOG.md")
        return
    post_with_fallback("/api/lessons", {"lessons": lessons})


def detect_skill_version() -> str:
    env = os.environ.get("SKILL_VERSION")
    if env:
        return env
    candidates = [
        CLAUDE_HOME / "skills" / "digital-claude" / "references" / "release-notes.md",
        Path("c:/Progetti/Claude-Skill-Coordinator/references/release-notes.md"),  # legacy clone Windows
    ]
    for p in candidates:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        versions = re.findall(r"^##\s+v(\d+)\.(\d+)\.(\d+)\b", text, re.MULTILINE)
        if not versions:
            continue
        m = max(versions, key=lambda v: (int(v[0]), int(v[1]), int(v[2])))
        return f"v{m[0]}.{m[1]}.{m[2]}"
    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="non manda POST, stampa solo")
    args = ap.parse_args()

    cwd = Path.cwd()

    if not in_git_repo(cwd):
        return 0
    if is_skill_repo(cwd):
        return 0

    jsonl = find_session_jsonl(cwd)
    if not jsonl:
        return 0

    usage = aggregate_usage(jsonl)
    if usage["input_tokens"] == 0 and usage["output_tokens"] == 0:
        # sessione senza scambio AI: niente da loggare
        return 0

    meta = parse_session_meta(jsonl)
    category = detect_category(meta["first_user_text"])

    # files_touched: unione di git diff e tool_use Edit/Write nel jsonl
    files_set = set(files_touched(cwd)) | set(files_touched_from_jsonl(jsonl, cwd))

    # Override categoria da files_touched (più affidabile del prompt regex):
    # - tocchi file della skill → miglioramento_skill
    # - tocchi systemd unit, crontab, scripts ops → ops
    if category == "modifica":
        files_lower = " ".join(files_set).lower()
        if "/.claude/skills/" in files_lower or "skill.md" in files_lower:
            category = "miglioramento_skill"
        elif any(k in files_lower for k in ("/etc/systemd/", ".service", "crontab", "/ops/", "nginx", "/etc/cron")):
            category = "ops"

    # status: 'partial' se ci sono errori unresolved (heuristic: >2 tool errors o
    # >20% delle tool call hanno fallito). Altrimenti 'ok'.
    calls = meta["tool_calls_count"] or 0
    errs = meta["tool_errors_count"] or 0
    if errs >= 3 or (calls > 0 and errs / calls > 0.20):
        status = "partial"
    else:
        status = "ok"

    payload = {
        "project_path": str(cwd),
        "category": category,
        "files_touched": sorted(files_set),
        "duration_seconds": meta["duration_seconds"],
        "tool_calls_count": meta["tool_calls_count"],
        "summary": meta["summary"],
        "status": status,
        "skill_version": detect_skill_version(),
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cache_read_tokens": usage["cache_read_input_tokens"],
        "cache_creation_tokens": usage["cache_creation_input_tokens"],
        "session_jsonl": jsonl.name,
        "model_used": usage.get("model_used"),
        "agents_used": meta.get("agents_used", []),
        "models": list({usage.get("model_used"), *meta.get("agent_models", [])} - {None}),
    }
    # Bridge da UserPromptSubmit hook: leggi l'ultimo suggerimento di routing
    # per questa sessione (se presente).
    try:
        sid = jsonl.stem  # filename = "<session_id>.jsonl"
        route_file = Path(f"/tmp/claude-route-{sid}.json")
        # Apertura atomica (no TOCTOU): apri direttamente, gestisci FileNotFoundError.
        with route_file.open(encoding="utf-8") as fh:
            route_data = json.loads(fh.read())
        if isinstance(route_data, dict):
            suggested = route_data.get("model_suggested")
            _ALLOWED_MODELS = {"haiku", "sonnet", "opus"}
            if isinstance(suggested, str) and suggested in _ALLOWED_MODELS:
                payload["model_suggested"] = suggested
    except (OSError, json.JSONDecodeError):
        pass
    # Cap esplicito via env (es. CAP_TOKENS=120000). Se omesso, la dashboard
    # applica il default per categoria.
    cap_env = os.environ.get("CAP_TOKENS")
    if cap_env and cap_env.isdigit():
        payload["tokens_budget_max"] = int(cap_env)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        lessons = parse_lessons_from_log(cwd)
        print(f"auto_log_task [dry-run]: {len(lessons)} lezioni da AI_AGENT_LOG.md")
        return 0

    # Invia log principale alla dashboard (con buffering automatico se offline)
    task_id: str | None = None
    if post_with_fallback("/api/log", payload):
        print(f"auto_log_task: ✓ inviato alla dashboard. tokens={usage['input_tokens']}/{usage['output_tokens']}")
    else:
        print(f"auto_log_task: ⚠️  offline, dati salvati localmente. Verranno inviati quando la dashboard si riconnette.")

    # Invia lezioni compilate da AI_AGENT_LOG.md (non bloccante)
    lessons = parse_lessons_from_log(cwd)
    if lessons:
        post_lessons(lessons, task_id, dry_run=False)

    # Invia errore se sessione parziale (non bloccante)
    base = discover_dashboard_url() or "http://localhost:3001"
    post_errors(meta, task_id, base, dry_run=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
