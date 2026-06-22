# Piano Evoluzione Digital-Claude — Giugno 2026

Generato: 2026-06-22 | Fonti: web research (40 finding) + gap analysis (728 sessioni)

## Stato attuale vs obiettivo

| Metrica | Ora | Obiettivo |
|---------|-----|-----------|
| Autonomia | 40% | 80% |
| Self-improvement | 10% | 70% |
| Qualità output | 50% | 80% |
| Costo/sessione | alto | -40% |
| Context uso | 40% | 80% |

## Livelli

### LIVELLO 0 — Fix critico canale dati (prerequisito di tutto)
**Finding**: 728 sessioni, lesson=null 100%, agents_used=[] 100%, duration_s=0.
Il loop self-improvement è architettonicamente completo ma il canale dati è vuoto.

Fix:
1. `duration_s` — calcola da timestamp SessionStart/Stop (env Claude Code)
2. `agents_used` — PostToolUse hook traccia chiamate Agent in /tmp/session_agents_{ID}.json
3. `lesson` — propose_lesson.py scrive in AI_AGENT_LOG.md invece di stampare a schermo

Effort: 1 giorno | Impatto: sblocca drain auto-curriculum, reflexion loop, SkillOpt

### LIVELLO 1 — Quick wins (2-4h ciascuno)

| ID | Upgrade | Effort | Impatto chiave | Stato |
|----|---------|--------|----------------|-------|
| 1A | Context Mode MCP | S | -63x token context (315KB→5KB) | ⏳ skip — package non pubblico |
| 1B | context_budget_scan hookato | S | stop context rot silenzioso | ⏳ skip — script fa altro (project scan) |
| 1C | cache_bundle_builder SessionStart | S | -15% costo sessioni brevi-medie | ✅ 2026-06-22 |
| 1D | Cloud Routines drain 24/7 | S | drain affidabile anche se LXC giù | ⏳ skip — drain ha dipendenze locali DB |
| 1E | Agent Hook verifier (statico) | S | +35% qualità — avvisa su SKILL/JSON/Python | ✅ 2026-06-22 |

### LIVELLO 2 — Evoluzioni strutturali (1-3 giorni)

| ID | Upgrade | Dipendenza | Impatto chiave |
|----|---------|------------|----------------|
| 2A | SkillOpt loop | L0 | +23% qualità skill automatica |
| 2B | ACE playbook evolving | L0 | CLAUDE.md che si auto-migliora |
| 2C | Supermemory MCP | — | memoria cross-sessione vera (+conflict res) |
| 2D | Morning briefing drain | L0 | da reattivo a proattivo (Telegram mattina) |

### LIVELLO 3 — Frontiera (L effort)

| ID | Upgrade | Impatto |
|----|---------|---------|
| 3A | Dynamic Workflows | 100 subagenti paralleli, drain in 30s |
| 3B | EvoSkill | apprende da traiettorie fallite |

## Roadmap

```
Settimana 1: L0 (gg 1-2) → 1A+1B+1C (gg 3) → 1E (gg 4) → 1D (gg 5)
Settimana 2-3: 2A, 2D, 2C
Settimana 4+: 2B, 3A, 3B
```

## Fonti chiave
- Context Mode MCP: mindstudio.ai/blog/context-mode-claude-code-315kb-to-5kb-session-compression
- SkillOpt: github.com/microsoft/SkillOpt (arxiv 2605.23904)
- ACE framework: arxiv.org/pdf/2510.04618
- EvoSkill: github.com/sentient-agi/EvoSkill
- Cloud Routines: code.claude.com/docs/en/scheduled-tasks
- Agent Hooks verifier: code.claude.com/docs/en/agent-sdk/hooks
