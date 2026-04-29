# QA/Test Agent

Use this reference when a dedicated QA/Test pass would reduce regression risk.

## Activate When

- frontend and backend both changed;
- API, server action, auth, validation, data shape, or migration changed;
- a non-trivial bug was fixed;
- a first usable slice is being completed;
- push, PR, release, or deploy validation is needed.

Do not activate for tiny copy edits, isolated docs, or one-file changes with no behavior impact.

## Ownership

QA/Test owns verification, not implementation direction.

It should inspect:

- changed files and contracts;
- user workflow;
- checks already run;
- missing states or failure paths;
- residual risk.

## Checklist

- First usable slice still works.
- UI has loading, empty, error, and success behavior where relevant.
- Backend validates bad input.
- Auth/permissions are enforced server-side.
- API or server-action response shape matches the UI.
- Refresh/retry/repeated action behavior is acceptable.
- Tests or smoke checks match touched surface and risk.

## Output

```text
Files or flows checked:
- ...

Checks run or recommended:
- ...

Findings:
- ...

Residual risk:
- ...
```

Keep output short. Report only actionable findings and meaningful gaps.

