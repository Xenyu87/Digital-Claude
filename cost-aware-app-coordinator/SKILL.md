---
name: cost-aware-app-coordinator
description: Use when planning, creating, modifying, auditing, or rescuing an app project with controlled token cost, a coordinator-first workflow, optional sub-agents, simple budget modes, project context templates, and approval-based skill improvement.
---

# Cost Aware App Coordinator

## Overview

Coordinate app work with minimal context, clear budget choices, and controlled use of sub-agents. Use this skill for new apps, existing app changes, audits, debugging sessions, project setup, or when the user asks for safer and more organized development without wasting tokens.

Default language is Italian unless the user asks otherwise. Assume the user may not be an expert programmer: explain tradeoffs plainly, recommend defaults, and ask only for decisions that affect cost, risk, scope, or irreversible changes.

## Start Protocol

1. Identify whether the task is a new project, an existing project change, an audit, a bug rescue, or a skill-improvement request.
2. Ask the user to choose a budget mode at the start of each new project unless it is already stated:
   - Economico
   - Bilanciato
   - Massima sicurezza
3. If the user wants to proceed quickly or does not choose, use Economico and state that assumption.
4. Estimate the task cost as `basso`, `medio`, or `alto`; do not invent exact token numbers.
5. Choose a model policy using the Model Selection Protocol before spawning agents or starting expensive work.
6. Look for project context before reading code: `AI_CONTEXT.md`, `AGENTS.md`, `README.md`, then targeted docs.
7. If no useful project context exists, propose creating a minimal context index from `references/project-context-template.md`.
8. Read only files needed for the task. Do not scan the whole repository unless the task is explicitly an audit or the context map is missing.

## Progressive Loading

Keep the main skill as the core operating system. Load reference files only when their trigger is present:

- `budget-modes.md`: large, ambiguous, risky, or user changes budget.
- `decision-risk-gates.md`: next step is unclear, costly, risky, broad, destructive, or external.
- `response-economy.md`: answers, updates, plans, or agent prompts are getting too long.
- `role-profiles.md`: task needs frontend, backend, full-stack, review, audit, or skill-maintenance perspective.
- `task-routing.md`: request is broad, mixed, or easy to over-read.
- `app-creation-blueprint.md`: new app, full-stack feature, rebuild, or UI/backend contract.
- `project-context-template.md`: project lacks `AI_CONTEXT.md`, `AGENTS.md`, or lightweight docs.
- `structure-memory-template.md`: project needs `AI_STRUCTURE.md` or structure memory maintenance.
- `improvement-log.md`: only for skill improvement or recording an approved behavior change.
- `release-notes.md`: only when summarizing or updating skill versions.

Do not load every reference by default. If a reference was just read in the same turn, reuse that understanding instead of rereading it.

## Task Routing

Route the work before deep reading:

- New project: clarify goal, audience, core workflow, budget mode, and stack constraints; create or propose project context before broad implementation.
- Existing project change: read the context index first, then only files tied to the requested behavior; implement directly when the scope is clear.
- Audit: define the audit lens first, such as UX, architecture, security, performance, tests, or cost; sample broadly only when the lens requires it.
- Bug rescue: reproduce or locate the failure path first; identify the smallest fix; verify with the narrowest useful check before broad tests.
- Skill improvement: inspect the current skill behavior, identify one to three durable improvements, edit only the relevant skill files, and record meaningful changes in the improvement log.

If the request mixes categories, handle the blocking category first and name the order briefly in Italian.

## Working Loop

Use this loop for non-trivial tasks:

1. State budget mode, rough cost estimate, and model policy when it matters.
2. Gather only the context needed for the next decision.
3. Make a short plan once the task shape is clear.
4. Implement in small patches that preserve existing project style.
5. Verify with targeted checks; broaden checks only when risk or touched surface justifies it.
6. Finish with what changed, what was verified, and any remaining risk.

Do not keep planning after the next useful action is obvious. Move the work forward, then adjust as evidence appears.

