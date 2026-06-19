---
name: digital-claude
description: Coordinates non-trivial software tasks (new app, audit, bug rescue, migration, deploy, cross-module refactor, skill improvement). Activates when planning, stack choice, multi-agent, AI_*.md files are needed. DO NOT use for single-string fix, local rename, color change, isolated single-file edit, conceptual questions.
---

# Cost-Aware App Coordinator

Coordinates software project work while reducing token waste and excessive output length. Supports multi-agent handoff via `AI_*.md` files.

## Language

Default: **Italiano**. Cambia solo se l'utente scrive in altra lingua. Termini tecnici inglesi vanno bene (commit, branch, endpoint).

## When NOT to use this skill

- Conceptual question that doesn't require modifications
- One-line trivial task
- More specific skill already active (e.g., `claude-api`, `init`, `security-review`)
- Conversation outside software domain

In these cases, respond directly without protocol.

## 0. Fast path (small modifications)

If the task is a local change (≤5 known files, clear scope, no auth/data/migrations/deploy):

- do not open `references/`, do not open `recipes/`, do not spawn `Agent`
- just modify
- output in 2 lines: `Done: ... / Verify: ...`

All remaining sections (1-20) are for tasks that do NOT fall here. When in doubt, start with fast path; escalate to full protocol only if you discover greater scope or risk.

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

### 1.6 Auto-trigger: Enum Sync Checklist

**Attiva se il diff tocca un valore enum-like** (155× occorrenza — la lezione più ricorrente del dataset):
- `CHECK ... = ANY(ARRAY[...])` in schema.sql
- `type X = 'a' | 'b' | ...` o `z.enum([...])` in TypeScript
- Array di opzioni in filter/select/tab UI

**Checklist obbligatoria prima di chiudere il task** (esegui `grep` su ogni punto):
1. `schema.sql` — CHECK constraint aggiornato
2. Tipo TS corrispondente — union/enum allineato
3. Componenti UI — `grep '<valore>'` nei `.tsx` che enumerano le opzioni
4. Route API — validazioni/switch allineati al nuovo valore
5. `coordination_log.py` / `route_hint.py` — se tocca categorie o modelli interni

Se manca anche uno solo → non chiudere il task.

## 2. Budget mode

<!-- thresholds-auto -->
## Auto-Discovered Cost Thresholds (updated 2026-06-18, n=267 sessioni)
| categoria | warn (p75) | ceiling (p90) | n |
|---|---|---|---|
| modifica | $50.70 | $75.31 | 196 |
| ops | $0.26 | $0.46 | 29 |
| miglioramento_skill | $83.91 | $130.40 | 23 |
| domanda | $3.49 | $7.00 | 19 |
Superare ceiling = sessione in overrun. Chiudi e apri nuovo task.
<!-- /thresholds-auto -->

Nota: questa tabella ($, auto-aggiornata da dati osservati) copre solo le 3 categorie con dati sufficienti. §18 usa cap in **token** per le 6 categorie di §1 — sono limiti diversi (monitoraggio costo vs hard cap pre-task), non in conflitto.

- **Economical** (default): minimal reads, short output
- **Balanced**: targeted reads on impacted files
- **Maximum safety**: extended reads, double-check, audit

Default Economical, automatic escalation on risk gates. User can force. Category-specific defaults (new app/audit/skill improvement = Balanced; modify/bug rescue = Economical) in `references/task-routing.md`. Budget details: `references/budget-modes.md`.

## 3. Model selection

**Default sub-agent: Haiku** per esplorazione/QA/ops. **Main agent: Sonnet** (opusplan se disponibile — Sonnet in esecuzione, Opus automatico in plan mode). Scala sub-agent su fallimento esplicito o categoria complessa.

**Baseline 2026-06**: Haiku 4.5 · Sonnet 4.6 · Opus 4.8. Escalation rules refer to family, not minor version.

