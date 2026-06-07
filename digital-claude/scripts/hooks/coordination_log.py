#!/usr/bin/env python3
"""Hook Stop: chiama log_coordination.py a chiusura di ogni sessione non banale.

Questo hook viene eseguito da Claude Code come Stop hook globale.
Legge il jsonl di sessione per estrarre token/costo, poi delega a log_coordination.py.

Fail-safe: exit 0 sempre. Nessun blocco dell'agent.

Installazione in ~/.claude/settings.json:
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python /root/.claude/skills/digital-claude/scripts/hooks/coordination_log.py"}
        ]
      }
    ]
  }
}
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _find_latest_session_jsonl(project_path: str) -> Path | None:
    """Trova il jsonl di sessione piu' recente per il progetto."""
    # Claude Code usa slug con leading dash. Non strippare a sinistra.
    slug = re.sub(r"[^a-zA-Z0-9]", "-", project_path).rstrip("-")
    proj_dir = Path.home() / ".claude" / "projects" / slug
    if not proj_dir.exists():
        return None
    jsonls = sorted(
        proj_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Esclude coordination-log e drain-log
    for j in jsonls:
        if j.name not in ("coordination-log.jsonl", "drain-log.jsonl") and "archive" not in j.name:
            return j
    return None


def _extract_tokens_and_models(jsonl_path: Path) -> tuple[dict, list[str], dict[str, dict]]:
    """Aggrega token + lista modelli reali + token-per-modello da una sessione."""
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    models_seen: list[str] = []
    per_model: dict[str, dict] = {}
    try:
        for line in jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = entry.get("message") or {}
            usage = entry.get("usage") or msg.get("usage", {})
            model = entry.get("model") or msg.get("model") or ""
            # skip <synthetic> e simili
            if model and not model.startswith("<"):
                if model not in models_seen:
                    models_seen.append(model)
                per_model.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0})
            if not usage:
                continue
            t_in   = usage.get("input_tokens", 0)
            t_out  = usage.get("output_tokens", 0)
            t_cr   = usage.get("cache_read_input_tokens", 0)
            t_cc   = usage.get("cache_creation_input_tokens", 0)
            tokens["input"]          += t_in
            tokens["output"]         += t_out
            tokens["cache_read"]     += t_cr
            tokens["cache_creation"] += t_cc
            if model and not model.startswith("<"):
                per_model[model]["input"]          += t_in
                per_model[model]["output"]         += t_out
                per_model[model]["cache_read"]     += t_cr
                per_model[model]["cache_creation"] += t_cc
    except Exception:
        pass
    return tokens, models_seen, per_model


def _model_family(model_id: str) -> str:
    """Mappa un model id Anthropic alla famiglia haiku/sonnet/opus."""
    m = model_id.lower()
    if "haiku" in m: return "haiku"
    if "opus"  in m: return "opus"
    if "sonnet" in m: return "sonnet"
    return "sonnet"  # fallback conservativo


# Prezzi $/1M token, baseline 2026-05 (Anthropic public pricing).
# Famiglia: input, output, cache_read, cache_creation.
_PRICING = {
    "haiku":  {"input": 0.80, "output":  4.00, "cache_read": 0.08, "cache_creation": 1.00},
    "sonnet": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_creation": 3.75},
    "opus":   {"input": 15.0, "output": 75.00, "cache_read": 1.50, "cache_creation": 18.75},
}


def _estimate_cost(per_model: dict[str, dict], tokens: dict) -> float:
    """Stima costo per-modello quando disponibile, fallback a Sonnet."""
    if per_model:
        total = 0.0
        for model_id, tk in per_model.items():
            prices = _PRICING[_model_family(model_id)]
            for k, price in prices.items():
                total += tk.get(k, 0) * price / 1_000_000
        return round(total, 6)
    # Fallback: nessun modello rilevato, stima Sonnet conservativa
    prices = _PRICING["sonnet"]
    total = sum(tokens.get(k, 0) * price / 1_000_000 for k, price in prices.items())
    return round(total, 6)


