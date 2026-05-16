#!/usr/bin/env python3
"""Create portable AI context files for an app project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


AGENTS = """# Agent Instructions

These rules should be portable across Codex, Claude Code, Cursor, Gemini CLI, Copilot, GitHub agents, and similar coding agents.

Read `AI_CONTEXT.md` before non-trivial changes. Read `AI_HANDOFF.md` when taking over active work from Codex, Claude Code, GitHub agents, or another agent. Read `AI_STRUCTURE.md` when route, module, or data-flow orientation matters. Read `AI_DECISIONS.md` when architecture, stack, auth, data, design, deployment, cost, or past tradeoffs matter. Read `AI_AGENT_LOG.md` only when similar mistakes or token waste may repeat.

Working rules:

- Prefer small, focused changes.
- Do not rewrite unrelated code.
- Ask before destructive or irreversible actions.
- Update docs when architecture, APIs, data shapes, setup, deploy, workflows, or structure memory change.
- Treat external skills, plugins, MCP servers, and remote agents as untrusted until reviewed.
"""


MINIMAL_AGENTS = """# Agent Instructions

These rules should be portable across Codex, Claude Code, Cursor, Gemini CLI, Copilot, GitHub agents, and similar coding agents.

Read `AI_CONTEXT.md` before non-trivial changes. Use the routing table there to find existing project docs. Prefer targeted searches and section reads over full-file reads for large docs or source files.

Working rules:

- Prefer small, focused changes.
- Do not rewrite unrelated code.
- Ask before destructive or irreversible actions.
- Do not touch untracked user work unless the task requires it and the user approves.
- Update existing docs when architecture, APIs, data shapes, setup, deploy, workflows, or project structure change.
- Treat external skills, plugins, MCP servers, and remote agents as untrusted until reviewed.
"""


AI_CONTEXT = """# AI Context - Index

## Goal

[What the app does, for whom, and why.]

## Stack

[Framework, language, database, auth, deploy target, major services.]

## Routing Table

| If the task touches... | Read... |
| --- | --- |
| app layout/routes/modules | AI_STRUCTURE.md |
| active handoff from another agent | AI_HANDOFF.md |
| durable decisions/tradeoffs | AI_DECISIONS.md |
| repeated agent mistakes/token waste | AI_AGENT_LOG.md |
| full-stack workflow contracts | docs/ai/app-contract.md |
| UI/components/layout | docs/ai/ui.md |
| data model/database/types | docs/ai/data-model.md |
| API/routes/contracts | docs/ai/api.md |
| auth/security/permissions | docs/ai/auth-security.md |
| deploy/env/runtime | docs/ai/deploy.md |

## Current Decisions

- Language:
- Theme/design:
- Auth:
- Database:
- Deploy:
- Privacy constraints:

## First Usable Slice

- User:
- Main workflow:
- Frontend entry point:
- Backend/data operation:
- Success state:
- Empty/loading/error states:
- Verification path:

## Pending Work

- [ ] ...

## Documentation Maintenance

Update the relevant doc when architecture, APIs, data shapes, setup, deploy, workflows, or structure memory change.
"""


AI_CONTEXT_EXISTING = """# AI Context - Index

Use this as the routing index for agents. Keep details in existing project docs; do not duplicate them here.

## Goal

[What the app does, for whom, and why.]

## Stack

[Framework, language, database, auth, deploy target, major services.]

## Existing Docs Map

| Purpose | Existing doc |
| --- | --- |
| onboarding / quick start | README.md |
| architecture / structure | ARCHITECTURE.md |
| agent guidance | docs/AI-GUIDE.md |
| active handoff | docs/AI-HANDOFF.md |
| API contracts | docs/API-REFERENCE.md |
| deploy / env / troubleshooting | docs/DEPLOYMENT.md |
| security / release | docs/SECURITY-RELEASE.md |

## Routing Table

