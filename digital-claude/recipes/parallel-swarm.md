# Parallel Swarm — Lanciare 2-3 Subagent Indipendenti in Parallelo

Quando il task ha 2-3 componenti **totalmente indipendenti** (nessuna dipendenza dati, file non overlapping), il coordinatore può lanciare più subagent in parallelo.

**Anti-pattern**: "parallelizza sempre" — il default è sequenziale per motivi di context e comunicazione.

## Quando usare Parallel Swarm

Tutte le 4 condizioni devono essere vere:

1. **Task indipendenti** — nessuno dipende dall'output dell'altro
   - ✅ "Scrivi test per module X" + "Documenta module Y" → indipendenti
   - ❌ "Implementa backend" + "Implementa frontend che dipende dal backend" → dipendenti

2. **File set non overlapping** — nessun file viene toccato da più di un agente
   - ✅ Agent A: `src/auth/`, Agent B: `src/ui/`
   - ❌ Agent A: `src/auth.ts`, Agent B: `src/auth.ts` → CONFLICT

3. **Budget disponibile** — `tokens_residui > (cost_A + cost_B) * 1.5`
   - Safety factor 1.5 = 50% buffer
   - Se budget insufficiente, run sequenziale

4. **Entrambi completabili in <1 sessione** — non parallelizzare se uno richiede 10+ turni
   - Total work = A_turni + B_turni, non A_turni * B_turni in parallelo (costo explodes)

## Pattern: 2-Agent Swarm

```yaml
# esempio: security audit + UI review paralleli
swarm:
  name: "security-ui-review"
  agents:
    - agent: "security-hardener"
      model: sonnet
      task: |
        Audit sicurezza del codebase dashboard:
        - SSH/firewall/auth exposure
        - Secrets management
        - CORS/CSRF
        Output: JSON {findings: [...], severity: "low|medium|high", recommendations: [...]}
      files_scope: ["src/api/", "src/lib/auth.ts"]

    - agent: "code-reviewer"
      model: opus  
      task: |
        Review qualità UI delle pagine dashboard:
        - Readability, performance, accessibility
        - Component reusability
        - Styling consistency
        Output: JSON {issues: [...], score: 0-10, suggestions: [...]}
      files_scope: ["src/components/", "src/app/"]

  merge_handler: "log both to coordination-log with [parallel-swarm-result]"
  timeout: 3600  # 1 ora per agente
```

## Pattern: 3-Agent Swarm (Raro)

```yaml
swarm:
  name: "feature-backend-frontend-tests"
  agents:
    - agent: "code-implementer"
      task: "Implementa endpoint /api/feature"
      files: ["src/api/feature.ts"]
    
    - agent: "code-implementer"  # seconda istanza
      task: "Implementa UI component Feature"
      files: ["src/components/Feature.tsx"]
    
    - agent: "qa-tester"
      task: "Scrivi test per Feature (attendi output API + UI)"
      files: ["tests/feature.test.ts"]
      depends_on: ["api", "ui"]  # sequenza DENTRO il qa-tester
```

## Varianti comuni

### 1. Backend Feature + UI Feature
```
Agent A: code-implementer (backend)
Agent B: code-implementer (frontend)
Merge: log both; frontend dev testa integrazione locale
```

### 2. Security Audit + Code Review
```
Agent A: security-hardener (scoperto: auth bug)
Agent B: code-reviewer (scoperto: performance issue)
Merge: prioritizza per criticità
```

### 3. Test Write + Doc Write
```
Agent A: qa-tester (scrivi pytest)
Agent B: doc-writer (scrivi README per feature)
Merge: entrambi di qualità indipendente
```

### 4. Refactor Local + Refactor Other Locale
```
Agent A: code-implementer (refactor auth/)
Agent B: code-implementer (refactor ui/ styling)
Merge: hand-test insieme per regressione
```

## Anti-Pattern: Cosa NON parallelizzare

- ❌ "Implementa DB schema" + "Scrivi app che usa schema" → B dipende da A
- ❌ "Refactor shared utility" + "Usa utility in 2 file" → shared state conflict
- ❌ "Migrare DB" + "Cambiare query SQL" → tight coupling
- ❌ Task che richiedono decision del coordinatore nel mezzo

## Implementazione nel Coordinatore

Il coordinatore che rileva un brief con pattern di parallelismo:

```python
# brief: "Aggiungi feature X (backend) e scrivi i test"
if is_parallel_opportunity(brief):
    # Identify independent tasks
    tasks = extract_parallel_tasks(brief)  # [backend_feature, test_write]
    
    # Check all 4 conditions
    if all_conditions_met(tasks, budget, files):
        # Launch agents in parallel
        results = parallel([
            Agent(subagent_type="code-implementer", task=tasks[0]),
            Agent(subagent_type="qa-tester", task=tasks[1])
        ])
        
        # Log as [parallel-swarm-result]
        merge_swarm_results(results)
```

## Output Format

Dopo che entrambi gli agenti finiscono:

```json
{
  "type": "parallel-swarm-result",
  "timestamp": "2026-05-24T13:45:00Z",
  "agents": [
    {
      "name": "security-hardener",
      "status": "completed",
      "duration_minutes": 8,
      "findings": [...]
    },
    {
      "name": "code-reviewer",
      "status": "completed", 
      "duration_minutes": 12,
      "issues": [...]
    }
  ],
  "total_duration": 12,  # max of the two (parallel)
  "merge_summary": "Entrambi completati. Security: 2 high findings. Review: 1 medium issue su performance."
}
```

## Fallback: Se un agente fallisce

Se Agent A finisce con errori:
- Agent B prosegue comunque (indipendente)
- Log del fallimento A
- Verdetto: "A failed, B succeeded. A must be retried sequenziale, B done."

Non bloccare B per colpa di A.

## Note

- Costo di parallelismo: 2 agenti = 2× cost (non <2×). Se budget tight, run sequenziale.
- Coordinamento: gli agenti NON si comunicano direttamente. Coordinatore legge entrambi gli output.
- Utile su task ampi (2-3h caduno) dove il parallelismo risparmiailwall time (6h → 3h per l'utente).