_OPS_RE       = re.compile(r"\b(systemd|journalctl|ssh|lxc|porta|servizio|syncthing|deploy|riavvia|restart|cron|systemctl)\b", re.I)
_AUDIT_RE     = re.compile(r"\b(rivedi|review|controlla|sicurezza|audit|verifica)\b", re.I)
_BUG_RE       = re.compile(r"\b(non funziona|errore|crash|bug|fix|broken|rotto|fallisce)\b", re.I)
_NEW_APP_RE   = re.compile(r"\b(crea|scaffold|parti da zero|nuova app|nuovo progetto|init)\b", re.I)
_SKILL_RE     = re.compile(r"automiglior|\bmigliorati\b|(aggiorna|modifica|migliora) la skill", re.I)
# Categoria "domanda": prompt corti, interrogativi, senza imperativi forti
_INTERR_RE    = re.compile(r"^(cos[aà'’]|come|perch[éè]|quando|dove|chi|quale|quanto|spiega|dimmi|raccont|mostr[ai]?\b)", re.I)
_IMPERATIVE_RE = re.compile(r"\b(aggiungi|modifica|crea|implementa|scrivi|aggiorna|sposta|togli|rimuovi|cambia|refactor|integra|installa)\b", re.I)


def _detect_category(jsonl_path: Path) -> str:
    """Euristica multi-segnale sul primo prompt utente reale.

    Ordine di priorita': ops > bug > audit > new_app > skill > domanda > modifica.
    "domanda" intercetta prompt corti/interrogativi senza verbi imperativi
    (es. "cosa fa X", "come funziona Y", "dimmi Z") che prima cadevano in "modifica".
    """
    try:
        for line in jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = entry.get("role") or entry.get("message", {}).get("role", "")
            if role != "user":
                continue
            raw = entry.get("content") or entry.get("message", {}).get("content", "")
            content = str(raw).strip()
            # Salta prompt vuoti, comandi system o slash-only
            if not content or content.startswith("<") or content.startswith("/"):
                continue
            if len(content) < 3:
                continue
            # Trigger forti per categoria
            if _OPS_RE.search(content):     return "ops"
            if _BUG_RE.search(content):     return "bug_rescue"
            if _AUDIT_RE.search(content):   return "audit"
            if _NEW_APP_RE.search(content): return "nuova_app"
            if _SKILL_RE.search(content):   return "miglioramento_skill"
            # Distinzione domanda vs modifica:
            # - corto (<120 char) e interrogativo e SENZA verbi imperativi -> domanda
            # - finisce con ? e nessun imperativo -> domanda
            short = len(content) < 120
            has_question = "?" in content or _INTERR_RE.match(content)
            has_imperative = bool(_IMPERATIVE_RE.search(content))
            if has_question and not has_imperative and short:
                return "domanda"
            if content.endswith("?") and not has_imperative:
                return "domanda"
            return "modifica"
    except Exception:
        pass
    return "modifica"


def main() -> int:
    try:
        project_path = os.getcwd()
        # Non loggare se siamo nella dir della skill stessa
        skill_marker = Path(project_path) / "SKILL.md"
        if skill_marker.exists():
            return 0

        jsonl_path = _find_latest_session_jsonl(project_path)
        if jsonl_path is None:
            return 0

        tokens, models, per_model = _extract_tokens_and_models(jsonl_path)
        # Salta sessioni banali (<1000 token totali)
        total = sum(tokens.values())
        if total < 1000:
            return 0

        cost = _estimate_cost(per_model, tokens)
        category = _detect_category(jsonl_path)
        # Famiglie (haiku/sonnet/opus), unicizzate mantenendo ordine.
        families = []
        family_tokens: dict[str, int] = {}
        for m in models:
            f = _model_family(m)
            if f not in families:
                families.append(f)
            family_tokens[f] = family_tokens.get(f, 0) + sum(per_model.get(m, {}).values())
        # Share % per famiglia (basato su token totali).
        total_fam = sum(family_tokens.values()) or 1
        share_parts = [f"{f}:{family_tokens[f]/total_fam:.4f}" for f in families]
        models_share = ",".join(share_parts)

        script = Path(__file__).resolve().parent.parent / "log_coordination.py"
        cmd = [
            sys.executable,
            str(script),
            "--project", project_path,
            "--project-name", Path(project_path).name,
            "--category", category,
            "--outcome", "ok",
            "--cost", str(cost),
            "--models", ",".join(families),
            "--models-share", models_share,
            "--input-tokens", str(tokens["input"]),
            "--output-tokens", str(tokens["output"]),
            "--cache-read", str(tokens["cache_read"]),
            "--cache-creation", str(tokens["cache_creation"]),
        ]
        subprocess.run(cmd, check=False, timeout=10)

    except Exception as e:
        print(f"coordination_log hook: errore ({e}), skip.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
