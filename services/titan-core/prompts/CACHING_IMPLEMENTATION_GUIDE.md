# Prompt Caching Implementation Guide

## 🎯 Quick Start: Add Caching to Any AI Call

This guide shows you how to implement prompt caching across your entire codebase for maximum cost savings.

---

## 📘 Implementation Patterns

### Pattern 1: Anthropic Claude (90% Reduction)

#### BEFORE (No Caching)

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{
        "role": "user",
        "content": f"You are an expert. Analyze this: {user_input}"
    }]
)
# ❌ Costs $3/1M tokens - NO CACHING
```

#### AFTER (With Caching) ✅

```python
from anthropic import AsyncAnthropic
from prompts.cache_manager import get_cached_system_prompt, cache_monitor

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load cached system prompt
system_prompt = get_cached_system_prompt("viral_ad_expert", provider="anthropic")

response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    system=system_prompt,  # 🎯 CACHED (~2000 tokens)
    messages=[{
        "role": "user",
        "content": f"Analyze this: {user_input}"  # Only this changes
    }]
)

# Track metrics
if hasattr(response, 'usage'):
    usage = response.usage
    cache_monitor.record_anthropic_request(
        input_tokens=usage.input_tokens,
        cached_tokens=getattr(usage, 'cache_read_input_tokens', 0),
        output_tokens=usage.output_tokens,
        cache_hit=getattr(usage, 'cache_read_input_tokens', 0) > 0
    )

# ✅ Costs $0.30/1M tokens after first call - 90% SAVINGS
```

---

### Pattern 2: OpenAI GPT-4o (50% Reduction)

#### BEFORE (No Caching)

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are an expert..."},  # Changes per call
        {"role": "user", "content": user_input}
    ]
)
# ❌ No caching - inconsistent system message
```

#### AFTER (With Caching) ✅

```python
from openai import AsyncOpenAI
from prompts.cache_manager import get_cached_system_prompt, cache_monitor

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load cached system prompt (keeps it consistent)
system_prompt = get_cached_system_prompt("viral_ad_expert", provider="openai")

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},  # 🎯 CONSISTENT = CACHED
        {"role": "user", "content": user_input}
    ]
)

# Track metrics (OpenAI provides cache info in usage)
if hasattr(response, 'usage'):
    usage = response.usage
    cache_monitor.record_openai_request(
        model="gpt-4o-mini",
        input_tokens=usage.prompt_tokens,
        cached_tokens=getattr(usage, 'prompt_tokens_details', {}).get('cached_tokens', 0),
        output_tokens=usage.completion_tokens
    )

# ✅ OpenAI auto-caches consistent prefixes - 50% SAVINGS
```

---

### Pattern 3: Gemini (Optimized Prompts)

#### BEFORE (No Optimization)

```python
import google.generativeai as genai

model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")

response = model.generate_content(
    f"You are an expert... Analyze: {user_input}"  # All mixed together
)
# ❌ No separation, hard to optimize
```

#### AFTER (With Cached Prompts) ✅

```python
import google.generativeai as genai
from prompts.cache_manager import get_cached_system_prompt

model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")

# Load cached system context
system_context = get_cached_system_prompt("viral_ad_expert", provider="gemini")

# Construct prompt with clear separation
prompt = f"""{system_context}

TASK: Analyze this content.

CONTENT:
{user_input}

RESPONSE:"""

response = model.generate_content(prompt)

# ✅ Consistent system prompt, ready for future Gemini caching
```

---

## 🛠️ Step-by-Step: Add Caching to Your Module

### Step 1: Create Your Cached Prompt

Create a file in `/services/titan-core/prompts/cached/your_prompt_name.txt`:

```text
You are an Expert Social Media Analyst specializing in engagement prediction.

EXPERTISE:
- Platform algorithms (TikTok, Instagram, YouTube 2025)
- Engagement metrics and KPIs
- Viral content patterns
- Audience psychology

EVALUATION CRITERIA:
1. Hook effectiveness (0-3s capture)
2. Retention mechanics (watch time)
3. Engagement triggers (comments, shares, saves)
4. Algorithmic compatibility

Provide scores 0-100 with detailed reasoning.
```

**Guidelines:**
- Keep it 1500-2500 tokens (sweet spot for caching ROI)
- Make it comprehensive (cover all use cases)
- Keep it stable (changes invalidate cache)
- Focus on system knowledge (not user data)

### Step 2: Import Cache Manager

```python
from prompts.cache_manager import (
    get_cached_system_prompt,
    cache_monitor
)
```

