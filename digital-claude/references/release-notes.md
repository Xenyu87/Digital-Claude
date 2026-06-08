# Release Notes

Note di rilascio sul comportamento osservabile della skill. Pensate per chi la usa, non per chi la sviluppa.

## Formato

```
## vX.Y.Z — YYYY-MM-DD
### Aggiunto
- ...
### Cambiato
- ...
### Rimosso
- ...
### Note di migrazione
- ...
```

## v1.3.0 — 2026-06-07
### Aggiunto
- **Circuit Breaker Finanziario** (`scripts/budget_guard.py`): ogni subprocess `claude` spawnato dalla skill ora gira con tripla guardia — `--max-budget-usd` nativo (hard kill della CLI), `--max-turns`, timeout wall-clock. Al breach: log in `reports/circuit-breaker.jsonl` + alert in `/api/skill-feedback`. Wired in `drain.py` (10¢/task) e `supreme_court.py` (5¢/giudice).
- **Sandbox Patching** (`scripts/validate_patch.py`): gate deterministici (tsc/lint/build/pytest/validate_skill) eseguiti su worktree isolato prima del merge. Solo le patch che compilano raggiungono il branch. Protocollo: `references/sandbox-patching.md`.
- **Pricing per-modello** (dashboard `pricing.ts`): `PRICES_BY_MODEL` con tariffe reali per haiku/sonnet/opus. I costi mostrati in `/economy` ora riflettono il modello effettivamente usato; i task haiku costano ~15× meno di prima nell'interfaccia.

### Cambiato
- `supreme_court.py`: ogni agente usa `run_guarded()` invece di `subprocess.run` cieco — cap 5¢, max 3 turni, timeout 45s.
- `drain.py resolve_tbd_lessons`: spawn `claude` sostituito con `run_guarded()` — cap 10¢, max 4 turni.

## v1.2.0 — 2026-06-06
### Aggiunto
- **Reasoning Trap (§3)**: vietato `thinking: adaptive` e reasoning esteso per decisioni tool-routing. Fonte: arxiv 2510.22977. Riduce tool hallucination in task agentici.
- **Feedback dashboard→skill**: `inject_lessons.py` legge `GET /api/skill-feedback?status=pending` e inietta candidati di promozione e routing insight come `<system-reminder>` a SessionStart.
- **Efficacy tracking lezioni**: colonna `lessons.status` (pending/applied/ineffective), endpoint `PATCH /api/lessons`, controlli UI per-lezione.
- **Azione sync-skill**: aggiunta all'allowlist QuickActions, eseguita via `/api/actions/run` (no shell injection). Bottone visibile in `/skill-version` quando c'è drift.
### Note di migrazione
- Applicare lo snippet SQL in `supabase/schema.sql` (sezione "Migration: lesson efficacy + skill_feedback") sul DB Neon prima di usare le nuove feature.

## v1.1.0 — 2026-05-22
### Aggiunto
- **Coordination sedimentation**: log JSONL strutturato per ogni task chiuso (`scripts/log_coordination.py`, hook `scripts/hooks/coordination_log.py`). Schema: ts, task_id, project, category, tokens, cost_usd, outcome, lesson.
- **MAR Reviewer** (`~/.claude/agents/mar-reviewer.md`): audit cross-modulo con 3 reviewer Sonnet paralleli (security/perf/readability) + aggregatore Haiku. Ricetta `recipes/mar-audit.md`. Trigger automatico in `specialist-agents.md` per diff >5 file.
- **Debate scope**: `scope-checkpoint.md` ora include il protocollo debate a 2 persona Haiku (scope minimo vs espanso) prima di interrompere l'utente. Costo ~$0.03.
- **Background drain** (`scripts/drain.py`): manutenzione notturna automatizzata (TBD, errori, compaction, validazione drift). Timer systemd in `assets/scripts/drain.timer|service`. Log in `~/.claude/projects/<slug>/memory/drain-log.jsonl`.
- **Auto-curriculum settimanale** (domenica, flag `--curriculum-weekly` in drain): analisi coordination-log 7gg, propone voci `<auto-proposed-curriculum>` in `improvement-log.md`.
- **Pipeline DSL** (`references/pipeline-dsl.md`, `scripts/run_pipeline.py`): pipeline YAML con DAG di dipendenze tra subagent. Due ricette: `feature-with-tests.yml`, `bugfix-locked.yml`.
- **External routing opt-in** (`scripts/external_router.py`, `references/external-routing.md`): routing verso OpenRouter/DeepSeek, disabilitato di default, solo categoria ops, warning obbligatorio al primo uso.
- **Dashboard**: nuova tabella `coordination_log` (migration SQL), API `POST/GET /api/coordination-log`, pagina `/economy/patterns`, pagina `/drain`.
### Note di migrazione
- Applica migration SQL: `supabase/migrations/20260522_coordination_log.sql` sul DB Neon.
- Opzionale: installa hook Stop `scripts/hooks/coordination_log.py` in `~/.claude/settings.json`.
- Opzionale: attiva timer drain (`systemctl --user enable --now drain.timer`).

