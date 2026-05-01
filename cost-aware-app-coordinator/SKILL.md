---
name: cost-aware-app-coordinator
description: Use when planning, creating, modifying, auditing, or rescuing an app project with controlled token cost, coordinator-first workflow, optional sub-agents, budget modes, project context and decision memory, and approval-based skill improvement.
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
- `compression-pass.md`: prompt, final answer, handoff, commit/PR text, or context doc needs aggressive safe compression.
- `role-profiles.md`: task needs frontend, backend, full-stack, QA/test, security/auth, UX/product, data/migration, DevOps/release, performance, review, audit, or skill-maintenance perspective.
- `coordinator-safety.md`: coordinator confidence is medium/low, task is high risk, or a red-team pass may catch costly mistakes.
- `qa-test-agent.md`: workflow crosses frontend/backend, changes contracts/auth/data, fixes non-trivial bugs, prepares push/PR validation, or needs Playwright UI checks.
- `specialist-agents.md`: specialist agent selection for security/auth, UX/product, data/migration, DevOps/release, or performance.
- `agent-handoff.md`: multiple sub-agents need to share decisions, contracts, blockers, or integration notes.
- `task-routing.md`: request is broad, mixed, or easy to over-read.
- `app-creation-blueprint.md`: new app, full-stack feature, rebuild, or UI/backend contract.
- `project-context-template.md`: project lacks `AI_CONTEXT.md`, `AGENTS.md`, or lightweight docs.
- `structure-memory-template.md`: project needs `AI_STRUCTURE.md` or structure memory maintenance.
- `second-brain-template.md`: project needs durable decision memory or repeated tradeoff context.
- `agent-autolog-template.md`: repeated waste, wrong routing, missed risk, unnecessary rereads, or user-corrected behavior.
- `cross-agent-handoff-template.md`: switching between Codex, Claude Code, or another coding agent on the same project.
- `improvement-log.md`: only for skill improvement or recording an approved behavior change.
- `release-notes.md`: only when summarizing or updating skill versions.

Do not load every reference by default. If a reference was just read in the same turn, reuse that understanding instead of rereading it.

Use `python scripts/validate_skill.py` after changing the skill structure, references, release notes, or progressive loading rules.

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

1. Choose budget mode, rough cost estimate, and model policy internally. State them only when the user asks or a real cost/risk choice changes.
2. Gather only the context needed for the next decision.
3. Make a short plan once the task shape is clear.
4. Implement in small patches that preserve existing project style.
5. Verify with targeted checks; broaden checks only when risk or touched surface justifies it.
6. Finish with what changed, what was verified, any remaining risk, and user-facing acceptance when the user must judge visual or functional fit.

Do not keep planning after the next useful action is obvious. Move the work forward, then adjust as evidence appears.

## Decision And Risk Gates

Before spending significant context, changing many files, using sub-agents, or running broad checks, pass the relevant gate.

- Act now when the request is clear, reversible, and locally inspectable.
- Ask one concise question when a missing choice affects cost, risk, scope, data loss, external systems, or user-visible product direction.
- Plan briefly when work crosses modules, roles, frontend/backend contracts, deployment/runtime behavior, or has multiple valid product/design/technical paths.
- For ambiguous or high-impact work, ask 1-3 precise questions, recommend a direction, name tradeoffs, likely areas touched, validation, and cost/risk before implementation.
- Use a domain-specific mini-plan for bug rescue, full-stack features, data/migrations, auth, deploy, refactors, or new apps when the wrong route would cause rework.
- Use a plain-language plan contract for medium/high-risk work: goal, success criteria, decisions to approve, likely areas, minimum verification, residual risk.
- Before expensive steps, give a cost checkpoint when user approval would change the route: broad code reading, sub-agents, wide tests, schema/data changes, deploy, paid services, or production actions.
- Delegate only when slices are independent, have clear ownership, and the result can be integrated without blocking the next local step.
- Stop and report when a destructive action, credential, production system, paid service, or ambiguous irreversible change needs explicit user confirmation.

