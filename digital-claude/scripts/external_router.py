#!/usr/bin/env python3
"""Router esterno opzionale verso OpenRouter/DeepSeek.

DISABILITATO DI DEFAULT. Attivare solo con EXTERNAL_ROUTER_ENABLED=true.
Mai usare per codice di prodotto, credenziali, dati personali.

Uso:
    from scripts.external_router import ExternalRouter
    router = ExternalRouter()
    output = router.route(prompt="...", category="ops")

Se EXTERNAL_ROUTER_ENABLED != 'true', route() ritorna None (fallback al router locale).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Categorie autorizzate per routing esterno
ALLOWED_CATEGORIES = frozenset({"ops"})

# Target supportati
SUPPORTED_TARGETS = {"deepseek", "openrouter"}

# Flag per avvertire una sola volta per sessione
_warned_this_session = False

# Path per log
_SKILL_DIR = Path(__file__).resolve().parent.parent


def _log_external_use(category: str, target: str) -> None:
    """Logga l'uso del router esterno in coordination-log."""
    log_script = _SKILL_DIR / "scripts" / "log_coordination.py"
    if not log_script.exists():
        return
    try:
        import subprocess
        subprocess.run(
            [
                sys.executable, str(log_script),
                "--project", os.getcwd(),
                "--category", category,
                "--outcome", "ok",
                "--keywords", "external_router", target,
            ],
            check=False,
            timeout=5,
        )
    except Exception:
        pass


class ExternalRouter:
    """Router verso provider esterni. Fail-safe: ritorna None su qualsiasi errore."""

    def __init__(self) -> None:
        self.enabled = os.environ.get("EXTERNAL_ROUTER_ENABLED", "false").lower() == "true"
        self.target = os.environ.get("EXTERNAL_ROUTER_TARGET", "deepseek").lower()
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")

    def _warn_once(self) -> None:
        global _warned_this_session
        if _warned_this_session:
            return
        _warned_this_session = True
        print(
            "\n[EXTERNAL ROUTER] ATTENZIONE: questa chiamata viene instradata a provider "
            f"esterno ({self.target}). I dati NON passano da Anthropic. "
            "Assicurati di non inviare codice di prodotto, credenziali o dati personali.\n",
            file=sys.stderr,
        )

    def _validate(self, category: str) -> bool:
        """Verifica che la categoria sia autorizzata e l'env sia configurato."""
        if not self.enabled:
            return False
        if category not in ALLOWED_CATEGORIES:
            print(
                f"[external_router] categoria '{category}' non autorizzata per routing esterno. "
                "Solo 'ops' e' consentito. Fallback locale.",
                file=sys.stderr,
            )
            return False
        if self.target not in SUPPORTED_TARGETS:
            print(f"[external_router] target '{self.target}' non supportato.", file=sys.stderr)
            return False
        if not self.api_key:
            print("[external_router] OPENROUTER_API_KEY non impostata. Fallback locale.", file=sys.stderr)
            return False
        return True

    def _call_openrouter(self, prompt: str, model: str = "deepseek/deepseek-chat") -> str | None:
        """Chiama OpenRouter API. Ritorna il testo o None su errore."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/digital-claude",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[external_router] errore chiamata: {e}", file=sys.stderr)
            return None

    def route(self, prompt: str, category: str = "ops") -> str | None:
        """Esegue il routing esterno se abilitato e autorizzato.

        Ritorna il testo di risposta, oppure None se fallback al locale.
        """
        if not self._validate(category):
            return None

        self._warn_once()

        # Modello per target
        model_map = {
            "deepseek": "deepseek/deepseek-chat",
            "openrouter": "deepseek/deepseek-chat",  # default su OpenRouter
        }
        model = model_map.get(self.target, "deepseek/deepseek-chat")

        result = self._call_openrouter(prompt, model)
        if result is not None:
            _log_external_use(category, self.target)
        return result


if __name__ == "__main__":
    # Test rapido
    router = ExternalRouter()
    if not router.enabled:
        print("External router disabilitato (EXTERNAL_ROUTER_ENABLED != true). OK.", file=sys.stderr)
    else:
        out = router.route("Ciao, funziona?", category="ops")
        print(f"Output: {out}", file=sys.stderr)
    sys.exit(0)
