#!/usr/bin/env python3
"""Buffer locale per dati quando la dashboard non è raggiungibile.

La coda di buffering persiste in ~/.claude/skills/digital-claude/reports/offline-queue.jsonl
Quando la dashboard si riconnette, i dati vengono inviati e la coda svuotata.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from dashboard_client import post_to_dashboard, discover_dashboard_url


SKILL_PATH = Path(__file__).parent.parent
QUEUE_FILE = SKILL_PATH / "reports" / "offline-queue.jsonl"


def ensure_queue_dir() -> None:
    """Crea la cartella reports se non esiste."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)


def enqueue_message(endpoint: str, payload: dict[str, Any]) -> None:
    """Salva un messaggio nella coda offline.

    Args:
        endpoint: es. "/api/log", "/api/skill-version"
        payload: dict da inviare
    """
    ensure_queue_dir()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "payload": payload,
    }
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"📋 Messaggio accodato per invio futuro (coda: {QUEUE_FILE})", file=sys.stderr)


def flush_queue() -> bool:
    """Invia tutti i messaggi in coda alla dashboard.

    Returns:
        True se riuscito, False se dashboard ancora irraggiungibile.
    """
    if not QUEUE_FILE.exists():
        return True  # Niente da inviare

    entries = []
    try:
        with open(QUEUE_FILE, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except Exception as e:
        print(f"⚠️  Errore lettura coda offline: {e}", file=sys.stderr)
        return False

    if not entries:
        return True  # Coda vuota

    dashboard = discover_dashboard_url()
    if not dashboard:
        print(
            f"⚠️  Dashboard ancora irraggiungibile. Coda offline contiene {len(entries)} messaggi.",
            file=sys.stderr,
        )
        return False

    # Tenta invio di tutti i messaggi
    success_count = 0
    for entry in entries:
        endpoint = entry["endpoint"]
        payload = entry["payload"]
        if post_to_dashboard(endpoint, payload):
            success_count += 1

    print(f"✓ Svuotata coda offline: {success_count}/{len(entries)} messaggi inviati.")

    if success_count == len(entries):
        # Tutti riusciti, elimina la coda
        QUEUE_FILE.unlink(missing_ok=True)
        return True
    else:
        # Alcuni falliti, mantieni la coda
        return False


def post_with_fallback(endpoint: str, payload: dict[str, Any]) -> bool:
    """Invia un messaggio, con buffering automatico se la dashboard non è raggiungibile.

    Args:
        endpoint: es. "/api/log"
        payload: dict da inviare

    Returns:
        True se inviato subito, False se bufferizzato offline.
    """
    if post_to_dashboard(endpoint, payload):
        # Connesso, tenta anche di svuotare la coda se esiste
        flush_queue()
        return True
    else:
        # Non connesso, accoda
        enqueue_message(endpoint, payload)
        return False


if __name__ == "__main__":
    if sys.argv[1:2] == ["--flush"]:
        success = flush_queue()
        sys.exit(0 if success else 1)
