# Cross-Agent Handoff Template

Use this to create `AI_HANDOFF.md` when the same project may be edited by Codex, Claude Code, or another coding agent.

This file is a baton pass, not a diary. Keep only what helps the next agent continue safely.

```markdown
# AI Handoff

Last updated: YYYY-MM-DD HH:mm
From: Codex | Claude Code | Other
To: Codex | Claude Code | Any

## Current Goal

[One sentence.]

## State

- Done:
- In progress:
- Not started:

## Changed Files

- `path`: [reason]

## Decisions

- [Decision that affects the next step]

## Open Risks

- [Risk, blocker, or assumption]

## Next Step

[Single best next action.]

## Do Not Repeat

- [Only if it prevents rework or waste]
```

Rules:

- Read after `AI_CONTEXT.md` when taking over active work.
- Update after non-trivial changes or before switching agents.
- Do not paste diffs, logs, or routine command output.
- Move durable decisions to `AI_DECISIONS.md`.
- Move stable structure to `AI_STRUCTURE.md`.
- Move repeated mistakes or token waste to `AI_AGENT_LOG.md`.
