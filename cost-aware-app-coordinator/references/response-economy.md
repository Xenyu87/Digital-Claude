# Response Economy

Use this reference when answers, updates, or agent prompts are getting longer than the task needs.

## Defaults

- Say the budget mode and model policy once, then do not repeat them unless they change.
- Keep progress updates to one short sentence, and skip them when nothing user-relevant changed.
- Use compact plans only when they reduce risk or coordinate work.
- Summarize command output; do not paste it unless requested.
- Prefer one precise file link over a list of every related file.
- Do not explain routine edits as "I changed X because Y"; reserve reasons for risk, tradeoffs, blockers, or user decisions.
- Be most precise in `Da fare per te` items: commands to run, env vars to set, accounts to connect, manual checks, or choices needed.

## Final Answer Shapes

Small task:

```text
Fatto: [outcome]. Verifica: [check].
```

Medium task:

```text
Fatto:
- ...

Verifica:
- ...

Da fare per te:
- ... [only if needed]
```

Review or audit:

```text
Findings:
- [severity] [file:line] [issue and impact]

Checked:
- ...

Residual risk:
- ...
```

## Compression Rules

- Remove background the user already knows.
- Replace process narration with the final decision.
- Delete routine reasons after completed work.
- Merge repeated caveats into one residual risk.
- Keep examples out unless the user asks or the format is hard to infer.
- Use exact limits when needed: sentence count, bullet count, files, or checks.

## When To Expand

Expand only for:

- high-risk decisions;
- unclear user goals;
- security, auth, payments, privacy, data loss, or production incidents;
- teaching requests;
- user action is required;
- user explicitly asking for detail.
