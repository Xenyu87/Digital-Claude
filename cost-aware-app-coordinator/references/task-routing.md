# Task Routing

Use this reference when the user request is broad, mixed, or easy to over-read.

## New Project

- Clarify the app goal, target user, primary workflow, and budget mode.
- Define the smallest frontend/backend contract that can support the first usable workflow.
- Use the decision and risk gates before choosing stack, auth, database, payments, or deployment.
- Prefer building the usable first screen over a marketing page unless the user asks for a landing page.
- Create or propose `AGENTS.md`, `AI_CONTEXT.md`, and only relevant `docs/ai/*.md` files before deep implementation.
- Keep first implementation focused on the smallest complete workflow.
- Use `app-contract.md` for small full-stack apps before splitting docs by area.

## Existing Project Change

- Read `AI_CONTEXT.md`, `AGENTS.md`, or `README.md` first when present.
- Search for the feature, route, component, command, or error message tied to the request.
- Use risk gates before changing shared contracts, auth, data, migrations, or production config.
- Avoid whole-repo scans unless local context is missing or the change crosses architecture boundaries.
- Run the narrowest check that can catch the likely regression.
- Use sub-agents only for separable slices with clear ownership and model labels.
- When a change crosses UI and backend, identify the shared contract first: route, endpoint, data shape, auth rule, and error behavior.

## Audit

- Ask or infer the audit lens: UX, architecture, security, performance, tests, deploy, cost, or maintainability.
- Sample enough files to support findings, but avoid summarizing the whole codebase.
- Lead with issues by severity and include file references when possible.
- Separate confirmed findings from assumptions.
- Keep the report short unless the user asks for a full audit.

## Bug Rescue

- Capture the symptom, expected behavior, and likely entry point.
- Prefer reproducing the failure or locating the failing path before editing.
- Patch the smallest cause that explains the symptom.
- Verify the original failure path, then add broader checks only if shared behavior changed.
- Stop and report if the failure points to credentials, external services, production data, or destructive recovery steps.

## Skill Improvement

- Treat the user's explicit "improve this skill" request as approval for scoped edits.
- Look for repeated waste, unclear routing, missing safety checks, weak output rules, or stale references.
- Make one to three durable improvements per pass.
- Prefer behavior rules and compact templates over long explanations.
- Update release notes and the improvement log when behavior changes.
- Prefer shorter rules that change behavior over long explanatory prose.
