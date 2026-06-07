#!/usr/bin/env python3
"""Fetch lezioni, errori, e decision snapshot per SessionStart.

Output su stdout → iniettato come <system-reminder> tramite hook SessionStart.
Se la dashboard è down o non ci sono dati, stampa niente (silenzioso).

Scopo: la skill usa automaticamente le lezioni passate, decision snapshot, e feedback per evitare errori già visti.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")
if not BASE.startswith(("http://", "https://")):
    raise SystemExit(f"SKILL_DASHBOARD_URL schema non valido (deve essere http/https): {BASE}")


def fetch(path: str) -> list[dict]:
    try:
        req = urllib.request.Request(f"{BASE.rstrip('/')}{path}")
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read().decode()).get("rows", [])
    except Exception:
        return []


def fetch_setting(key: str) -> str | None:
    try:
        req = urllib.request.Request(f"{BASE.rstrip('/')}/api/settings?key={key}")
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read().decode()).get("value")
    except Exception:
        return None


def _drain_summary_if_recent() -> str | None:
    """Legge drain-log.jsonl e ritorna riassunto se c'è stato un run nelle ultime 12h."""
    try:
        import re as _re
        cwd = Path.cwd()
        slug = _re.sub(r"[^a-zA-Z0-9]", "-", str(cwd)).rstrip("-")
        log_path = Path.home() / ".claude" / "projects" / slug / "memory" / "drain-log.jsonl"
        if not log_path.exists():
            return None
        lines = log_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return None
        last = json.loads(lines[-1])
        ts_str = last.get("ts", "")
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        if age_h > 12:
            return None
        sub = last.get("sub_activities", [])
        parts = []
        for a in sub:
            if a.get("status") == "ok" and a.get("detail"):
                parts.append(f"{a['name']}: {a['detail']}")
        outcome = last.get("outcome", "?")
        summary = "; ".join(parts) if parts else "nessuna attività rilevante"
        return f"🌙 Drain stanotte ({outcome}): {summary}"
    except Exception:
        return None


def rel(iso: str) -> str:
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - t).days
        return f"{days}g fa" if days > 0 else "oggi"
    except Exception:
        return ""


def _pending_session_block() -> str | None:
    """Legge AI_HANDOFF.md e ritorna il blocco PROSSIMA SESSIONE se presente."""
    handoff = Path.cwd() / "AI_HANDOFF.md"
    if not handoff.exists():
        return None
    try:
        text = handoff.read_text(encoding="utf-8")
        marker = "## ⏸ PROSSIMA SESSIONE"
        if marker not in text:
            return None
        # Estrai tutto fino al prossimo ## heading
        start = text.index(marker)
        rest = text[start:]
        end = rest.find("\n## ", len(marker))
        block = rest[:end].strip() if end != -1 else rest.strip()
        # Prendi solo le righe con i task (###, -, **) — max 20 righe
        relevant = [l for l in block.splitlines()
                    if l.startswith(("###", "- ", "**", "⏸"))][:20]
        if not relevant:
            return None
        return "⏸ Sessione sospesa — lavoro in attesa:\n" + "\n".join(relevant)
    except Exception:
        return None


def main() -> None:
    # Solo in repo git con AI_HANDOFF.md (progetti attivi con la skill)
    if not (Path.cwd() / "AI_HANDOFF.md").exists():
        return

    lines: list[str] = []

    # Sessione sospesa: mostra subito il lavoro pendente
    pending = _pending_session_block()
    if pending:
        lines.append(pending)

    # Pillar 1: Decision Snapshot (SessionStart priming)
    try:
        skill_dir = Path(__file__).parent.parent
        snapshot_script = skill_dir / "scripts" / "decision_snapshot_builder.py"
        if snapshot_script.exists():
            result = subprocess.run(
                ["python3", str(snapshot_script)],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.stdout.strip():
                lines.append(result.stdout.strip())
    except Exception:
        pass  # Silenzioso se fallisce

    lessons = fetch("/api/lessons?limit=8")
    errors = fetch("/api/errors?limit=5")

    if lessons:
        lines.append("📚 Lezioni dai task precedenti (evita questi errori):")
        for l in lessons:
            badge = {"spreco": "spreco", "errore": "errore", "pattern": "pattern"}.get(
                l.get("pattern_type", ""), "?"
            )
            times = l.get("occurrences", 1)
            rule = l.get("rule", "").strip()
            promoted = " ✓ in SKILL.md" if l.get("promoted_to") else ""
            times_str = f" ({times}×)" if times > 1 else ""
            lines.append(f"  • [{badge}]{times_str} {rule}{promoted}")

    if errors:
        lines.append("⚠ Errori non risolti da sessioni precedenti:")
        for e in errors:
            when = rel(e.get("created_at", ""))
            lines.append(f"  • {e.get('error_type','?')}: {e.get('message','')[:100]} ({when})")

    feedback = fetch("/api/skill-feedback?status=pending&limit=5")
    if feedback:
        lines.append("🔁 Feedback dashboard (candidati promozione / routing insight):")
        kind_labels = {"promotion_candidate": "promozione", "routing_insight": "routing", "efficacy_alert": "efficacia"}
        for f in feedback:
            kind_label = kind_labels.get(f.get("kind", ""), f.get("kind", ""))
            lines.append(f"  • [{kind_label}] {f.get('title', '').strip()}")

    # Drain summary (solo se autopilot abilitato)
    if str(fetch_setting("autopilot") or "").lower() == "true":
        drain_summary = _drain_summary_if_recent()
        if drain_summary:
            lines.append(drain_summary)

    if lines:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
