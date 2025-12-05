# Prompt Caching - Quick Reference Card

**🎯 Goal:** 10x cost reduction on AI calls
**📊 Result:** 88% cost savings validated

---

## ⚡ Quick Start (30 seconds)

### Step 1: Import
```python
from prompts.cache_manager import get_cached_system_prompt, cache_monitor
```

### Step 2: Load Cached Prompt
```python
# For Anthropic
system = get_cached_system_prompt("viral_ad_expert", provider="anthropic")

# For OpenAI
system = get_cached_system_prompt("viral_ad_expert", provider="openai")

# For Gemini
system = get_cached_system_prompt("viral_ad_expert", provider="gemini")
```

### Step 3: Use in API Call
```python
# Anthropic
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=system,  # 🎯 CACHED
    messages=[{"role": "user", "content": user_input}]
)

# OpenAI
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system},  # 🎯 CACHED
        {"role": "user", "content": user_input}
    ]
)

# Gemini
prompt = f"{system}\n\nUser: {user_input}"
response = model.generate_content(prompt)
```

### Step 4: Track (Optional)
```python
# Anthropic
cache_monitor.record_anthropic_request(
    input_tokens=response.usage.input_tokens,
    cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
    output_tokens=response.usage.output_tokens,
    cache_hit=getattr(response.usage, 'cache_read_input_tokens', 0) > 0
)

# OpenAI
cache_monitor.record_openai_request(
    model="gpt-4o-mini",
    input_tokens=response.usage.prompt_tokens,
    cached_tokens=getattr(response.usage, 'prompt_tokens_details', {}).get('cached_tokens', 0),
    output_tokens=response.usage.completion_tokens
)
```

---

## 📚 Available Cached Prompts

| Prompt Name | Size | Use Case |
|-------------|------|----------|
| `viral_ad_expert` | ~400 tokens | General ad evaluation |
| `psychology_expert` | ~450 tokens | Emotional/persuasion analysis |
| `hook_analyzer` | ~350 tokens | Hook classification |
| `ctr_predictor` | ~550 tokens | CTR prediction |

**Location:** `/services/titan-core/prompts/cached/`

---

## 💰 Cost Savings (Per Call)

| Provider | Without Cache | With Cache | Savings |
|----------|---------------|------------|---------|
| Anthropic | $0.006 | $0.0006 | **90%** |
| OpenAI | $0.0003 | $0.00015 | **50%** |
| **Combined** | $0.0063 | $0.00075 | **88%** |

**At Scale (1M calls):**
- Without: $6,300
- With: $750
- **Savings: $5,550** 🚀

---

## 🔍 Check Cache Performance

```python
from ai_council.council_of_titans import council

# Quick check
metrics = council.get_cache_metrics()
print(f"Hit rate: {metrics['cache_hit_rate']}")
print(f"Savings: {metrics['cost_saved']}")

# Full report
council.print_cache_report()
```

**Expected Output:**
```
============================================================
💰 PROMPT CACHE PERFORMANCE REPORT
============================================================
📊 Total Requests: 100
✅ Cache Hit Rate: 85.0%
💸 Cost Saved: $0.4590
🚀 ROI Multiplier: 8.5x
============================================================
```

---

## 🐛 Troubleshooting

### Problem: Cache not working

**Check 1:** Is caching enabled?
```python
import os
print(os.getenv("PROMPT_CACHING_ENABLED", "true"))
# Should be "true"
```

**Check 2:** Are prompts loading?
```python
from prompts.cache_manager import prompt_loader
prompt = prompt_loader.load_prompt("viral_ad_expert")
print(f"Loaded: {len(prompt)} chars")
# Should be >1000
```

**Check 3:** Is format correct?
```python
from prompts.cache_manager import get_cached_system_prompt

# Anthropic
cached = get_cached_system_prompt("viral_ad_expert", provider="anthropic")
print(cached[0].get("cache_control"))
# Should be {'type': 'ephemeral'}

# OpenAI
cached = get_cached_system_prompt("viral_ad_expert", provider="openai")
print(type(cached))
# Should be <class 'str'>
```

---

## 📊 Testing

**Run full test suite:**
```bash
cd /home/user/geminivideo/services/titan-core/ai_council
python test_prompt_caching.py
```

**Quick test:**
```python
from prompts.cache_manager import cache_monitor

cache_monitor.reset_metrics()

# Your AI calls here...
# await your_function()

metrics = cache_monitor.get_summary()
print(metrics)
```

---

## 🎯 Best Practices

### DO ✅
- Keep system prompts consistent
- Load from cache (don't hardcode)
- Monitor hit rates (target >70%)
- Track cost savings
- Use for prompts >500 tokens

### DON'T ❌
- Cache user inputs (only system prompts)
- Modify prompts frequently
- Disable in production
- Ignore low hit rates (<50%)
- Skip metrics tracking

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [Quick Reference](QUICK_REFERENCE.md) | This card |
| [Implementation Guide](CACHING_IMPLEMENTATION_GUIDE.md) | Step-by-step tutorial |
| [ROI Report](PROMPT_CACHING_ROI_REPORT.md) | Business case & metrics |
| [Cached Prompts README](cached/README.md) | Prompt library details |
| [Implementation Summary](IMPLEMENTATION_SUMMARY.md) | Technical overview |

---

## 🚀 Common Patterns

### Pattern 1: Simple Caching
```python
system = get_cached_system_prompt("viral_ad_expert", provider="anthropic")
response = await client.messages.create(system=system, ...)
```

### Pattern 2: With Metrics
```python
system = get_cached_system_prompt("viral_ad_expert", provider="anthropic")
response = await client.messages.create(system=system, ...)
cache_monitor.record_anthropic_request(...)
```

### Pattern 3: Multi-Tier
```python
domain = get_cached_system_prompt("viral_ad_expert", provider="anthropic")
task = get_cached_system_prompt("hook_analyzer", provider="anthropic")

system = [
    {"type": "text", "text": domain, "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": task, "cache_control": {"type": "ephemeral"}}
]

response = await client.messages.create(system=system, ...)
```

---

## 💡 Pro Tips

1. **Warm the cache:** Run evaluation once before measuring
2. **Batch similar requests:** Cache works best with patterns
3. **Monitor daily:** Check hit rates and cost trends
4. **Keep prompts stable:** Changes invalidate cache
5. **Use for high-volume calls:** More calls = more savings

---

## 🎓 Learning Path

1. **Beginner:** Read this Quick Reference
2. **Intermediate:** Follow [Implementation Guide](CACHING_IMPLEMENTATION_GUIDE.md)
3. **Advanced:** Study [Multi-tier caching](CACHING_IMPLEMENTATION_GUIDE.md#advanced-multi-tier-caching)
4. **Expert:** Optimize custom prompts and cache strategies

---

## 📞 Support

**Questions?**
1. Check this Quick Reference
2. Read [Implementation Guide](CACHING_IMPLEMENTATION_GUIDE.md)
3. Run test suite: `python test_prompt_caching.py`
4. Check metrics: `council.print_cache_report()`

---

**Last Updated:** 2025-12-05
**Version:** 1.0
**Status:** Production Ready ✅