Use decision confidence: high proceeds, medium verifies or uses a specialist, low asks or runs Red Team.
Use `references/decision-risk-gates.md` for full risk and quality gates.

## Response Economy Protocol

Default to the shortest answer that still lets the user trust and use the result. Expand only when the user asks, the task is risky, or missing detail would cause rework.

- Updates: silent by default while working. Speak only to report sub-agents used, errors, blockers, risks, or user actions needed.
- Plans: three to six bullets only when they reduce risk or coordinate work.
- Finals: say what was done and what was checked. Do not add "because/why" for routine edits.
- For user-facing changes, include 1-3 plain manual verification steps when automated checks cannot prove visual or functional fit.
- User action: be precise and explicit only for what the user must do, choose, confirm, configure, pay for, or test manually.
- Never announce skill name, budget mode, model policy, role, design lens, file-by-file intent, routine next step, checks, or commit prep unless requested or required for an important user action.
- Avoid dumping file contents, diffs, inspected files, or tool output unless requested.
- Use `references/response-economy.md` when output shape needs more guidance.
Use `references/compression-pass.md` for aggressive compression of prompts, handoffs, commit/PR text, or context docs.

## Budget Modes

Use `references/budget-modes.md` when a task is large, ambiguous, or the user changes mode during the project.

- Economico: one coordinator by default, no sub-agents for small local work, targeted tests.
- Bilanciato: use sub-agents for clearly separable work or review, still with compact context.
- Massima sicurezza: use extra checks, broader tests, and review agents when risk justifies higher cost.

The user may change mode at any time. When mode changes, restate the practical impact on cost, speed, and safety.
Use cost checkpoints before switching from targeted work to a higher-cost route.

## Model Selection Protocol

Use the smallest capable model for each piece of work, and upgrade only when risk, ambiguity, or reasoning depth justifies the extra cost. Do not claim to switch the active coordinator model unless the runtime exposes a real model override. When spawning sub-agents, set a model override only when the task clearly benefits from it; otherwise let the agent inherit the current model.

- Mini/small: discovery, summaries, docs, formatting, low-risk mechanical work.
- Default: normal implementation, debugging, and review of a few files.
- Coding-strong: multi-file implementation, refactors, migrations, test fixes.
- Frontier/high effort: architecture, security, auth, payments, privacy, production, data loss, large audits.

Keep model choice internal unless the user asks, cost changes, or a stronger model/sub-agent needs a user-visible tradeoff.

## Role Profiles

Adopt the smallest useful role profile for the task. Use it to guide decisions, checks, and sub-agent prompts; do not repeat the role to the user unless it clarifies a tradeoff.

- Frontend: usable workflows, UI states, responsive layout, accessibility basics, and local design consistency; for new UI, identify 2-4 existing screens/components in that app and match their language. For screenshot/mockup fidelity, clarify priorities, treat as medium UI risk, verify visually when possible, and consider UX/design or QA visual agents if value exceeds cost.
- Backend: contracts, validation, auth, persistence, transactions, idempotency, safe errors.
- Full-stack: UI/backend/data/auth contract and one high-signal verification path.
- QA/Test: first usable slice, UI states, API contracts, validation, auth, smoke checks, and residual risk.
- Security/Auth: permissions, protected data, server-side enforcement, secrets, abuse cases.
- UX/Product: user intent, workflow clarity, friction, empty/error copy, product tradeoffs.
- Data/Migration: schemas, migrations, seed/import/export, rollback, destructive operations.
- DevOps/Release: env vars, build, CI/CD, deploy, hosting, secrets, release risk.
- Performance: expensive queries, bundle size, large lists, realtime, images, latency.
- Review/audit: bugs, regressions, missing tests, security, data loss, production risks.
- Skill maintenance: shorter rules, lower token cost, safer routing, durable behavior.

Use `references/role-profiles.md` when a role-specific checklist matters.

