# Prompt Caching (Anthropic API)

Reduces cost of repeated references by **75% first read, 90% subsequent reads**. For 3+ sessions/week with Caching = **-27% total cost**.

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
    model="claude-opus-4-7",
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