### Step 3: Load Cached Prompt

```python
# For Anthropic
system_prompt = get_cached_system_prompt("your_prompt_name", provider="anthropic")

# For OpenAI
system_prompt = get_cached_system_prompt("your_prompt_name", provider="openai")

# For Gemini
system_prompt = get_cached_system_prompt("your_prompt_name", provider="gemini")
```

### Step 4: Use in API Call

See patterns above for provider-specific implementation.

### Step 5: Track Metrics

```python
# Record the request (provider-specific)
cache_monitor.record_anthropic_request(...)
# or
cache_monitor.record_openai_request(...)

# View metrics anytime
cache_monitor.print_summary()
```

---

## 📊 Real-World Example: Hook Classifier

### Before Caching

```python
async def classify_hook(self, script: str) -> str:
    """Classify hook type using AI"""
    response = await self.client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""You are a hook analysis expert.

Classify this hook into one of:
- pattern_interrupt
- curiosity_gap
- shock
- question
- bold_claim
- story

Hook: {script[:100]}

Return ONLY the type."""
        }]
    )
    return response.content[0].text.strip()
```

**Cost per 1000 classifications:** ~$2.00

### After Caching ✅

```python
from prompts.cache_manager import get_cached_system_prompt, cache_monitor

async def classify_hook(self, script: str) -> str:
    """Classify hook type using AI with caching"""

    # Load cached system prompt
    system_prompt = get_cached_system_prompt("hook_analyzer", provider="anthropic")

    response = await self.client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        system=system_prompt,  # CACHED
        messages=[{
            "role": "user",
            "content": f"Classify this hook:\n\n{script[:100]}\n\nReturn ONLY the type."
        }]
    )

    # Track metrics
    if hasattr(response, 'usage'):
        cache_monitor.record_anthropic_request(
            input_tokens=response.usage.input_tokens,
            cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
            output_tokens=response.usage.output_tokens,
            cache_hit=getattr(response.usage, 'cache_read_input_tokens', 0) > 0
        )

    return response.content[0].text.strip()
```

**Cost per 1000 classifications:** ~$0.20

**SAVINGS: $1.80 (90% reduction)**

---

## 🧪 Testing Your Implementation

### Test 1: Verify Caching Works

```python
import asyncio
from prompts.cache_manager import cache_monitor

async def test_caching():
    # Reset metrics
    cache_monitor.reset_metrics()

    # Call your function twice with same input
    result1 = await your_cached_function("test input")
    result2 = await your_cached_function("test input")

    # Check metrics
    metrics = cache_monitor.get_summary()

    print(f"Total requests: {metrics['total_requests']}")
    print(f"Cache hit rate: {metrics['cache_hit_rate']}")
    print(f"Cost saved: {metrics['cost_saved']}")

    # Verify cache hit on second call
    assert float(metrics['cache_hit_rate'].replace('%', '')) > 0, "No cache hits!"

    print("✅ Caching working correctly!")

asyncio.run(test_caching())
```

### Test 2: Measure ROI

```python
async def benchmark_roi():
    """Compare cost with vs without caching"""

    # Disable caching
    import os
    os.environ["PROMPT_CACHING_ENABLED"] = "false"

    # ... re-initialize your client ...

    # Run 100 calls, track cost
    cost_without = ...

    # Enable caching
    os.environ["PROMPT_CACHING_ENABLED"] = "true"

    # ... re-initialize your client ...

    # Run 100 calls, track cost
    cost_with = ...

    # Calculate ROI
    savings = cost_without - cost_with
    roi = cost_without / cost_with

    print(f"Cost without: ${cost_without:.4f}")
    print(f"Cost with: ${cost_with:.4f}")
    print(f"Savings: ${savings:.4f} ({(savings/cost_without)*100:.1f}%)")
    print(f"ROI: {roi:.1f}x")
```

---

## ⚡ Advanced: Multi-Tier Caching

For complex workflows, use multiple cached prompts:

```python
# Tier 1: Domain expert prompt (shared across all tasks)
domain_prompt = get_cached_system_prompt("viral_ad_expert", provider="anthropic")

# Tier 2: Task-specific context (cached per task type)
task_context = get_cached_system_prompt("hook_analyzer", provider="anthropic")

# Combine in system message
system_message = [
    {
        "type": "text",
        "text": domain_prompt,
        "cache_control": {"type": "ephemeral"}  # Cache tier 1
    },
    {
        "type": "text",
        "text": task_context,
        "cache_control": {"type": "ephemeral"}  # Cache tier 2
    }
]

response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    system=system_message,
    messages=[{"role": "user", "content": user_input}]
)

# Result: Multi-tier caching for maximum efficiency
```

