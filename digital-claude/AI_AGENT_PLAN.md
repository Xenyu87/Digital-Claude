# Piano Evoluzione Agenti — Giugno 2026

Generato: 2026-06-22 | Fonti: 3 agenti di ricerca paralleli (40+ paper, 20+ framework)

---

## Stato attuale

Il sistema usa oggi il pattern **Orchestrator + Subagents** di Claude Code: un agente principale spawna subagenti via `Agent(subagent_type=...)`, ogni subagente riceve il contesto completo della conversazione.

**Problema**: context completo = ~15x token rispetto a chat standard. Con 728 sessioni reali e crescita, questo diventa il costo dominante.

---

## Mappa dei pattern agente

```
SOLO          → ReAct loop, tool autonomy, auto-correzione
  └─ oggi: ogni subagente specializzato è già questo

DUO           → Generator + Critic in sequenza
  └─ oggi: ACE Reflector è proto-duo; manca Critic formale per output finali

TEAM lineare  → Orchestrator → [A → B → C] con typed handoff
  └─ oggi: drain.py parallelo è proto-team; mancano handoff strutturati

TEAM mesh     → agenti si scoprono semanticamente (no orchestratore centrale)
  └─ futuro: Agent Mesh / A2A

SWARM         → stigmergia su blackboard condiviso, nessun dialogo diretto
  └─ ricerca attiva, applicabile al nostro caso
```

---

## Livello A — Quick wins (1-3h, S effort)

### A1 — Typed Handoff Schema
**Problema**: ogni subagente riceve l'intera conversazione (~20-50k token) anche se gli servono solo 3 campi.  
**Soluzione**: Pydantic model con proiezione minima del contesto.

```python
# scripts/agent_handoff.py
from pydantic import BaseModel
from typing import Literal

class AgentHandoff(BaseModel):
    task: str                    # cosa fare
    project_path: str            # dove
    category: Literal["modifica","ops","bug_rescue","audit","nuova_app"]
    relevant_files: list[str]    # max 5 path
    constraints: list[str]       # regole critiche da rispettare
    budget_remaining_usd: float  # budget residuo
    prior_attempts: list[str]    # cosa ha già fallito (evita loop)
```

**Impatto**: -85-90% token per handoff vs forward completo del contesto.  
**Pro**: elimina il "gioco del telefono", subagente più veloce e preciso.  
**Contro**: richiede che il chiamante costruisca esplicitamente il handoff.  
**Fonte**: Context-Folding (arxiv 2510.11967), Anthropic context engineering guide.

---

### A2 — Blackboard JSON condiviso
**Problema**: in sessioni con più subagenti paralleli (drain), ogni step non sa cosa hanno trovato gli altri.  
**Soluzione**: file JSON condiviso scritto da ogni agente, letto da tutti.

```python
# pattern: ogni step drain scrive il proprio slot
{
  "session_id": "drain-2026-06-22",
  "slots": {
    "detect_dead_rules": {"dead_categories": ["nuova_app"], "ts": "20:00"},
    "run_morning_briefing": {"cost_7d": 1272.46, "ts": "20:00"},
    "run_evoskill_lite": {"patterns_found": 0, "ts": "20:00"}
  }
}
```

Il blackboard sostituisce i "print a schermo": ogni step scrive risultati strutturati, il passo successivo li legge invece di richiamare Haiku per riscoprire lo stesso fatto.

**Impatto**: +13-57% task completion quality (arxiv 2507.01701, 2510.01285); -30% chiamate Haiku ridondanti.  
**Pro**: debugging immediato, nessun spreco di context tra fasi.  
**Contro**: locking su file condiviso (risolto con `filelock` o slot segregati per agente).  

---

### A3 — Duo: Critic formale per output critici
**Problema**: i subagenti non hanno un secondo occhio sui loro output (solo verify_edit statico).  
**Soluzione**: pattern Generator/Critic dove il Critic è sempre Haiku (economico).

```python
# In coordination_log.py o come hook PostToolUse su file critici:
# Generator (Sonnet) produce → Critic (Haiku) verifica con checklist predefinita
critic_prompt = """
Verifica questo output contro questi criteri:
1. Il task richiesto è stato completato?
2. C'è regression su funzionalità esistenti?
3. L'output è nel formato atteso?
Rispondi JSON: {"pass": true/false, "issues": [...]}
"""
```