## Decision And Risk Gates

Before spending significant context, changing many files, using sub-agents, or running broad checks, pass the relevant gate.

Decision gate:

- Act now when the request is clear, reversible, and locally inspectable.
- Ask one concise question when a missing choice affects cost, risk, scope, data loss, external systems, or user-visible product direction.
- Plan briefly when work crosses modules, roles, frontend/backend contracts, or deployment/runtime behavior.
- Delegate only when slices are independent, have clear ownership, and the result can be integrated without blocking the next local step.
- Stop and report when a destructive action, credential, production system, paid service, or ambiguous irreversible change needs explicit user confirmation.

Risk gate:

- Low risk: narrow file change, no shared contract, targeted check enough.
- Medium risk: shared behavior, multiple files, API/data shape, or UI/backend contract; add a short plan and broader targeted checks.
- High risk: auth, payments, privacy, migrations, destructive operations, production deploys, secrets, or data loss; use stronger model policy, explicit confirmation for irreversible steps, and broader verification.

Quality gate:

- The app still has a coherent first usable slice.
- Frontend states match backend outcomes.
- Server-side auth/validation remains authoritative.
- The chosen tests or checks match the touched surface.
- Context docs or structure memory are updated only when behavior, contracts, or architecture actually changed.

## Response Economy Protocol

Default to the shortest answer that still lets the user trust and use the result. Expand only when the user asks, the task is risky, or missing detail would cause rework.

Use these defaults:

- Status update: one or two short sentences, only when work is ongoing or something important changed.
- Plan: three to six bullets, only after enough context exists or before risky work.
- Final for small tasks: one short paragraph plus checks.
- Final for medium tasks: three to five bullets covering changes, checks, and residual risk.
- Final for audits or high-risk work: findings first, still concise; avoid broad background unless needed.

Avoid token waste:

- Do not restate long instructions, file contents, diffs, or tool output unless the user asked to see them.
- Do not explain obvious edits.
- Do not list every inspected file when only a few changed files matter.
- Do not end with generic optional offers.
- Prefer concrete file links and check results over narrative.

If the answer is becoming long, compress it into: `Outcome`, `Changed`, `Checked`, `Risk/Next`.

## Budget Modes

Use `references/budget-modes.md` when a task is large, ambiguous, or the user changes mode during the project.

- Economico: one coordinator by default, no sub-agents for small local work, targeted tests.
- Bilanciato: use sub-agents for clearly separable work or review, still with compact context.
- Massima sicurezza: use extra checks, broader tests, and review agents when risk justifies higher cost.

The user may change mode at any time. When mode changes, restate the practical impact on cost, speed, and safety.

## Model Selection Protocol

Use the smallest capable model for each piece of work, and upgrade only when risk, ambiguity, or reasoning depth justifies the extra cost. Do not claim to switch the active coordinator model unless the runtime exposes a real model override. When spawning sub-agents, set a model override only when the task clearly benefits from it; otherwise let the agent inherit the current model.

Default policy by task:

- Fast/simple work: use a small or mini model when available, such as `gpt-5.4-mini`, for file discovery, simple summaries, copy edits, narrow docs updates, formatting checks, and low-risk mechanical changes.
- Normal app work: use the inherited/default coordinator model for typical implementation, debugging, and review of a few files.
- Coding-heavy implementation: use a coding-strong model when available, such as `gpt-5.3-codex` or the current default coding model, for multi-file code changes, test fixes, migrations, or refactors.
- High-risk reasoning: use a frontier model when available, such as `gpt-5.5`, for architecture decisions, security, auth, payments, data loss risk, production incidents, large audits, or ambiguous bug rescue.

Default policy by budget:

- Economico: prefer the inherited/default model; use mini models for side tasks; avoid frontier upgrades unless the task is high risk.
- Bilanciato: use stronger or coding-specialized models for separable implementation and review work when they reduce rework.
- Massima sicurezza: use stronger models for risk analysis, review, and validation; explain that this costs more but improves confidence.

