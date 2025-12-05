# Claude 4 Opus Upgrade - AI Council Enhancement

**Date:** December 5, 2025
**Version:** November 2025 Tech
**Status:** Production Ready

## Overview

The AI Council has been upgraded to use **Claude 4 Opus** (November 2025) as its primary psychological analysis engine, replacing Claude 3.5 Sonnet. This upgrade brings significant improvements in nuanced psychological analysis, extended thinking capabilities, and cost optimization through prompt caching.

## What Changed

### Model Upgrades

#### Claude 4 Opus (`claude-opus-4-5-20251101`)
- **Primary Use:** Complex psychological analysis with extended thinking
- **Strengths:**
  - Superior understanding of psychological triggers and human behavior
  - Extended thinking for deep reasoning (up to 5000 thinking tokens)
  - Better cultural and demographic nuance
  - Enhanced viral pattern recognition for 2025 trends
- **Weight:** 40% (increased from 30%)

#### Claude 4 Sonnet (`claude-sonnet-4-5-20250929`)
- **Fallback Use:** General scoring when Opus is unavailable
- **Strengths:** Balanced performance, faster than Opus
- **Cost:** More economical than Opus

#### Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
- **Optional Use:** Quick pre-filtering and validation
- **Strengths:** Fastest, cheapest for simple checks
- **Method:** `get_claude_haiku_quick_check()`

### New Weights (November 2025)

```
┌─────────────────────────────────────────┐
│ AI COUNCIL WEIGHTING                    │
├─────────────────────────────────────────┤
│ 1. Claude 4 Opus (Psychology)      40%  │  ← INCREASED
│ 2. Gemini 2.0 Flash Thinking      35%  │  ← DECREASED
│ 3. GPT-4o (Logic/Structure)       15%  │  ← DECREASED
│ 4. DeepCTR (Data/Math)            10%  │
└─────────────────────────────────────────┘
```

**Rationale:** Claude 4 Opus demonstrates superior psychological analysis capabilities, justifying the increased weight from 30% to 40%.

## New Features

### 1. Extended Thinking

Claude 4 Opus can now use **extended thinking** for complex psychological analysis:

```python
# Automatically enabled in get_claude_opus_critique()
response = await council.get_claude_opus_critique(
    script="Your ad script here",
    use_extended_thinking=True  # Default
)

# Response includes:
{
    "score": 87.5,
    "source": "Claude 4 Opus",
    "reasoning": "Claude's internal thought process...",
    "extended_thinking_used": True
}
```

**How it works:**
- Claude internally "thinks" before responding (up to 5000 tokens)
- This thinking process is extracted and included in the response
- Provides transparency into the reasoning behind scores
- Particularly useful for edge cases and nuanced content

### 2. Prompt Caching (90% Cost Savings)

The system prompt is now cached using Anthropic's prompt caching:

```python
self.cached_psychology_system = [
    {
        "type": "text",
        "text": """Elite psychology expert prompt...""",
        "cache_control": {"type": "ephemeral"}  # Cached!
    }
]
```

**Benefits:**
- First request: Normal cost + cache creation
- Subsequent requests: **90% savings** on system prompt tokens
- Cache lasts for 5 minutes (ephemeral)
- Automatic cache management by Anthropic SDK

**Cost Tracking:**
```python
response = await council.evaluate_script("Your script")
claude_breakdown = response['breakdown']['claude_4_opus']

print(f"Cache savings: {claude_breakdown['cache_savings']}")
# Output: "Cache savings: 2450 tokens" or "No cache"
```

### 3. Enhanced Response Structure

The `evaluate_script()` method now returns richer information:

```python
result = await council.evaluate_script(script)

# New fields
print(result['council_version'])
# → "November 2025 - Claude 4 Opus Edition"

print(result['breakdown']['claude_4_opus'])
# → {
#     "score": 87.5,
#     "weight": "40%",
#     "reasoning": "First 200 chars of reasoning...",
#     "extended_thinking": True,
#     "cache_savings": "2450 tokens"
# }

print(result['weights'])
# → {
#     "claude_4_opus": "40%",
#     "gemini_2_0_thinking": "35%",
#     "gpt_4o": "15%",
#     "deep_ctr": "10%"
# }
```

### 4. Tiered Model Selection

Three Claude models are now available for different use cases:

```python
# Opus - Deep psychological analysis (default)
await council.get_claude_opus_critique(script)

# Sonnet - Faster general scoring (fallback)
# Used automatically if Opus fails

# Haiku - Quick validation (optional)
await council.get_claude_haiku_quick_check(script)
```

## SDK Requirements

### Updated Dependencies

```txt
# Before
anthropic>=0.8.1

# After
anthropic>=0.40.0  # Required for Claude 4 and new features
```

**Installation:**
```bash
cd /home/user/geminivideo/services/titan-core
pip install --upgrade anthropic
```

## API Key Configuration

No changes required - uses existing `ANTHROPIC_API_KEY`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage Examples

### Basic Usage (Unchanged)

```python
from ai_council.council_of_titans import council

# Simple evaluation (all new features automatic)
result = await council.evaluate_script(
    script="Struggling with burnout? Here's how...",
    visual_features={
        "has_human_face": True,
        "hook_type": "pattern_interrupt"
    }
)

print(f"Score: {result['final_score']}")
print(f"Verdict: {result['verdict']}")
```

### Advanced Usage (New Features)