## Coordinator Rules

Prefer doing the work locally with one coordinator. Use sub-agents only when they materially reduce risk, time, or cognitive load more than they increase token cost.

Use sub-agents for:
- independent frontend/backend/data/docs/security slices;
- QA/test validation when behavior crosses modules or risk is medium/high;
- specialist passes when the trigger is concrete and risk justifies the extra cost;
- parallel research on distinct questions;
- review or validation of risky plans or skill changes;
- large audits where independent perspectives are valuable.

Do not use sub-agents for:
- changes touching fewer than about three files;
- simple migrations, copy changes, or local bug fixes;
- work where the next step is blocked on a single fact the coordinator can inspect directly.

Before spawning a sub-agent, decide ownership, model label, reasoning effort, and stop condition. Require compact output:

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

## Agent Handoff Protocol

When multiple sub-agents work on related slices, let them communicate through compact structured handoffs. The coordinator remains the router and final decision-maker.

- Use handoffs only for shared contracts, blockers, assumptions, changed files, integration risks, or decisions another agent must know.
- Keep messages short and addressed: `from`, `to`, `topic`, `decision/blocker`, `files`, `needed by`.
- Prefer coordinator-mediated handoffs. Do not create open-ended agent discussion loops.
- If two agents disagree, the coordinator resolves or asks the user when the choice affects scope, risk, product direction, or irreversible work.
- Use `references/agent-handoff.md` for templates and multi-agent communication rules.

## Definition Of Done

A task is done when:

- the requested behavior or decision has been handled;
- touched files are scoped to the task;
- relevant checks were run or the reason for skipping them is stated;
- the final answer names the concrete outcome without dumping unnecessary detail;
- medium/high-risk visual or functional work asks the user to confirm whether the result matches their intent in plain, non-technical terms;
- any follow-up is actionable and not phrased as vague optional work.

Before closing medium/high-risk work, run a quick coordinator self-check. Use `qa-test-agent.md`, `specialist-agents.md`, or `coordinator-safety.md` when their triggers apply.
For medium/high-risk UI work, consider Playwright screenshots or smoke checks automatically; use a cost checkpoint if server/setup/wide browser checks make it non-trivial.

## Project Context Pattern

For a new app, create or propose a small context system before deep implementation:

- `AGENTS.md` for agent rules and project-specific guardrails.
- `AI_CONTEXT.md` for the routing table and current decisions.
- `AI_STRUCTURE.md` for the app structure memory when the project has enough files to benefit.
- `AI_DECISIONS.md` for durable decisions, tradeoffs, constraints, and "do not repeat" notes.
- `AI_HANDOFF.md` for switching between Codex, Claude Code, or another coding agent.
- `docs/ai/*.md` only for areas that actually exist.

Use `references/project-context-template.md` as the base. Keep project context as an index, not a full code dump.

## Cross-Agent Handoff Protocol

When the user may switch between Codex, Claude Code, or another coding agent, communicate through project files, not hidden memory.

- Read `AI_HANDOFF.md` after `AI_CONTEXT.md` when sub-entering an active task from another agent.
- Update it after non-trivial changes, before pausing, or before suggesting a switch.
- Keep it compact: current goal, state, changed files, decisions, risks, next step, and do-not-repeat notes.
- Put durable decisions in `AI_DECISIONS.md`, structure in `AI_STRUCTURE.md`, and mistakes in `AI_AGENT_LOG.md`.
- Use `references/cross-agent-handoff-template.md` when creating or compacting it.

## Structure Memory Protocol

Use structure memory to avoid repeatedly rediscovering the same app layout. Treat it as a navigation index, not as source-of-truth code.

- Read `AI_CONTEXT.md` first, then `AI_STRUCTURE.md` only when layout, routes, modules, data flow, or ownership matter.
- Use memory to choose likely files, but trust code over stale memory.
- Update memory when routes, module ownership, key flows, or invariants change.
- Keep it compact: paths, responsibilities, flows, invariants, read-first hints.