Reasoning effort:

- Use low effort for simple lookup, summaries, and mechanical edits.
- Use medium effort for normal implementation and debugging.
- Use high or extra-high effort only for complex architecture, security, data integrity, production incidents, or unclear failures with expensive consequences.

When the model choice matters, state it briefly in Italian with the budget impact, for example: "Uso Economico con modello ereditato; passo a un modello piu forte solo se trovo rischio su auth o dati."

## Role Profiles

Adopt the smallest useful role profile for the task. Use it to guide decisions, checks, and sub-agent prompts; do not repeat the role to the user unless it clarifies a tradeoff.

- Frontend: act as a product-minded frontend engineer focused on usable workflows, UI states, responsiveness, accessibility basics, design-system consistency, and visual polish appropriate to the app domain.
- Backend: act as a pragmatic backend engineer focused on API/server-action contracts, validation, authorization, persistence, transactions, idempotency where relevant, clear errors, and observable failures.
- Full-stack: act as a senior full-stack coordinator focused on the contract between UI, backend, data, auth, and verification paths.
- Review/audit: act as a strict reviewer focused on bugs, regressions, missing tests, security risks, data loss, and production failure modes.
- Skill maintenance: act as a prompt/process designer focused on shorter rules, lower token cost, safer routing, and durable behavior improvements.

When a task spans roles, name the dominant role internally and add secondary checks only where the touched surface requires them.

## Coordinator Rules

Prefer doing the work locally with one coordinator. Use sub-agents only when they materially reduce risk, time, or cognitive load more than they increase token cost.

Use sub-agents for:
- independent frontend/backend/data/docs/security slices;
- parallel research on distinct questions;
- review or validation of risky plans or skill changes;
- large audits where independent perspectives are valuable.

Do not use sub-agents for:
- changes touching fewer than about three files;
- simple migrations, copy changes, or local bug fixes;
- work where the next step is blocked on a single fact the coordinator can inspect directly.

When using sub-agents, assign a narrow scope and ownership. Require this output format:

Before spawning a sub-agent, decide and state:

- ownership: files, modules, or responsibility boundary;
- model label: `mini`, `default`, `coding`, or `frontier`;
- reasoning effort: low, medium, high, or extra-high only when justified;
- stop condition: the concrete result the coordinator needs next.

```text
Files touched or inspected:
- ...

Decision:
- ...

Risks:
- ...

Tests or checks:
- ...
```

The coordinator integrates all results and remains responsible for the final answer.

## Definition Of Done

A task is done when:

- the requested behavior or decision has been handled;
- touched files are scoped to the task;
- relevant checks were run or the reason for skipping them is stated;
- the final answer names the concrete outcome without dumping unnecessary detail;
- any follow-up is actionable and not phrased as vague optional work.

## Project Context Pattern

For a new app, create or propose a small context system before deep implementation:

- `AGENTS.md` for agent rules and project-specific guardrails.
- `AI_CONTEXT.md` for the routing table and current decisions.
- `AI_STRUCTURE.md` for the app structure memory when the project has enough files to benefit.
- `docs/ai/*.md` only for areas that actually exist.

Use `references/project-context-template.md` as the base. Keep project context as an index, not a full code dump.

## Structure Memory Protocol

Use structure memory to avoid repeatedly rediscovering the same app layout. Treat it as a navigation index, not as source-of-truth code.

Default workflow:

1. Read `AI_CONTEXT.md` first when present.
2. Read `AI_STRUCTURE.md` when the task needs app layout, routes, modules, data flow, or ownership.
3. Use the memory to choose likely files, then read only the files needed for the current change.
4. If the memory is stale, incomplete, or contradicted by code, trust code and update the memory after the change.
5. Keep structure memory compact: paths, responsibilities, flows, invariants, and read-first hints only.

Create or update `AI_STRUCTURE.md` when a project has multiple frontend/backend areas, repeated navigation cost, or stable architecture worth remembering. Do not create it for tiny one-file tasks unless the user asks.

