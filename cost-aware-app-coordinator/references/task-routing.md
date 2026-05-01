# Task Routing

Use this reference when the user request is broad, mixed, or easy to over-read.

## New Project

- Clarify the app goal, target user, primary workflow, and budget mode.
- Plan the first usable workflow before choosing detailed architecture.
- Define the smallest frontend/backend contract that can support the first usable workflow.
- Use the decision and risk gates before choosing stack, auth, database, payments, or deployment.
- Prefer building the usable first screen over a marketing page unless the user asks for a landing page.
- Create or propose `AGENTS.md`, `AI_CONTEXT.md`, and only relevant `docs/ai/*.md` files before deep implementation.
- Keep first implementation focused on the smallest complete workflow.
- Use `app-contract.md` for small full-stack apps before splitting docs by area.

## Existing Project Change

- Read `AI_CONTEXT.md`, `AGENTS.md`, or `README.md` first when present.
- Search for the feature, route, component, command, or error message tied to the request.
- If the change has multiple valid technical routes, give a short recommended route before editing.
- For medium/high-risk user-facing changes, define success in terms the user can judge without reading code.
- Use risk gates before changing shared contracts, auth, data, migrations, or production config.
- Avoid whole-repo scans unless local context is missing or the change crosses architecture boundaries.
- Run the narrowest check that can catch the likely regression; for important UI, consider Playwright screenshots or smoke checks automatically.
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
- Ask whether to prioritize a fast fix or a root-cause pass when the tradeoff matters.
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

## Universal Plan Triggers

Use a short plan before implementation when the request touches:

- data model, migrations, imports, exports, or retroactivity;
- auth, roles, permissions, privacy, or protected data;
- deploy, env vars, CI/CD, hosting, or production services;
- refactors where behavior must remain stable;
- external APIs, paid services, or irreversible actions;
- multi-step features crossing UI, backend, and data.

Use the question bank in `decision-risk-gates.md` when one missing answer would change the route.

## User-Facing Acceptance

Use a final acceptance prompt when the task changes what the user sees or a workflow they manually use:

- screens, forms, dashboards, reports, charts, navigation, copy, or layout;
- important business behavior where the user knows the intended result better than the code;
- screenshot/mockup fidelity or feature behavior requested in natural language.

For these cases, consider Playwright when it can confirm visual layout or workflow behavior before asking the user for final acceptance.

Skip it for purely internal docs, mechanical refactors, small type/lint fixes, or changes already fully covered by automated checks.

If the user reports a mismatch, treat it as useful product feedback first. Log it in `AI_AGENT_LOG.md` only if it was caused by a missed instruction, wrong assumption, weak verification, or repeated process problem.

For user-facing work, include 1-3 plain `Come provarlo` steps in the final answer unless automated checks fully cover the outcome or there is nothing useful for the user to click/see.
