# Specialist Agents

Use specialist agents only when the trigger is concrete. They are available tools, not default participants.

## Selection Rule

Spawn a specialist when:

- the touched surface matches its trigger;
- the coordinator can give clear ownership;
- the expected finding would change implementation, verification, or release risk;
- the extra token cost is justified by risk or rework avoided.

Do not spawn specialists for small local edits, simple copy changes, or speculative concerns.

## Security/Auth

Trigger:

- auth, roles, permissions, sessions, protected APIs, secrets, private data, abuse/rate limits.

Output focus:

- server-side enforcement;
- data exposure;
- unsafe errors;
- missing auth tests or checks;
- residual security risk.

## UX/Product

Trigger:

- new app, first usable slice, onboarding, forms, complex workflows, unclear product direction.

Output focus:

- user goal;
- friction;
- missing states/copy;
- confusing hierarchy;
- product tradeoffs requiring user decision.

## Data/Migration

Trigger:

- schema changes, migrations, seed data, import/export, delete/archive, ownership lifecycle.

Output focus:

- migration safety;
- rollback;
- compatibility;
- data loss risk;
- validation and invariants.

## DevOps/Release

Trigger:

- deploy, CI/CD, build config, env vars, secrets, hosting, production runtime, release prep.

Output focus:

- build/deploy blockers;
- missing env or secrets;
- release checklist;
- rollback and observability;
- residual operational risk.

## Performance

Trigger:

- large lists, expensive queries, dashboards, media-heavy pages, realtime, slow tests/builds, bundle risk.

Output focus:

- likely bottleneck;
- measurement or smoke check;
- cheap optimization;
- risk if deferred.

## Output

```text
Specialist:
Trigger:
Files or flows inspected:
Findings:
Required changes:
Checks:
Residual risk:
```

Keep output compact and evidence-based.