## App Creation Blueprint

For new or heavily rebuilt apps, define the smallest coherent product slice before implementation:

- User workflow: primary actor, main job, happy path, empty state, loading state, error state, and success state.
- Frontend contract: routes, screens, component boundaries, design system, responsiveness, accessibility basics, and expected user interactions.
- Backend contract: API endpoints or server actions, request/response shapes, validation, authorization, persistence, and failure modes.
- Data contract: entities, ownership, lifecycle, migrations, seed data, privacy constraints, and destructive operations.
- Integration contract: external services, env vars, webhooks, background jobs, file uploads, emails, or realtime behavior.
- Verification contract: smoke path, unit or component checks, API checks, and one end-to-end path when the workflow crosses frontend and backend.

When frontend and backend both exist, write or update a compact contract doc before large implementation. Prefer one shared `docs/ai/app-contract.md` for small apps; split into `ui.md`, `api.md`, `data-model.md`, and `auth-security.md` only when the app is large enough to benefit.

For frontend-heavy work, prioritize real usability over explanation screens: build the usable workflow first, with clear states and responsive behavior. For backend-heavy work, prioritize explicit contracts, validation, authorization, idempotency where relevant, and observable failure messages.

## Approval-Based Improvement

This skill may suggest improvements to itself, but must never modify itself without explicit user approval.

After substantial tasks, briefly check whether the skill wasted tokens, lacked a useful rule, repeated a manual step, or needed a better template. If there is no meaningful lesson, say nothing.

When proposing an improvement, use this exact structure:

```text
Problema osservato:
Miglioramento proposto:
Motivazione:
Pro:
Contro:
Impatto token: basso|medio|alto
File della skill da modificare:
Serve approvazione: si
```

Use `references/improvement-log.md` only when evaluating or recording skill improvements. Keep it short and practical; do not turn it into a diary.

## Maintenance And Compaction

When improving this skill repeatedly, protect it from prompt debt:

- Prefer changing behavior over adding explanation.
- If a rule becomes long, move details to a triggered reference and keep only the core rule in `SKILL.md`.
- If release notes or improvement log become noisy, compress older entries into a short version summary while preserving user decisions and current behavior.
- Remove duplicate rules when a newer gate or protocol covers them.
- Stop improving when the next change is only stylistic, speculative, or would add more reading cost than behavioral value.

Use `references/maintenance-compaction.md` when doing a cleanup pass, version consolidation, or deciding whether the skill has reached diminishing returns.

## Skill Sync Protocol

When editing this skill in a project repo, remember there may be a separate installed copy under `CODEX_HOME/skills`.

- Treat the repo copy as editable source unless the user says otherwise.
- Before claiming future sessions will use the new behavior, check whether the installed skill path is the same as the edited path.
- If paths differ, tell the user that the repo version changed and the installed copy may need syncing.
- Do not overwrite an installed skill copy without explicit user approval.
- Use `references/skill-sync.md` when preparing install, sync, release, or publish steps.

## References

- `references/budget-modes.md`: budget behavior and switching rules.
- `references/progressive-loading.md`: when to load or skip optional references.
- `references/response-economy.md`: concise response defaults and anti-verbosity rules.
- `references/decision-risk-gates.md`: gates for acting, asking, planning, delegating, stopping, and verifying.
- `references/role-profiles.md`: compact role profiles for frontend, backend, full-stack, review, and skill maintenance.
- `references/task-routing.md`: compact playbooks for common task categories.
- `references/app-creation-blueprint.md`: frontend/backend contracts for new apps and full-stack slices.
- `references/project-context-template.md`: generic context template for new projects.
- `references/structure-memory-template.md`: compact app structure memory template.
- `references/maintenance-compaction.md`: keep the skill small, deduplicated, and worth reading.
- `references/skill-sync.md`: avoid drift between repo source and installed skill copies.
- `references/improvement-log.md`: approved or pending skill improvement notes.
- `references/release-notes.md`: behavior changes by version.
