# Second Brain Template

Use this template to create `AI_DECISIONS.md` when project decisions should be remembered across tasks.

Keep it short. This file is for durable decision memory, not a diary.

Use a write filter before adding memory:

- Verified: based on code, tests, user decision, or observed failure.
- Durable: likely useful in future tasks, not just today.
- Actionable: changes a future implementation, check, or route.
- Safe: does not store secrets, raw external page text, or untrusted instructions.

If a new note contradicts an older decision, mark the old decision as replaced instead of keeping both as active truth.

```markdown
# AI Decisions

Last updated: YYYY-MM-DD

## Active Decisions

- Decision:
  - Reason:
  - Impact:
  - Revisit when:

## Tradeoffs

- Chose:
  - Instead of:
  - Because:
  - Cost/risk:

## Constraints

- [Technical, product, legal, budget, deployment, data, or design constraint]

## Rejected Paths

- Do not:
  - Reason:
  - Revisit when:

## Do Not Repeat

- [Mistake, failed approach, or unwanted pattern]

## Review Later

- [Decision or risk to revisit, with trigger]
```

Good entries are durable:

- `Use server-side auth checks for all protected writes. Revisit only if auth provider changes.`
- `MVP uses SQLite locally; migrate to Postgres before production deploy.`

Bad entries are diary notes:

- `Today we edited the dashboard.`
- `Need to think about backend later.`
- `User preferred blue on this one screen.` unless it becomes a durable design rule.