**Opus 4.8 API notes**: effort defaults to `high` (no need to set); fast mode via `speed: "fast"`; adaptive thinking via `thinking: {type: "adaptive"}` only (no `budget_tokens`); prompt cache min now **1,024 tokens** (down from 2,048 on 4.7); mid-conversation system messages supported (inject updated instructions mid-loop without restating full prompt).

**Tool-routing & Reasoning Trap** (arxiv 2510.22977): per decisioni di *selezione/uso tool* non attivare `thinking: adaptive` né reasoning esteso — amplifica le tool hallucination. Usare i gate deterministici della delega (tabella sub-task, Gate 1-5) e le regole di routing. Il reasoning esteso resta appropriato per design/debug, mai per "quale tool chiamo adesso".

**Main agent**: chosen by user, not changeable by skill. If risk rises (auth, migrations), suggest changing model with `/model` (press `d` in picker to make it default in session), don't assume.

**Fallback model per overload/indisponibilità** (CLI ≥2.1.166): flag di avvio `--fallback-model <a,b>` (lista comma-separated, riprova il primario all'inizio). NON è una chiave di `settings.json` (lo schema 2.1.x non la accetta): per renderlo "default" serve un alias di shell, es. `alias claude='claude --fallback-model claude-opus-4-8,claude-sonnet-4-6'`. Attenzione: scatta solo su modello *overloaded/non disponibile*, NON su risposte sbagliate in loop — il caso submi/xmanager resta coperto dall'escalation manuale di §15 (`/model opus`), non da questo flag.

**Sub-agent (routing by sub-task category)**: automatically sets `model` on `Agent`:

| Sub-task | Model | When |
|---|---|---|
| file exploration (wide grep, README/structure read, "where is X") | `haiku` | respond to main agent in 1-2 paragraphs, no patch |
| QA test runner, lint, type-check, log summary | `haiku` | structured, deterministic output |
| isolated 1-3 file edit with clear scope | `sonnet` | direct edits, no design |
| security audit/cross-module review | `sonnet` | except if risk gate active |
| architectural design, stack choice, migration plan | `opus` | only if main agent is already Opus or Maximum Safety gate |
| final synthesis / pre-commit review of long plan | `opus` | when retry cost > Opus cost |

Default per main category (combined with budget §2):

- **ops** + Economical → Haiku for main agent suggested (commands and logs)
- **modify** + Economical → Sonnet, Haiku for preliminary exploration
- **audit** + Balanced → Sonnet for scan, Opus only for final synthesis if finding requires it
- **new app** + Balanced → Sonnet for scaffolding, Opus only for initial stack design
- **bug rescue** → Sonnet; Haiku for reproduction/logs; Opus only if cause unclear after 2 attempts
- **skill improvement** → Sonnet; Opus for section redesign, never for small edits

Single escalation per turn: if Haiku fails, escalate to Sonnet with context of failure, don't restart from scratch — coerente con "Haiku default" sopra.

**Core subagent (uso frequente)** — catalogo completo (27 agenti) in `references/specialist-agents.md`:

| Subagent | Model | Use for |
|---|---|---|
| `Explore` (built-in) | haiku | grep/glob, "where is X", fast file read on known paths |
| `ops-runner` | haiku | systemctl/journalctl/cron/ss/df: quick commands, no decisions |
| `code-implementer` | sonnet | edit 1-5 files with decided scope, local refactor, wire-up |
| `code-debugger` | sonnet | bug rescue: reproduce → isolate → fix → verify |
| `code-reviewer` / `mar-reviewer` | sonnet / opus | pre-commit review: diff semplice → code-reviewer; cross-module o risk gate → mar-reviewer (3 reviewers) |
| `architect` | opus | new feature, stack choice, data model design |

**Flags for dispatched subagent**: subagents accept `--model`, `--permission-mode` for one-off override. Fast mode uses Opus 4.8 by default (2.5x faster output, 3x cheaper than previous fast mode). Practical examples in `references/specialist-agents.md`.

**Model pre-selection (v1.1.0)**: before applying the table, extract difficulty from brief with `scripts/difficulty_estimator.py`. Baseline score 0.5, adjust for keywords (hard +0.3, easy -0.15, vague +0.2). See `references/difficulty-routing.md`.

**Budget-Aware Override (v1.1.0)**: if `tokens_residual < 20k`, ignore task-type choice and force Haiku. Script: `scripts/budget_aware_router.py`. Check before starting big task.

**Delegation rule** (anti-pattern: "I'll do it with Opus because I have it"):
- Code exploration senza target noto, >2 round esplorativi → `Explore`. Non per grep singolo su path noto.
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

Six gates that main agent must respect before executing inline. Bypassable only with explicit override (see below).

**Gate 1 — routing-hint has priority**: if prompt contains `<routing-hint>` with non-empty `suggested_subagent` and `model: sonnet|haiku`, main agent does NOT execute inline — even if already Opus. Immediately spawn `Agent(subagent_type=<suggested>, model=<suggested_model>)`. Exception: trivial task (<2 files, <1 turn, clear fast path). **Se routing-hint assente** → applica default per categoria dalla tabella §3.

**Gate 2 — Opus ceiling for modify category**: if task requires edits on >3 files, delegation to `code-implementer` (sonnet) is mandatory. Main agent only does planning + result verification; does not directly touch production files.

**Gate 3 — Haiku for exploration**: ricerca senza target noto, >2 round esplorativi, "where is X", "read README/structure" → `Explore` (haiku). Non scatta su grep singolo con path noto — solo su esplorazione iterativa senza destinazione chiara.

**Gate 4 — ops + Economical**: ops category + Economical budget → `ops-runner` (haiku) for systemctl/journalctl/cron/ss/df commands. No bash inline if output needs parsing.

**Explicit override**: if user writes "do it yourself", "don't delegate", "stay on main", gate is bypassed for that turn. Indicate in response: `[gate bypassed on user request]`. Details and examples: `references/auto-delegation-gate.md`.

**Gate 5 — bypass-guardian in bypass mode**: if user activated bypass-permissions (`/permission 3` or equivalent) **and** task contains risky/irreversible actions (rm, force-push, DROP, modify `/etc/`, credentials, deploy to stable), spawn `bypass-guardian` (sonnet) **before** executing. Proceed only after verdict 🟢 GREEN or 🟡 YELLOW with recommendations followed. On 🔴 RED stop and ask explicit user confirmation. This gate is NOT bypassable by "do it yourself" — requires explicit confirmation on specific risk.

**Gate 6 — git remote verification (ALWAYS, non bypassable)**: before ANY `git push` (normal or force), verify:
1. Read `scripts/.git_remotes.json` — check that the repo being pushed matches the allowlist entry for this project.
2. Show the user: `PUSH → <remote_url> (<repo_name>)` and wait for explicit confirmation.
3. On `--force`: also show which remote commits will be overwritten (`git log HEAD..origin/branch --oneline`).
If the remote URL does NOT match the allowlist → **stop immediately**, show the mismatch, ask user to confirm or correct the remote. This gate was added after an accidental force-push to the wrong repo (`digital-codex` instead of `Digital-Claude`).

## 4. Initial context reading

Only these files if they exist, in order:

1. `AI_ANCHORS.md` — fatti immutabili del progetto (stack, porte, auth, prezzi, deploy). Caricato **sempre per primo**: zero esplorazione necessaria per questi fatti.
2. `AI_RESUME.md` — cross-project session memory entry point: what was in progress, last file touched, next step. See `references/session-memory.md`.
3. `AI_HANDOFF.md` (if taking over from another agent)
4. `AI_MISTAKE_REGISTER.md` — per-project mistake registry: pattern ricorrenti specifici del codebase, con peso e decadimento. Leggere se il task tocca le aree elencate.
5. `AI_CONTEXT.md`
6. `AGENTS.md`
7. `CLAUDE.md`
8. `AI_STRUCTURE.md` (only if task touches modules or contracts)
9. `AI_DECISIONS.md` (only if current decision crosses past one)
10. `README.md` (only if previous ones insufficient)

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
- **Proxmox hardening / server security checklist** → `references/proxmox-security-checklist.md`
- **pentest esterno / scan homelab / nuclei / nikto / shodan** → `references/pentest-playbook.md`
- MCP integrations (GitHub/Linear/Slack/Notion/...) → `references/mcp-integrations.md`
- maintenance → `references/maintenance-compaction.md`, `references/compression-pass.md`, `references/skill-sync.md`, `references/improvement-log.md`, `references/release-notes.md`
- coordinator safety → `references/coordinator-safety.md`
- prompt caching (Anthropic API) → `references/prompt-caching.md`
- self-improvement → `references/self-improvement.md`, `references/reflexion-loop.md`
- auto-promoted rules (confirmed via dashboard /feedback) → `references/auto-promoted-lessons.md`
- drain / auto-curriculum / overnight maintenance → `references/background-drain.md`
- jarvis guardrails (circuit breaker, sandbox patching, fase 2 inbox/eventi) → `references/jarvis-guardrails.md`
- sandbox patching protocol (worktree + validate_patch.py loop) → `references/sandbox-patching.md`
- coordination log / sedimentation → `references/coordination-sedimentation.md`
- DAG pipeline of subagents → `references/pipeline-dsl.md`
- external routing opt-in → `references/external-routing.md`
- loading tuning → `references/progressive-loading.md`
- session memory / resume across machines / per-file memo → `references/session-memory.md`

## 6. Working loop

For non-trivial tasks: budget+model internally → minimal context → mini-plan if needed → small patches → targeted verification → short closure. Stop planning when next step is obvious.

After each non-trivial file edit: update `AI_HANDOFF.md` section "File toccati in questo task" with `path → one-line memo` (per-file working memory, last line = last touched file). See `references/session-memory.md`.

**Context rot** (Anthropic, 2026): la precisione cala all'aumentare dei token nel context. Se `turns > 8` oppure `token_burn > 120k`: prima scrivi stato corrente in `AI_HANDOFF.md`, poi suggerisci compaction ("apriamo un nuovo task?"). Lo stato va salvato **prima** della compaction, non dopo.

### 6.5 In-Flight Scope Drift Check

Solo su trigger (non ogni 3 turni): utente cambia obiettivo dichiarato, oppure prima di una delega a subagente. Calcola drift score tra brief originale e lavoro completato.

**Thresholds**:
- 0.0–0.3: ✅ ON_TRACK — continua
- 0.3–0.6: ⚠️ DRIFT_WARNING → riallinea il piano in una riga, chiedi conferma utente prima di procedere
- >0.6: 🛑 HARD_DIVERGENCE → stop immediato, mostra divergenza all'utente, attendi conferma esplicita prima di qualsiasi azione

**Script**: `scripts/scope_drift_detector.py` (calculates score with file divergence heuristic, category shift, token burn, semantic divergence).

**Agent monitor** (v1.1.0): for non-trivial task (>2h, >5 files), call `scope-verifier` agent (Sonnet) every 3 turns. Provides independent verdict: ON_TRACK, DRIFT, DIVERGE with score and suggestion. For small tasks, inline drift detector sufficient.

**Log**: add to coordination-log the `drift_check` section with score, severity, reason. See `references/in-flight-scope-monitor.md`.

**Store plan at 200k**: quando il token count si avvicina a 200k, scrivere il piano corrente in `AI_HANDOFF.md` prima di delegare ai subagenti — garantisce coerenza su task lunghi (pattern Anthropic multi-agent research, 2026).

## 7. Output economy

Default:

```
Done: <concise action>
Verify: <how user checks>
```

Details only for: risks, non-obvious choices, blockers, user actions. When user must configure/choose/confirm/pay/test, add a `For you:` section.

**Token self-discipline (sempre attiva, non solo se richiesto):**
- Azioni non ambigue ("committa", "installa", "fixa") → esegui subito, nessuna conferma intermedia. Un solo blocco di tool call, non sequenze di status→diff→add→commit separate.
- Contesto sessione alto (>100k token visibili) → preferire Bash one-liner, non Read su file già noti, non re-leggere file appena editati.
- Non terminare con riepilogo se l'azione era ovvia. "Tutto pulito" dopo un git status non vale un turno da 4%.
- Routing hint Haiku/Explore → se il task lo permette, rispondere inline senza escalare a tool pesanti.

**Activation announcement**: on first turn of non-trivial session (classified category, budget chosen), open with single line like: `🛠 Skill: digital-claude · cat:<category> · budget:<mode>`. Only first line, no extra preambles. Skip to fast path.

**Model mismatch warning**: immediately after the activation line, if main agent is plain `opus` (not `opusplan`) AND category is `modifica`/`domanda`/`ops`, emit: `⚠ Main agent: Opus fisso — considera \`/model opusplan\` (Sonnet in esecuzione, Opus solo in plan mode, ~3× risparmio).` Skip if already on `opusplan`, `sonnet`, or `haiku`. Skip if category is `nuova_app`, `audit`, or `skill_improvement`.

Complete rules: `references/response-economy.md`.

## 8. Decision gates and risk

Before risky or irreversible actions (delete, force-push, DB modification, migrations, dependency removal, secrets), stop and ask.

Confidence: high → proceed; medium → verify/specialist; low → ask/red team. See `references/decision-risk-gates.md`.

**Ambiguous scope**: if task is vague, mixes multiple goals, or user is non-programmer with open technical choices, activate protocol in `references/scope-checkpoint.md` before writing code.

## 9. Specialists

Sub-agent only if risk or time saved justifies token cost. **Never parallelize by default**: cost grows non-linearly with agent count.

**Activate** for: wide cross-file search, second opinion, independent slice, wide audit. **DO NOT activate** for: <3 files, local fix, copy change, single-fact lookup checkable by main.

**Anti-pattern spawn eccessivo** (Anthropic warning): Claude Opus 4.x tende a spawnare subagenti anche per task sequenziali o edit singolo file. Gate 1-5 sono il freno — rispettarli anche quando sembra "utile" delegare.

**Nested subagents** (Claude Code ≥2.1.172, depth ≤5): un subagente con tool `Agent` può spawnare a sua volta subagenti. Ogni livello moltiplica i token ~7×/ramo — usa solo per pattern già previsti (es. `mar-reviewer` con 3 reviewer + aggregatore), default depth 1.

In Claude Code: tool `Agent` with `subagent_type` — list depends on environment, see `references/specialist-agents.md`. Self-contained briefing: objective, minimal context, format. Never "you decide".

**Escalation subagente fallito**: se un subagente fallisce o restituisce output insufficiente → 1° retry con contesto aggiuntivo; se fallisce ancora → escalation al modello superiore (haiku→sonnet→opus); se fallisce a opus → stop e chiedi all'utente.

**Return format obbligatorio per subagenti**: max 10-15 righe. Struttura: file toccati · esito · prossimo passo. Dettagli verbosi → scrivi su file e restituisci solo il path. Un subagente che torna 50 file con snippet brucia tutto il risparmio della delega.

Profiles: `references/role-profiles.md`, `references/specialist-agents.md`, `references/qa-test-agent.md`.

### 9.1 When to parallelize (v1.1.0)

**Parallel swarm** (launch 2-3 agents simultaneously) only if all 4 conditions true:

1. **Independent tasks** — none depends on other's output
2. **Non-overlapping file set** — no file touched by 2+ agents
3. **Budget available** — `tokens_residual > (cost_A + cost_B) * 1.5`
4. **Both completable <1 session**

Default: sequential. See `recipes/parallel-swarm.md` for examples and anti-patterns.

### 9.2 Delegation brief quality (code tasks)

When briefing `code-implementer` or `code-debugger` for functions >20 lines, SQL queries, or React components, include explicitly in the prompt:
- Null/undefined: ogni prop required è garantita? ogni array può essere vuoto?
- Async: ogni `await` ha error boundary o è in try/catch del chiamante?
- Tipi: confronti cross-layer usano stesso tipo (cast esplicito se necessario)?
- SQL: ogni subquery correlata su tutti i campi di raggruppamento, mai interpolazione diretta di input utente
- Leggere `AI_MISTAKE_REGISTER.md` se il task tocca aree a rischio noto nel progetto
- Tool descriptions: anche piccole precisazioni alle descrizioni degli strumenti producono miglioramenti drammatici (Anthropic SWE-bench, 2026) — curare ogni parola nel `description:` quando si definisce un nuovo tool o MCP.

**Briefing compatto per subagenti**: usare `AI_SCORE.md` (skill dir) come contesto comportamentale invece di incollare SKILL.md intero. Risparmio ~2500 token per delega.

## 10. Handoff between agents

Two levels:

- **between different agents** (separate sessions, other tools): shared files in repo (`AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AI_DECISIONS.md`, `AI_AGENT_LOG.md`, `AI_HANDOFF.md`).
- **between sub-agents same session**: don't talk directly, coordinator is router. Short tasks: pass result of A in prompt of B (filtered). Long tasks: use `AI_HANDOFF.md` as bulletin board. Resume active agent: `SendMessage`.

When taking over read `AI_HANDOFF.md` first. Update it after non-trivial modifications. Durable decisions → promote to `AI_DECISIONS.md`.

Details: `references/agent-handoff.md`, `references/cross-agent-handoff-template.md`.

## 11. Definition of Done

Task closed when: behavior handled, files touched limited to task, relevant checks executed (or skip reason declared), final output short. For UI/functional at medium/high risk: user confirms in plain language + evaluates Playwright screenshot.

**Pre-close checklist (run mentally before every "done"):**
- Side effects applied? (build, restart, reload, migration, config push)
- Verified working? (curl, systemctl status, browser check — not just "should work")
- User can actually see/use the change right now without extra steps?

If any answer is no → do it, don't delegate it.
- Session memory saved? Update `## State` + `## Next Step` in `AI_HANDOFF.md`, then run `python scripts/update_ai_resume.py <project_root>` so `AI_RESUME.md` reflects the latest state for the next session or machine.

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
- (8×) Spezzare in commit atomici per feature (scaffolding base → chat → jobs → terminal → sync) riduce il rischio di rollback e semplifica la review.
- (155×) Quando si aggiunge un nuovo enum al sistema (categoria/stato), allineare subito tutti i punti — DB, label UI, colori, regex, docs — prima di chiudere il task. Vedi §1.6 per checklist dettagliata.

## 15. Bug rescue

Reproduce with minimal reads → propose fix if cause non-obvious → update `AI_AGENT_LOG.md` if recurring pattern.

**State cause before fixing**: per ogni fix non banale (causa non autoevidente, es. non un typo/import mancante), scrivi una riga `Hypothesis: <X causa <sintomo>>` prima di editare. Niente ipotesi = niente fix.

**Same-hypothesis guard**: prima di un 2° tentativo, verifica se punta alla stessa hypothesis del fix fallito. Se sì e non è stata falsificata da nuova evidenza (log/assert) → STOP, non applicarlo: falsifica l'ipotesi o cambiane una. Conta come tentativo verso l'escalation sotto.

**Error delta check**: dopo ogni tentativo, confronta l'errore prima/dopo (messaggio, riga, stack frame). Identico → il fix ha mancato il bersaglio, ri-localizza la causa. Diverso (anche se ancora fallisce) → progresso, continua sulla nuova pista invece di tornare alla precedente.

**Escalation modello main agent dopo fix falliti**: se 2 fix consecutivi non risolvono lo stesso bug riportato dall'utente, fermati prima di un terzo tentativo. Riassumi in 1-2 righe i tentativi falliti e suggerisci esplicitamente `/model opus` per il main agent (vedi §3 "Main agent: chosen by user, not changeable by skill"). Non riprovare con lo stesso modello su un loop.

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
