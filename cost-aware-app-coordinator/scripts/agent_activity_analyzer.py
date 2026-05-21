#!/usr/bin/env python3
"""Infer work domains and recommended experts from local Codex session logs."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


DOMAINS = {
    "frontend": ["frontend", "component", ".tsx", ".jsx", ".css", "vite", "react", "ui"],
    "backend": ["backend", "controller", "service", "route", "api", "express"],
    "qa/test": ["test", "spec", "playwright", "vitest", "jest", "npm test"],
    "docs/context": ["README", "AGENTS.md", "AI_CONTEXT.md", "docs/", ".md"],
    "devops": ["docker", "deploy", "workflow", "nginx", "env", "build"],
    "security": ["auth", "jwt", "secret", "permission", "session", ".env"],
    "data": ["migration", "schema", "database", "prisma", "sql", "model"],
    "context-cost": ["Get-Content", "cat ", "rg ", "context_budget", "token"],
}
EXPERTS = {
    "frontend": "Frontend/UX expert",
    "backend": "Backend/API contract expert",
    "qa/test": "QA/Test expert",
    "docs/context": "Context/documentation maintainer",
    "devops": "DevOps/release expert",
    "security": "Security/auth expert",
    "data": "Data/migration expert",
    "context-cost": "Context optimizer",
}


def read_sessions(limit: int) -> list[dict[str, object]]:
    root = Path.home() / ".codex" / "sessions"
    if not root.exists():
        return []
    files = sorted(root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    rows: list[dict[str, object]] = []
    for file in files:
        cwd = ""
        text_parts: list[str] = []
        tokens = 0
        tool_calls = 0
        model = ""
        ts = ""
        try:
            with file.open("r", encoding="utf-8") as handle:
                for raw in handle:
                    text_parts.append(raw[:1800])
                    if '"type":"session_meta"' in raw or '"type":"turn_context"' in raw:
                        data = json.loads(raw)
                        payload = data.get("payload", {})
                        cwd = payload.get("cwd", cwd)
                        model = payload.get("model", model)
                        ts = ts or str(data.get("timestamp") or "")
                    elif '"type":"function_call"' in raw:
                        tool_calls += 1
                    elif '"type":"token_count"' in raw:
                        data = json.loads(raw)
                        usage = (data.get("payload", {}).get("info") or {}).get("last_token_usage") or {}
                        tokens = int(usage.get("total_tokens", tokens) or tokens)
        except (OSError, json.JSONDecodeError):
            continue
        if cwd:
            rows.append(
                {
                    "timestamp": ts,
                    "project": Path(cwd).name,
                    "path": cwd,
                    "model": model,
                    "tokens": tokens,
                    "tool_calls": tool_calls,
                    "text": "\n".join(text_parts).lower(),
                }
            )
    return rows


def score(rows: list[dict[str, object]], project_filter: str | None) -> dict[str, object]:
    domains = collections.Counter()
    projects = collections.Counter()
    project_tokens = collections.Counter()
    for row in rows:
        project = str(row["project"])
        projects[project] += 1
        project_tokens[project] += int(row["tokens"])
        if project_filter and Path(str(row["path"])).resolve() != Path(project_filter).resolve():
            continue
        text = str(row["text"])
        for domain, markers in DOMAINS.items():
            domains[domain] += sum(text.count(marker.lower()) for marker in markers)
    top_domains = [{"domain": key, "score": value} for key, value in domains.most_common(8) if value]
    suggested = []
    for item in top_domains[:5]:
        expert = EXPERTS[str(item["domain"])]
        reason = f"High {item['domain']} activity in recent sessions."
        suggested.append({"expert": expert, "reason": reason})
    if domains["context-cost"] > 80 and not any(item["expert"] == "Context optimizer" for item in suggested):
        suggested.insert(0, {"expert": "Context optimizer", "reason": "Many read/search/token markers detected."})
    return {
        "sessions_scanned": len(rows),
        "project_filter": project_filter or "",
        "top_projects": [{"name": k, "sessions": v, "tokens": project_tokens[k]} for k, v in projects.most_common(8)],
        "top_domains": top_domains,
        "suggested_experts": suggested[:6],
        "note": "Inferred from local Codex logs, not official agent identity.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project")
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = score(read_sessions(args.limit), args.project)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Sessions scanned: {result['sessions_scanned']}")
        print("Top domains:")
        for item in result["top_domains"]:
            print(f"- {item['domain']}: {item['score']}")
        print("Suggested experts:")
        for item in result["suggested_experts"]:
            print(f"- {item['expert']}: {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
