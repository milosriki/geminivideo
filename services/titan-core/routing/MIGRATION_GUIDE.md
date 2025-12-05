# Migration Guide - Smart Model Routing

This guide helps you migrate from direct model calls to smart routing for 80% cost savings.

## Overview

Smart routing is a **drop-in replacement** for existing model calls. You can:
1. Keep existing code working (no breaking changes)
2. Gradually migrate to smart routing
3. Run A/B tests to compare performance

## Migration Strategies

### Strategy 1: Drop-in Replacement (Recommended)

Replace the existing ensemble with the smart version. No API changes required.

**Before:**
```python
from backend_core.engines.ensemble import council

result = await council.evaluate_script(script, niche)
```

**After:**
```python
from backend_core.routing.integration import smart_council as council

result = await council.evaluate_script(script, niche)
# Same API, but with smart routing!
```

### Strategy 2: Parallel Testing

Run both systems in parallel to compare.

```python
from backend_core.engines.ensemble import council as original_council
from backend_core.routing.integration import smart_council

# Run both
original_result = await original_council.evaluate_script(script, niche)
smart_result = await smart_council.evaluate_script(script, niche)

# Compare results
print(f"Original: {original_result['final_score']}")
print(f"Smart: {smart_result['final_score']}")
print(f"Cost: ${smart_result['_routing_metadata']['cost']:.6f}")
```

### Strategy 3: Gradual Rollout with A/B Testing

Use A/B testing to gradually roll out to users.

```python
from backend_core.routing.ab_testing import ab_test_manager

# Enable A/B testing
ab_test_manager.enabled = True

# 50% of traffic gets smart routing
# System automatically assigns strategies

# Monitor results
results = ab_test_manager.get_results()
if results['winner']['strategy'] == 'smart_routing':
    # Increase traffic to smart routing
    pass
```

## Step-by-Step Migration

### Step 1: Install Dependencies

Ensure httpx is installed:
```bash
pip install httpx>=0.25.0
```

### Step 2: Set Environment Variables

```bash
# Required API keys (you already have these)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."

# Optional routing configuration
export ROUTER_ESCALATION_THRESHOLD=0.7
export ROUTER_ENABLE_ESCALATION=true
export ROUTER_COST_OPTIMIZATION=true
```

### Step 3: Test Smart Routing

Run the example to verify everything works:
```bash
python services/titan-core/routing/example_usage.py
```

### Step 4: Update Imports

Replace direct model calls:

**Option A: Ensemble Evaluation**
```python
# Old
from backend_core.engines.ensemble import council

# New
from backend_core.routing.integration import smart_council as council
```

**Option B: Single Model Execution**
```python
# Old
from anthropic import AsyncAnthropic
anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await anthropic.messages.create(...)

# New
from backend_core.routing.integration import smart_executor
result = await smart_executor.execute(
    text=prompt,
    task_type="analysis"
)
```

### Step 5: Monitor Performance

```python
from backend_core.routing.dashboard import router_dashboard

# Get dashboard
dashboard = router_dashboard.get_dashboard()

# Check savings
print(f"Cost savings: {dashboard['overview']['cost_savings_percentage']:.1f}%")

# Check quality
print(f"Avg confidence: {dashboard['overview']['avg_confidence']:.3f}")
```

### Step 6: Optimize Configuration

Based on your metrics, adjust settings:

```python
from backend_core.routing import ModelRouter

# More aggressive cost optimization
router = ModelRouter(
    escalation_threshold=0.6,  # Lower = fewer escalations = more cost savings
    cost_optimization_mode=True
)

# Quality-focused
router = ModelRouter(
    escalation_threshold=0.8,  # Higher = more escalations = better quality
    cost_optimization_mode=False
)
```

## Integration Points

### 1. AI Council Orchestrator

**File:** `services/titan-core/ai_council/orchestrator.py`

**Current:**
```python
from backend_core.engines.ensemble import council

critique = await council.evaluate_script(last_msg)
```

**Updated:**
```python
from backend_core.routing.integration import smart_council as council

critique = await smart_council.evaluate_script(last_msg)
# Includes routing metadata in critique['_routing_metadata']
```

### 2. API Endpoints

**File:** `services/titan-core/api/main.py`

Add routing endpoints:
```python
from backend_core.routing.api import router as routing_router

app.include_router(routing_router, prefix="/api/v1/routing", tags=["routing"])
```