## v0.1.0 — 2026-04-29
### Aggiunto
- prima release: skill con 19 reference, validator, file `AI_*.md` per handoff multi-agente.

## v1.0.0 — 2026-05-17
### Aggiunto
- **Categoria `ops`** (sistema/infra) accanto a nuova_app/modifica/audit/bug_rescue/miglioramento_skill. Heuristic regex in `auto_log_task.py` la rileva da parole come `systemd|syncthing|ssh|lxc|porta|servizio|deploy|riavvia`.
- **`references/homelab-ops.md`**: reference operativo (mappa LXC/porte, comandi `systemctl`/`journalctl`/`ss`, pattern ricorrenti, anti-pattern). Caricato dal progressive loading quando il task tocca ops.
### Cambiato
- `scripts/auto_log_task.py` ora estrae dal jsonl: `duration_seconds` (delta primo/ultimo timestamp), `tool_calls_count` (entry con `content.type == "tool_use"`), `summary` (primo prompt utente, 160 char), `category` (euristica regex). Prima erano default fissi.
### Note di migrazione
- DB: `ALTER TABLE tasks DROP CONSTRAINT tasks_category_check; ADD CONSTRAINT tasks_category_check CHECK (category = ANY (ARRAY['nuova_app','modifica','audit','bug_rescue','miglioramento_skill','ops']));` — già applicato su Neon.
- Dashboard v0.0.8: vedi `dashboard-claude-coordinator/AI_HANDOFF.md`.

## v0.9.9 — 2026-05-16
### Aggiunto
- `scripts/auto_log_task.py`: parsa il jsonl di sessione Claude Code (`~/.claude/projects/<cwd-encoded>/<sessionId>.jsonl`), aggrega usage tokens (input/output/cache read/cache create), POST a `/api/log` della dashboard.
- Hook Stop globale chiama anche `auto_log_task.py` (insieme a `propose_lesson` e `check_version`).
### Note di migrazione
- richiede migrazione SQL su Neon (5 colonne `tasks`: vedi `skill-dashboard/AI_HANDOFF.md` v0.0.6).
- limite Claude Code: `category`, `duration`, `tool_calls` non sono esposti agli hook esterni → restano default. Il **costo è stimato** dai token coi prezzi Opus 4.x indicativi.

## v0.9.8 — 2026-05-15
### Cambiato
- `scripts/propose_lesson.py`: ora skippa silenziosamente quando il cwd è un repo di skill (marker: `SKILL.md` + `references/`). Le skill hanno già `improvement-log.md`/`release-notes.md`; non serve Reflexion meta sui propri commit di maintenance.
### Note di migrazione
- bug "meta-rumore" emerso da uso reale: ad ogni commit della skill il hook generava voce TBD vuota in `AI_AGENT_LOG.md` della skill stessa.

## v0.9.7 — 2026-05-15
### Aggiunto
- `scripts/hooks/pre-commit`: hook git versionato che lancia `run_tests.py` (validator + 26 test) prima di ogni commit alla skill. Blocca su fail.
- `scripts/install_hooks.py`: installer cross-platform (`python scripts/install_hooks.py` copia il hook in `.git/hooks/`).
### Note di migrazione
- una tantum: `python scripts/install_hooks.py` (già eseguito sul repo sorgente). Da ora ogni `git commit` esegue test+validator. Bypass eccezionale: `git commit --no-verify`.

## v0.9.6 — 2026-05-15
### Aggiunto
- `tests/` con pytest: 26 test (7 su `check_version` — copertura regressione bug v0.9.5, 7 su `propose_lesson` — filesystem + dedup TBD, 12 su `validate_skill` — frontmatter, heading, smoke).
- `scripts/run_tests.py`: wrapper che lancia validator + pytest in un comando solo.
- Subagent custom **qa-tester** (`~/.claude/agents/qa-tester.md`): il coordinator può ora delegare scrittura test a un agent specializzato (`Agent(subagent_type="qa-tester", ...)`).
### Note di migrazione
- richiede `pip install pytest` una volta (già fatto).
- esegui `python scripts/run_tests.py` prima di ogni commit alla skill.

