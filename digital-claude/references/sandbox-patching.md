# Sandbox Patching — Linter Coercitivo

Fase 1B del piano Jarvis Guardrails (implementato 2026-06-07).

## Principio

Gli agenti non toccano i file di produzione direttamente. Lavorano in un **git worktree isolato** (nativo Claude Code, `isolation:"worktree"`). Un gate deterministico valida la patch prima del merge. Solo le patch che superano i gate raggiungono il branch di lavoro; l'utente non vede mai output rotto.

Nessun runtime custom: si riusa `Agent(isolation:"worktree")` + `validate_patch.py` + i tool-check già esistenti (tsc, run_tests.py, validate_skill.py).

## Loop standard (orchestrato dal main agent)

```
1. Agent(subagent_type="code-implementer", isolation:"worktree", prompt=<task>)
   → Il subagente modifica file nel worktree isolato; ritorna (worktree_path, branch).

2. python3 scripts/validate_patch.py <worktree_path> --json-only
   → JSON: {"passed": bool, "gates": [{"gate": str, "ok": bool, "output": str}]}

3a. Se passed=true  → merge worktree su branch corrente; l'utente vede il diff pulito.
3b. Se passed=false e tentativi < 3
      → SendMessage all'agente (stesso ID, contesto intatto) con gli errori di gates[].output.
        L'agente corregge nello stesso worktree; torna al passo 2.
3c. Se 3 tentativi falliti → freeze (niente merge), report all'utente.
```

Ogni retry opera nello stesso worktree (contesto agente intatto). Il gate non "decide" cosa sistemare — rimanda l'errore grezzo all'agente, che ha già tutto il contesto.

## Gate rilevati automaticamente da validate_patch.py

| Progetto | Gate |
|---|---|
| `package.json` + `tsconfig.json` | `tsc --noEmit` |
| `package.json` | `npm run lint --if-present` |
| Next.js (`next.config.*`) | `npm run build --if-present` |
| `scripts/run_tests.py` | `python scripts/run_tests.py` |
| `SKILL.md` + `scripts/validate_skill.py` | `python scripts/validate_skill.py` |

Se nessun gate rilevato: `passed=true` (no gate = no blocco).

## Quando attivare il protocollo

- Task che modificano **≥3 file** di produzione → sempre worktree + validate
- Task su file critici (`src/app/api/**`, `SKILL.md`, schema DB, auth) → sempre
- Task fast-path (<2 file noti, scope ovvio) → opzionale (overhead non vale)

## Gate coercitivo PreToolUse (opzionale, default OFF)

`scripts/delegation_gate.py` può bloccare `Edit/Write` diretti del main agent su glob protetti finché non è attivo `CLAUDE_SANDBOX=1` (marker worktree). **Non attivato di default** per non irrigidire i task fast-path. Da valutare dopo aver validato il loop manuale.

## Files

- `scripts/validate_patch.py` — eseguibile standalone + importabile
- `references/sandbox-patching.md` — questo file (protocollo)
