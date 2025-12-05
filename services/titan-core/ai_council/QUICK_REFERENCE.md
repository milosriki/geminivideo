# OpenAI November 2025 - Quick Reference Guide

## Model Selection at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OPENAI MODEL SELECTOR                                │
└─────────────────────────────────────────────────────────────────────────────┘

Need complex reasoning?          → o1
Need fast validation?            → o1-mini
Need vision analysis?            → gpt-4o-2024-11-20
Need cost optimization?          → gpt-4o-mini
Need bulk processing?            → Batch API + gpt-4o-mini

┌─────────────────────────────────────────────────────────────────────────────┐
│                          COST COMPARISON                                    │
└─────────────────────────────────────────────────────────────────────────────┘

1000 Scripts Analysis:

Old GPT-4o:           ██████████████████████████████████████████████  $50.00
GPT-4o-mini:         █████                                             $5.00  (90% ↓)
Batch + GPT-4o-mini: ██                                                $2.50  (95% ↓)

┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUALITY vs SPEED vs COST                               │
└─────────────────────────────────────────────────────────────────────────────┘

             Quality    Speed      Cost
o1           ⭐⭐⭐⭐⭐    ⭐⭐         💰💰💰💰
o1-mini      ⭐⭐⭐⭐      ⭐⭐⭐        💰💰💰
gpt-4o       ⭐⭐⭐⭐      ⭐⭐⭐⭐      💰💰💰
gpt-4o-mini  ⭐⭐⭐       ⭐⭐⭐⭐⭐     💰
Batch        ⭐⭐⭐       ⭐           💰
```

---

## Code Snippets

### 1. Simple Evaluation (Recommended)
```python
from council_of_titans import council

# Cost-optimized with gpt-4o-mini
result = await council.evaluate_script(script)
print(f"Score: {result['final_score']}")
```

### 2. High-Quality Reasoning
```python
# Use o1 for complex analysis
result = await council.evaluate_script(script, use_o1=True)
```

### 3. Vision Analysis
```python
# Analyze thumbnail with GPT-4o Vision
result = await council.evaluate_script(
    script,
    image_path="/path/to/thumbnail.jpg"
)
print(result['vision_analysis'])
```

### 4. Batch Processing
```python
# Queue 1000 scripts for overnight analysis
batch_id = await council.batch_create_job(scripts)

# Retrieve results next day (50% cheaper!)
results = await council.batch_retrieve_results(batch_id)
```

### 5. Direct Model Access
```python
# o1 reasoning
o1_result = await council.get_openai_o1_critique(script)

# gpt-4o-mini with structured output
mini_result = await council.get_gpt4o_critique_simple(script)

# Vision analysis
vision = await council.get_gpt4o_vision_analysis(image_path)
```

---

## When to Use What

### Use o1 When:
- ✅ Final approval for high-budget campaigns
- ✅ Complex script requiring deep logical analysis
- ✅ Strategic decision-making
- ✅ Learning from top-performing content
- ❌ Don't use for: Bulk scoring, simple validation

### Use o1-mini When:
- ✅ Quick validation checks
- ✅ Pre-screening before full review
- ✅ QA processes
- ✅ Rapid iteration cycles
- ❌ Don't use for: Final approvals, complex reasoning

### Use GPT-4o-2024-11-20 When:
- ✅ Video thumbnail analysis
- ✅ Visual composition evaluation
- ✅ Color psychology assessment
- ✅ Multimodal (image + text) analysis
- ❌ Don't use for: Text-only tasks (use mini instead)

### Use GPT-4o-mini When:
- ✅ High-volume script evaluation (100+ scripts)
- ✅ A/B test variations
- ✅ Quick scoring (0-100 ratings)
- ✅ Real-time preview feedback
- ✅ Cost-sensitive applications
- ❌ Don't use for: Complex reasoning, vision tasks

### Use Batch API When:
- ✅ Non-urgent bulk analysis (24h turnaround OK)
- ✅ A/B testing 50-500 variations
- ✅ Historical data processing
- ✅ Overnight analysis jobs
- ✅ Maximum cost savings needed (95% reduction)
- ❌ Don't use for: Real-time feedback, urgent requests

---

## Response Structures

### Standard Evaluation
```python
{
    "final_score": 87.5,
    "breakdown": {
        "gemini_2_0_thinking": 88.0,
        "openai": 89.0,
        "openai_model": "gpt-4o-mini",
        "claude_3_5": 85.0,
        "deep_ctr": 87.0
    },
    "verdict": "APPROVE",
    "council_members": {...}
}
```

### With Vision Analysis
```python
{
    "final_score": 87.5,
    "breakdown": {...},
    "verdict": "APPROVE",
    "vision_analysis": {
        "visual_score": 85.0,
        "has_human_face": true,
        "scene_description": "Close-up with emotion",
        "attention_elements": ["Human face", "Bold text"]
    }
}
```

### Structured Score (gpt-4o-mini)
```python
{
    "score": 87.0,
    "confidence": 0.92,
    "reasoning": "Strong hook with pattern interrupt...",
    "source": "GPT-4o-mini (Structured)"
}
```

---

## Environment Setup

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional (defaults shown)
export OPENAI_O1_MODEL="o1"
export OPENAI_GPT4O_MINI="gpt-4o-mini"
export OPENAI_GPT4O_LATEST="gpt-4o-2024-11-20"

# Enable batch processing
export OPENAI_BATCH_ENABLED="true"
```