## v0.9.5 — 2026-05-15
### Cambiato
- `scripts/check_version.py` e `/skill-status` command: la versione viene ora estratta come **semver max** (era prima match testuale, che ritornava sempre v0.1.0 perché in cima al file per ragioni storiche). Bug silenzioso: la dashboard mostrava `in_sync=true` su valori sbagliati anche con drift reale.
### Note di migrazione
- nessuna. La dashboard riceverà ora ping con versioni corrette al prossimo Stop hook.

## v0.9.4 — 2026-05-14
### Aggiunto
- slash command `/skill-status`: mostra stato skill in chat (versioni, drift, AI_*.md presenti, voci TBD, dashboard up/down, hook configurati). Alternativa rapida ad aprire dashboard.
- `references/scope-checkpoint.md`: protocollo "rispecchia → 2-3 scelte → primo step piccolo" per task ambigui o utente non programmer.
- §8 Gate decisionali rimanda al checkpoint quando lo scope è vago.

## v0.9.3 — 2026-05-14
### Aggiunto
- slash command `/newproject` (`~/.claude/commands/newproject.md`): crea scaffolding nuovo progetto dalla chat in italiano, senza comandi tecnici.
- §7 SKILL.md: annuncio attivazione su 1 riga (`🛠 Skill · cat · budget`) per sessioni non banali (salta in fast path).
- §16 SKILL.md: regola "Completamento voci TBD" — la skill compila in automatico al primo turno le voci `<TBD ...>` scritte dal hook nella sessione precedente.
### Cambiato
- `scripts/propose_lesson.py`: scrive direttamente in `AI_AGENT_LOG.md` del progetto attivo con placeholder `<TBD ...>` invece di stampare un template. L'utente non deve mai copiare/incollare.

## v0.9.2 — 2026-05-14
### Aggiunto
- `scripts/check_version.py`: confronta versione sorgente↔installata + POST `/api/skill-version` alla dashboard.
- Hook Stop globale chiama anche `check_version.py` accanto a `propose_lesson.py`.

## v0.9.1 — 2026-05-13
### Aggiunto
- `scripts/log_task.py`: POST best-effort verso skill-dashboard. Env: `SKILL_DASHBOARD_URL`.

## v0.9.0 — 2026-05-13
### Aggiunto
- `reflexion-loop.md` + `skill_library/` + `scripts/propose_lesson.py`: Reflexion + Voyager applicato alla skill.
- §16 SKILL.md: loop "incident → knowledge update" + skill library.

## v0.8.0 — 2026-05-13
### Aggiunto
- §19 Integrazioni MCP + `mcp-integrations.md` (GitHub/Linear/Slack/Notion/Filesystem con format `Server:tool`).
- README "Compatibilità": skill come standard aperto (Claude Code/Codex/Cursor/Gemini/Copilot).
### Cambiato
- validator: `SKILL_MAX_LINES` 350→450 (Anthropic best-practice è 500).
### Note di migrazione
- ora puoi citare tool MCP nei prompt (`GitHub:create_issue`, ecc.); i write su sistemi esterni sono gate hard.

## v0.2.0–v0.7.0 — 2026-05-02/13 *(archivio compatto)*
- v0.7: validator glob, specialist-agents.md, §4 AI_STRUCTURE/AI_DECISIONS condizionati, sync_skill include recipes
- v0.6: §0 Fast path; SKILL.md 307→190 righe
- v0.5: recipes/ (5), default-stacks, deploy-paths, visual-first-testing; §12 Step 0/2/3
- v0.4.1/v0.4: comunicazione sub-agent via AI_HANDOFF.md; selezione modello sub-agent auto
- v0.3.x: assets/templates/, sync_skill.py, validator frontmatter, evaluations/scenarios.md
- v0.2: §3 model selection, §6 working loop, §11 definition of done, progressive-loading.md


---
**Versionamento**: patch = fix no-behavior-change · minor = sezione/reference/ruolo · major = cambio default/rimozione. Una voce per release; solo ciò che un utente nota; refactoring in `improvement-log.md`.
