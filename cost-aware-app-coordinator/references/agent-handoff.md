# Agent Handoff

Use this reference when two or more sub-agents need to coordinate.

## Principle

Sub-agents communicate through compact handoffs. The coordinator routes, deduplicates, resolves conflicts, and owns the final decision.

Avoid free-form discussion loops. Use structured messages only when another agent needs the information.

## Handoff Message

```text
From:
To:
Topic:
Decision or blocker:
Files/contracts affected:
Assumptions:
Needed by:
Risk:
```

## Filtered Context

Before delegating or handing off, include only:

- objective and stop condition;
- owned files, modules, routes, contracts, or commands;
- relevant constraints and user-approved decisions;
- known blockers, risks, and validation expected;
- exact output format needed by the coordinator.

Do not pass full chat history, broad diffs, unrelated logs, large command output, or speculative background. Summarize long evidence and include file paths or commands the next agent can inspect if needed.

## When To Send

Send a handoff when:

- frontend and backend contract changes;
- data shape or auth rule affects another slice;
- a blocker prevents progress;
- one agent changed files another agent depends on;
- tests reveal an integration risk;
- a decision must be confirmed before another slice continues.

## When Not To Send

Do not send a handoff for:

- local implementation details that do not affect another slice;
- repeated status updates;
- speculative ideas;
- broad commentary already visible in the shared plan.

## Conflict Handling

If agents disagree:

1. Coordinator compares evidence and touched contracts.
2. Coordinator chooses the lower-risk option when reversible.
3. Coordinator asks the user when the choice changes product direction, data model, auth, cost, or irreversible behavior.
4. Coordinator records durable decisions in `AI_DECISIONS.md` when relevant.

## Final Integration

Coordinator summarizes:

- accepted decisions;
- unresolved blockers;
- files/contracts changed;
- verification needed across slices.
