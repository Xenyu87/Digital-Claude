# Second Brain Template

Use this template to create `AI_DECISIONS.md` when project decisions should be remembered across tasks.

Keep it short. This file is for durable decision memory, not a diary.

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