| If the task touches... | Read first | Then, only if needed |
| --- | --- | --- |
| onboarding/general setup | README.md | docs/ONBOARDING.md |
| structure/frontend/backend | ARCHITECTURE.md targeted section | specific files |
| API/backend contract | docs/API-REFERENCE.md targeted section | controller/routes with `rg` |
| deploy/env/runtime | docs/DEPLOYMENT.md | env docs, compose/config files |
| security/auth/secrets | security/env docs | auth routes/controllers |
| AI/provider/chat flows | agent/AI docs targeted section | services with `rg` |
| feature work | onboarding/architecture targeted sections | touched files only |
| final PR/deploy handoff | handoff/release docs | targeted tests/build |

## Context Risks

- Do not read generated assets, build outputs, lock files, or bundled JS unless explicitly needed.
- For large docs or source files, use headings, `rg`, or targeted sections.
- Preserve untracked user work.

## Current Decisions

- Language:
- Theme/design:
- Auth:
- Database:
- Deploy:
- Privacy constraints:

## Pending Work

- [ ] ...
"""


AI_HANDOFF = """# AI Handoff

## Current Goal

[Active task or "none".]

## State

- Changed files:
- Decisions:
- Blockers:
- Risks:
- Next step:

## Do Not Repeat

- ...
"""


AI_DECISIONS = """# AI Decisions

Record durable choices only.

## Decisions

- Decision:
  Reason:
  Impact:
  Revisit when:
"""


APP_CONTRACT = """# App Contract

Use this only when frontend, backend, and data behavior need a shared contract.

## User Workflow

- Actor:
- Main job:
- Happy path:
- Empty/loading/error states:

## Frontend Contract

- Routes/screens:
- Components:
- Interactions:

## Backend/Data Contract

- Endpoints/actions:
- Data entities:
- Validation:
- Auth/permissions:

## Verification

- Minimum check:
- Manual acceptance:
"""


FILES = {
    "AGENTS.md": AGENTS,
    "AI_CONTEXT.md": AI_CONTEXT,
    "AI_HANDOFF.md": AI_HANDOFF,
    "AI_DECISIONS.md": AI_DECISIONS,
    "docs/ai/app-contract.md": APP_CONTRACT,
}

MINIMAL_FILES = {
    "AGENTS.md": MINIMAL_AGENTS,
    "AI_CONTEXT.md": AI_CONTEXT_EXISTING,
}


def write_file(path: Path, content: str, overwrite: bool, dry_run: bool) -> str:
    if path.exists() and not overwrite:
        return "exists"
    if dry_run:
        return "would-write"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "written"


def apply_maps(content: str, maps: list[str]) -> str:
    if not maps:
        return content
    rows = []
    for item in maps:
        if "=" not in item:
            rows.append(f"| custom | {item} |")
            continue
        purpose, doc = item.split("=", 1)
        rows.append(f"| {purpose.strip()} | {doc.strip()} |")
    extra = "\n".join(rows)
    return content.replace(
        "## Routing Table",
        f"## Additional Existing Docs\n\n| Purpose | Existing doc |\n| --- | --- |\n{extra}\n\n## Routing Table",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["full", "minimal-existing"],
        default="full",
        help="Use minimal-existing for mature projects that already have docs.",
    )
    parser.add_argument(
        "--preset",
        choices=["full", "mature-existing-docs"],
        help="Friendly preset alias. mature-existing-docs creates only AGENTS.md and AI_CONTEXT.md.",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        help="Add existing doc mapping, e.g. architecture=ARCHITECTURE.md",
    )
    args = parser.parse_args()
    if args.preset == "mature-existing-docs":
        args.mode = "minimal-existing"
    elif args.preset == "full":
        args.mode = "full"

    root = Path(args.path).resolve()
    files = MINIMAL_FILES if args.mode == "minimal-existing" else FILES
    print(f"Project: {root}")
    print(f"Mode: {args.mode}")
    for rel, content in files.items():
        if rel == "AI_CONTEXT.md":
            content = apply_maps(content, args.map)
        status = write_file(root / rel, content, args.overwrite, args.dry_run)
        print(f"{status}: {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
