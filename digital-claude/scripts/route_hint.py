#!/usr/bin/env python3
"""
UserPromptSubmit hook: classifica il prompt utente ed emette un blocco
<routing-hint> che l'orchestrator legge per decidere quale subagent invocare.

Input (stdin, JSON dal harness Claude Code):
    { "session_id":..., "cwd":..., "prompt": "<testo utente>", ... }

Output (stdout, finisce nel contesto della sessione):
    <routing-hint>
    classified: <category>
    suggested_subagent: <nome>
    model: <haiku|sonnet|opus>
    budget_max: <token>
    reason: <breve>
    </routing-hint>

Mai bloccante: errori → silent (exit 0, no output). Mai output >300 char.
"""
from __future__ import annotations

import json
import re
import sys

# Riusa la stessa regex del logger per coerenza con la classificazione
# post-sessione (auto_log_task.py).
_CATEGORY_PATTERNS = [
    ("ops",                 r"\b(systemd|journalctl|syncthing|ssh|sshd|lxc|proxmox|cron(tab)?|firewall|iptables|nginx|deploy(o|are)?|servizio|service|porta\s*\d+|reboot|riavvia(re)?|backup|monta(re)?|mount|cron job)\b"),
    ("miglioramento_skill", r"\b(aggiorna(re)? la skill|automigliorati|migliora(re)? la skill|miglioramento skill|skill\.md)\b"),
    ("nuova_app",           r"\b(crea(re)?|scaffold|parti(re)? da zero|nuovo progetto|nuova app|inizia(re)? un)\b"),
    ("audit",               r"\b(rivedi|review|audit|valuta|controlla|analizza|cosa possiamo migliorare|second opinion)\b"),
    ("bug_rescue",          r"\b(non funziona|errore|crash|bug|rotto|fix|risolvi|debug|stack ?trace)\b"),
]

# Comandi imperativi brevi: eseguire in un unico blocco tool, niente conferma intermedia, niente riepilogo
_IMPERATIVE_PATTERNS = [
    r"^(committa|commit|committa tutto|pusha|push)[\s!.]*$",
    r"^(installa|install|disinstalla|aggiorna|update|upgrade)[\s\w!.]*$",
    r"^(fixa|fix|risolvi|correggi)[\s\w!.]*$",
    r"^(riavvia|restart|reboot|reload|ferma|stop|avvia|start)[\s\w!.]*$",
    r"^(elimina|cancella|rimuovi|delete|remove)[\s\w!.]*$",
    r"^(continua|vai|procedi|esegui|fai|apply|applica)[\s\w!.]*$",
    r"^si[\s!.]*$",
]

# Pattern per "esplorazione" (haiku-tier) — domande dove serve grep/find/lettura
# ma non edit. Sono indizi forti che ha senso delegare ad Explore.
_EXPLORE_PATTERNS = [
    r"\bdove (sta|si trova|è|e')\b",
    r"\bcerca(re)?\b",
    r"\btrov(a|ami|are)\b",
    r"\bquanti? (file|funzioni|classi|test)\b",
    r"\b(grep|find|glob)\b",
    r"\bcome funziona\b",
    r"\bspiega(mi)?\b",
    r"\bcos(a|') (c'?è|fa|sono|significa)\b",
]

# Mappa categoria → (subagent default, modello, budget token).
# Allineata con tabella in SKILL.md §3. Tieni budget conservativi.
_ROUTING = {
    "ops":                 ("ops-runner",       "haiku",  50_000),
    "miglioramento_skill": ("code-implementer", "sonnet", 200_000),
    "nuova_app":           ("architect",        "opus",   600_000),
    "audit":               ("code-reviewer",    "sonnet", 400_000),
    "bug_rescue":          ("code-debugger",    "sonnet", 250_000),
    "modifica":            ("code-implementer", "sonnet", 200_000),
}

# Rapporto di costo rispetto al modello di sessione (approssimato).
# Mostrato nel routing-hint per rendere la scelta visceralmente visibile.
_COST_LABEL = {
    "haiku":  "~15× più economico di sonnet",
    "sonnet": "modello di default",
    "opus":   "~5× più costoso di sonnet — solo se strettamente necessario",
}


def classify(prompt: str) -> tuple[str, str]:
    """Ritorna (category, reason)."""
    t = (prompt or "").lower()
    if not t.strip():
        return "modifica", "prompt vuoto"
    # esplorazione ha priorità su modifica: se sembra una query di ricerca,
    # mandiamola a Explore anche se la regex di categoria dice "modifica".
    for pat in _EXPLORE_PATTERNS:
        if re.search(pat, t):
            return "explore", f"match esplorazione: {pat[:30]}"
    for cat, pat in _CATEGORY_PATTERNS:
        if re.search(pat, t):
            return cat, f"match {cat}"
    return "modifica", "fallback"


def _is_imperative(prompt: str) -> bool:
    t = prompt.strip().lower()
    return any(re.match(p, t) for p in _IMPERATIVE_PATTERNS)


def route(prompt: str) -> dict:
    cat, reason = classify(prompt)
    batch_mode = _is_imperative(prompt)
    if cat == "explore":
        return {
            "category": "explore",
            "subagent": "Explore",
            "model": "haiku",
            "budget": 30_000,
            "cost_label": _COST_LABEL["haiku"],
            "spawn_hint": 'Agent(subagent_type="Explore", prompt="...")',
            "reason": reason,
        }
    subagent, model, budget = _ROUTING.get(cat, _ROUTING["modifica"])
    return {
        "category": cat,
        "subagent": subagent,
        "model": model,
        "budget": budget,
        "reason": reason,
        "cost_label": _COST_LABEL.get(model, ""),
        "spawn_hint": f'Agent(subagent_type="{subagent}", prompt="...")',
        "batch_mode": batch_mode,
    }


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 0
    prompt = data.get("prompt") or data.get("user_message") or ""
    if not isinstance(prompt, str) or not prompt.strip():
        return 0
    # Salta slash-command (gestiti dal harness) e prompt non-imperativi troppo corti
    if prompt.lstrip().startswith("/"):
        return 0
    if len(prompt) < 12 and not _is_imperative(prompt):
        return 0
    r = route(prompt)
    # Bridge per Stop hook: il logger leggerà /tmp/claude-route-<sid>.json
    # per popolare `model_suggested` nel payload /api/log.
    sid = data.get("session_id")
    if isinstance(sid, str) and sid:
        try:
            import os
            tmp_path = f"/tmp/claude-route-{sid}.json"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "model_suggested": r["model"],
                        "subagent_suggested": r["subagent"],
                        "category_suggested": r["category"],
                    },
                    f,
                )
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass
    lines = [
        "<routing-hint>",
        f"classified: {r['category']}",
        f"suggested_subagent: {r['subagent']}",
        f"model: {r['model']}",
        f"budget_max: {r['budget']}",
        f"reason: {r['reason']}",
    ]
    if r.get("cost_label"):
        lines.append(f"cost: {r['cost_label']}")
    if r.get("spawn_hint"):
        lines.append(f"spawn: {r['spawn_hint']}")
    if r.get("batch_mode"):
        lines.append("batch_mode: true — esegui in un unico blocco tool, niente conferma, niente riepilogo finale")
    lines.append("</routing-hint>")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
