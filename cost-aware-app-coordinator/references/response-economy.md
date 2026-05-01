# Response Economy

Use this reference when answers, updates, or agent prompts are getting longer than the task needs.

## Defaults

- Keep budget mode, model policy, role, and skill name internal unless the user asks or a real user-visible cost/risk choice changes.
- Stay silent during routine work. Do not narrate reading, editing, testing, or successful routine steps.
- Send one short progress update only for sub-agents used, errors, blockers, risks, explicit status requests, or actions the user must take.
- Use compact plans only when they reduce risk or coordinate work.
- Summarize command output; do not paste it unless requested.
- Prefer one precise file link over a list of every related file.
- Do not explain routine edits as "I changed X because Y"; reserve reasons for risk, tradeoffs, blockers, or user decisions.
- Be most precise in `Da fare per te` items: commands to run, env vars to set, accounts to connect, manual checks, or choices needed.
- For non-programmer users, prefer `Come provarlo` over code details when the change is visual or functional.
- Do not announce design lens, implementation intent, files you are about to edit, checks you are about to run, or commit/push preparation unless the user must decide something.

## Progress Update Gate

Before sending an update while working, it must answer yes to at least one:

- Is the user blocked or needed?
- Is a sub-agent being used and should the user know cost/risk changed?
- Is there risk, destructive action, cost, credential, or external system impact?
- Did an error, failed check, or blocker occur?
- Did the user ask for status?

If not, keep working silently.

Forbidden routine updates:

- `Uso [skill] in modalita...`
- `Mi metto il cappello...`
- `Scelgo una struttura...`
- `Ora modifico...`
- `Aggiorno anche...`
- `I controlli sono puliti, faccio...`
- `Preparo un commit...`

Allowed important updates:

- `Uso un agente QA per verificare il flusso auth.`
- `Errore: build fallita su [check].`
- `Blocco: manca [env/credential/decision].`
- `Da fare per te: [action].`

## Final Answer Shapes

Small task:

```text
Fatto: [outcome]. Verifica: [check].
```

Medium task:

```text
Fatto:
- ...

Verifica:
- ...

Come provarlo:
- ... [1-3 plain steps only for user-facing behavior]

Da fare per te:
- ... [only if needed]
```

Review or audit:

```text
Findings:
- [severity] [file:line] [issue and impact]

Checked:
- ...

Residual risk:
- ...
```

## Compression Rules

- Remove background the user already knows.
- Replace process narration with the final decision.
- Delete routine reasons after completed work.
- Merge repeated caveats into one residual risk.
- Keep examples out unless the user asks or the format is hard to infer.
- Use exact limits when needed: sentence count, bullet count, files, or checks.

## When To Expand

Expand only for:

- high-risk decisions;
- unclear user goals;
- security, auth, payments, privacy, data loss, or production incidents;
- teaching requests;
- user action is required;
- user explicitly asking for detail.
