#!/usr/bin/env python3
"""Telegram notification helper for runner confirmations.

Secrets are read from environment variables or a local env file. The script
never prints the bot token.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECRET_FILE = ROOT / "reports" / "runner-secrets.env"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def telegram_config(secret_file: Path = DEFAULT_SECRET_FILE) -> dict[str, object]:
    file_values = load_env_file(secret_file)
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or file_values.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or file_values.get("TELEGRAM_CHAT_ID", "")
    return {
        "secret_file": str(secret_file),
        "secret_file_exists": secret_file.exists(),
        "token_configured": bool(token),
        "chat_id_configured": bool(chat_id),
        "ready": bool(token and chat_id),
        "chat_id": chat_id if chat_id else "",
    }


def token_from_sources(secret_file: Path = DEFAULT_SECRET_FILE) -> str:
    file_values = load_env_file(secret_file)
    return os.environ.get("TELEGRAM_BOT_TOKEN") or file_values.get("TELEGRAM_BOT_TOKEN", "")


def discover_chats(secret_file: Path = DEFAULT_SECRET_FILE) -> dict[str, object]:
    token = token_from_sources(secret_file)
    if not token:
        return {"ok": False, "error": "telegram_token_missing", "status": telegram_config(secret_file), "chats": []}
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/getUpdates", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 - CLI helper must return a safe JSON error.
        return {"ok": False, "error": str(exc), "status": telegram_config(secret_file), "chats": []}
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_telegram_response", "chats": []}
    chats: dict[str, dict[str, object]] = {}
    for item in parsed.get("result", []) if isinstance(parsed, dict) else []:
        message = item.get("message") or item.get("edited_message") or {}
        chat = message.get("chat") if isinstance(message, dict) else {}
        if not isinstance(chat, dict) or "id" not in chat:
            continue
        chat_id = str(chat.get("id"))
        chats[chat_id] = {
            "chat_id": chat_id,
            "type": chat.get("type", ""),
            "title": chat.get("title") or " ".join(str(chat.get(key, "")).strip() for key in ["first_name", "last_name"] if chat.get(key)).strip(),
            "username": chat.get("username", ""),
        }
    return {
        "ok": bool(parsed.get("ok")) if isinstance(parsed, dict) else False,
        "chats": list(chats.values()),
        "hint": "Se non vedi chat, manda prima un messaggio al bot su Telegram e rilancia questo comando.",
    }


def send_message(text: str, secret_file: Path = DEFAULT_SECRET_FILE) -> dict[str, object]:
    file_values = load_env_file(secret_file)
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or file_values.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or file_values.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return {"ok": False, "error": "telegram_not_configured", "status": telegram_config(secret_file)}
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 - CLI helper must return a safe JSON error.
        return {"ok": False, "error": str(exc), "status": telegram_config(secret_file)}
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = {"raw": body[:500]}
    return {"ok": bool(parsed.get("ok")) if isinstance(parsed, dict) else False, "response": parsed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--secret-file", default=str(DEFAULT_SECRET_FILE))
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    sub.add_parser("chats")
    send = sub.add_parser("send-test")
    send.add_argument("--text", default="Test conferme runner Codex: Telegram configurato.")
    args = parser.parse_args()

    secret_file = Path(args.secret_file)
    if args.command == "send-test":
        result = send_message(args.text, secret_file)
    elif args.command == "chats":
        result = discover_chats(secret_file)
    else:
        result = telegram_config(secret_file)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print("Telegram ready" if result.get("ready") or result.get("ok") else "Telegram not configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
