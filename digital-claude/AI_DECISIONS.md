# AI Decisions

## 2026-05-22 - Lavagna Visual Regression

- Decision: use Playwright for dashboard-level Lavagna checks.
- Why: Python smoke tests can confirm generated markers, but cannot verify React Flow renders, toggles UI child nodes, or remains usable after frontend changes.
- Setup: `@playwright/test`, Playwright Chromium, `playwright.config.js`, `tests/visual/blueprint-board.spec.js`.
- Fixture: `tests/fixtures/visual-blueprint-app` contains four buttons and one chart so button/chart scanner behavior and canvas expand/collapse are deterministic.
- Command: `npm run test:visual`.
- Environment note: minimal Linux hosts need `npx playwright install chromium` and `npx playwright install-deps chromium`; restricted sandboxes may need elevated permission for local server sockets.

## 2026-05-23 - Lavagna Frontend Preview

- Decision: add a side-by-side frontend preview to the Lavagna.
- Why: graph nodes are much more useful when the user can see the UI element or component they represent.
- First slice: prefer configured live URLs from `app-blueprint.json` (`frontend_preview_url` or `preview_url`), otherwise render a generated preview directly in React from scanner nodes. `/frontend-preview?project=...` remains compatibility/debug output.
- Interaction: canvas node selection highlights generated preview elements; live iframe previews receive `highlight-node` messages when supported.
- Constraint: live iframe previews may be blocked by app frame policy or auth. The generated preview is the reliable fallback and the Playwright target.

Record durable choices only.

## Decisions

- Decision: `AI_RESUME.md` is the first file to read in a new project chat.
  Reason: it gives latest state, git status, recent commits, and next step with minimal token cost.
  Impact: agents should not scan the repo before checking this file when present.
  Revisit when: it becomes stale often or exceeds about 80 lines.

- Decision: dashboard reorganization should start with client-side tabs/sections, not separate server routes.
  Reason: existing dashboard is generated as one HTML report and React Flow is mounted inside it; tabs are lower risk.
  Impact: forms/actions can keep existing endpoints while UI becomes less cluttered.
  Revisit when: dashboard needs deep linking, auth, or multi-user hosting.

- Decision: persistent runner remains safe/report-only unless explicitly redesigned.
  Reason: background AI execution needs kill switches, budgets, provider configuration, and approval gates.
  Impact: runner UI can configure intent and queue metadata, but does not grant code-writing autonomy.
  Revisit when: a dedicated runner architecture is approved.

- Decision: the Lavagna should guide app work, not expose raw scanner output by default.
  Reason: raw nodes such as toolbar buttons, scripts, and incidental endpoints make the board feel complicated and reduce trust.
  Impact: default board views should prioritize focus, flows, real issues, scanner hypotheses, actions, and evidence; technical nodes move to diagnostics or drill-down.
  Revisit when: users need a developer-only graph mode as the primary workflow.

## 2026-06-22 - Stop Hook Async Collaboration Pattern

- Decision: non implementato.
  Reason: nessun use case attuale di pipeline multi-agente con sincronizzazione via DB. Effort M senza beneficio misurabile ora.
  Pattern: Stop hook controlla flag condiviso su DB, blocca o permette stop in base a dipendenze pendenti tra agenti paralleli (fonte: DEV Community agent-room).
  Revisit when: si avvia una pipeline con 2+ subagenti che devono coordinarsi su output condivisi.

## 2026-06-22 - Drain pipeline: fase parallela prima di sequenziale

- Decision: drain.py esegue prima una fase parallela (ThreadPoolExecutor max_workers=4) per step indipendenti, poi fase sequenziale per step che scrivono SKILL.md o dipendono da output precedenti.
- Why: i 7 step paralleli (analyze_tool_errors, decay_mistake_register, detect_session_anomalies, detect_dead_rules, run_ai_news_intake, run_morning_briefing, run_evoskill_lite) non condividono stato scrivibile, quindi possono girare in concorrenza sicura. I 15 step sequenziali che toccano SKILL.md restano serializzati per evitare conflitti.
- Trade-off: max_workers=4 è conservativo per non saturare CPU su LXC con risorse limitate. Alzarlo richiede profiling.
- Revisit when: si aggiungono step paralleli che scrivono su file condivisi, o si misura contention su SKILL.md.

## 2026-06-22 - verify_edit.py come PostToolUse command hook

- Decision: validazione di SKILL.md (line count ≤450), JSON syntax, Python syntax avviene tramite hook PostToolUse command (non agent), eseguito su ogni Edit/Write/MultiEdit.
- Why: un agent hook avrebbe latenza maggiore e costo token per ogni edit; un command hook è sincrono, zero-costo, e sufficiente per check strutturali.
- Trade-off: se verify_edit.py lancia un'eccezione uncaught, exit non-zero può bloccare l'Edit. Il codice deve essere robusto e fare exit 0 in caso di errore interno non critico.
- Revisit when: le validazioni diventano semantiche (non solo strutturali) e richiedono un LLM.

## 2026-06-22 - evoskill_lite status=frontier

- Decision: evoskill_lite estrae failure pattern da sessioni outcome=failed/partial e li scrive in `reports/failure-patterns.jsonl`, ma non modifica SKILL.md autonomamente.
- Why: raccogliere dati prima di agire riduce il rischio di degradare SKILL.md con pattern rumorosi. La propagazione richiede una soglia minima da definire manualmente.
- Trade-off: rallenta il ciclo di miglioramento, ma protegge la stabilità della skill.
- Revisit when: si accumula un corpus sufficiente di failure pattern validati e si definisce una metrica di confidenza.
