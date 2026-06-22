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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DRAIN_BRANCH_PREFIX = "drain"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
from budget_guard import run_guarded, notify_breach  # type: ignore


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
        "Niente PII, niente nomi propri.\n\n"
        "IMPORTANTE: rispondi SOLO con le righe nel formato richiesto. "
        "Non usare tool, non leggere file — tutto il contesto è già nel prompt."
    )

    # max_turns=2: consente tool_use + risposta se necessario, senza loop.
    # Con max_turns=4 il subprocess impiegava 50+ secondi causando timeout a 120s.
    # La istruzione no-tool nel prompt riduce ulteriormente i turni e il costo.
    # timeout=90: margine per sistema carico di notte (misurato: ~20s interattivo, ~57s notturno).
    guarded = run_guarded(prompt, model="haiku", budget_cents=10, max_turns=2, timeout=90)
    if guarded["killed"]:
        notify_breach("resolve_tbd_lessons", 10, guarded.get("cost_usd"), guarded["reason"])
        result["status"] = "error"
        result["detail"] = f"circuit breaker: {guarded['reason']}"
        return result
    out = guarded["text"]
    code = guarded["exit_code"]
    err = ""
    if code != 0:
        result["status"] = "error"
        result["detail"] = f"claude CLI exit {code}"
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
    """Raggruppa errori ricorrenti dal DB dashboard e propone lezioni per i pattern ≥3 occorrenze."""
    import urllib.request
    import urllib.error

    result = {"name": "analyze_tool_errors", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")

    # Fetch errori raggruppati dal DB
    clusters: list[dict] = []
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/errors?grouped=true&limit=50")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        clusters = data.get("rows", [])
    except Exception:
        # Fallback: leggi coordination-log.jsonl locale
        slug = proj_slug(project_path)
        log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
        if not log_path.exists():
            result["detail"] = "dashboard non raggiungibile e coordination-log.jsonl non trovato"
            return result
        cutoff = datetime.now(timezone.utc).timestamp() - 30 * 86400
        raw_errors: list[str] = []
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
                if ts < cutoff:
                    continue
                if rec.get("outcome") in ("failed", "partial"):
                    lesson = rec.get("lesson") or ""
                    cat = rec.get("category", "")
                    raw_errors.append(f"{cat}: {lesson}" if lesson else cat)
        except Exception as e:
            result["status"] = "error"
            result["detail"] = str(e)
            return result
        from collections import Counter
        for pattern, count in Counter(e[:60] for e in raw_errors).most_common(10):
            if count >= 2:
                clusters.append({"error_type": "coordination_log", "message_sample": pattern,
                                  "count": count, "ids": []})

    if not clusters:
        result["detail"] = "nessun errore aperto nel DB"
        return result

    # Considera solo cluster con count >= 2
    recurring = [c for c in clusters if int(c.get("count", 1)) >= 2]
    if not recurring:
        result["detail"] = f"{len(clusters)} gruppi totali, nessuno ricorrente (min 2)"
        return result

    # Per cluster con count >= 3: crea lezione se admin_secret disponibile
    lessons_created = 0
    if admin_secret:
        for c in recurring:
            if int(c.get("count", 0)) < 3:
                continue
            error_type = c.get("error_type", "unknown")
            msg = c.get("message_sample", "")
            try:
                lesson_body = json.dumps({
                    "pattern_type": "errore",
                    "description": f"Errore ricorrente ({c['count']}×): {error_type} — {msg[:120]}",
                    "rule": f"Quando si incontra '{error_type}': verificare {msg[:160]}",
                    "source": "drain_analyze_errors",
                }).encode()
                lesson_req = urllib.request.Request(
                    f"{dashboard_url}/api/lessons",
                    data=lesson_body,
                    headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                    method="POST",
                )
                with urllib.request.urlopen(lesson_req, timeout=10):
                    pass
                lessons_created += 1
            except Exception:
                pass

            # Risolvi i singoli record dopo aver creato la lezione
            ids = [i for i in c.get("ids", []) if i]
            if ids:
                try:
                    resolve_body = json.dumps({"ids": ids, "resolved": True}).encode()
                    resolve_req = urllib.request.Request(
                        f"{dashboard_url}/api/errors",
                        data=resolve_body,
                        headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                        method="PATCH",
                    )
                    with urllib.request.urlopen(resolve_req, timeout=10):
                        pass
                except Exception:
                    pass

    reg_added = _update_mistake_register(project_path, recurring)
    result["status"] = "ok"
    result["detail"] = (
        f"{len(recurring)} pattern ricorrenti, {lessons_created} lezioni create"
        + (f", {reg_added} aggiunti a AI_MISTAKE_REGISTER.md" if reg_added else "")
    )
    return result


def _update_mistake_register(project_path: str, patterns: list[dict]) -> int:
    """Aggiunge pattern verificati ad AI_MISTAKE_REGISTER.md. Ritorna righe aggiunte."""
    register_file = Path(project_path) / "AI_MISTAKE_REGISTER.md"
    if not register_file.exists() or not patterns:
        return 0
    text = register_file.read_text(encoding="utf-8")
    today = date.today().isoformat()
    added = 0
    for p in patterns:
        sample = p.get("message_sample", "")[:80].replace("|", "/")
        area = p.get("error_type", "generico")[:30]
        count = int(p.get("count", 1))
        # Salta se pattern simile già presente (prime 35 char come fingerprint)
        if sample[:35] in text:
            continue
        row = f"| {sample} | {area} | {count} | {today} | verificare — aggiornare Fix |"
        # Inserisci prima della riga vuota dopo la tabella (o in fondo)
        lines = text.splitlines()
        insert_at = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("| ") and "|---|" not in lines[i]:
                insert_at = i + 1
                break
        lines.insert(insert_at, row)
        text = "\n".join(lines) + "\n"
        added += 1
    if added:
        register_file.write_text(text, encoding="utf-8")
    return added


def decay_mistake_register(project_path: str) -> dict:
    """Decrementa peso dei pattern in AI_MISTAKE_REGISTER.md non visti da 30+ giorni.
    Rimuove le righe con peso ≤ 0.
    """
    result = {"name": "decay_mistake_register", "status": "skip", "detail": ""}
    register_file = Path(project_path) / "AI_MISTAKE_REGISTER.md"
    if not register_file.exists():
        result["detail"] = "AI_MISTAKE_REGISTER.md non trovato"
        return result
    text = register_file.read_text(encoding="utf-8")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    lines = text.splitlines()
    new_lines: list[str] = []
    decayed = removed = 0
    for line in lines:
        # Righe dati: | testo | area | NUMERO | YYYY-MM-DD | fix |
        if line.startswith("| ") and "|---|" not in line:
            parts = [p.strip() for p in line.split("|")]
            # parts[0]="" parts[1]=pattern parts[2]=area parts[3]=peso parts[4]=data parts[5]=fix parts[6]=""
            if len(parts) >= 6 and parts[3].isdigit() and re.match(r"\d{4}-\d{2}-\d{2}", parts[4]):
                try:
                    ultimo = date.fromisoformat(parts[4])
                    peso = int(parts[3])
                    if ultimo < cutoff:
                        peso -= 1
                        decayed += 1
                        if peso <= 0:
                            removed += 1
                            continue
                        parts[3] = str(peso)
                        line = "| " + " | ".join(parts[1:-1]) + " |"
                except ValueError:
                    pass
        new_lines.append(line)
    if decayed == 0:
        result["detail"] = "nessun pattern da decadere"
        return result
    register_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    result["status"] = "ok"
    result["detail"] = f"{decayed} pattern decaduti, {removed} rimossi (peso 0)"
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


def sediment_handoff(project_path: str) -> dict:
    """Compatta AI_HANDOFF.md in 3 strati temporali per impedirne la crescita illimitata.

    Stratum_0 (ultimi 2gg): full · Stratum_1 (3-30gg): header + prime 3 righe
    Stratum_2 (>30gg): solo header. Vecchie sezioni restano nel git history.
    """
    result = {"name": "sediment_handoff", "status": "skip", "detail": ""}
    handoff = Path(project_path) / "AI_HANDOFF.md"
    if not handoff.exists():
        result["detail"] = "AI_HANDOFF.md non trovato"
        return result

    text = handoff.read_text(encoding="utf-8")
    total_lines = len(text.splitlines())
    if total_lines < 80:
        result["detail"] = f"{total_lines} righe — sotto soglia (80), skip"
        return result

    # Splitta per sezioni con header ## DATE
    section_re = re.compile(r"^(##\s+\d{4}-\d{2}-\d{2}.*)", re.MULTILINE)
    parts = section_re.split(text)
    # parts = [preamble, header1, body1, header2, body2, ...]
    preamble = parts[0] if parts else ""
    sections: list[tuple[str, str]] = []  # (header, body)
    for i in range(1, len(parts) - 1, 2):
        sections.append((parts[i], parts[i + 1] if i + 1 < len(parts) else ""))

    if len(sections) <= 2:
        result["detail"] = f"{len(sections)} sezioni — non abbastanza per sedimentare"
        return result

    today = date.today()
    new_parts: list[str] = [preamble]
    compressed = 0

    for header, body in sections:
        # Estrai data dall'header (formato: ## 2026-06-08 ...)
        m = re.search(r"(\d{4}-\d{2}-\d{2})", header)
        if not m:
            new_parts.extend([header, body])
            continue
        try:
            section_date = date.fromisoformat(m.group(1))
        except ValueError:
            new_parts.extend([header, body])
            continue
        age_days = (today - section_date).days

        if age_days <= 2:
            # Stratum 0: full retention
            new_parts.extend([header, body])
        elif age_days <= 30:
            # Stratum 1: header + prime 3 righe non vuote del body
            body_lines = [l for l in body.splitlines() if l.strip()][:3]
            truncated_body = "\n" + "\n".join(body_lines) + "\n[...sedimentato — dettaglio in git history]\n\n"
            new_parts.extend([header, truncated_body])
            compressed += 1
        else:
            # Stratum 2: solo header
            new_parts.extend([header, "\n[sedimentato]\n\n"])
            compressed += 1

    if compressed == 0:
        result["detail"] = "nessuna sezione da sedimentare"
        return result

    handoff.write_text("".join(new_parts), encoding="utf-8")
    new_lines = len(handoff.read_text(encoding="utf-8").splitlines())
    result["status"] = "ok"
    result["detail"] = (
        f"{compressed} sezioni sedimentate · {total_lines}→{new_lines} righe"
    )
    return result


def regenerate_score(project_path: str) -> dict:
    """Controlla se SKILL.md è cambiato dall'ultima generazione di AI_SCORE.md.

    Se il checksum è cambiato, aggiunge un avviso in AI_SCORE.md e aggiorna
    il checksum salvato. La rigenerazione manuale resta a carico dell'utente
    (troppo soggettiva per affidarla a Haiku senza revisione).
    """
    import hashlib
    result = {"name": "regenerate_score", "status": "skip", "detail": ""}

    skill_md = SKILL_DIR / "SKILL.md"
    score_md = SKILL_DIR / "AI_SCORE.md"
    checksum_file = SKILL_DIR / "scripts" / ".score_checksum"

    if not skill_md.exists():
        result["detail"] = "SKILL.md non trovato"
        return result

    current_hash = hashlib.sha256(skill_md.read_bytes()).hexdigest()[:16]
    stored_hash = checksum_file.read_text().strip() if checksum_file.exists() else ""

    if current_hash == stored_hash:
        result["detail"] = f"checksum invariato ({current_hash[:8]}) — score in sync"
        return result

    # Checksum cambiato: aggiorna file e aggiungi avviso se score esiste
    checksum_file.write_text(current_hash)
    if score_md.exists():
        score_text = score_md.read_text(encoding="utf-8")
        warning = f"<!-- SKILL.md aggiornato ({current_hash[:8]}) — rivedere score in prossima sessione -->\n"
        # Sostituisci avviso precedente se presente, altrimenti aggiungi in cima
        if "<!-- SKILL.md aggiornato" in score_text:
            score_text = re.sub(r"<!-- SKILL\.md aggiornato.*?-->\n", warning, score_text)
        else:
            score_text = warning + score_text
        score_md.write_text(score_text, encoding="utf-8")

    result["status"] = "ok"
    result["detail"] = f"checksum aggiornato {stored_hash[:8] or 'n/a'}→{current_hash[:8]}" + (
        " · avviso aggiunto in AI_SCORE.md" if score_md.exists() else " · AI_SCORE.md non trovato"
    )
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


def create_lessons_from_failed_tasks(project_path: str) -> dict:
    """Crea lezioni automatiche dai task partial/failed delle ultime 24h.

    Chiamata solo se autopilot attivo. Le lezioni vengono create via POST /api/lessons
    che gestisce deduplicazione (upsert su rule), quindi è idempotente.
    """
    import urllib.request
    import urllib.error

    result = {"name": "create_lessons_from_failed_tasks", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")
    if not admin_secret:
        result["detail"] = "ADMIN_SECRET non impostato, skip"
        return result

    # Fetch task partial/failed ultime 24h
    try:
        req = urllib.request.Request(
            f"{dashboard_url}/api/tasks?status=partial,failed&hours=24&limit=20"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        result["detail"] = f"fetch tasks fallito: {e}"
        return result

    # Frasi conversazionali (conferma/diniego) senza valore come lezione:
    # frequenti su task partial di categoria miglioramento_skill, dove il
    # "summary" è l'ultimo messaggio utente, non una descrizione dell'errore.
    _CONFIRMATION_RE = re.compile(
        r"^(ok|si|s[iì]|no|procedi|continua|conferma(to)?|va bene|perfetto|fatto|grazie|bene|d'accordo|esatto)[\s.,!]*$",
        re.I,
    )

    tasks = data.get("rows", [])
    tasks = [t for t in tasks if (t.get("summary") or "").strip()]
    tasks = [
        t for t in tasks
        if not _CONFIRMATION_RE.match(t["summary"].strip())
    ]
    if not tasks:
        result["detail"] = "nessun task partial/failed con summary nelle ultime 24h"
        return result

    created = skipped = 0
    for t in tasks:
        summary = t["summary"].strip()
        category = t.get("category", "")
        status = t.get("status", "")
        rule = summary[:300]
        description = (
            f"Task {status} ({category}): {summary[:120]}"
        )
        try:
            body = json.dumps({
                "pattern_type": "errore",
                "description": description,
                "rule": rule,
                "task_id": t.get("id"),
                "source": "drain_failed_tasks",
            }).encode()
            req = urllib.request.Request(
                f"{dashboard_url}/api/lessons",
                data=body,
                headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read())
            if resp_data.get("inserted", 0) > 0:
                created += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1

    result["status"] = "ok"
    result["detail"] = f"{created} lezioni create, {skipped} già esistenti o saltate"
    return result


def run_ai_news_intake(project_path: str) -> dict:
    """Lancia intake-watchdog.mjs se sono passate >48h dall'ultimo run ok.

    Il watchdog gestisce internamente la cadenza e il lock: chiamarlo anche se
    <48h è sicuro (esce subito con skip). Qui forziamo solo se lo stato dice
    che è il momento giusto, per non sprecare token.
    """
    result = {"name": "run_ai_news_intake", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    import urllib.request

    # Leggi stato intake dal dashboard
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/ai-news/check")
        with urllib.request.urlopen(req, timeout=10) as resp:
            state = json.loads(resp.read())
    except Exception as e:
        result["detail"] = f"stato intake non leggibile: {e}"
        return result

    if state.get("running"):
        result["detail"] = "intake già in esecuzione, skip"
        return result

    # Controlla se sono passate >48h dall'ultimo ok
    last_ok = state.get("last_check_at") if state.get("last_check_status") == "ok" else None
    needs_run = True
    if last_ok:
        from datetime import datetime as dt
        elapsed_h = (datetime.now(timezone.utc) - dt.fromisoformat(last_ok.replace("Z", "+00:00"))).total_seconds() / 3600
        needs_run = elapsed_h >= 48

    if not needs_run:
        result["detail"] = f"ultimo run ok {int(elapsed_h)}h fa, skip (soglia 48h)"
        return result

    watchdog = Path(project_path) / "ops" / "intake-watchdog.mjs"
    if not watchdog.exists():
        result["detail"] = f"intake-watchdog.mjs non trovato in {project_path}/ops"
        return result

    code, out, err = run(["node", str(watchdog), "--force"], cwd=project_path, capture=True)
    result["status"] = "ok" if code == 0 else "error"
    combined = (out + " " + err).strip()[:200]
    result["detail"] = combined or f"exit {code}"
    return result


def run_ideation(project_path: str) -> dict:
    """Lancia intake-ideation.mjs ogni 7+ giorni: skill che analizza sé stessa."""
    result = {"name": "run_ideation", "status": "skip", "detail": ""}
    script = Path(project_path) / "ops" / "intake-ideation.mjs"
    if not script.exists():
        result["detail"] = "intake-ideation.mjs non trovato"
        return result
    state_file = Path(project_path) / "ops" / "lib" / "ideation-state.json"
    try:
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
        if state.get("last_run_at"):
            from datetime import datetime as dt
            elapsed_d = (datetime.now(timezone.utc) - dt.fromisoformat(state["last_run_at"].replace("Z", "+00:00"))).total_seconds() / 86400
            if elapsed_d < 7:
                result["detail"] = f"ultimo run {int(elapsed_d)}gg fa, skip (soglia 7gg)"
                return result
    except Exception:
        pass
    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    env = {**os.environ, "DASHBOARD_API": dashboard_url}
    r = subprocess.run(["node", str(script)], cwd=project_path, capture_output=True, text=True, timeout=120, env=env)
    code, out, err = r.returncode, r.stdout.strip(), r.stderr.strip()
    result["status"] = "ok" if code == 0 else "error"
    result["detail"] = (out + " " + err).strip()[:200] or f"exit {code}"
    return result


def detect_session_anomalies(project_path: str) -> dict:
    """Rileva sessioni anomale per costo (>3x media categoria, ultime 24h).

    Fonte dati: GET /api/coordination-log?limit=500 (ultimi 30gg).
    Fallback: query Postgres diretta via psycopg2 o subprocess psql.
    Scrive record tipo "anomaly" in drain-log.jsonl.
    """
    import urllib.request

    result = {"name": "detect_anomalies", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    log_path = drain_log_path(project_path)

    cutoff_30d = datetime.now(timezone.utc).timestamp() - 30 * 86400
    cutoff_24h = datetime.now(timezone.utc).timestamp() - 86400

    rows: list[dict] = []

    # Tentativo 1: HTTP GET sull'endpoint dashboard
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/coordination-log?limit=500")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        rows = data.get("rows", [])
    except Exception:
        rows = []

    # Tentativo 2: psycopg2 diretto
    if not rows:
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            try:
                import psycopg2  # type: ignore
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute(
                    "SELECT ts, category, cost_usd FROM coordination_log "
                    "WHERE ts >= now() - interval '30 days' ORDER BY ts DESC LIMIT 500"
                )
                for r in cur.fetchall():
                    rows.append({"ts": r[0].isoformat(), "category": r[1], "cost_usd": float(r[2] or 0)})
                cur.close()
                conn.close()
            except ImportError:
                pass
            except Exception:
                pass

    # Tentativo 3: subprocess psql
    if not rows:
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            query = (
                "SELECT ts, category, cost_usd FROM coordination_log "
                "WHERE ts >= now() - interval '30 days' ORDER BY ts DESC LIMIT 500;"
            )
            code, out, _ = run(["psql", db_url, "-t", "-A", "-F", "\t", "-c", query])
            if code == 0:
                for line in out.strip().splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        try:
                            rows.append({
                                "ts": parts[0],
                                "category": parts[1],
                                "cost_usd": float(parts[2]),
                            })
                        except (ValueError, IndexError):
                            pass

    if not rows:
        result["detail"] = "dati non disponibili (endpoint e DB non raggiungibili)"
        return result

    # Calcola media per categoria sugli ultimi 30gg
    from collections import defaultdict
    cat_costs: dict[str, list[float]] = defaultdict(list)
    recent_rows: list[dict] = []

    for r in rows:
        ts_str = r.get("ts", "")
        try:
            from datetime import datetime as dt
            ts = dt.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        cost = float(r.get("cost_usd") or 0)
        cat = r.get("category", "unknown")
        if ts >= cutoff_30d:
            cat_costs[cat].append(cost)
        if ts >= cutoff_24h:
            recent_rows.append({"ts": ts_str, "ts_epoch": ts, "category": cat, "cost_usd": cost})

    if not recent_rows:
        result["detail"] = "nessuna sessione nelle ultime 24h"
        return result

    cat_avg: dict[str, float] = {
        cat: sum(costs) / len(costs) for cat, costs in cat_costs.items() if costs
    }

    anomalies_written = 0
    for r in recent_rows:
        cat = r["category"]
        cost = r["cost_usd"]
        avg = cat_avg.get(cat, 0)
        if avg <= 0:
            continue
        ratio = cost / avg
        if ratio > 3.0:
            record = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": "anomaly",
                "session_ts": r["ts"],
                "category": cat,
                "cost_usd": cost,
                "avg_cost": round(avg, 6),
                "ratio": round(ratio, 2),
            }
            try:
                append_drain_log(log_path, record)
                anomalies_written += 1
            except Exception:
                pass

    result["status"] = "ok"
    result["detail"] = (
        f"{anomalies_written} anomalie rilevate"
        if anomalies_written
        else f"nessuna anomalia su {len(recent_rows)} sessioni (ultime 24h)"
    )
    return result


def discover_cost_thresholds(project_path: str) -> dict:
    """Calcola p75/p90 di cost_usd per categoria dal coordination-log.jsonl.

    Aggiorna il blocco <!-- thresholds-auto --> in SKILL.md se i valori sono cambiati.
    Se SKILL.md supererebbe 450 righe, scrive solo scripts/thresholds.json.
    """
    from collections import defaultdict

    result = {"name": "discover_cost_thresholds", "status": "skip", "detail": ""}

    slug = proj_slug(project_path)
    log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
    if not log_path.exists():
        result["detail"] = "coordination-log.jsonl non trovato"
        return result

    cat_costs: dict[str, list[float]] = defaultdict(list)
    total = 0
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cat = rec.get("category", "").strip()
            cost = rec.get("cost_usd")
            if cat and cost is not None:
                try:
                    cat_costs[cat].append(float(cost))
                    total += 1
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        return result

    if total == 0:
        result["detail"] = "nessun record con category+cost_usd"
        return result

    def percentile(values: list[float], p: float) -> float:
        sorted_v = sorted(values)
        idx = (len(sorted_v) - 1) * p / 100
        lo, hi = int(idx), min(int(idx) + 1, len(sorted_v) - 1)
        return sorted_v[lo] + (sorted_v[hi] - sorted_v[lo]) * (idx - lo)

    today = date.today().isoformat()
    rows: list[dict] = []
    for cat, costs in cat_costs.items():
        if len(costs) < 5:
            continue
        rows.append({
            "categoria": cat,
            "warn_p75": round(percentile(costs, 75), 2),
            "ceiling_p90": round(percentile(costs, 90), 2),
            "n": len(costs),
        })

    if not rows:
        result["detail"] = f"{total} sessioni analizzate, nessuna categoria con ≥5 sessioni"
        return result

    # Scrivi thresholds.json (sempre)
    thresholds_json = SKILL_DIR / "scripts" / "thresholds.json"
    new_data = {"updated_at": today, "n_sessions": total, "thresholds": rows}
    old_data: dict = {}
    if thresholds_json.exists():
        try:
            old_data = json.loads(thresholds_json.read_text(encoding="utf-8"))
        except Exception:
            pass

    old_rows = {r["categoria"]: r for r in old_data.get("thresholds", [])}
    new_rows = {r["categoria"]: r for r in rows}
    changed_cats = [
        cat for cat, r in new_rows.items()
        if old_rows.get(cat, {}).get("warn_p75") != r["warn_p75"]
        or old_rows.get(cat, {}).get("ceiling_p90") != r["ceiling_p90"]
    ]

    thresholds_json.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")

    if not changed_cats:
        result["status"] = "skip"
        result["detail"] = f"{total} sessioni analizzate, {len(rows)} categorie invariate"
        return result

    # Costruisci blocco markdown
    table_rows = "\n".join(
        f"| {r['categoria']} | ${r['warn_p75']:.2f} | ${r['ceiling_p90']:.2f} | {r['n']} |"
        for r in sorted(rows, key=lambda x: x["n"], reverse=True)
    )
    block = (
        f"<!-- thresholds-auto -->\n"
        f"## Auto-Discovered Cost Thresholds (updated {today}, n={total} sessioni)\n"
        f"| categoria | warn (p75) | ceiling (p90) | n |\n"
        f"|---|---|---|---|\n"
        f"{table_rows}\n"
        f"Superare ceiling = sessione in overrun. Chiudi e apri nuovo task.\n"
        f"<!-- /thresholds-auto -->"
    )

    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        result["detail"] = "SKILL.md non trovato, thresholds.json scritto"
        result["status"] = "ok"
        return result

    content = skill_md.read_text(encoding="utf-8")

    # Sostituisci blocco esistente o inseriscilo dopo la riga "## 2. Budget mode"
    if "<!-- thresholds-auto -->" in content:
        new_content = re.sub(
            r"<!-- thresholds-auto -->.*?<!-- /thresholds-auto -->",
            block,
            content,
            flags=re.DOTALL,
        )
    else:
        # Inserisci dopo la riga "## 2. Budget mode"
        insert_marker = "## 2. Budget mode"
        if insert_marker in content:
            idx = content.index(insert_marker)
            end_of_line = content.index("\n", idx)
            new_content = content[:end_of_line + 1] + "\n" + block + "\n" + content[end_of_line + 1:]
        else:
            new_content = content + "\n\n" + block + "\n"

    new_line_count = len(new_content.splitlines())
    if new_line_count > 450:
        result["status"] = "ok"
        result["detail"] = (
            f"{total} sessioni analizzate, {len(changed_cats)} categorie aggiornate — "
            f"SKILL.md salterebbe a {new_line_count} righe (>450), solo thresholds.json scritto"
        )
        return result

    skill_md.write_text(new_content, encoding="utf-8")
    result["status"] = "ok"
    result["detail"] = f"{total} sessioni analizzate, {len(changed_cats)} categorie aggiornate in SKILL.md"
    return result


def _ts_to_epoch(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def detect_dead_rules(project_path: str) -> dict:
    """Rileva categorie/modelli definiti in SKILL.md ma mai visti nei dati reali (90gg).

    Scrive findings in drain-log.jsonl e scripts/dead-rules-cache.json.
    """
    result = {"name": "detect_dead_rules", "status": "skip", "detail": ""}

    slug = proj_slug(project_path)
    log_path_coord = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
    if not log_path_coord.exists():
        result["detail"] = "coordination-log.jsonl non trovato"
        return result

    cutoff_90d = datetime.now(timezone.utc).timestamp() - 90 * 86400

    seen_categories: set[str] = set()
    seen_models: set[str] = set()
    agents_ever_used = False
    n_sessions = 0
    rows: list[dict] = []

    try:
        for line in log_path_coord.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            n_sessions += 1
            rows.append(rec)
            ts_str = rec.get("ts", "")
            try:
                from datetime import datetime as dt
                ts = dt.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
            except Exception:
                ts = 0

            if ts >= cutoff_90d:
                cat = rec.get("category", "").strip()
                if cat:
                    seen_categories.add(cat)
                models = rec.get("models", []) or []
                if isinstance(models, list):
                    for m in models:
                        if isinstance(m, str):
                            seen_models.add(m.lower())
                agents = rec.get("agents_used", []) or []
                if agents:
                    agents_ever_used = True
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        return result

    # Leggi SKILL.md per estrarre categorie e modelli definiti
    skill_md = SKILL_DIR / "SKILL.md"
    defined_categories: set[str] = set()
    defined_models: set[str] = set()

    if skill_md.exists():
        skill_text = skill_md.read_text(encoding="utf-8")
        # Categorie: pattern **nome** grassetto vicino a parole chiave categoria
        cat_patterns = re.findall(r"\*\*([a-z_]+(?:\s+[a-z_]+)?)\*\*", skill_text)
        known_cats = {"new app", "modify app", "audit", "bug_rescue", "bug rescue",
                      "skill improvement", "ops", "modifica", "domanda", "nuova_app"}
        for cp in cat_patterns:
            if cp.lower() in known_cats:
                defined_categories.add(cp.lower())
        # Modelli citati
        for model in ("haiku", "sonnet", "opus"):
            if model in skill_text.lower():
                defined_models.add(model)

    dead_categories = sorted(defined_categories - {c.lower() for c in seen_categories})
    dead_models = sorted(defined_models - seen_models)
    delegation_not_tracked = not agents_ever_used

    # Auto-check: ultimi 7 giorni — verifica se il tracking delegation è migliorato
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).timestamp()
    recent_total = sum(1 for r in rows if _ts_to_epoch(r.get("ts", "")) >= cutoff_7d)
    recent_with_agents = sum(
        1 for r in rows
        if _ts_to_epoch(r.get("ts", "")) >= cutoff_7d and r.get("agents_used")
    )
    tracking_check = {
        "sessions_last_7d": recent_total,
        "with_agents_tracked": recent_with_agents,
        "fix_working": recent_with_agents > 0,
    }

    findings = {
        "dead_categories": dead_categories,
        "dead_models": dead_models,
        "delegation_not_tracked": delegation_not_tracked,
        "tracking_check": tracking_check,
    }

    today = date.today().isoformat()

    # Scrivi in drain-log.jsonl
    drain_log = drain_log_path(project_path)
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "dead_rules_report",
        "project": Path(project_path).name,
        "findings": findings,
        "n_sessions_analyzed": n_sessions,
        "window_days": 90,
    }
    try:
        append_drain_log(drain_log, record)
    except Exception:
        pass

    # Scrivi dead-rules-cache.json
    cache_path = SKILL_DIR / "scripts" / "dead-rules-cache.json"
    cache_data = {**findings, "updated_at": today, "n_sessions": n_sessions, "window_days": 90}
    try:
        cache_path.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"scrittura dead-rules-cache.json fallita: {e}"
        return result

    n_dead = len(dead_categories) + len(dead_models) + (1 if delegation_not_tracked else 0)
    result["status"] = "ok"
    result["detail"] = f"{n_dead} regole inattive trovate (cat:{len(dead_categories)}, models:{len(dead_models)}, delegation:{delegation_not_tracked})"
    return result


def auto_process_ai_news(project_path: str) -> dict:
    """Auto-processa le AI news: dismiss vecchie low/none, skill_feedback per high+skill.

    - news relevance=none o low più vecchie di 7gg → dismissed (bulk)
    - news relevance=high + target=skill → crea skill_feedback promotion_candidate
    """
    import urllib.request

    result = {"name": "auto_process_ai_news", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")
    if not admin_secret:
        result["detail"] = "ADMIN_SECRET non impostato, skip"
        return result

    # Fetch tutte le news proposed non dismissed
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/ai-news?limit=200&status=proposed")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        result["detail"] = f"fetch ai_news fallito: {e}"
        return result

    rows = data.get("rows", [])
    if not rows:
        result["detail"] = "nessuna news proposed"
        return result

    cutoff_7d = datetime.now(timezone.utc).timestamp() - 7 * 86400
    dismiss_ids: list[int] = []
    feedback_created = 0

    for r in rows:
        relevance = r.get("relevance", "none")
        target = r.get("target", "none")
        news_id = r.get("id")
        fetched_at = r.get("fetched_at", "")

        # Auto-dismiss: low/none più vecchie di 7gg
        if relevance in ("none", "low"):
            try:
                ts = datetime.fromisoformat(fetched_at.replace("Z", "+00:00")).timestamp()
                if ts < cutoff_7d:
                    dismiss_ids.append(int(news_id))
            except Exception:
                pass
            continue

        # skill_feedback per high+skill (medium+skill solo se very recent non già in feedback)
        if relevance == "high" and target == "skill":
            title = r.get("title", "")[:200]
            proposed_change = r.get("proposed_change") or r.get("rationale") or ""
            try:
                fb = json.dumps({
                    "kind": "routing_insight",
                    "title": f"[AI News] {title}",
                    "detail": proposed_change[:500],
                    "source": "drain_ai_news",
                    "payload": {
                        "ai_news_id": news_id,
                        "effort": r.get("effort"),
                        "risk": r.get("risk"),
                        "affects": r.get("affects", []),
                    },
                }).encode()
                fb_req = urllib.request.Request(
                    f"{dashboard_url}/api/skill-feedback",
                    data=fb,
                    headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                    method="POST",
                )
                with urllib.request.urlopen(fb_req, timeout=10):
                    pass
                # Aggiorna status news → in_plan
                status_req = urllib.request.Request(
                    f"{dashboard_url}/api/ai-news?id={news_id}",
                    data=json.dumps({"status": "in_plan"}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="PATCH",
                )
                with urllib.request.urlopen(status_req, timeout=10):
                    pass
                feedback_created += 1
            except Exception:
                pass

    # Bulk dismiss
    dismissed = 0
    if dismiss_ids:
        try:
            body = json.dumps({"ids": dismiss_ids, "dismissed": True}).encode()
            req = urllib.request.Request(
                f"{dashboard_url}/api/ai-news?id=0",
                data=body,
                headers={"Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
            dismissed = len(dismiss_ids)
        except Exception:
            pass

    result["status"] = "ok"
    result["detail"] = (
        f"{feedback_created} high+skill → skill_feedback, {dismissed} low/none dismissed"
    )
    return result


def promote_acknowledged_feedback(project_path: str) -> dict:
    """Scrive in references/auto-promoted-lessons.md le regole confermate dall'utente.

    Legge skill_feedback con status=acknowledged e applied_to_skill_at=null,
    appende ogni regola nel file di riferimento, poi segna applied_to_skill_at.
    """
    import urllib.request
    import urllib.error

    result = {"name": "promote_acknowledged_feedback", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")
    if not admin_secret:
        result["detail"] = "ADMIN_SECRET non impostato, skip"
        return result

    try:
        req = urllib.request.Request(f"{dashboard_url}/api/skill-feedback?status=acknowledged&limit=20")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        result["detail"] = f"fetch skill_feedback fallito: {e}"
        return result

    rows = data.get("rows", [])
    to_promote = [r for r in rows if not r.get("applied_to_skill_at")]
    if not to_promote:
        result["detail"] = "nessun feedback da promuovere"
        return result

    auto_file = SKILL_DIR / "references" / "auto-promoted-lessons.md"
    today = date.today().isoformat()
    promoted = 0

    for item in to_promote:
        title = item.get("title", "").strip()
        detail = item.get("detail", "").strip()
        source = item.get("source", "drain")
        confirmed = (item.get("acknowledged_at") or today)[:10]

        if not title:
            continue

        entry = f"\n### {today} — {title}\n"
        if detail:
            entry += f"*Contesto*: {detail}\n"
        entry += f"*Fonte*: {source} · *Confermato*: {confirmed}\n"

        try:
            with open(auto_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            result["status"] = "error"
            result["detail"] = f"scrittura file fallita: {e}"
            return result

        try:
            body = json.dumps({"id": item["id"], "applied_to_skill": True}).encode()
            req = urllib.request.Request(
                f"{dashboard_url}/api/skill-feedback",
                data=body,
                headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
            promoted += 1
        except Exception:
            pass

    result["status"] = "ok" if promoted > 0 else "skip"
    result["detail"] = f"{promoted} regole scritte in auto-promoted-lessons.md"
    return result


def _run_skill_assay_safe(project_path: str) -> dict:
    """Wrapper isolato per run_skill_assay: importa skill_assay.py a runtime."""
    try:
        from skill_assay import run_skill_assay  # type: ignore
        return run_skill_assay(project_path)
    except ImportError:
        return {"name": "skill_assay", "status": "skip", "detail": "skill_assay.py non trovato"}
    except Exception as e:
        return {"name": "skill_assay", "status": "error", "detail": str(e)}


def court_review_lesson_promotion(project_path: str) -> dict:
    """Corte Suprema: delibera sulla promozione automatica di lezioni ad alta ricorrenza.

    Lezioni con occurrences >= 5, status != ineffective, promoted_to IS NULL
    vengono sottoposte alla Corte (3 agenti paralleli). Se approvate, vengono
    promosse in SKILL.md §14 e marcate promoted_to nel DB.
    """
    result = {"name": "court_review_lesson_promotion", "status": "skip", "detail": ""}

    dashboard_url = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
    admin_secret = os.environ.get("ADMIN_SECRET", "")
    PROMOTION_THRESHOLD = 5

    try:
        import urllib.request as _ur
        req = _ur.Request(f"{dashboard_url}/api/lessons?limit=50")
        with _ur.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        rows = data.get("rows", [])
    except Exception as e:
        result["detail"] = f"fetch lessons fallito: {e}"
        return result

    candidates = [
        r for r in rows
        if (r.get("occurrences") or 0) >= PROMOTION_THRESHOLD
        and r.get("status", "pending") != "ineffective"
        and not r.get("promoted_to")
    ]

    if not candidates:
        result["detail"] = f"nessuna lezione con occurrences>={PROMOTION_THRESHOLD} da promuovere"
        return result

    court_script = SKILL_DIR / "scripts" / "supreme_court.py"
    if not court_script.exists():
        result["detail"] = "supreme_court.py non trovato"
        return result

    skill_md = SKILL_DIR / "SKILL.md"
    approved = []
    rejected = []

    for lesson in candidates[:3]:  # max 3 per run per contenere i costi
        rule = (lesson.get("rule") or "").strip()
        occ = lesson.get("occurrences", 0)
        if not rule:
            continue

        question = f"Promuovere questa lezione in SKILL.md §14 (auto-curriculum)?"
        context = (
            f"Regola: {rule}\n"
            f"Occorrenze: {occ} sessioni reali\n"
            f"Pattern type: {lesson.get('pattern_type', 'N/A')}\n"
            f"Ultima vista: {str(lesson.get('last_seen_at', ''))[:10]}"
        )

        try:
            proc = subprocess.run(
                ["python3", str(court_script),
                 "--question", question,
                 "--context", context],
                capture_output=True, text=True, timeout=120
            )
            verdict = "approve" if proc.returncode == 0 else "reject"
        except Exception as e:
            verdict = "reject"
            print(f"drain [court] error lezione {lesson.get('id')}: {e}", file=sys.stderr)

        if verdict == "approve":
            approved.append(lesson)
            # Appendi in SKILL.md §14
            today = date.today().isoformat()
            entry = f"\n- [{today}] (auto-promosso, {occ}×) {rule}"
            try:
                content = skill_md.read_text(encoding="utf-8")
                if "## 14." in content or "## 14 " in content:
                    # Inserisci dopo la prima riga del §14
                    marker = next(
                        (m for m in ["## 14.", "## 14 "] if m in content), None
                    )
                    if marker:
                        idx = content.index(marker)
                        next_section = content.find("\n## ", idx + 1)
                        insert_at = next_section if next_section != -1 else len(content)
                        content = content[:insert_at] + entry + "\n" + content[insert_at:]
                        skill_md.write_text(content, encoding="utf-8")
                else:
                    with open(skill_md, "a", encoding="utf-8") as f:
                        f.write(f"\n\n## 14. Auto-curriculum (promozioni automatiche)\n{entry}\n")
            except Exception as e:
                print(f"drain [court] scrittura SKILL.md fallita: {e}", file=sys.stderr)
                continue

            # Marca promoted_to nel DB
            if admin_secret:
                try:
                    body = json.dumps({
                        "id": lesson["id"],
                        "status": "applied",
                        "promoted_to": f"SKILL.md §14 (auto, {today})"
                    }).encode()
                    req = _ur.Request(
                        f"{dashboard_url}/api/lessons",
                        data=body,
                        headers={"Content-Type": "application/json", "x-admin-secret": admin_secret},
                        method="PATCH",
                    )
                    with _ur.urlopen(req, timeout=10):
                        pass
                except Exception:
                    pass
        else:
            rejected.append(lesson)

    parts = []
    if approved:
        parts.append(f"{len(approved)} promosse in SKILL.md §14")
    if rejected:
        parts.append(f"{len(rejected)} rifiutate dalla Corte")

    result["status"] = "ok" if approved else ("skip" if not candidates else "ok")
    result["detail"] = ", ".join(parts) if parts else "nessuna azione"
    return result


# ── Morning briefing ──────────────────────────────────────────────────────────

def run_morning_briefing(project_path: str) -> dict:
    """Genera briefing mattutino: stats 7gg da coordination-log → dashboard + file locale."""
    result: dict = {"name": "morning_briefing", "status": "skip", "detail": ""}
    try:
        slug = re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")
        log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
        if not log_path.exists():
            result["detail"] = "coordination-log non trovato"
            return result

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        sessions: list[dict] = []
        for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = entry.get("timestamp") or entry.get("ts") or ""
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    sessions.append(entry)
            except ValueError:
                pass

        if not sessions:
            result["detail"] = "nessuna sessione negli ultimi 7gg"
            return result

        total_cost = sum(float(s.get("cost_usd", 0) or 0) for s in sessions)
        categories: dict[str, int] = {}
        outcomes: dict[str, int] = {}
        for s in sessions:
            cat = s.get("category") or "unknown"
            categories[cat] = categories.get(cat, 0) + 1
            out = s.get("outcome") or "ok"
            outcomes[out] = outcomes.get(out, 0) + 1

        top_cat = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        cat_summary = ", ".join(f"{c}:{n}" for c, n in top_cat[:5])
        errors = outcomes.get("error", 0) + outcomes.get("partial", 0)
        avg_cost = total_cost / len(sessions) if sessions else 0

        lines = [
            f"# Morning Briefing — {date.today()}",
            f"",
            f"**Sessioni ultimi 7gg**: {len(sessions)} | **Costo totale**: ${total_cost:.3f} | **Avg/sessione**: ${avg_cost:.3f}",
            f"**Categorie**: {cat_summary}",
            f"**Esiti**: ok={outcomes.get('ok', 0)}, errori/parziali={errors}",
        ]

        # Leggi eventuale top-lesson dal drain-log recente
        drain_log = SKILL_DIR / "reports" / "drain-log.jsonl"
        if drain_log.exists():
            recent_lines = drain_log.read_text(encoding="utf-8", errors="ignore").splitlines()
            for raw in reversed(recent_lines[-50:]):
                try:
                    entry = json.loads(raw)
                    detail = entry.get("detail") or ""
                    if detail and len(detail) > 20:
                        lines.append(f"**Ultimo drain**: {detail[:120]}")
                        break
                except Exception:
                    pass

        briefing_md = "\n".join(lines)

        # Scrivi file locale
        reports_dir = SKILL_DIR / "reports"
        reports_dir.mkdir(exist_ok=True)
        (reports_dir / "morning-briefing.md").write_text(briefing_md + "\n", encoding="utf-8")

        # Invia a dashboard
        try:
            sys.path.insert(0, str(SKILL_DIR / "scripts"))
            from buffering_client import post_with_fallback  # type: ignore
            post_with_fallback("/api/log", {
                "type": "morning_briefing",
                "project": Path(project_path).name,
                "summary": briefing_md,
                "sessions_7d": len(sessions),
                "cost_7d_usd": round(total_cost, 4),
                "errors_7d": errors,
            })
        except Exception:
            pass

        result["status"] = "ok"
        result["detail"] = f"{len(sessions)} sessioni, ${total_cost:.3f} — briefing scritto"
    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
    return result


# ── SkillOpt-lite ─────────────────────────────────────────────────────────────

def run_skillopt_lite(project_path: str) -> dict:
    """Propone ed applica UN edit mirato a SKILL.md usando SkillOpt apply_edit.

    Pipeline: leggi contesto (dead rules + anomalie recenti) → chiedi a Haiku
    UN patch JSON → valida (target esiste, line count ≤ 450) → applica.
    """
    result: dict = {"name": "skillopt_lite", "status": "skip", "detail": ""}
    try:
        from skillopt.optimizer.skill import apply_edit  # type: ignore
    except ImportError:
        result["detail"] = "skillopt non installato (pip install skillopt)"
        return result

    try:
        skill_path = SKILL_DIR / "SKILL.md"
        if not skill_path.exists():
            result["detail"] = "SKILL.md non trovato"
            return result

        skill_content = skill_path.read_text(encoding="utf-8")
        current_lines = len(skill_content.splitlines())

        # Raccogli contesto: dead rules + anomalie
        context_parts: list[str] = []
        dead_cache = SKILL_DIR / "scripts" / "dead-rules-cache.json"
        if dead_cache.exists():
            try:
                dc = json.loads(dead_cache.read_text(encoding="utf-8"))
                dead_cats = dc.get("dead_categories") or []
                if dead_cats:
                    context_parts.append(f"Categorie non usate da 60gg: {', '.join(str(c) for c in dead_cats[:5])}")
            except Exception:
                pass

        slug = re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")
        log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "coordination-log.jsonl"
        if log_path.exists():
            cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            errors: list[str] = []
            for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]:
                try:
                    e = json.loads(line)
                    if (e.get("outcome") in ("error", "partial")) and e.get("category"):
                        ts_str = e.get("timestamp") or e.get("ts") or ""
                        try:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if ts >= cutoff:
                                errors.append(e["category"])
                        except ValueError:
                            pass
                except Exception:
                    pass
            if errors:
                from collections import Counter
                top = Counter(errors).most_common(3)
                context_parts.append(f"Categorie con più errori ultimi 14gg: {', '.join(f'{c}({n})' for c, n in top)}")

        if not context_parts:
            result["detail"] = "nessun contesto disponibile, skip"
            return result

        context_str = "\n".join(context_parts)
        line_budget = 450 - current_lines

        prompt = f"""Sei un ottimizzatore di skill per agenti AI. Analizza questo contesto su SKILL.md e proponi UN SOLO miglioramento.

CONTESTO (dati reali dalle sessioni):
{context_str}

SKILL.md ha attualmente {current_lines} righe (limite: 450, budget disponibile: {line_budget} righe).

Produci SOLO un JSON valido con questa struttura:
{{"op": "replace"|"append"|"insert_after"|"delete", "target": "testo esatto da trovare in SKILL.md" (ometti per append), "content": "nuovo testo" (ometti per delete)}}

Regole:
- "target" deve essere una stringa ESATTA che appare in SKILL.md
- Per "append": aggiunge in fondo, content max 5 righe
- Per "replace": sostituisce target con content, content deve essere più corto di target
- Per "delete": rimuove target (solo se è una regola morta o duplicata)
- NON modificare il frontmatter YAML iniziale (righe con "description:" o "---")
- NON modificare §0, §1, §3 (core routing e model selection)
- Output: solo il JSON, niente altro

SKILL.md (prime 80 righe per contesto):
{chr(10).join(skill_content.splitlines()[:80])}"""

        proc = subprocess.run(
            ["claude", "--permission-mode", "default", "--model", "haiku", "--print", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            result["detail"] = f"claude CLI errore: {proc.stderr[:100]}"
            return result

        raw = (proc.stdout or "").strip()
        # Estrai JSON dall'output (potrebbe avere testo attorno)
        import re as _re
        m = _re.search(r'\{[^{}]*"op"[^{}]*\}', raw, _re.DOTALL)
        if not m:
            result["detail"] = f"nessun JSON valido nell'output: {raw[:80]}"
            return result

        edit_dict = json.loads(m.group())
        op = edit_dict.get("op")
        if op not in ("append", "insert_after", "replace", "delete"):
            result["detail"] = f"op non valido: {op}"
            return result

        # Valida che target esista in SKILL.md (per op != append)
        if op != "append":
            target = edit_dict.get("target", "")
            if target and target not in skill_content:
                result["detail"] = f"target non trovato in SKILL.md: {target[:60]}"
                return result

        # Applica
        new_content = apply_edit(skill_content, edit_dict)
        new_lines = len(new_content.splitlines())

        if new_lines > 450:
            result["detail"] = f"edit rigettato: risulterebbe in {new_lines} righe (max 450)"
            return result

        skill_path.write_text(new_content, encoding="utf-8")
        result["status"] = "ok"
        result["detail"] = f"edit '{op}' applicato: {current_lines}→{new_lines} righe"

    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
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

    _auto = _autopilot_enabled(dashboard_url)
    _skip = lambda name: {"name": name, "status": "skip", "detail": "autopilot disabilitato"}

    # Tuple (nome, callable) — il nome è noto prima dell'esecuzione, così le eccezioni non diventano "unknown"
    steps: list[tuple[str, object]] = [
        ("complete_tbd_entries",           lambda: complete_tbd_entries(project_path)),
        ("analyze_tool_errors",            lambda: analyze_tool_errors(project_path)),
        ("decay_mistake_register",         lambda: decay_mistake_register(project_path)),
        ("sediment_handoff",               lambda: sediment_handoff(project_path)),
        ("regenerate_score",               lambda: regenerate_score(project_path)),
        ("run_compaction",                 lambda: run_compaction(project_path)),
        ("validate_skill_drift",           lambda: validate_skill_drift(project_path)),
        ("evaluate_lessons",               lambda: evaluate_lessons(project_path) if _auto else _skip("evaluate_lessons")),
        ("create_lessons_from_failed_tasks", lambda: create_lessons_from_failed_tasks(project_path) if _auto else _skip("create_lessons_from_failed_tasks")),
        ("run_ai_news_intake",             lambda: run_ai_news_intake(project_path) if _auto else _skip("run_ai_news_intake")),
        ("auto_process_ai_news",           lambda: auto_process_ai_news(project_path) if _auto else _skip("auto_process_ai_news")),
        ("detect_session_anomalies",       lambda: detect_session_anomalies(project_path)),
        ("discover_cost_thresholds",       lambda: discover_cost_thresholds(project_path)),
        ("detect_dead_rules",              lambda: detect_dead_rules(project_path)),
        ("skill_assay",                    lambda: _run_skill_assay_safe(project_path)),
        ("promote_acknowledged_feedback",  lambda: promote_acknowledged_feedback(project_path) if _auto else _skip("promote_acknowledged_feedback")),
        ("run_ideation",                   lambda: run_ideation(project_path) if _auto else _skip("run_ideation")),
        ("court_review_lesson_promotion",  lambda: court_review_lesson_promotion(project_path) if _auto else _skip("court_review_lesson_promotion")),
        ("run_morning_briefing",           lambda: run_morning_briefing(project_path)),
        ("run_skillopt_lite",              lambda: run_skillopt_lite(project_path) if _auto else _skip("run_skillopt_lite")),
    ]

    for step_name, fn in steps:
        try:
            r = fn()
        except Exception as e:
            r = {"name": step_name, "status": "error", "detail": str(e)}
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
        if is_sunday:
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
