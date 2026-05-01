# Budget Modes

Use this reference when the task is a new project, the user changes mode, or cost/risk tradeoffs matter.

## Economico

Default mode.

- Use one coordinator by default.
- Prefer the inherited/default model; use a mini model for simple side tasks when available.
- Upgrade to a stronger model only for high-risk ambiguity, data loss risk, security, auth, payments, or production incidents.
- Read only the project index and task-relevant files.
- Avoid sub-agents unless the task is too broad or risky for one pass.
- Prefer targeted checks over full test suites when the change is narrow.
- Use the shortest useful status updates and final summaries.

Good for:
- small fixes;
- first project setup;
- early exploration;
- users watching token cost closely.

## Bilanciato

- Use the coordinator plus sub-agents for separable work.
- Use stronger or coding-specialized models for implementation or review slices when they reduce rework.
- Use mini models for isolated discovery, docs summaries, or low-risk verification.
- Run broader checks when behavior crosses modules.
- Add a review pass for important architecture, data, auth, payment, or deployment changes.
- Keep each agent prompt narrow and each agent output compressed.
- Summaries may include short rationale, but avoid background unless it changes a decision.

Good for:
- feature work touching multiple areas;
- project bootstrap with frontend and backend decisions;
- medium-risk refactors.

## Massima sicurezza

- Use extra review and validation when the cost is justified.
- Prefer stronger models and higher reasoning effort for risk analysis, architecture, security, data, and QA passes.
- Use mini models only for clearly mechanical side tasks.
- Prefer separate security, data, and QA passes for high-risk changes.
- Run wider tests and inspect failure modes.
- Explain that this mode costs more tokens and time.
- Spend detail on risks, evidence, and verification; keep progress chatter short.

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

## Cost Checkpoints

Use a cost checkpoint before a step that may noticeably increase token use, runtime, or external risk:

- broad repository exploration instead of targeted files;
- sub-agents or specialist review;
- wide test suites instead of targeted checks;
- schema, migration, import/export, or retroactive data changes;
- deploy, production, paid services, or external account changes.

Format:

```text
Checkpoint costo:
Sto per fare: ...
Costo stimato: basso|medio|alto
Perche serve: ...
Alternativa economica: ...
Serve approvazione: si|no
```

If the user has already explicitly chosen the higher-cost route, keep the checkpoint internal unless risk or approval changes.

## Model Choice Labels

When useful, describe model choice with simple labels instead of over-explaining internals:

- `mini`: summaries, discovery, mechanical edits, simple docs.
- `default`: normal app work and most focused bug fixes.
- `coding`: multi-file implementation, refactors, migrations, test fixes.
- `frontier`: architecture, security, auth, payments, data loss risk, production incidents, large audits.

If exact model names are available in the runtime, map these labels to the smallest capable option. If exact model names are not available, keep the labels and do not pretend a specific model was used.
