#!/usr/bin/env python3
"""Background drain: manutenzione automatica notturna su un progetto.

Gira su branch dedicato drain/YYYY-MM-DD, mai su master.
Fail-safe: ogni sub-attivita' e' isolata in try/except, exit 0 sempre.

Uso:
    python scripts/drain.py --project /path/al/progetto
    python scripts/drain.py --project /path --curriculum-weekly  # solo domenica

Prerequisiti: gh CLI installata e autenticata, git configurato.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DRAIN_BRANCH_PREFIX = "drain"


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list[str], cwd: str | Path | None = None, capture: bool = True) -> tuple[int, str, str]:
    """Esegue un comando, ritorna (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=capture,
            text=True,
            check=False,
            timeout=120,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def proj_slug(project_path: str) -> str:
    # Claude Code usa lo slug con leading dash (es. -root-Progetti-foo).
    # Non strippare il dash iniziale, altrimenti i path non matchano la directory reale.
    return re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")


def drain_log_path(project_path: str) -> Path:
    slug = proj_slug(project_path)
    base = Path.home() / ".claude" / "projects" / slug / "memory"
    base.mkdir(parents=True, exist_ok=True)
    return base / "drain-log.jsonl"


def append_drain_log(log_path: Path, record: dict) -> None:
    line = json.dumps(record, ensure_ascii=False)
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    tmp = log_path.with_suffix(".jsonl.tmp")
    tmp.write_text(existing + line + "\n", encoding="utf-8")
    tmp.replace(log_path)


# ── Sub-attivita' ─────────────────────────────────────────────────────────────

def complete_tbd_entries(project_path: str) -> dict:
    """Compila righe <TBD ...> in AI_AGENT_LOG.md via haiku CLI."""
    result = {"name": "complete_tbd_entries", "status": "skip", "detail": ""}
    log_file = Path(project_path) / "AI_AGENT_LOG.md"
    if not log_file.exists():
        result["detail"] = "AI_AGENT_LOG.md non trovato"
        return result

    text = log_file.read_text(encoding="utf-8")
    tbd_lines = [l for l in text.splitlines() if "<TBD" in l]
    if not tbd_lines:
        result["detail"] = "nessuna voce TBD"
        return result

    # Prendi diff recente per contesto
    _, diff_stat, _ = run(["git", "diff", "HEAD~1", "HEAD", "--stat"], cwd=project_path)
    _, log_out, _ = run(["git", "log", "--oneline", "-5"], cwd=project_path)

    prompt = (
        f"Hai {len(tbd_lines)} voci TBD in AI_AGENT_LOG.md. "
        f"Basandoti su questi dati git:\n\nGit stat:\n{diff_stat}\n\nCommit:\n{log_out}\n\n"
        f"Voci TBD:\n" + "\n".join(tbd_lines) + "\n\n"
        "Per ognuna, scrivi una lezione tecnica breve (1 riga). "
        "Formato: <vecchia riga TBD> --> <lezione>. "
        "Niente PII, niente nomi propri."
    )

    code, out, err = run(
        ["claude", "--model", "haiku", "--print", prompt],
        cwd=project_path,
    )
    if code != 0:
        result["status"] = "error"
        result["detail"] = f"claude CLI: {err[:200]}"
        return result

    # Applica le sostituzioni nel file
    new_text = text
    for line in out.splitlines():
        if "-->" in line:
            parts = line.split("-->", 1)
            old = parts[0].strip()
            new = parts[1].strip()
            if old in new_text:
                new_text = new_text.replace(old, new, 1)

    log_file.write_text(new_text, encoding="utf-8")
    result["status"] = "ok"
    result["detail"] = f"{len(tbd_lines)} voci TBD compilate"
    return result


def analyze_tool_errors(project_path: str) -> dict:
    """Raggruppa errori ricorrenti da coordination-log e propone lezioni."""
    result = {"name": "analyze_tool_errors", "status": "skip", "detail": ""}

    slug = proj_slug(project_path)
    log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
    if not log_path.exists():
        result["detail"] = "coordination-log.jsonl non trovato"
        return result

    # Leggi ultimi 30gg
    cutoff = datetime.now(timezone.utc).timestamp() - 30 * 86400
    errors: list[str] = []
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Controlla data
            ts_str = rec.get("ts", "")
            try:
                from datetime import datetime as dt
                ts = dt.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if ts < cutoff:
                continue
            if rec.get("outcome") in ("failed", "partial"):
                lesson = rec.get("lesson") or ""
                cat = rec.get("category", "")
                errors.append(f"{cat}: {lesson}" if lesson else cat)
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        return result

    if not errors:
        result["detail"] = "nessun errore negli ultimi 30gg"
        return result

    # Raggruppa per testo simile (pattern semplice: primi 40 char)
    from collections import Counter
    pattern_counts = Counter(e[:40] for e in errors)
    top_patterns = [p for p, c in pattern_counts.most_common(5) if c >= 2]

    if not top_patterns:
        result["detail"] = "nessun pattern ricorrente (min 2 occorrenze)"
        return result

    # Scrivi proposte in improvement-log.md
    improvement_log = SKILL_DIR / "references" / "improvement-log.md"
    if improvement_log.exists():
        today = date.today().isoformat()
        entries = "\n".join(
            f"- {today} — auto-proposed — pattern errore ricorrente: {p} — da drain analyze_tool_errors <auto-proposed>"
            for p in top_patterns
        )
        text = improvement_log.read_text(encoding="utf-8")
        # Inserisce prima di "## Regole"
        if "## Regole" in text:
            text = text.replace("## Regole", entries + "\n## Regole", 1)
        else:
            text += "\n" + entries + "\n"
        improvement_log.write_text(text, encoding="utf-8")

    result["status"] = "ok"
    result["detail"] = f"{len(top_patterns)} pattern proposti"
    return result


def run_compaction(project_path: str) -> dict:
    """Compatta AI_*.md se >500 righe. Non promuove senza umano."""
    result = {"name": "run_compaction", "status": "skip", "detail": ""}
    ai_files = list(Path(project_path).glob("AI_*.md"))
    compacted = []
    for f in ai_files:
        try:
            lines = len(f.read_text(encoding="utf-8").splitlines())
            if lines > 500:
                # Lancia il validator per documentare lo stato
                code, out, _ = run(
                    [sys.executable, str(SKILL_DIR / "scripts" / "validate_skill.py")],
                    cwd=str(SKILL_DIR),
                )
                compacted.append(f"{f.name} ({lines} righe) — compaction richiesta, validazione: {'ok' if code == 0 else 'fail'}")
        except Exception as e:
            compacted.append(f"{f.name}: errore ({e})")

    if not compacted:
        result["detail"] = "nessun file AI_*.md supera 500 righe"
        return result

    result["status"] = "ok"
    result["detail"] = "; ".join(compacted) + " — revisione umana necessaria prima del merge"
    return result


def validate_skill_drift() -> dict:
    """Esegue validate_skill.py e check_handoff_drift.py."""
    result = {"name": "validate_skill_drift", "status": "skip", "detail": ""}

    validator = SKILL_DIR / "scripts" / "validate_skill.py"
    drift_check = SKILL_DIR / "scripts" / "check_handoff_drift.py"

    outputs = []
    if validator.exists():
        code, out, _ = run([sys.executable, str(validator)], cwd=str(SKILL_DIR))
        outputs.append(f"validator: {'OK' if code == 0 else 'FAIL'}\n{out[:500]}")
        result["status"] = "ok" if code == 0 else "error"
    if drift_check.exists():
        code2, out2, _ = run([sys.executable, str(drift_check)], cwd=str(SKILL_DIR))
        outputs.append(f"drift: {'OK' if code2 == 0 else 'FAIL'}\n{out2[:500]}")

    result["detail"] = "\n".join(outputs)
    return result


def summarize_changes(project_path: str, sub_results: list[dict]) -> str:
    """Genera il body markdown del PR."""
    today = date.today().isoformat()
    lines = [
        f"# Drain automatico — {today}",
        "",
        "## Sub-attivita'",
    ]
    for r in sub_results:
        icon = "OK" if r["status"] == "ok" else ("SKIP" if r["status"] == "skip" else "FAIL")
        lines.append(f"- [{icon}] **{r['name']}**: {r.get('detail', '')}")
    lines += [
        "",
        "## Nota",
        "Questo PR e' generato automaticamente dal drain notturno.",
        "Revisionare e mergiare manualmente se le modifiche sono corrette.",
        "Le modifiche a `improvement-log.md` hanno tag `<auto-proposed>` per identificarle.",
    ]
    return "\n".join(lines)


# ── Auto-curriculum settimanale ───────────────────────────────────────────────

def run_curriculum_weekly(project_path: str) -> dict:
    """Analisi settimanale (solo domenica): propone voci curriculum da coordination-log."""
    result = {"name": "curriculum_weekly", "status": "skip", "detail": ""}

    slug = proj_slug(project_path)
    log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
    if not log_path.exists():
        result["detail"] = "coordination-log.jsonl non trovato"
        return result

    # Ultimi 7gg
    cutoff = datetime.now(timezone.utc).timestamp() - 7 * 86400
    records: list[dict] = []
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = rec.get("ts", "")
            try:
                from datetime import datetime as dt
                ts = dt.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if ts >= cutoff:
                records.append(rec)
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        return result

    if not records:
        result["detail"] = "nessun record negli ultimi 7gg"
        return result

    from collections import Counter, defaultdict

    proposals: list[str] = []
    today = date.today().isoformat()

    # Pattern a: over-budget per categoria
    cat_costs: dict[str, list[float]] = defaultdict(list)
    for r in records:
        cat_costs[r.get("category", "?")].append(r.get("cost_usd", 0))
    for cat, costs in cat_costs.items():
        avg = sum(costs) / len(costs)
        if avg > 1.0:  # soglia $1 medio per task
            proposals.append(
                f"- {today} — auto-proposed-curriculum — over-budget ricorrente in '{cat}' "
                f"(avg ${avg:.2f}/task, {len(costs)} task) — rivedere routing modello — priority:high <auto-proposed-curriculum>"
            )

    # Pattern b: errori tool ripetuti
    error_records = [r for r in records if r.get("outcome") in ("failed", "partial")]
    if len(error_records) >= 2:
        proposals.append(
            f"- {today} — auto-proposed-curriculum — {len(error_records)} task falliti/parziali "
            f"negli ultimi 7gg — analizzare pattern errori in coordination-log — priority:med <auto-proposed-curriculum>"
        )

    # Pattern c: escalation frequente (models contiene opus quando la categoria non dovrebbe)
    escalations = [
        r for r in records
        if "opus" in [m.lower() for m in r.get("models", [])]
        and r.get("category") in ("ops", "modifica")
    ]
    if len(escalations) >= 2:
        proposals.append(
            f"- {today} — auto-proposed-curriculum — {len(escalations)} escalation Opus su categorie "
            f"ops/modifica negli ultimi 7gg — priority:high <auto-proposed-curriculum>"
        )

    if not proposals:
        result["detail"] = "nessun pattern critico rilevato"
        return result

    # Scrivi in improvement-log.md
    improvement_log = SKILL_DIR / "references" / "improvement-log.md"
    if improvement_log.exists():
        text = improvement_log.read_text(encoding="utf-8")
        entries = "\n".join(proposals)
        if "## Regole" in text:
            text = text.replace("## Regole", entries + "\n## Regole", 1)
        else:
            text += "\n" + entries + "\n"
        improvement_log.write_text(text, encoding="utf-8")

    result["status"] = "ok"
    result["detail"] = f"{len(proposals)} voci curriculum proposte"
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Background drain: manutenzione automatica")
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--curriculum-weekly", action="store_true",
                    help="Esegui auto-curriculum (solo se domenica)")

    try:
        args = ap.parse_args()
    except SystemExit:
        return 0

    project_path = str(Path(args.project).resolve())
    log_path = drain_log_path(project_path)

    # Non girare su dirty working tree
    code, status_out, _ = run(["git", "status", "--porcelain"], cwd=project_path)
    if status_out.strip():
        print(f"drain: working tree modificato, skip.", file=sys.stderr)
        return 0

    # Crea/vai su branch drain
    today_str = date.today().isoformat()
    branch_name = f"{DRAIN_BRANCH_PREFIX}/{today_str}"
    run(["git", "checkout", "-b", branch_name], cwd=project_path)

    sub_results: list[dict] = []

    # Sub-attivita' 1-4
    for fn in [
        lambda: complete_tbd_entries(project_path),
        lambda: analyze_tool_errors(project_path),
        lambda: run_compaction(project_path),
        lambda: validate_skill_drift(),
    ]:
        try:
            r = fn()
        except Exception as e:
            r = {"name": "unknown", "status": "error", "detail": str(e)}
        sub_results.append(r)
        print(f"drain [{r['name']}]: {r['status']} — {r.get('detail', '')}", file=sys.stderr)

    # Auto-curriculum (solo domenica o se flag esplicito)
    if args.curriculum_weekly:
        from datetime import datetime as dt
        is_sunday = dt.now().weekday() == 6
        if is_sunday or args.curriculum_weekly:
            try:
                r = run_curriculum_weekly(project_path)
            except Exception as e:
                r = {"name": "curriculum_weekly", "status": "error", "detail": str(e)}
            sub_results.append(r)
            print(f"drain [curriculum]: {r['status']} — {r.get('detail', '')}", file=sys.stderr)

    # PR body
    pr_body = summarize_changes(project_path, sub_results)

    # Commit se ci sono modifiche
    code, changed, _ = run(["git", "status", "--porcelain"], cwd=project_path)
    pr_url = ""
    if changed.strip():
        run(["git", "add", "-A"], cwd=project_path)
        run(
            ["git", "commit", "-m", f"drain: manutenzione automatica {today_str}"],
            cwd=project_path,
        )
        run(["git", "push", "-u", "origin", branch_name], cwd=project_path)

        # Apre PR con label drain
        code_pr, pr_out, _ = run(
            ["gh", "pr", "create",
             "--title", f"[drain] Manutenzione automatica {today_str}",
             "--body", pr_body,
             "--label", "drain"],
            cwd=project_path,
        )
        pr_url = pr_out if code_pr == 0 else ""

    # Log esecuzione
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": Path(project_path).name,
        "branch": branch_name,
        "sub_activities": sub_results,
        "pr_url": pr_url,
        "outcome": "ok" if all(r["status"] != "error" for r in sub_results) else "partial",
    }
    try:
        append_drain_log(log_path, record)
    except Exception as e:
        print(f"drain: errore log ({e})", file=sys.stderr)

    # Torna a main/master
    _, main_branch, _ = run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=project_path
    )
    main_branch = main_branch.replace("refs/remotes/origin/", "") or "main"
    run(["git", "checkout", main_branch], cwd=project_path)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"drain: errore fatale ({e}), exit 0.", file=sys.stderr)
        sys.exit(0)