---

## 📈 Monitoring in Production

### Daily Cache Report

```python
from prompts.cache_manager import cache_monitor

# Run daily (cron job)
def daily_cache_report():
    metrics = cache_monitor.get_summary()

    # Alert if cache hit rate is low
    hit_rate = float(metrics['cache_hit_rate'].replace('%', ''))

    if hit_rate < 50:
        print("⚠️ WARNING: Cache hit rate below 50%!")
        print("   Possible causes:")
        print("   - System prompts changing too frequently")
        print("   - Cache TTL too short")
        print("   - Need to warm up cache")

    # Log to analytics
    log_to_analytics({
        "cache_hit_rate": hit_rate,
        "cost_saved": metrics['cost_saved'],
        "roi_multiplier": metrics['roi_multiplier']
    })

    # Print summary
    cache_monitor.print_summary()
```

### Real-Time Monitoring

```python
# Add to your API/service
@app.get("/cache/metrics")
async def get_cache_metrics():
    """Endpoint to check cache performance"""
    return cache_monitor.get_summary()

@app.post("/cache/reset")
async def reset_cache_metrics():
    """Reset cache metrics (admin only)"""
    cache_monitor.reset_metrics()
    return {"status": "reset"}
```

---

## 🎓 Best Practices Summary

### DO ✅

1. **Cache large, stable prompts** (1500-2500 tokens ideal)
2. **Separate system from user content** (only cache system)
3. **Keep prompts consistent** (changes break cache)
4. **Monitor cache hit rates** (>70% is good)
5. **Track cost savings** (prove ROI)
6. **Test before deploying** (verify cache works)

### DON'T ❌

1. **Don't cache user inputs** (always changing)
2. **Don't modify prompts frequently** (kills cache efficiency)
3. **Don't ignore low hit rates** (investigate and fix)
4. **Don't disable in production** (leaving money on table)
5. **Don't cache tiny prompts** (<500 tokens, not worth it)
6. **Don't forget to track metrics** (can't improve what you don't measure)

---

## 📞 Troubleshooting

### Problem: Low Cache Hit Rate (<50%)

**Diagnosis:**
```python
cache_monitor.print_summary()  # Check hit rate
```

**Solutions:**
1. Ensure system prompts are loaded from cache (not hardcoded)
2. Verify prompts aren't being modified per request
3. Check if cache TTL is too short (Anthropic: 5min)
4. Warm up cache before measuring

### Problem: No Cost Savings Showing

**Diagnosis:**
```python
metrics = cache_monitor.get_summary()
print(f"Total requests: {metrics['total_requests']}")
print(f"Cache hits: {cache_monitor.metrics.cache_hits}")
```

**Solutions:**
1. Ensure `cache_monitor.record_*_request()` is being called
2. Check if metrics file exists: `/tmp/prompt_cache_metrics.json`
3. Verify API responses include usage data
4. Reset and re-test: `cache_monitor.reset_metrics()`

### Problem: Caching Not Working

**Diagnosis:**
```python
# Check environment
import os
print(f"Caching enabled: {os.getenv('PROMPT_CACHING_ENABLED', 'true')}")

# Check prompt loading
from prompts.cache_manager import prompt_loader
try:
    prompt = prompt_loader.load_prompt("viral_ad_expert")
    print(f"✅ Prompt loaded: {len(prompt)} chars")
except Exception as e:
    print(f"❌ Error loading prompt: {e}")
```

**Solutions:**
1. Set `PROMPT_CACHING_ENABLED=true` in environment
2. Verify prompt files exist in `/prompts/cached/`
3. Check file permissions on prompt files
4. Ensure cache_manager is imported correctly

---

## 🚀 Migration Checklist

Migrating existing code to use caching:

- [ ] Create cached system prompt files
- [ ] Import cache_manager in modules
- [ ] Replace hardcoded prompts with `get_cached_system_prompt()`
- [ ] Add Anthropic `cache_control` directives
- [ ] Add metrics tracking with `cache_monitor.record_*_request()`
- [ ] Test cache hit rates (>70%)
- [ ] Measure cost savings
- [ ] Update documentation
- [ ] Monitor in production
- [ ] Celebrate 10x ROI! 🎉

---

**Need help?** Check the test suite: `ai_council/test_prompt_caching.py`

**Last Updated**: 2025-12-05
