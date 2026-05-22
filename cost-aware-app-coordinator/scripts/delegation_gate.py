#!/usr/bin/env python3
"""PreToolUse hook — blocca Edit/Write/MultiEdit dal main agent
quando l'ultimo routing-hint suggerisce un subagent con model
sonnet|haiku e nessun Agent e' stato spawnato dopo quel hint.

Override: l'utente puo' includere nel prompt una delle frasi
"fallo tu", "non delegare", "rimani sul main", "skip gate".
"""
import json
import os
import re
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
if tool not in ("Edit", "Write", "MultiEdit"):
    sys.exit(0)

transcript = data.get("transcript_path", "")
if not transcript or not os.path.exists(transcript):
    sys.exit(0)

override_re = re.compile(
    r"(fallo tu|non delegare|rimani sul main|skip gate|do it yourself)",
    re.I,
)
hint_re = re.compile(r"<routing-hint>(.+?)</routing-hint>", re.S)
model_re = re.compile(r"model:\s*(\w+)")
subagent_re = re.compile(r"suggested_subagent:\s*(\S+)")

lines = []
try:
    with open(transcript) as f:
        for raw in f:
            try:
                lines.append(json.loads(raw))
            except Exception:
                continue
except Exception:
    sys.exit(0)

last_hint = None
hint_idx = -1
override = False
agent_after_hint = False

for i, msg in enumerate(lines):
    mtype = msg.get("type")
    if mtype == "user":
        text = json.dumps(msg, ensure_ascii=False)
        m = hint_re.search(text)
        if m:
            block = m.group(1)
            mm = model_re.search(block)
            ms = subagent_re.search(block)
            last_hint = {
                "model": mm.group(1) if mm else None,
                "subagent": ms.group(1) if ms else None,
            }
            hint_idx = i
            agent_after_hint = False
            override = bool(override_re.search(text))
    elif mtype == "assistant" and hint_idx >= 0:
        content = msg.get("message", {}).get("content", [])
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Agent":
                agent_after_hint = True

if not last_hint:
    sys.exit(0)
if last_hint.get("model") not in ("sonnet", "haiku"):
    sys.exit(0)
if override or agent_after_hint:
    sys.exit(0)

msg = (
    "DELEGATION GATE: routing-hint suggerisce subagent="
    f"{last_hint.get('subagent')} model={last_hint.get('model')}, "
    f"ma stai per eseguire {tool} dal main agent.\n"
    "Azione richiesta: spawna Agent(subagent_type='"
    f"{last_hint.get('subagent')}', model='{last_hint.get('model')}') "
    "con brief autocontenuto, oppure chiedi all'utente di scrivere "
    "'fallo tu' nel prompt per bypassare il gate."
)
print(msg, file=sys.stderr)
sys.exit(2)
