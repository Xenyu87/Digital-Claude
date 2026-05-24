---
name: cost-aware-app-coordinator
description: Coordinates non-trivial software tasks (new app, audit, bug rescue, migration, deploy, cross-module refactor, skill improvement). Activates when planning, stack choice, multi-agent, AI_*.md files are needed. DO NOT use for single-string fix, local rename, color change, isolated single-file edit, conceptual questions.
---

# Cost-Aware App Coordinator

Coordinates software project work while reducing token waste and excessive output length. Supports multi-agent handoff via `AI_*.md` files.

## Language

Default: English. Change only if the user writes in another language.

## When NOT to use this skill

- Conceptual question that doesn't require modifications
- One-line trivial task
- More specific skill already active (e.g., `claude-api`, `init`, `security-review`)
- Conversation outside software domain

In these cases, respond directly without protocol.

## 0. Fast path (small modifications)

If the task is a local change (1-3 known files, clear scope, no auth/data/migrations/deploy):

- do not open `references/`, do not open `recipes/`, do not spawn `Agent`
- just modify
- output in 2 lines: `Done: ... / Verify: ...`

All remaining sections (1-19) are for tasks that do NOT fall here. When in doubt, start with fast path; escalate to full protocol only if you discover greater scope or risk.

## 1. Task classification

Categories (internal, do not print): **new app**, **modify app**, **audit**, **bug rescue**, **skill improvement**, **ops**.

Typical triggers → category:
- "create/scaffold/start from scratch" → new app
- "add/change/refactor/move" → modify app
- "review/audit/check security" → audit
- "systemd/journalctl/ssh/lxc/port/service/syncthing/deploy/restart" → ops (infrastructure, not code)
- "not working/error/crash" → bug rescue
- "update the skill/self-improve" → skill improvement

Even without explicit declaration, classify from the main verb and repo state. Details: `references/task-routing.md`.

### 1.5 Auto-trigger: Scope Checkpoint

**Automatically activates** `references/scope-checkpoint.md` if the brief contains 2+ of the following patterns:

- **2+ separate action verbs**: "add X *and* modify Y *and* refactor Z" → 🚩 multi-layer
- **Vague words without context**: "improve", "make", "optimize", "clean" → ambiguous
- **Uncertain time scope**: estimated >400k tokens or >1 session → high risk
- **Uncertain file count** (>5): "check everything", "review the module" → vague

**Procedure**: count action verbs in the brief. If N ≥ 2:
1. Activate **internal scope debate** with 2 Haikus (minimal vs. expanded scope)
2. If convergence >70% → proceed with minimal scope
3. If <70% → mirror back to user and ask choice

**Preventive cost** (~$0.01) vs. **scope creep risk** (~100k token wastage = ~$5). Favorable trade-off.

## 2. Budget mode

- **Economical** (default): minimal reads, short output
- **Balanced**: targeted reads on impacted files
- **Maximum safety**: extended reads, double-check, audit

Default Economical, automatic escalation on risk gates. User can force. Category-specific defaults (new app/audit/skill improvement = Balanced; modify/bug rescue = Economical) in `references/task-routing.md`. Budget details: `references/budget-modes.md`.

## 3. Model selection

Smallest model capable of closing the task (`haiku` < `sonnet` < `opus` by cost).

**Baseline 2026-05**: Haiku 4.5 · Sonnet 4.6 · Opus 4.7. Escalation rules refer to family, not minor version.

**Main agent**: chosen by user, not changeable by skill. If risk rises (auth, migrations), suggest changing model with `/model` (press `d` in picker to make it default in session), don't assume.

**Sub-agent (routing by sub-task category)**: automatically sets `model` on `Agent`:

