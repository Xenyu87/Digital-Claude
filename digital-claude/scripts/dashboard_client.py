#!/usr/bin/env python3
"""Helper per connessione alla dashboard centralizzata con fallback automatico.

Discovery order:
  1. SKILL_DASHBOARD_URL env var (se impostata dall'utente)
  2. localhost:3001 (fallback per dev locale)
  3. 192.168.1.147:3001 (dashboard centralizzata in LAN)

Se nessuno risponde, ritorna None e loga warning.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Optional


DISCOVERY_ENDPOINTS = [
    "http://localhost:3001",
    "http://192.168.1.147:3001",
]


def discover_dashboard_url() -> Optional[str]:
    """Scopri l'URL della dashboard con fallback.

    Returns:
        URL raggiungibile della dashboard, oppure None se nessuno risponde.
    """
    # 1. Env var impostata esplicitamente
    env_url = os.environ.get("SKILL_DASHBOARD_URL")
    if env_url:
        candidates = [env_url]
    else:
        candidates = DISCOVERY_ENDPOINTS

    for url in candidates:
        if _test_endpoint(url):
            return url

    # Nessuno raggiungibile
    return None


def _test_endpoint(url: str, timeout: int = 2) -> bool:
    """Testa se un endpoint della dashboard è raggiungibile."""
    try:
        test_url = url.rstrip("/") + "/api/health"
        req = urllib.request.Request(test_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 404)  # 404 OK se l'endpoint non esiste, almeno il server risposte
    except Exception:
        return False


def post_to_dashboard(endpoint: str, payload: dict[str, Any]) -> bool:
    """Invia un POST alla dashboard.

    Args:
        endpoint: es. "/api/skill-version"
        payload: dict da inviare come JSON

    Returns:
        True se riuscito, False se failed (con log).
    """
    dashboard_url = discover_dashboard_url()

    if not dashboard_url:
        print(
            f"⚠️  Dashboard centralizzata non raggiungibile (tentati: {', '.join(DISCOVERY_ENDPOINTS)}). "
            "Skill continua in modalità offline.",
            file=sys.stderr,
        )
        return False

    url = dashboard_url.rstrip("/") + endpoint
    data = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print(
            f"⚠️  POST a {endpoint} fallito: {e}. Continuando offline.",
            file=sys.stderr,
        )
        return False


if __name__ == "__main__":
    # Test
    url = discover_dashboard_url()
    if url:
        print(f"✓ Dashboard trovata: {url}")
    else:
        print("✗ Nessuna dashboard raggiungibile")
        sys.exit(1)
