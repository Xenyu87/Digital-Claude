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
        # --permission-mode default evita lo skip dangerous (rifiutato da root via systemd).
        # Niente tool call previste: il drain applica le sostituzioni in Python.
        ["claude", "--permission-mode", "default", "--model", "haiku", "--print", prompt],
        cwd=project_path,
    )
    if code != 0:
        result["status"] = "error"
        result["detail"] = f"claude CLI: {err[:200]}"
        return result

    # Applica le sostituzioni nel file.
    # Sicurezza: accetta solo sostituzioni dove `old` è una riga TBD nota
    # e `new` non contiene pattern riservati (evita injection da output LLM).
    _RESERVED = {"-->", "<TBD", "<script", "<%", "$(", "`"}
    new_text = text
    tbd_set = set(tbd_lines)
    for line in out.splitlines():
        if "-->" not in line:
            continue
        parts = line.split("-->", 1)
        old = parts[0].strip()
        new = parts[1].strip()
        if old not in tbd_set:
            continue
        if any(tok in new for tok in _RESERVED):
            continue
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


def validate_skill_drift(project_path: str) -> dict:
    """Esegue validate_skill.py (sulla skill) e check_handoff_drift.py (sul progetto)."""
    result = {"name": "validate_skill_drift", "status": "skip", "detail": ""}

    validator = SKILL_DIR / "scripts" / "validate_skill.py"
    drift_check = SKILL_DIR / "scripts" / "check_handoff_drift.py"

    outputs = []
    if validator.exists():
        code, out, _ = run([sys.executable, str(validator)], cwd=str(SKILL_DIR))
        outputs.append(f"validator: {'OK' if code == 0 else 'FAIL'}\n{out[:500]}")
        result["status"] = "ok" if code == 0 else "error"
    if drift_check.exists():
        # drift checker usa Path.cwd(): va eseguito nel progetto target,
        # non nella skill (altrimenti segnala drift su file della skill).
        code2, out2, _ = run([sys.executable, str(drift_check)], cwd=project_path)
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


# ── Skill Exchange check ──────────────────────────────────────────────────────

SKILL_EXCHANGE_PATH = Path("/root/Progetti/SKILL_EXCHANGE.md")
SKILL_EXCHANGE_MARKER = "[ ] digital-claude"


def check_skill_exchange(project_path: str) -> dict:
    """Legge SKILL_EXCHANGE.md e segnala in improvement-log.md le feature di codex non ancora adottate da claude."""
    result = {"name": "check_skill_exchange", "status": "skip", "detail": ""}

    if not SKILL_EXCHANGE_PATH.exists():
        result["detail"] = "SKILL_EXCHANGE.md non trovato"
        return result

    text = SKILL_EXCHANGE_PATH.read_text(encoding="utf-8")

    # Raccogli i titoli delle feature non ancora adottate da claude (salta code block)
    unadopted: list[str] = []
    current_title = ""
    in_code_block = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if line.startswith("### "):
            current_title = line.lstrip("#").strip()
        if SKILL_EXCHANGE_MARKER in line and current_title:
            unadopted.append(current_title)

    if not unadopted:
        result["detail"] = "nessuna feature codex da valutare"
        return result

    improvement_log = SKILL_DIR / "references" / "improvement-log.md"
    if not improvement_log.exists():
        result["detail"] = f"{len(unadopted)} feature trovate ma improvement-log.md assente"
        return result

    today = date.today().isoformat()
    existing = improvement_log.read_text(encoding="utf-8")

    # Filtra solo quelle non già presenti nel log (evita duplicati per le stesse feature)
    new_entries = []
    for feat in unadopted:
        tag = f"<skill-exchange> {feat[:60]}"
        if tag not in existing:
            new_entries.append(
                f"- {today} — skill-exchange — feature codex non adottata: {feat} — valutare adozione in digital-claude {tag}"
            )

    if not new_entries:
        result["detail"] = f"{len(unadopted)} feature già segnalate in precedenza"
        return result

    entries_text = "\n".join(new_entries)
    if "## Regole" in existing:
        updated = existing.replace("## Regole", entries_text + "\n## Regole", 1)
    else:
        updated = existing + "\n" + entries_text + "\n"
    improvement_log.write_text(updated, encoding="utf-8")

    result["status"] = "ok"
    result["detail"] = f"{len(new_entries)} nuove feature codex segnalate in improvement-log.md"
    return result


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