---

## Common Patterns

### Pattern 1: Cost-Optimized Pipeline
```python
# Stage 1: Fast pre-screening (o1-mini)
quick_result = await council.get_openai_o1_critique(script, mode="mini")

if quick_result['score'] > 70:
    # Stage 2: Full council review (gpt-4o-mini)
    full_result = await council.evaluate_script(script)

    if full_result['final_score'] > 85:
        # Stage 3: Deep analysis (o1)
        detailed = await council.evaluate_with_detailed_critique(script)
```

### Pattern 2: Multimodal Evaluation
```python
# Analyze script + thumbnail together
result = await council.evaluate_script(
    script=script_text,
    image_path=thumbnail_path,
    visual_features={
        "hook_type": "pattern_interrupt",
        "scene_count": 3,
        "high_contrast": True
    }
)

# Check visual and text alignment
text_score = result['final_score']
visual_score = result['vision_analysis']['visual_score']
alignment = abs(text_score - visual_score) < 10  # Within 10 points
```

### Pattern 3: Batch A/B Testing
```python
# Generate 100 variations
variations = [generate_variant(i) for i in range(100)]

# Queue for overnight analysis
batch_id = await council.batch_create_job(variations)

# Next day: retrieve and rank
results = await council.batch_retrieve_results(batch_id)
top_scripts = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
```

---

## Troubleshooting Quick Fixes

### Error: "Model not found"
```bash
# Update OpenAI client
pip install --upgrade openai
```

### Error: "Batch API disabled"
```bash
export OPENAI_BATCH_ENABLED=true
```

### Error: "Vision analysis failed"
```python
# Check image exists
import os
assert os.path.exists(image_path), "Image not found"

# Or use URL instead
image_path = "https://example.com/image.jpg"
```

### Error: "Reasoning tokens exceeded"
```python
# o1 has token limits - break into smaller chunks
chunks = split_script_into_chunks(long_script)
results = [await council.get_openai_o1_critique(chunk) for chunk in chunks]
```

---

## Migration Checklist

- [ ] Update `council_of_titans.py` (done by AGENT 33)
- [ ] Update `config.py` with new model settings
- [ ] Set environment variables
- [ ] Test with examples: `python openai_2025_examples.py`
- [ ] Update API keys if needed (o1 access)
- [ ] Enable batch API if desired
- [ ] Monitor costs in first week
- [ ] Update downstream services using council

---

## Performance Tips

1. **Default to gpt-4o-mini** - 90% cheaper, same quality for scoring
2. **Use o1 sparingly** - Only for high-stakes decisions
3. **Batch when possible** - 50% additional savings
4. **Cache vision analysis** - Don't re-analyze same thumbnails
5. **Parallel processing** - Council runs all models in parallel

---

## Support

- **Documentation**: `/services/titan-core/ai_council/OPENAI_2025_UPGRADE.md`
- **Examples**: `/services/titan-core/ai_council/openai_2025_examples.py`
- **Config**: `/services/titan-core/ai_council/config.py`
- **OpenAI Docs**: https://platform.openai.com/docs/models

---

**Last Updated**: December 2025 by AGENT 33
