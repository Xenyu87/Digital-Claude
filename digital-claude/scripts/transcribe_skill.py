#!/usr/bin/env python3
"""
RNA Transcription: genera una session-directive contestualizzata per SKILL.md.

Approccio deterministico — nessuna chiamata LLM, istantaneo.
Legge le categorie recenti del progetto corrente e produce un overlay
di 15-25 righe che dice a Claude quali sezioni di SKILL.md priorizzare
e quali sono irrilevanti per questo contesto.

Output su stdout → iniettato come <system-reminder> da SessionStart hook.
Silenzioso se dashboard down o progetto non riconosciuto.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

BASE = os.environ.get("SKILL_DASHBOARD_URL", "http://localhost:3001")


# Mappa categoria → sezioni da priorizzare / de-priorizzare
SECTION_MAP: dict[str, dict[str, list[str]]] = {
    "modifica": {
        "high": ["§0 fast path", "§3 model selection + delegation gate", "§6 working loop", "§7 output economy", "§11 definition of done"],
        "low": ["§12 new app creation", "§14 audit", "§15 bug rescue", "§16 skill improvement"],
        "budget": "economical",
        "subagent_hint": "code-implementer per edit >3 file",
    },
    "nuova_app": {
        "high": ["§0 fast path", "§3 model selection", "§12 creating new app", "§10 handoff", "§6 working loop"],
        "low": ["§14 audit", "§15 bug rescue", "§16 skill improvement", "§17 maintenance"],
        "budget": "balanced",
        "subagent_hint": "architect per stack design iniziale",
    },
    "audit": {
        "high": ["§14 audit", "§3 model selection", "§9 specialists", "§8 decision gates", "§11 done"],
        "low": ["§12 new app", "§15 bug rescue", "§17 maintenance"],
        "budget": "balanced",
        "subagent_hint": "code-security-scanner o code-reviewer",
    },
    "bug_rescue": {
        "high": ["§15 bug rescue", "§3 model selection", "§6 working loop", "§8 decision gates"],
        "low": ["§12 new app", "§14 audit", "§16 skill improvement"],
        "budget": "economical",
        "subagent_hint": "code-debugger per bug non banali",
    },
    "ops": {
        "high": ["§3 model selection (haiku per ops)", "§8 decision gates", "§6 working loop"],
        "low": ["§12 new app", "§14 audit", "§16 skill improvement", "§9 specialists"],
        "budget": "economical",
        "subagent_hint": "ops-runner per comandi systemctl/journalctl",
    },
    "miglioramento_skill": {
        "high": ["§16 skill improvement", "§3 model selection", "§20 validator", "§5 progressive loading"],
        "low": ["§12 new app", "§14 audit", "§15 bug rescue"],
        "budget": "balanced",
        "subagent_hint": "validate_skill.py prima di ogni modifica SKILL.md",
    },
    "domanda": {
        "high": ["§0 fast path (risposta diretta)", "§7 output economy"],
        "low": ["§9 specialists", "§12 new app", "§14 audit"],
        "budget": "economical",
        "subagent_hint": None,
    },
}

DEFAULT_CATEGORY = "modifica"


def fetch_recent_categories(project_path: str, limit: int = 20) -> list[str]:
    """Recupera le categorie recenti per questo progetto dalla dashboard."""
    try:
        url = f"{BASE.rstrip('/')}/api/tasks?limit={limit}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as r:
            data = json.loads(r.read().decode())
        rows = data.get("rows", [])
        # Filtra per progetto corrente (project_path contiene la cwd)
        project_rows = [
            row for row in rows
            if project_path.lower() in (row.get("project_path") or "").lower()
            or Path(project_path).name.lower() in (row.get("project_path") or "").lower()
        ]
        cats = [r.get("category") for r in project_rows if r.get("category")]
        return cats[:limit]
    except Exception:
        return []


def dominant_category(cats: list[str]) -> str:
    """Restituisce la categoria più frequente, con fallback a DEFAULT_CATEGORY."""
    if not cats:
        return DEFAULT_CATEGORY
    counts: dict[str, int] = {}
    for c in cats:
        counts[c] = counts.get(c, 0) + 1
    return max(counts, key=lambda k: counts[k])


def build_directive(category: str, project_name: str) -> str:
    """Costruisce la session-directive RNA per categoria e progetto."""
    mapping = SECTION_MAP.get(category, SECTION_MAP[DEFAULT_CATEGORY])
    high = ", ".join(mapping["high"])
    low = ", ".join(mapping["low"])
    budget = mapping["budget"]
    subagent = mapping.get("subagent_hint") or "nessuno specifico"

    lines = [
        f"🧬 RNA Skill — sessione contestualizzata [{project_name} · {category}]",
        f"  Sezioni ad alta priorità: {high}",
        f"  Sezioni de-priorizzate: {low}",
        f"  Budget mode: {budget}",
        f"  Subagent suggerito: {subagent}",
    ]
    return "\n".join(lines)


def main() -> None:
    # Solo se siamo in un progetto con AI_HANDOFF.md
    cwd = Path.cwd()
    if not (cwd / "AI_HANDOFF.md").exists():
        return

    project_name = cwd.name
    cats = fetch_recent_categories(str(cwd))
    category = dominant_category(cats)

    directive = build_directive(category, project_name)
    print(directive)


if __name__ == "__main__":
    main()