### 3. Pipeline Integration

**File:** `services/titan-core/api/pipeline.py`

Replace direct model calls with smart executor:
```python
from backend_core.routing.integration import smart_executor

# For any model call
result = await smart_executor.execute(
    text=input_text,
    task_type="classification",  # or "creative", "analysis", etc.
)
```

## Backwards Compatibility

The smart routing system maintains 100% API compatibility:

```python
# Original API
result = await council.evaluate_script(script, niche)
# Returns: {"verdict": ..., "final_score": ..., "feedback": ...}

# Smart routing API (same!)
result = await smart_council.evaluate_script(script, niche)
# Returns: {"verdict": ..., "final_score": ..., "feedback": ..., "_routing_metadata": {...}}
```

The only difference is the additional `_routing_metadata` field, which you can ignore if not needed.

## Common Issues & Solutions

### Issue 1: API Keys Not Set

**Error:** `ANTHROPIC_API_KEY environment variable not set`

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

### Issue 2: Import Errors

**Error:** `ModuleNotFoundError: No module named 'httpx'`

**Solution:**
```bash
pip install httpx>=0.25.0
```

### Issue 3: Low Confidence Scores

**Problem:** Average confidence below 0.7

**Solution:**
```python
# Adjust escalation threshold
router.escalation_threshold = 0.6  # Lower threshold

# Or disable cost optimization
router.cost_optimization_mode = False
```

### Issue 4: High Costs

**Problem:** Not seeing expected cost savings

**Solution:**
```python
# Enable cost optimization
router.cost_optimization_mode = True

# Check complexity classification
from backend_core.routing.analytics import analytics
summary = analytics.get_summary()
print(summary['by_complexity'])

# Adjust classification if needed
```

## Performance Expectations

After migration, you should see:

### Cost Savings
- **Simple tasks**: 90-95% savings (mini models)
- **Medium tasks**: 50-70% savings (standard models)
- **Complex tasks**: 0-20% savings (still use premium models)
- **Overall**: 70-80% savings

### Quality Maintenance
- **Confidence scores**: > 0.75 average
- **Escalation rate**: 10-20%
- **Accuracy**: Same as original system

### Latency
- **Simple tasks**: Faster (smaller models)
- **Medium tasks**: Same
- **Complex tasks**: Same
- **With escalation**: +1-2 seconds

## Monitoring & Alerts

Set up monitoring:

```python
from backend_core.routing.dashboard import router_dashboard

# Get alerts
dashboard = router_dashboard.get_dashboard()
for alert in dashboard['alerts']:
    print(f"[{alert['level']}] {alert['message']}")
    print(f"Action: {alert['action']}")
```

Configure alert thresholds:
- **Low confidence**: < 0.6 → Use better models
- **High escalation**: > 30% → Review classification
- **High costs**: > $0.01/request → Enable cost optimization

## Rollback Plan

If you need to rollback:

1. **Change imports back:**
```python
# Rollback
from backend_core.engines.ensemble import council
```

2. **Keep smart routing disabled:**
```python
# Use original system
ENABLE_SMART_ROUTING=false
```

3. **No database changes needed** - routing is stateless

## Success Criteria

Migration is successful when:

✅ Cost savings > 70%
✅ Average confidence > 0.75
✅ Escalation rate < 25%
✅ No increase in error rates
✅ Latency impact < 10%

## Support

For issues:
1. Check logs: `router_dashboard.get_dashboard()['alerts']`
2. View analytics: `analytics.get_summary()`
3. Export report: `analytics.export_report('/tmp/report.json')`

## Next Steps

After successful migration:

1. **Enable A/B testing** to optimize routing strategies
2. **Set up monitoring** dashboards
3. **Tune thresholds** based on your use case
4. **Share results** with the team

---

## Quick Reference

### Import Changes
```python
# Before → After
ensemble.council → routing.integration.smart_council
```

### Configuration
```python
ROUTER_ESCALATION_THRESHOLD=0.7
ROUTER_ENABLE_ESCALATION=true
ROUTER_COST_OPTIMIZATION=true
```

### Monitoring
```python
router_dashboard.get_dashboard()  # Complete view
analytics.get_summary()           # Cost analysis
ab_test_manager.get_results()     # A/B test results
```

### CLI
```bash
python routing/cli.py status      # Current status
python routing/cli.py cost        # Cost analysis
python routing/cli.py dashboard   # Full dashboard
```
