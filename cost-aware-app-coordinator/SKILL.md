---
name: cost-aware-app-coordinator
description: Use when planning, creating, modifying, auditing, or rescuing an app project with controlled token cost, a coordinator-first workflow, optional sub-agents, simple budget modes, project context templates, and approval-based skill improvement.
---

# Cost Aware App Coordinator

## Overview

Coordinate app work with minimal context, clear budget choices, and controlled use of sub-agents. Use this skill for new apps, existing app changes, audits, debugging sessions, project setup, or when the user asks for safer and more organized development without wasting tokens.

Default language is Italian unless the user asks otherwise. Assume the user may not be an expert programmer: explain tradeoffs plainly, recommend defaults, and ask only for decisions that affect cost, risk, scope, or irreversible changes.

## Start Protocol

1. Identify whether the task is a new project, an existing project change, an audit, a bug rescue, or a skill-improvement request.
2. Ask the user to choose a budget mode at the start of each new project unless it is already stated:
   - Economico
   - Bilanciato
   - Massima sicurezza
3. If the user wants to proceed quickly or does not choose, use Economico and state that assumption.
4. Estimate the task cost as `basso`, `medio`, or `alto`; do not invent exact token numbers.
5. Look for project context before reading code: `AI_CONTEXT.md`, `AGENTS.md`, `README.md`, then targeted docs.
6. If no useful project context exists, propose creating a minimal context index from `references/project-context-template.md`.
7. Read only files needed for the task. Do not scan the whole repository unless the task is explicitly an audit or the context map is missing.

## Budget Modes

Use `references/budget-modes.md` when a task is large, ambiguous, or the user changes mode during the project.

- Economico: one coordinator by default, no sub-agents for small local work, targeted tests.
- Bilanciato: use sub-agents for clearly separable work or review, still with compact context.
- Massima sicurezza: use extra checks, broader tests, and review agents when risk justifies higher cost.

The user may change mode at any time. When mode changes, restate the practical impact on cost, speed, and safety.

## Coordinator Rules

Prefer doing the work locally with one coordinator. Use sub-agents only when they materially reduce risk, time, or cognitive load more than they increase token cost.

Use sub-agents for:
- independent frontend/backend/data/docs/security slices;
- parallel research on distinct questions;
- review or validation of risky plans or skill changes;
- large audits where independent perspectives are valuable.

Do not use sub-agents for:
- changes touching fewer than about three files;
- simple migrations, copy changes, or local bug fixes;
- work where the next step is blocked on a single fact the coordinator can inspect directly.

When using sub-agents, assign a narrow scope and ownership. Require this output format:

```text
Files touched or inspected:
- ...

Decision:
- ...

Risks:
- ...

Tests or checks:
- ...
```

The coordinator integrates all results and remains responsible for the final answer.

## Project Context Pattern

For a new app, create or propose a small context system before deep implementation:

- `AGENTS.md` for agent rules and project-specific guardrails.
- `AI_CONTEXT.md` for the routing table and current decisions.
- `docs/ai/*.md` only for areas that actually exist.

Use `references/project-context-template.md` as the base. Keep project context as an index, not a full code dump.

## Approval-Based Improvement

This skill may suggest improvements to itself, but must never modify itself without explicit user approval.

After substantial tasks, briefly check whether the skill wasted tokens, lacked a useful rule, repeated a manual step, or needed a better template. If there is no meaningful lesson, say nothing.

When proposing an improvement, use this exact structure:

```text
Problema osservato:
Miglioramento proposto:
Motivazione:
Pro:
Contro:
Impatto token: basso|medio|alto
File della skill da modificare:
Serve approvazione: si
```

Use `references/improvement-log.md` only when evaluating or recording skill improvements. Keep it short and practical; do not turn it into a diary.

## References

- `references/budget-modes.md`: budget behavior and switching rules.
- `references/project-context-template.md`: generic context template for new projects.
- `references/improvement-log.md`: approved or pending skill improvement notes.
- `references/release-notes.md`: behavior changes by version.
