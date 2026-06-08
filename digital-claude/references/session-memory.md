# Session Memory (cross-project, cross-machine)

## Why (no hooks)

Memory lives in **versioned text files inside the project repo** — portable via git/syncthing.
Works identically on LXC (SSH) and VS Code on Windows. No xattr, no /dev/shm, no settings.json dependency.

## Files used (no new files)

| File | Role |
|---|---|
| `AI_RESUME.md` | Synthetic state of the last session: goal, branch, last commit, latest work, next step |
| `AI_HANDOFF.md` | Current working memory: state, per-file memos, next action |
| `AI_AGENT_LOG.md` | Durable lessons (not volatile session state) |

## On start (capacity 1)

1. If `AI_RESUME.md` exists → Read it. Extract: Current State, Latest Work, Next Step, last file touched.
2. If Next Step references `AI_HANDOFF.md` → Read it for per-file memos.
3. Announce to user: *"Riprendendo da: [Next Step]. Ultimo file: [last file]."*

**Trigger rule**: apply even for seemingly small tasks — if `AI_RESUME.md` exists, one Read gives full continuity at minimal token cost.

## During work (capacity 2)

After each non-trivial file edit, Edit `AI_HANDOFF.md` → section `## File toccati in questo task`:

```
- src/app/page.tsx → aggiunto componente HeroSection
- src/lib/pricing.ts → corretti prezzi Haiku (era 6× sovrastimato)
```

- Add or update the line for the file (one line per file, overwrite if already present).
- Last line in the list = last touched file → session entry point next time.
- Update `## Stato` with current progress in one sentence.

## On session end (capacity 3)

1. Edit `AI_HANDOFF.md`:
   - `## Stato` → short summary of what was done
   - `## Prossimo passo` → concrete next action
2. Run: `python scripts/update_ai_resume.py <project_root>`
   (regenerates `AI_RESUME.md` from git + AI_HANDOFF.md sections)
3. Durable lesson → `AI_AGENT_LOG.md`

## Cross-machine propagation

- No absolute paths hardcoded. `update_ai_resume.py` uses git + relative Path → cross-OS.
- To propagate skill changes to Windows: `git commit && git push` on this LXC, then on Windows: `git pull && python scripts/sync_skill.py`.

## What NOT to use

- `/dev/shm/jarvis_state.json` — volatile, LXC-only, lost on reboot
- `xattr` (setfattr/getfattr) — Linux-only, not portable, not versioned
- `reports/projects-state.json` inside the skill — lives on the machine, not the project