```python
# Access Claude 4 Opus directly
opus_result = await council.get_claude_opus_critique(
    script="Your script",
    use_extended_thinking=True
)

print(f"Claude's reasoning: {opus_result['reasoning']}")
print(f"Cache savings: {opus_result['cache_read_tokens']} tokens")

# Quick pre-filter with Haiku
haiku_result = await council.get_claude_haiku_quick_check(script)
if haiku_result['score'] < 60:
    print("Failed quick check, skipping expensive analysis")
else:
    # Run full council
    full_result = await council.evaluate_script(script)
```

### Cost Optimization Strategy

```python
async def analyze_batch(scripts: list[str]):
    """Optimize costs for batch analysis"""

    # Phase 1: Quick filter with Haiku (cheap)
    promising = []
    for script in scripts:
        quick = await council.get_claude_haiku_quick_check(script)
        if quick['score'] >= 70:
            promising.append(script)

    # Phase 2: Deep analysis with Opus (expensive but cached)
    results = []
    for script in promising:
        # Prompt caching saves 90% after first request
        result = await council.evaluate_script(script)
        results.append(result)

    return results
```

## Performance Characteristics

### Speed
- **Claude 4 Opus:** 3-5 seconds (with extended thinking)
- **Claude 4 Sonnet:** 1-2 seconds
- **Claude 3.5 Haiku:** 0.5-1 seconds

### Cost (per 1M tokens)
- **Opus Input:** $15 ($1.50 with cache)
- **Opus Output:** $75
- **Sonnet Input:** $3 ($0.30 with cache)
- **Haiku Input:** $0.80 ($0.08 with cache)

### Quality
- **Psychological Analysis:** Opus > Sonnet >> Haiku
- **Nuanced Understanding:** Opus excels at complex emotional triggers
- **Viral Trend Recognition:** Opus trained on 2025 data

## Migration Guide

### Breaking Changes
**None.** The upgrade is backward compatible.

### Recommended Actions

1. **Update SDK:**
   ```bash
   pip install --upgrade "anthropic>=0.40.0"
   ```

2. **Test Integration:**
   ```bash
   cd services/titan-core/ai_council
   python -m pytest test_pipeline_integration.py
   ```

3. **Monitor Costs:**
   - First week: Track cache hit rate
   - Expect 70-90% cache hits after warm-up
   - Monitor `cache_read_tokens` in responses

4. **Review Weights:**
   - New 40% weight for Claude 4 Opus
   - Approve threshold may need adjustment
   - Test with sample scripts

### Rollback Plan

If issues arise, rollback by editing `council_of_titans.py`:

```python
# Temporarily revert to Claude 3.5 Sonnet
self.claude_opus = "claude-3-5-sonnet-20241022"
```

## Monitoring & Observability

### Key Metrics to Track

```python
# After each evaluation
result = await council.evaluate_script(script)

# Track these
metrics = {
    "claude_score": result['breakdown']['claude_4_opus']['score'],
    "claude_weight": 0.40,
    "extended_thinking": result['breakdown']['claude_4_opus']['extended_thinking'],
    "cache_hit": result['breakdown']['claude_4_opus']['cache_savings'] != "No cache",
    "final_score": result['final_score']
}
```

### Expected Behavior

- **Cache Hit Rate:** 70-90% after first request
- **Score Changes:** May see 2-5 point shifts due to improved psychology
- **Reasoning Quality:** More detailed and nuanced
- **Response Time:** Slightly slower due to extended thinking (3-5s vs 1-2s)

## Troubleshooting

### Issue: "Extended thinking not available"
**Solution:** Update to `anthropic>=0.40.0`

### Issue: High costs
**Cause:** Cache not hitting
**Solution:**
- Ensure system prompt isn't changing
- Check cache TTL (5 minutes)
- Consider warming cache with common scripts

### Issue: Scores differ from Claude 3.5
**Expected:** Claude 4 Opus has different calibration
**Action:**
- Review score distributions over 100+ samples
- Adjust approval thresholds if needed
- Claude 4 tends to be more nuanced (lower scores for mediocre content)

### Issue: Fallback to Sonnet too often
**Cause:** Opus errors or timeouts
**Solution:**
- Check API key has Opus access
- Review error logs
- Increase timeout if needed

## Future Enhancements

### Potential Additions

1. **Computer Use API** (when available)
   - Automated UI testing for landing pages
   - Screenshot analysis of competitor ads
   - Real-time web scraping for trend analysis

2. **Multi-Modal Analysis**
   - Image/video analysis with Claude 4 Opus
   - Visual hook strength evaluation
   - Scene-by-scene psychological impact

3. **Adaptive Weighting**
   - Dynamic weights based on content type
   - Industry-specific weight profiles
   - A/B testing of weight configurations

4. **Reasoning Persistence**
   - Store Claude's thinking for training data
   - Build knowledge base of psychological patterns
   - Fine-tune smaller models on Opus reasoning

## References

- [Anthropic Claude 4 Announcement](https://www.anthropic.com/claude-4)
- [Extended Thinking Documentation](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)
- [Prompt Caching Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Council of Titans Source](/services/titan-core/ai_council/council_of_titans.py)

## Support

Questions or issues? Contact:
- **AI Team:** #ai-council-support
- **Documentation:** See inline code comments
- **Testing:** Run `test_pipeline_integration.py`

---

**Last Updated:** December 5, 2025
**Author:** AI Engineering Team
**Status:** ✅ Production Ready
