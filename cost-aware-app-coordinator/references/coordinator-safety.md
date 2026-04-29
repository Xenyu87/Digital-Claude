# Coordinator Safety

Use this reference when the coordinator might be wrong and the cost of being wrong matters.

## Self-Check Gate

Before medium/high-risk implementation or final answer, ask:

- Did I classify the task and risk correctly?
- Did I read the right context files?
- Did I miss auth, data, migration, deploy, performance, or QA risk?
- Are frontend and backend contracts aligned?
- Are checks proportional to the touched surface?
- Is any action irreversible, paid, external, or production-impacting?

Keep the self-check internal unless it changes the decision or leaves residual risk.

## Decision Confidence

- High: evidence is local, reversible, and checks are clear.
- Medium: assumptions exist or shared behavior changed; verify or use a specialist.
- Low: missing product/data/auth/deploy decision, irreversible risk, or unclear failure; ask the user or run Red Team.

## Red Team Agent

Use Red Team only for high-risk work or low-confidence decisions.

Ownership:

- find what the coordinator may be missing;
- challenge assumptions;
- identify missing specialists;
- identify insufficient checks;
- identify irreversible or hidden external risk.

Output:

```text
Concern:
Evidence:
Impact:
Suggested action:
Confidence:
```

Rules:

- Keep Red Team bounded to the plan or diff.
- Do not let Red Team rewrite implementation.
- Coordinator decides whether to accept, reject, or ask the user.

