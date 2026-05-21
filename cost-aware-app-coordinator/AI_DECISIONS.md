# AI Decisions

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