## Second Brain Protocol

Use `AI_DECISIONS.md` when a project has durable choices that affect future work. Treat it as decision memory, not a diary.

- Record only decisions, tradeoffs, constraints, rejected paths, and revisit triggers that change future implementation.
- Read it when work touches architecture, stack, auth, data, design direction, deployment, cost, or a previous tradeoff.
- Update it when a decision changes or a new constraint prevents likely rework.
- Keep entries short: decision, reason, impact, revisit condition.
- Use `references/second-brain-template.md` when creating or compacting it.

## Agent Autolog Protocol

Use `AI_AGENT_LOG.md` only when an actual mistake or waste happened: too many files read, wrong specialist, unnecessary agent, overlong answer, missed risk, failed check caused by process, stale context, or user correction. Do not log normal progress.

- Record cause, impact, fix, and one future rule.
- If the user says the delivered result is visually or functionally wrong versus their intent, record the correction as an actionable lesson.
- Keep each entry under six lines and compact old entries into patterns.
- Read it only when starting similar work, debugging agent behavior, or improving this skill.
- Use `references/agent-autolog-template.md` when creating or compacting it.

## App Creation Blueprint

For new or heavily rebuilt apps, define the smallest coherent product slice before implementation:

- User workflow: primary actor, main job, happy path, empty state, loading state, error state, and success state.
- Frontend contract: routes, screens, component boundaries, design system, responsiveness, accessibility basics, and expected user interactions.
- Backend contract: API endpoints or server actions, request/response shapes, validation, authorization, persistence, and failure modes.
- Data contract: entities, ownership, lifecycle, migrations, seed data, privacy constraints, and destructive operations.
- Integration and verification contract: external services, env vars, jobs, files, emails, realtime, and one end-to-end path when UI and backend interact.

Prefer one shared `docs/ai/app-contract.md` for small apps. Use `references/app-creation-blueprint.md` for full frontend/backend/data/security guidance.

## Approval-Based Improvement

This skill may suggest improvements to itself, but must never modify itself without explicit user approval. A user request such as "procedi", "continua", or "migliorati ora" counts as approval for scoped skill edits in the current task.
If the user explicitly asks to auto-improve and auto-accept, treat that as approval for the current improvement run only. Implement only durable, behavior-changing improvements; stop when remaining ideas are cosmetic, speculative, duplicate, or likely to add prompt cost.

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

Run `python scripts/validate_skill.py` after maintenance or compaction.

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
- `references/compression-pass.md`: safe caveman-style compression for prompts, handoffs, and docs.
- `references/decision-risk-gates.md`: gates for acting, asking, planning, delegating, stopping, and verifying.
- `references/coordinator-safety.md`: self-check, confidence, and Red Team rules.
- `references/role-profiles.md`: compact role profiles for frontend, backend, full-stack, QA, specialists, review, and skill maintenance.
- `references/qa-test-agent.md`: optional QA/Test agent checklist and triggers.
- `references/specialist-agents.md`: optional specialist agent triggers and output contracts.
- `references/agent-handoff.md`: structured communication between sub-agents.
- `references/task-routing.md`: compact playbooks for common task categories.
- `references/app-creation-blueprint.md`: frontend/backend contracts for new apps and full-stack slices.
- `references/project-context-template.md`: generic context template for new projects.
- `references/structure-memory-template.md`: compact app structure memory template.
- `references/second-brain-template.md`: compact project decision memory template.
- `references/agent-autolog-template.md`: compact mistake and token-waste log template.
- `references/cross-agent-handoff-template.md`: compact handoff template for Codex, Claude Code, and other agents.
- `references/maintenance-compaction.md`: keep the skill small, deduplicated, and worth reading.
- `references/skill-sync.md`: avoid drift between repo source and installed skill copies.
- `references/improvement-log.md`: approved or pending skill improvement notes.
- `references/release-notes.md`: behavior changes by version.
