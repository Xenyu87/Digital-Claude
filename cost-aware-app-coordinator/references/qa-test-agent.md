# QA/Test Agent

Use this reference when a dedicated QA/Test pass would reduce regression risk.

## Activate When

- frontend and backend both changed;
- API, server action, auth, validation, data shape, or migration changed;
- a non-trivial bug was fixed;
- a first usable slice is being completed;
- push, PR, release, or deploy validation is needed.
- UI changes need real-browser confidence: new page, redesign, screenshot fidelity, responsive layout, form, chart, dashboard, or navigation.

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
- Playwright screenshot or smoke check covers important UI changes when cost/setup is justified.

## Playwright Guidance

- Use existing project Playwright config when present.
- Prefer targeted screenshots and one or two meaningful interactions over broad browser matrices.
- Check desktop and mobile when responsive behavior matters.
- Use a cost checkpoint before installing browsers, creating test data, logging into external services, or running broad visual suites.

## Browser Check

For important UI changes, verify the smallest useful set:

- screenshot: one desktop viewport and one mobile viewport when responsive matters;
- console: no new obvious runtime errors on load or primary interaction;
- workflow: load target route, perform the main action or navigation, confirm visible result;
- state: check empty/loading/error/success only when touched by the change;
- artifact: save or mention screenshot/trace path only when useful for review.

Stop after the targeted confidence goal is met. Do not expand into full E2E unless the risk justifies it.

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
