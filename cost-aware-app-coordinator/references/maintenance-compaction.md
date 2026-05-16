# Maintenance And Compaction

Use this reference when improving the skill itself, consolidating versions, or deciding whether to stop.

## Keep

Keep rules that:

- change behavior;
- prevent repeated mistakes;
- reduce token cost;
- improve safety for irreversible or high-risk work;
- provide reusable templates.

## Move

Move detail out of `SKILL.md` into a reference when:

- it is only needed for one task type;
- it is a template;
- it is a long checklist;
- it duplicates a compact core rule.

## Compress

Compress older logs when they become noisy:

- preserve current behavior;
- preserve user approvals;
- summarize old version entries by theme;
- keep the latest meaningful changes explicit;
- remove diary-like detail.

## Delete Or Merge

Delete or merge rules when:

- a newer gate fully covers them;
- they repeat another section;
- they encourage reading more files without changing decisions;
- they add style preference but no operational value.

## Stop Criteria

Stop improving when the next idea is:

- cosmetic only;
- speculative;
- not testable in behavior;
- likely to increase token cost more than it saves;
- better handled by using the skill on real projects first.

## Auto-Improvement Runs

When the user asks to auto-improve until no improvements remain:

1. List candidates internally.
2. Keep only candidates that change behavior, reduce repeated error, reduce token cost, or improve safety.
3. Merge related candidates into one compact version.
4. Validate, sync, release, then reassess once.
5. Stop and report when remaining ideas fail the stop criteria.

Do not create endless version bumps. One or two compact releases are usually enough before real project usage should provide new evidence.

## Cheap Skill Review

For skill audits or "is this skill ok?" requests, start with the cheap path:

1. Run the skill validator.
2. Check frontmatter, folder structure, referenced files, line counts, and installed-copy drift.
3. Read full `SKILL.md` or references only when validation fails, behavior is unclear, or a qualitative review is requested.
4. Prefer targeted `rg` checks for TODOs, duplicate rules, stale references, and noisy sections.

This keeps maintenance accurate without spending the whole context on files that already pass structural checks.
