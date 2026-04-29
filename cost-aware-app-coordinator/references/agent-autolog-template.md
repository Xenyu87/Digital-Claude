# Agent Autolog Template

Use this template to create `AI_AGENT_LOG.md` only when real waste or mistakes need to be prevented from repeating.

Do not log normal work, status updates, or every command. This is an error and waste memory, not a diary.

```markdown
# AI Agent Log

Last compacted: YYYY-MM-DD

## Active Patterns

- Pattern:
  - Trigger:
  - Better rule:

## Recent Events

- Date:
  - Event:
  - Cause:
  - Impact:
  - Fix:
  - Future rule:

## Do Not Repeat

- [Specific behavior that wasted tokens, caused rework, or increased risk]
```

Log when:

- too many files were read before a routing decision;
- an unnecessary agent, specialist, or broad test was used;
- a required QA/security/data/deploy check was missed;
- the user corrected a repeated assumption or verbosity problem;
- stale context caused wrong work;
- final answers or handoffs became longer than useful.

Keep entries actionable:

- Bad: `Worked on auth and made mistakes.`
- Good: `Read route tree before AI_STRUCTURE.md; next time read AI_CONTEXT.md then route hint first.`
