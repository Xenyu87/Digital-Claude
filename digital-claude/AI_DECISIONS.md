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
