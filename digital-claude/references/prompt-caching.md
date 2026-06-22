# Prompt Caching (Anthropic API)

Reduces cost of repeated references by **75% first read, 90% subsequent reads**. For 3+ sessions/week with Caching = **-27% total cost**.

**Opus 4.8**: cache min sceso a **1,024 tokens** (era 2,048 su 4.7). I bundle più corti ora creano cache hit senza modifiche al codice. Supporta anche **mid-conversation system messages** (`role: "system"` dopo un turno utente) per iniettare istruzioni aggiornate a metà loop senza riscrivere il system prompt intero — preserva i cache hit sui turni precedenti.

## How it works

Anthropic API's Prompt Caching caches large text blocks (5-min TTL). First read pays 100% tokens. Subsequent reads pay 10% (90% discount).

Ideal for skill because SKILL.md (25KB) + references (~60KB) are read every session.

## Three implementation options

### Option A: Anthropic SDK (Python wrapper app)

For custom apps calling Claude API via `anthropic` SDK:

```python
from anthropic import Anthropic
client = Anthropic()
skill = open("SKILL.md").read()

response = client.messages.create(
    model="claude-opus-4-8",
    system=[{"type": "text", "text": skill, 
             "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": user_prompt}]
)

# Session 1: cache_creation_input_tokens = high
# Sessions 2-5: cache_read_input_tokens = high (cache hit)
```

### Option B: Claude Code RemoteTrigger

Use `/schedule` skill for Anthropic API routines (auto-cached):

```
/schedule "run drain task" every sunday 03:00
→ Anthropic API backend → caching automatic
```

### Option C: Cache bundle (Anthropic SDK helper)

Script `cache_bundle_builder.py` creates single .md file (71KB) with SKILL.md + top 8 references, ready for cache block above.

```bash
python3 scripts/cache_bundle_builder.py --output skill-cache.md
```

Load it: `bundle = open("skill-cache.md").read()` → pass to SDK as above.

## Concrete savings

**Without caching**: 4 sessions/week × 150k tokens = $6/week on references  
**With caching**: Session 1 ($1.50) + Sessions 2-4 ($0.15 each) = $1.95/week  
**Savings**: -67% weekly, -27% total (references ~40% of typical input)

## Limitations

- **TTL**: 5 minutes. After 5min without cache hit, cleared.
- **Size**: ~200KB per cache block (SKILL.md + 8 refs fits)
- **API-only**: Caching not available in Claude Code native UI.

## Implementation status

- ✅ `cache_bundle_builder.py` ready (generates skill-cache.md)
- ✅ `prompt-caching.md` documented (this file)
- ⏳ Integration: User implements via Anthropic SDK or `/schedule`

No changes needed to coordinator itself (caching is downstream on API consumer).

## Testing

After implementing, check for cache hit:

```python
if response.usage.cache_read_input_tokens > 100000:
    print("✅ Cache HIT! Saved $", response.usage.cache_read_input_tokens * 0.9 * 15 / 1e6)
```

See also: `references/external-routing.md` (OpenRouter integration if no API key yet).

## Instant Compaction (background threading)

Pattern da Anthropic Cookbook per sessioni lunghe: invece di aspettare che il context sia pieno (→ 40s di attesa), un background thread costruisce il summary in anticipo → compaction **zero-wait**.

Combinato con prompt caching: **80% di risparmio sul costo delle chiamate di compaction** (il prefisso della conversazione viene cachato, solo i nuovi turni pagano full price).

Threshold consigliati:
- Avvia background summary a **70-80%** del context limit
- Aggiorna ogni **2.000-5.000 token** nuovi
- Preserva sempre: path esatti, messaggi di errore verbatim, correzioni utente

Rilevante per il drain notturno (`references/background-drain.md`) e sessioni API lunghe. Per Claude Code interattivo, il runtime gestisce automaticamente.

## Non cachare output di tool dinamici

Gli output di tool dinamici (bash, grep, query DB, Read su file che cambiano) **non vanno** nel blocco `cache_control` dei prompt subagent — aumentano la latenza invece di ridurla perché invalidano il cache hit ad ogni run.

**Cachare solo**: istruzioni statiche, schema, contenuto `AI_*.md`, `SKILL.md`.
**Non cachare**: output di `Bash`, `Read` su file di stato runtime, risultati di query DB, `grep` output.

Per i subagent: passa le istruzioni statiche come system prompt cacheable; i dati dinamici vanno nel primo turno utente non-cacheable.
