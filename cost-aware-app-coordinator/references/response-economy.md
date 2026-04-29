# Response Economy

Use this reference when answers, updates, or agent prompts are getting longer than the task needs.

## Defaults

- Say the budget mode and model policy once, then do not repeat them unless they change.
- Keep progress updates to one or two short sentences.
- Use compact plans only when they reduce risk or coordinate work.
- Summarize command output; do not paste it unless requested.
- Prefer one precise file link over a list of every related file.

## Final Answer Shapes

Small task:

```text
Fatto: [outcome]. Verifica: [check or reason skipped].
```

Medium task:

```text
Outcome: ...
Changed: ...
Checked: ...
Risk/Next: ...
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
- Merge repeated caveats into one residual risk.
- Keep examples out unless the user asks or the format is hard to infer.
- Use exact limits when needed: sentence count, bullet count, files, or checks.

## When To Expand

Expand only for:

- high-risk decisions;
- unclear user goals;
- security, auth, payments, privacy, data loss, or production incidents;
- teaching requests;
- user explicitly asking for detail.

