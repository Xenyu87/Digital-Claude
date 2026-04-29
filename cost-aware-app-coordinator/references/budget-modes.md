# Budget Modes

Use this reference when the task is a new project, the user changes mode, or cost/risk tradeoffs matter.

## Economico

Default mode.

- Use one coordinator by default.
- Read only the project index and task-relevant files.
- Avoid sub-agents unless the task is too broad or risky for one pass.
- Prefer targeted checks over full test suites when the change is narrow.
- Summaries should be short and practical.

Good for:
- small fixes;
- first project setup;
- early exploration;
- users watching token cost closely.

## Bilanciato

- Use the coordinator plus sub-agents for separable work.
- Run broader checks when behavior crosses modules.
- Add a review pass for important architecture, data, auth, payment, or deployment changes.
- Keep each agent prompt narrow and each agent output compressed.

Good for:
- feature work touching multiple areas;
- project bootstrap with frontend and backend decisions;
- medium-risk refactors.

## Massima sicurezza

- Use extra review and validation when the cost is justified.
- Prefer separate security, data, and QA passes for high-risk changes.
- Run wider tests and inspect failure modes.
- Explain that this mode costs more tokens and time.

Good for:
- auth, billing, payments, privacy, migrations, production deploys;
- destructive or irreversible operations;
- large refactors.

## Switching Modes

The user can change mode at any time. When this happens:

1. Confirm the new mode in plain Italian.
2. State the practical impact: cost, speed, safety.
3. Continue from the current state; do not restart the task unless needed.

## Cost Estimate

Use only:

- `basso`: likely one pass, few files, no sub-agents.
- `medio`: several files or one limited sub-agent/review.
- `alto`: broad context, multiple agents, wide tests, or uncertain scope.

Never invent exact token counts.