# ── Helpers dashboard settings ───────────────────────────────────────────────

def _autopilot_enabled(dashboard_url: str) -> bool:
    """Legge il flag autopilot dalla dashboard. Default False se non raggiungibile."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/settings?key=autopilot")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return str(data.get("value", "false")).lower() == "true"
    except Exception:
        return False


# ── Lesson evaluator ─────────────────────────────────────────────────────────

def evaluate_lessons(project_path: str) -> dict:
    """Valuta lezioni pending con Claude Haiku e aggiorna status sulla dashboard.

    Criteri apply: concreta, azionabile, non duplicata di SKILL.md, occorrenze >= 1.
    Criteri ineffective: vaga, duplicata, rumore da caso isolato.
    Lezioni 'apply' con occorrenze >= 3 vengono promosse a skill_feedback per inject_lessons.py.
    """
    import urllib.request
    import urllib.error

    result = {"name": "evaluate_lessons", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")
    if not admin_secret:
        result["detail"] = "ADMIN_SECRET non impostato, skip"
        return result

    # 1. Fetch pending lessons
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/lessons?limit=100")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        result["detail"] = f"fetch lessons fallito: {e}"
        return result

    rows = data.get("rows", [])
    pending = [r for r in rows if r.get("status") == "pending"]
    if not pending:
        result["detail"] = "nessuna lezione pending"
        return result

    # Max 20 per run (costo contenuto, Haiku)
    pending = pending[:20]

    # 2. Contesto SKILL.md (prime 80 righe — regole e gate)
    skill_md = SKILL_DIR / "SKILL.md"
    skill_context = ""
    if skill_md.exists():
        skill_context = "\n".join(skill_md.read_text(encoding="utf-8").splitlines()[:80])

    # 3. Prompt di valutazione batch
    lessons_json = json.dumps(
        [{"id": r["id"], "description": r["description"], "rule": r["rule"],
          "occurrences": r.get("occurrences", 1), "type": r.get("pattern_type", "")}
         for r in pending],
        ensure_ascii=False,
    )

    prompt = (
        "Sei un valutatore di lezioni per una skill AI coordinator. "
        "Valuta ogni lezione e decidi 'apply' o 'ineffective'.\n\n"
        "APPLY se: regola concreta e azionabile, non già coperta da SKILL.md, "
        "seguibile in sessioni future, occorrenze >= 2 o critica anche se singola.\n"
        "INEFFECTIVE se: troppo generica ('fare attenzione'), duplicata di SKILL.md, "
        "o caso isolato non critico (occorrenze = 1 e regola ovvia).\n\n"
        f"Contesto SKILL.md (prime 80 righe):\n{skill_context[:1500]}\n\n"
        f"Lezioni:\n{lessons_json}\n\n"
        "Rispondi SOLO con JSON valido, nessun testo aggiuntivo:\n"
        '[{"id":"...","verdict":"apply|ineffective","reason":"una riga"}]'
    )

    code, out, err = run(
        ["claude", "--permission-mode", "default", "--model", "haiku", "--print", prompt],
        cwd=str(SKILL_DIR),
    )
    if code != 0:
        result["status"] = "error"
        result["detail"] = f"claude CLI errore: {err[:200]}"
        return result

    # 4. Parse verdetti
    try:
        json_match = re.search(r"\[.*\]", out, re.DOTALL)
        if not json_match:
            result["status"] = "error"
            result["detail"] = "output non parsabile come JSON array"
            return result
        verdicts = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        result["status"] = "error"
        result["detail"] = f"JSON parse error: {e}"
        return result

    # 5. Applica verdetti
    applied = ineffective = feedback_created = 0
    lesson_map = {r["id"]: r for r in pending}

    for v in verdicts:
        lid = v.get("id")
        verdict = v.get("verdict")
        if not lid or verdict not in ("apply", "ineffective"):
            continue

        new_status = "applied" if verdict == "apply" else "ineffective"

        # PATCH /api/lessons
        try:
            body = json.dumps({"id": lid, "status": new_status}).encode()
            req = urllib.request.Request(
                f"{dashboard_url}/api/lessons",
                data=body,
                headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
            if new_status == "applied":
                applied += 1
            else:
                ineffective += 1
        except Exception:
            continue

        # Promuovi a skill_feedback se apply + occorrenze >= 3
        lesson = lesson_map.get(lid)
        if lesson and new_status == "applied" and lesson.get("occurrences", 0) >= 3:
            try:
                fb = json.dumps({
                    "kind": "promotion_candidate",
                    "title": lesson.get("rule", "")[:200],
                    "detail": lesson.get("description", "")[:500],
                    "source": "drain_evaluate_lessons",
                    "payload": {"occurrences": lesson["occurrences"], "reason": v.get("reason", "")},
                }).encode()
                fb_req = urllib.request.Request(
                    f"{dashboard_url}/api/skill-feedback",
                    data=fb,
                    headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                    method="POST",
                )
                with urllib.request.urlopen(fb_req, timeout=10):
                    pass
                feedback_created += 1
            except Exception:
                pass

    result["status"] = "ok"
    result["detail"] = (
        f"{applied} applicate, {ineffective} inefficaci, "
        f"{feedback_created} promosse a skill_feedback"
    )
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Background drain: manutenzione automatica")
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--curriculum-weekly", action="store_true",
                    help="Esegui auto-curriculum (solo se domenica)")
    ap.add_argument("--skill-exchange", action="store_true",
                    help="Controlla SKILL_EXCHANGE.md per feature codex non adottate")

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

    # Crea/vai su branch drain (usa suffisso incrementale se esiste già)
    today_str = date.today().isoformat()
    branch_name = f"{DRAIN_BRANCH_PREFIX}/{today_str}"
    code_br, _, _ = run(["git", "checkout", "-b", branch_name], cwd=project_path)
    if code_br != 0:
        # Branch già esistente: aggiungi suffisso orario
        branch_name = f"{DRAIN_BRANCH_PREFIX}/{today_str}-{datetime.now().strftime('%H%M')}"
        code_br2, _, err_br = run(["git", "checkout", "-b", branch_name], cwd=project_path)
        if code_br2 != 0:
            print(f"drain: impossibile creare branch ({err_br}), abort.", file=sys.stderr)
            return 0

    sub_results: list[dict] = []
    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")

    # Sub-attivita' 1-5
    for fn in [
        lambda: complete_tbd_entries(project_path),
        lambda: analyze_tool_errors(project_path),
        lambda: run_compaction(project_path),
        lambda: validate_skill_drift(project_path),
        lambda: evaluate_lessons(project_path) if _autopilot_enabled(dashboard_url) else {"name": "evaluate_lessons", "status": "skip", "detail": "autopilot disabilitato"},
    ]:
        try:
            r = fn()
        except Exception as e:
            r = {"name": "unknown", "status": "error", "detail": str(e)}
        sub_results.append(r)
        print(f"drain [{r['name']}]: {r['status']} — {r.get('detail', '')}", file=sys.stderr)

    # Skill Exchange check (domenica o flag esplicito)
    if args.skill_exchange or (args.curriculum_weekly and datetime.now().weekday() == 6):
        try:
            r = check_skill_exchange(project_path)
        except Exception as e:
            r = {"name": "check_skill_exchange", "status": "error", "detail": str(e)}
        sub_results.append(r)
        print(f"drain [skill_exchange]: {r['status']} — {r.get('detail', '')}", file=sys.stderr)

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