| Sub-task | Model | When |
|---|---|---|
| file exploration (wide grep, README/structure read, "where is X") | `haiku` | respond to main agent in 1-2 paragraphs, no patch |
| QA test runner, lint, type-check, log summary | `haiku` | structured, deterministic output |
| isolated 1-3 file edit with clear scope | `sonnet` | direct edits, no design |
| security audit/cross-module review | `sonnet` | except if risk gate active |
| architectural design, stack choice, migration plan | `opus` | only if main agent is already Opus or Maximum Safety gate |
| final synthesis / pre-commit review of long plan | `opus` | when retry cost > Opus cost |

Scoring heuristic (choose between nearby options): `quality × 1 / log(1 + cost_ratio)`. Favors cheap-and-good over expensive-and-marginally-better.

Default per main category (combined with budget §2):

- **ops** + Economical → Haiku for main agent suggested (commands and logs)
- **modify** + Economical → Sonnet, Haiku for preliminary exploration
- **audit** + Balanced → Sonnet for scan, Opus only for final synthesis if finding requires it
- **new app** + Balanced → Sonnet for scaffolding, Opus only for initial stack design
- **bug rescue** → Sonnet; Haiku for reproduction/logs; Opus only if cause unclear after 2 attempts
- **skill improvement** → Sonnet; Opus for section redesign, never for small edits

When in doubt choose the smallest. Single escalation per turn: if Haiku fails, escalate to Sonnet with context of failure, don't restart from scratch. Extended table for specialist agent in `references/specialist-agents.md`.

**Local subagent catalog** (in `~/.claude/agents/`, each with explicit `model:`):

| Subagent | Model | Use for |
|---|---|---|
| `Explore` (built-in) | haiku | grep/glob, "where is X", fast file read on known paths |
| `ops-runner` | haiku | systemctl/journalctl/cron/ss/df: quick commands, no decisions |
| `homelab-admin` | sonnet | sysadmin decisions: configure services, LXC, network, Proxmox, port allocation, deploy workflow |
| `security-hardener` | sonnet | server/LXC security audit: SSH, firewall, ports, permissions — read-only and recommendations |
| `bypass-guardian` | sonnet | pre-execution review when bypass-permissions is ON and risky/irreversible actions present |
| `dependency-checker` | haiku | npm/pip audit: obsolete versions, known CVEs, unmaintained packages — read-only |
| `db-migrator` | sonnet | safe DB migrations with rollback: ALTER/DROP/ADD, SQLite↔Postgres conversions, initial schema |
| `disaster-recovery` | sonnet | environment recovery after catastrophic loss: LXC destroyed, config lost, services missing |
| `code-implementer` | sonnet | edit 1-5 files with decided scope, local refactor, wire-up |
| `qa-tester` | sonnet | test writing/run, regression testing on bugs |
| `code-debugger` | sonnet | bug rescue: reproduce → isolate → fix → verify |
| `doc-writer` | sonnet | AI_*.md / README / handoff after non-trivial modifications |
| `code-reviewer` | opus | pre-commit review of non-trivial diff (independent judgment) |
| `mar-reviewer` | opus | cross-module audit + pre-commit review of non-trivial diff (3 reviewers + aggregator) |
| `architect` | opus | new feature, stack choice, data model design |
| `scope-verifier` | sonnet | continuous monitor if work aligns with brief (v1.1.0) |

**Flags for dispatched subagent**: subagents accept `--model`, `--permission-mode` for one-off override. Fast mode uses Opus 4.7 by default. Practical examples in `references/specialist-agents.md`.

**Model pre-selection (v1.1.0)**: before applying the table, extract difficulty from brief with `scripts/difficulty_estimator.py`. Baseline score 0.5, adjust for keywords (hard +0.3, easy -0.15, vague +0.2). See `references/difficulty-routing.md`.

**Budget-Aware Override (v1.1.0)**: if `tokens_residual < 20k`, ignore task-type choice and force Haiku. Script: `scripts/budget_aware_router.py`. Check before starting big task.