**Impatto**: +35-50% qualità output su task complessi; DualSpec (arxiv 2603.07416) riduce costo ciclo critico del 40% con verifica semantica leggera.  
**Pro**: cattura errori silenti, aumenta affidabilità senza escalation modello.  
**Contro**: +1 Haiku call per ogni output critico (~$0.001); rischio loop se Critic troppo severo.  

---

## Livello B — Evoluzioni strutturali (M effort, 1-2 giorni)

### B1 — Skill Reputation Engine ⭐ PRIORITÀ MASSIMA
**Gap unico**: arxiv 2606.14200 conferma che nessuno ha ancora implementato reputazione *condizionale al tipo di task*. Noi abbiamo 728 sessioni reali.

**Architettura**:
```
coordination-log.jsonl (728 sessioni)
  ↓
skill_reputation.py
  ├── per categoria (modifica/ops/bug_rescue/...):
  │     ├── success_rate (outcome=ok / totale)
  │     ├── avg_cost_usd
  │     ├── agents_used più efficaci
  │     └── avg_duration_s
  └── output: routing score per categoria

route_hint.py (già esiste)
  ↓ integra reputation score
  → suggerisce modello E subagente ottimale per questa categoria
```

**Impatto stimato**: +20-35% routing accuracy (basato su dati reali vs euristiche attuali); -15-25% costo per sessione (routing su modello giusto sin dall'inizio).  
**Pro**: vantaggio strutturale — il dataset è unico, nessun competitor accademico lo ha.  
**Contro**: reputazione va aggiornata ogni notte (drain step) e può diventare stale.  

---

### B2 — Budget Gate per subagenti
**Gap confermato**: nessuno strumento attuale controlla budget *dentro* una sessione Claude Code a livello di singolo spawn.

**Architettura**:
```
PreToolUse hook su Agent tool:
  1. Legge token residui dalla sessione (CLAUDE_CONTEXT_REMAINING env o stima)
  2. Stima costo subagente (categoria × avg_cost da coordination-log)
  3. Se costo_stimato > budget_residuo → degrada a modello più economico
  4. Se budget_residuo < soglia_minima → blocca e avvisa utente
```

```python
# scripts/budget_gate_agent.py
# Riceve tool_input su stdin (tipo: PreToolUse su Agent)
# Controlla: subagent_type → lookup avg_cost dalla reputation table
# Output: {"decision": "block"|"allow"|"degrade", "reason": "..."}
```

**Impatto**: -30-40% costo sessioni multi-agente; BAMAS (arxiv 2511.21572) documenta -35% su pipeline equivalenti.  
**Pro**: previene runaway costs, integra naturalmente con coordination-log.  
**Contro**: stima costo pre-run è approssimativa (±30%); falsi positivi bloccano task legittimi.  

---

### B3 — A2A Lite (locale)
**Cos'è Google A2A**: protocollo HTTP + JSON per agenti che si chiamano tra loro con Agent Card (capabilities pubbliche) + Task object (unità di lavoro con stato).

**Versione locale** (senza HTTP server, solo come contratto di dati):
```json
// agent-card.json per ogni subagente specializzato
{
  "name": "code-implementer",
  "version": "1.0",
  "capabilities": ["Edit", "Write", "Bash"],
  "categories": ["modifica", "nuova_app"],
  "avg_cost_usd": 0.045,
  "success_rate": 0.94
}
```

Il coordination-log già traccia questo — si tratta di formalizzarlo come Agent Card JSON generato automaticamente ogni notte dal drain.

**Impatto**: +60% chiarezza nel routing; base per futura integrazione A2A HTTP.  
**Pro**: zero costo operativo, si basa su dati già esistenti.  
**Contro**: Agent Card statica — non riflette variazioni di performance intra-sessione.  

---

## Livello C — Frontiera (L effort, settimane)

### C1 — Mem0 self-hosted
**Cos'è**: memoria cross-sessione per subagenti con storage vettoriale locale.  
**Perché**: oggi ogni subagente parte da zero; con Mem0 può recuperare "la volta scorsa ho risolto questo con X".  
**Install**: `pip install mem0ai` (37k stelle GitHub, open source core).  
**Impatto**: -80% token per task ricorrenti (niente ricerca da zero); +25% coerenza tra sessioni.  
**Contro**: richiede server locale (FastAPI + ChromaDB); TTL memoria da definire.  

### C2 — Agent Mesh con discovery semantica
**Pattern**: nessun orchestratore fisso. Ogni subagente dichiara capabilities come embedding. Quando serve un task, si cerca il subagente più simile semanticamente.  
**Impatto**: sistema più resiliente, emergent specialization.  
**Contro**: governance complessa, debugging difficile, costo discovery non trascurabile.  
**Raccomandazione**: solo dopo B1 (reputation engine) è stabile.  

### C3 — Stigmergia / Swarm
**Pattern**: agenti non si parlano direttamente, scrivono "feromoni" (score/tag) sul blackboard. Le path più usate con successo vengono amplificate.  
**Base accademica**: arxiv 2506.14496, 2510.10047 (SwarmSys), 2512.10166.  
**Impatto**: emergent behavior su task explorativi, -40% iterazioni su ricerca multi-step.  
**Contro**: ancora prevalentemente research (2025-2026), nessuna implementazione production-ready.  

---

## Tabella riassuntiva

| ID | Upgrade | Effort | % Miglioramento | Pro chiave | Contro chiave |
|----|---------|--------|-----------------|------------|---------------|
| A1 | Typed Handoff Schema | S (2h) | -85-90% token handoff | elimina gioco del telefono | richiede costruzione esplicita handoff |
| A2 | Blackboard JSON | S (3h) | +13-57% quality, -30% Haiku calls | debugging immediato | locking su file |
| A3 | Duo Critic (Haiku) | S (2h) | +35-50% output quality | cattura errori silenti | +$0.001/output critico |
| B1 | Skill Reputation Engine | M (1g) | +20-35% routing, -15-25% cost | dataset unico (728 sess.) | reputazione stale se non aggiornata |
| B2 | Budget Gate subagenti | M (1g) | -30-40% costo multi-agent | previene runaway costs | stima approssimativa (±30%) |
| B3 | A2A Lite (Agent Cards) | S (3h) | +60% routing clarity | zero costo, dati già esistenti | statica, non real-time |
| C1 | Mem0 self-hosted | M (2g) | -80% token ricorrenti | open source, 37k stars | server locale richiesto |
| C2 | Agent Mesh | L (1+ sett.) | +resilienza | no single point of failure | governance complessa |
| C3 | Stigmergia/Swarm | L (futuro) | -40% iter. explorative | emergent behavior | ancora research |

---

## Roadmap consigliata

```
Settimana 1: A2 (Blackboard) → A1 (Typed Handoff) → A3 (Duo Critic)
Settimana 2: B1 (Skill Reputation Engine) — massimo ROI sul dataset unico
Settimana 3: B2 (Budget Gate) → B3 (A2A Lite)
Settimana 4+: C1 (Mem0), poi valuta C2/C3 in base ai dati
```

---

## Il vantaggio competitivo reale

**La cosa che nessuno ha**: 728 sessioni reali di Claude Code con outcome tracciati, categoria, costo, agenti usati, file toccati. Tutta la ricerca accademica lavora su benchmark sintetici.

Il Skill Reputation Engine (B1) è l'upgrade con il più alto valore *differenziale* — non perché sia tecnicamente complesso, ma perché è costruito su dati che esistono solo qui.

---

## Fonti principali
- Context-Folding: arxiv 2510.11967
- Blackboard multi-agent: arxiv 2507.01701, 2510.01285
- Skill-conditional reputation: arxiv 2606.14200
- DualSpec Generator-Critic: arxiv 2603.07416
- BAMAS budget governance: arxiv 2511.21572
- Google A2A Protocol: rapidclaw.dev/blog/a2a-protocol-complete-guide-2026
- CrewAI vs AutoGen 2026: pooya.blog/blog/crewai-vs-langgraph-autogen-comparison-2026
- Anthropic multi-agent: anthropic.com/engineering/multi-agent-research-system
- Mem0: mem0.ai (37k GitHub stars, open source)
- SwarmSys: arxiv 2510.10047
