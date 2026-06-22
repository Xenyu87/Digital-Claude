#!/usr/bin/env python3
"""Blackboard condiviso per sessioni drain multi-agente.

Pattern: ogni step scrive il proprio slot in reports/blackboard/<step>.json
(no locking — ogni step ha file isolato). read_all() mergia tutti gli slot.

Beneficio: step sequenziali possono leggere output di step paralleli
senza ricalcolare o fare chiamate ridondanti a Haiku/API.

Esempio:
    # In un drain step:
    from blackboard import write_slot, read_slot, init_session

    init_session("drain-2026-06-22")          # crea/azzera la dir
    write_slot("detect_dead_rules", {"dead_categories": ["nuova_app"], "ts": "20:00"})
    dead = read_slot("detect_dead_rules")     # {"dead_categories": [...]}
    all_slots = read_all()                    # merge di tutti gli slot disponibili
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
_BOARD_DIR = SKILL_DIR / "reports" / "blackboard"


def _slot_path(step_name: str) -> Path:
    return _BOARD_DIR / f"{step_name}.json"


def init_session(session_id: str | None = None) -> Path:
    """Crea (o azzera) la directory blackboard per questa sessione drain.

    Scrive un metadata.json con session_id e timestamp.
    Ritorna il path della board dir.
    """
    _BOARD_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_id": session_id or datetime.now(timezone.utc).strftime("drain-%Y-%m-%dT%H:%M"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "slots": [],
    }
    _atomic_write(_slot_path("__meta__"), meta)
    return _BOARD_DIR


def write_slot(step_name: str, data: dict) -> None:
    """Scrive il risultato di uno step nel proprio slot atomicamente.

    Aggiunge automaticamente: step_name, written_at.
    Thread-safe: ogni step scrive in un file separato.
    """
    _BOARD_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "step": step_name,
        "written_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    _atomic_write(_slot_path(step_name), payload)


def read_slot(step_name: str) -> dict:
    """Legge un singolo slot. Ritorna {} se non esiste."""
    path = _slot_path(step_name)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_all() -> dict[str, dict]:
    """Legge tutti gli slot disponibili (esclude __meta__).

    Ritorna: {step_name: slot_dict, ...}
    """
    if not _BOARD_DIR.exists():
        return {}
    result: dict[str, dict] = {}
    for p in _BOARD_DIR.glob("*.json"):
        if p.stem.startswith("__"):
            continue
        try:
            result[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return result


def get_value(step_name: str, key: str, default=None):
    """Shortcut: legge un singolo valore da uno slot."""
    return read_slot(step_name).get(key, default)


def clear() -> None:
    """Svuota tutti gli slot (usare all'inizio di ogni drain run)."""
    if not _BOARD_DIR.exists():
        return
    for p in _BOARD_DIR.glob("*.json"):
        try:
            p.unlink()
        except Exception:
            pass


def _atomic_write(path: Path, data: dict) -> None:
    """Scrive JSON in modo atomico (write tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    # Test rapido
    init_session("test-session")
    write_slot("step_a", {"found": 3, "items": ["x", "y", "z"]})
    write_slot("step_b", {"cost_usd": 1.23})
    all_slots = read_all()
    print(f"Slots: {list(all_slots.keys())}")
    print(f"step_a.found = {get_value('step_a', 'found')}")
    print(f"step_b.cost_usd = {get_value('step_b', 'cost_usd')}")
    clear()
    print("Cleared. Done.")
