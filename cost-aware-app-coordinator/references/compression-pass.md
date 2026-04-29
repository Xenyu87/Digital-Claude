# Compression Pass

Use this reference when text is too long and must keep meaning with fewer tokens.

Inspired by caveman-style compression: remove scaffolding, keep semantic payload.

## Compress

- Remove filler, hedging, repeated context, and process narration.
- Prefer nouns, verbs, file paths, decisions, risks, checks.
- Replace paragraphs with compact bullets or `Outcome / Changed / Checked / Risk`.
- Keep only details that change action, risk, verification, or future decisions.
- Merge duplicate caveats into one residual risk.

## Preserve

Do not over-compress:

- security fixes;
- breaking changes;
- data migrations;
- auth/permission decisions;
- production/deploy risk;
- irreversible or destructive actions;
- user-facing product decisions;
- future-debug context.

## Apply To

- final answers;
- agent handoffs;
- QA/specialist outputs;
- `AI_CONTEXT.md`, `AI_STRUCTURE.md`, `AI_DECISIONS.md`;
- commit and PR descriptions;
- release notes and improvement logs.

## Output Check

After compression, confirm:

- decision still clear;
- risk still visible;
- checks still named;
- next action still obvious;
- no critical context removed.