**Delegation rule** (anti-pattern: "I'll do it with Opus because I have it"):
- Code exploration/grep/find on >2 files → `Explore`. Never read 10 files in main session.
- Simple ops command (status/restart/tail) → `ops-runner`. Never bash inline in main session if output needs parsing.
- Edit with decided scope → `code-implementer`. Main session should NOT edit production code: plan + delegate.
- Non-trivial bug → `code-debugger`. Main session should NOT debug by feel.
- Architectural decision → `architect` (even if main is already Opus: isolated agent doesn't pollute main context).

### External routing (opt-in)

Disabled by default (`EXTERNAL_ROUTER_ENABLED=false`). If active, routes calls for `ops` category or Haiku-equivalent explorations to OpenRouter/DeepSeek. **Never** for production code, credentials, personal data, modify/audit/bug_rescue categories. On first use prints non-silenceable warning and logs in `coordination-log.jsonl` with `external_router: true`. Details: `references/external-routing.md`.

**Automatic context triggers** (dashboard emits `<routing-hint>` in prompt via UserPromptSubmit hook — when you see that block, respect `suggested_subagent` unless explicit reason not to):

```
<routing-hint>
classified: <category>
suggested_subagent: <name>
model: <haiku|sonnet|opus>
budget_max: <token>
</routing-hint>
```

### Auto-delegation gate (enforcement)

Four gates that main agent must respect before executing inline. Bypassable only with explicit override (see below).

**Gate 1 — routing-hint has priority**: if prompt contains `<routing-hint>` with non-empty `suggested_subagent` and `model: sonnet|haiku`, main agent does NOT execute inline — even if already Opus. Immediately spawn `Agent(subagent_type=<suggested>, model=<suggested_model>)`. Exception: trivial task (<2 files, <1 turn, clear fast path).

**Gate 2 — Opus ceiling for modify category**: if task requires edits on >3 files, delegation to `code-implementer` (sonnet) is mandatory. Main agent only does planning + result verification; does not directly touch production files.

**Gate 3 — Haiku for exploration**: pattern "grep/find on >2 files", "read README/structure", "where is X" → `Explore` (haiku) always. Main agent does not execute grep inline on >2 files.

**Gate 4 — ops + Economical**: ops category + Economical budget → `ops-runner` (haiku) for systemctl/journalctl/cron/ss/df commands. No bash inline if output needs parsing.

**Explicit override**: if user writes "do it yourself", "don't delegate", "stay on main", gate is bypassed for that turn. Indicate in response: `[gate bypassed on user request]`. Details and examples: `references/auto-delegation-gate.md`.

**Gate 5 — bypass-guardian in bypass mode**: if user activated bypass-permissions (`/permission 3` or equivalent) **and** task contains risky/irreversible actions (rm, force-push, DROP, modify `/etc/`, credentials, deploy to stable), spawn `bypass-guardian` (sonnet) **before** executing. Proceed only after verdict 🟢 GREEN or 🟡 YELLOW with recommendations followed. On 🔴 RED stop and ask explicit user confirmation. This gate is NOT bypassable by "do it yourself" — requires explicit confirmation on specific risk.

## 4. Initial context reading

Only these files if they exist, in order:

1. `AI_HANDOFF.md` (if taking over from another agent)
2. `AI_CONTEXT.md`
3. `AGENTS.md`
4. `CLAUDE.md`
5. `AI_STRUCTURE.md` (only if task touches modules or contracts)
6. `AI_DECISIONS.md` (only if current decision crosses past one)
7. `README.md` (only if previous ones insufficient)

Don't read entire repo: preventive reading burns context on unused files.

## 5. Progressive loading

`SKILL.md` is core always loaded. `references/*.md` only when concrete trigger present. If reference already read in this turn, reuse understanding instead of re-reading.

Reference activation map:

- task → `references/task-routing.md`
- budget → `references/budget-modes.md`, `references/response-economy.md`
- decision gates → `references/decision-risk-gates.md`
- ambiguous scope or non-programmer user → `references/scope-checkpoint.md`
- in-flight drift detection → `references/in-flight-scope-monitor.md`
- difficulty estimation and routing → `references/difficulty-routing.md` (v1.1.0+)
- auto-scope-checkpoint for multi-layer brief → `references/in-flight-scope-monitor.md` (v1.1.0+)
- roles → `references/role-profiles.md`, `references/specialist-agents.md`, `references/qa-test-agent.md`
- delegation gate / model drift → `references/auto-delegation-gate.md`
- handoff → `references/agent-handoff.md`, `references/cross-agent-handoff-template.md`
- app creation → `references/app-creation-blueprint.md`, `references/default-stacks.md`, `references/project-context-template.md`, `references/structure-memory-template.md`, `references/second-brain-template.md`, `references/agent-autolog-template.md`; ready recipes in `recipes/`
- app deploy → `references/deploy-paths.md` + scripts in `assets/scripts/deploy-*.sh`
- UI visual testing → `references/visual-first-testing.md`
- **ops** tasks (systemd, journalctl, ssh, lxc, proxmox, syncthing, cron, firewall, deploy, ports) → `references/homelab-ops.md`
- MCP integrations (GitHub/Linear/Slack/Notion/...) → `references/mcp-integrations.md`
- maintenance → `references/maintenance-compaction.md`, `references/compression-pass.md`, `references/skill-sync.md`, `references/improvement-log.md`, `references/release-notes.md`
- coordinator safety → `references/coordinator-safety.md`
- prompt caching (Anthropic API) → `references/prompt-caching.md`
- self-improvement → `references/self-improvement.md`, `references/reflexion-loop.md`
- drain / auto-curriculum / overnight maintenance → `references/background-drain.md`
- coordination log / sedimentation → `references/coordination-sedimentation.md`
- DAG pipeline of subagents → `references/pipeline-dsl.md`
- external routing opt-in → `references/external-routing.md`
- loading tuning → `references/progressive-loading.md`

## 6. Working loop

For non-trivial tasks: budget+model internally → minimal context → mini-plan if needed → small patches → targeted verification → short closure. Stop planning when next step is obvious.

### 6.5 In-Flight Scope Drift Check

Every 3 turns (or on trigger: files +3, token burn >150% expected, category shift): calculate drift score between original brief and completed work.

**Thresholds**:
- 0.0–0.3: ✅ ON_TRACK continue
- 0.3–0.6: ⚠️ DRIFT_WARNING → log + ask user confirmation before proceeding
- >0.6: 🛑 HARD_DIVERGENCE → offer "should we stop? can I open task2 for the rest?"

**Script**: `scripts/scope_drift_detector.py` (calculates score with file divergence heuristic, category shift, token burn, semantic divergence).

**Agent monitor** (v1.1.0): for non-trivial task (>2h, >5 files), call `scope-verifier` agent (Sonnet) every 3 turns. Provides independent verdict: ON_TRACK, DRIFT, DIVERGE with score and suggestion. For small tasks, inline drift detector sufficient.

**Log**: add to coordination-log the `drift_check` section with score, severity, reason. See `references/in-flight-scope-monitor.md`.

## 7. Output economy

Default:

```
Done: <concise action>
Verify: <how user checks>
```

Details only for: risks, non-obvious choices, blockers, user actions. When user must configure/choose/confirm/pay/test, add a `For you:` section.

**Activation announcement**: on first turn of non-trivial session (classified category, budget chosen), open with single line like: `🛠 Skill: cost-aware-app-coordinator · cat:<category> · budget:<mode>`. Only first line, no extra preambles. Skip to fast path.

Complete rules: `references/response-economy.md`.

## 8. Decision gates and risk

Before risky or irreversible actions (delete, force-push, DB modification, migrations, dependency removal, secrets), stop and ask.

Confidence: high → proceed; medium → verify/specialist; low → ask/red team. See `references/decision-risk-gates.md`.

**Ambiguous scope**: if task is vague, mixes multiple goals, or user is non-programmer with open technical choices, activate protocol in `references/scope-checkpoint.md` before writing code.

## 9. Specialists

Sub-agent only if risk or time saved justifies token cost. **Never parallelize by default**: cost grows non-linearly with agent count.

**Activate** for: wide cross-file search, second opinion, independent slice, wide audit. **DO NOT activate** for: <3 files, local fix, copy change, single-fact lookup checkable by main.

In Claude Code: tool `Agent` with `subagent_type` — list depends on environment, see `references/specialist-agents.md`. Self-contained briefing: objective, minimal context, format. Never "you decide".

Profiles: `references/role-profiles.md`, `references/specialist-agents.md`, `references/qa-test-agent.md`.

### 9.1 When to parallelize (v1.1.0)

**Parallel swarm** (launch 2-3 agents simultaneously) only if all 4 conditions true:

1. **Independent tasks** — none depends on other's output
2. **Non-overlapping file set** — no file touched by 2+ agents
3. **Budget available** — `tokens_residual > (cost_A + cost_B) * 1.5`
4. **Both completable <1 session**

Default: sequential. See `recipes/parallel-swarm.md` for examples and anti-patterns.

## 10. Handoff between agents

Two levels:

- **between different agents** (separate sessions, other tools): shared files in repo (`AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AI_DECISIONS.md`, `AI_AGENT_LOG.md`, `AI_HANDOFF.md`).
- **between sub-agents same session**: don't talk directly, coordinator is router. Short tasks: pass result of A in prompt of B (filtered). Long tasks: use `AI_HANDOFF.md` as bulletin board. Resume active agent: `SendMessage`.

When taking over read `AI_HANDOFF.md` first. Update it after non-trivial modifications. Durable decisions → promote to `AI_DECISIONS.md`.

Details: `references/agent-handoff.md`, `references/cross-agent-handoff-template.md`.

## 11. Definition of Done

Task closed when: behavior handled, files touched limited to task, relevant checks executed (or skip reason declared), final output short. For UI/functional at medium/high risk: user confirms in plain language + evaluates Playwright screenshot.

## 12. Creating a new app

- **Step 0** — recognize recipe in `recipes/` (landing, CRUD, dashboard, blog, bot). If no match, choose from `references/default-stacks.md` (A/B/C) — don't ask "which framework".
- **Step 1** — minimal scaffolding: structure + `AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AGENTS.md`, `CLAUDE.md`. No "for the future", no unrequested test/CI.
- **Step 2** — deploy early: right after first `npm run dev` works locally, configure deploy on Vercel/Netlify/Railway. See `references/deploy-paths.md` + `assets/scripts/`.
- **Step 3** — visual testing: after UI changes use pattern from `references/visual-first-testing.md`.

Files `AI_*.md`, `AGENTS.md`, `CLAUDE.md` ready in `assets/templates/`. Usage rules in reference `*-template.md`. Complete blueprint: `references/app-creation-blueprint.md`.

## 13. Modifying existing app

1. Read `AI_HANDOFF.md` or `AI_CONTEXT.md`.
2. Identify minimal impacted file set.
3. Modify only what's needed. No opportunistic refactor (increases diff and risk without value).
4. Update `AI_HANDOFF.md` if modification is non-trivial.
5. Short output per §7.

## 14. Audit

Read-only, no modifications without OK. Output: findings with severity, file:line, proposed fix. No narration.

## 15. Bug rescue

Reproduce with minimal reads → propose fix if cause non-obvious → update `AI_AGENT_LOG.md` if recurring pattern.

## 16. Skill improvement

For skill modifications: `references/skill-sync.md` for drift, `references/improvement-log.md` for entries, `references/release-notes.md` if behavior changes, `python scripts/validate_skill.py` before closing.

Skill **not modified without explicit approval** ("proceed"/"self-improve" valid for current session only). Proposal template and complete flow in `references/self-improvement.md`.

**Incident → knowledge update loop**: when user corrects skill behavior, immediately apply fix, add entry in `improvement-log.md`, register pattern in `AI_AGENT_LOG.md` of source project; after 3 occurrences promote rule in `SKILL.md` or relevant reference. Complete pattern: `references/reflexion-loop.md`. Helper: `python scripts/propose_lesson.py` (automatically writes `<TBD ...>` entries in `AI_AGENT_LOG.md` at end of non-trivial tasks).

**Complete TBD entries**: on first turn of new session, if `AI_AGENT_LOG.md` of active project contains entries with `<TBD ...>` placeholders, complete them immediately based on: list of touched files in entry, commit message, `git diff HEAD~1 HEAD --stat`. One lesson per entry, two lines. If insufficient context for useful preventive lesson, delete entry (nothing beats wrong). Don't ask confirmation per entry; show only summary at turn end.

**Skill library** (reusable Voyager snippets): `skill_library/` holds fragments from real use. Promote to `recipes/` or reference after 3+ uses.

For details on drain and auto-curriculum: `references/background-drain.md`.

## 17. Maintenance

Periodic compaction of `AI_*.md` files. See `references/maintenance-compaction.md` and `references/compression-pass.md`.

**Skill self-review**: at each minor release (see `references/release-notes.md`) re-run `python scripts/validate_skill.py` and read `references/progressive-loading.md` to check drift between trigger map and actual references. If installed copy diverges from canonical, use `references/skill-sync.md` + `scripts/sync_skill.py`.

## 18. Coordinator safety

Anti-loop, anti-overwrite, anti-waste rules: `references/coordinator-safety.md`.

**Hard token cap per task**: dashboard (`/api/log`) accepts `tokens_budget_max`. If current session exceeds cap, task marked `budget_exceeded` and Python logger signals event at next Stop. Set cap default in line with category (example: ops 50k, modify 200k, audit 400k, new app 600k, bug rescue 250k); user can force. Runtime sentinel: at half cap (50%) emit line `⚠ budget at 50% (X/Y tok · ~$Y.YY)` in current turn; at 80% ask confirmation before expensive reads.

Cost estimate in-session (Opus 4.x): `input×$15 + output×$75 + cache_read×$1.5 + cache_creation×$18.75` per million tokens. Quick example: 100k input + 20k output ≈ $1.50 + $1.50 = **~$3.00**. Use this formula for sentinel and answering "how much is this session costing?".

## 19. MCP Integrations

For tasks operating on external SaaS (GitHub, Linear, Slack, Notion, etc.) use MCP server with format `ServerName:tool_name` (e.g., `GitHub:create_issue`, `Linear:update_issue`). **Write** tools are hard gates, **read-only** are safe. Details and recommended server table: `references/mcp-integrations.md`.

**GitHub MCP** is configured globally (`~/.claude/mcp.json`, server `@modelcontextprotocol/server-github`). Use when:

| Trigger | Tool to use | When NOT to use |
|---|---|---|
| "search skill/repo on GitHub for X" | `github:search_repositories` | if answer already in `sources.json` |
| "what does this repo do" | `github:get_file_contents` (README/CHANGELOG) | for unknown or irrelevant repos |
| "find implementation examples" | `github:search_code` | if task is local, no GitHub |
| "latest commits/issues on X" | `github:search_commits`, `github:search_issues` | for repos unrelated to task |
| "read repo structure" | `github:get_repository_tree` | only if necessary to understand layout |

Rules: read-only always safe; write (`create_issue`, `create_pull_request`) only if user explicitly requests. Token goes in `.env.local` as `GITHUB_TOKEN` (classic PAT, scope `public_repo`).

Custom skills now open standard (Claude Code/Codex CLI/Cursor/Gemini CLI). MCP references `Server:tool` work cross-tool.

## 20. Validator

`scripts/validate_skill.py` checks: frontmatter conformant (name ≤64 char, description ≤1024), reference ↔ SKILL ↔ assets coherent (file and glob `assets/.../*.ext`), progressive loading map complete, duplicate headings, mandatory sections, `SKILL.md` <450 lines (Anthropic best-practice: <500), reference <120 lines, each cited recipe in `recipes/README.md`, each script in `assets/scripts/` and each template in `assets/templates/` referenced in corpus.

```bash
python scripts/validate_skill.py
```
