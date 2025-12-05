# Agent 44: Auto-Promotion System Integration Guide

## Overview

The Auto-Promotion System automatically detects A/B test winners, reallocates budgets, extracts insights, and creates compound learning effects.

**10x Leverage:** Each test makes the next one better through automated insight extraction and pattern storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTO-PROMOTION SYSTEM                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐│
│  │  AutoPromoter│─────▶│ Meta API     │─────▶│ Budget    ││
│  │              │      │ Integration  │      │ Realloc   ││
│  └──────┬───────┘      └──────────────┘      └───────────┘│
│         │                                                    │
│         │              ┌──────────────┐      ┌───────────┐ │
│         └─────────────▶│ Claude API   │─────▶│ Insight   │ │
│                        │ Integration  │      │ Extract   │ │
│                        └──────────────┘      └───────────┘ │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐│
│  │  Scheduler   │─────▶│ Check Every  │─────▶│ Auto      ││
│  │              │      │ 6 Hours      │      │ Promote   ││
│  └──────────────┘      └──────────────┘      └───────────┘│
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐│
│  │  Pattern DB  │◀─────│ Store        │◀─────│ Compound  ││
│  │              │      │ Insights     │      │ Learning  ││
│  └──────────────┘      └──────────────┘      └───────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Files Created

### 1. Core Module: `/services/ml-service/src/auto_promoter.py`

Main auto-promotion logic:
- `AutoPromoter` class - Detects winners and promotes them
- Statistical significance testing (95% confidence)
- Meta API budget reallocation (80/20 split)
- Claude API insight extraction
- Pattern storage for compound learning
- Cumulative improvement tracking

### 2. Scheduler: `/services/ml-service/src/auto_promotion_scheduler.py`

Background job scheduler:
- `AutoPromotionScheduler` class - Runs periodic checks
- Default: Check every 6 hours
- Daily summary reports (9 AM)
- Weekly compound learning reports (Monday 9 AM)
- Manual trigger support

### 3. API Endpoints: `/services/ml-service/src/auto_promotion_endpoints.py`

FastAPI endpoints:
- `POST /api/ab/auto-promote/check` - Check single experiment
- `POST /api/ab/auto-promote/check-all` - Check all active experiments
- `GET /api/ab/auto-promote/history` - Get promotion history
- `GET /api/ab/auto-promote/compound-report` - Cumulative improvement report
- `GET /api/ab/auto-promote/dashboard` - Full dashboard data
- `GET /api/ab/auto-promote/scheduler/status` - Scheduler status
- `POST /api/ab/auto-promote/scheduler/trigger` - Force immediate check

## Integration Steps

### Step 1: Add to main.py startup

Add to the `startup_event()` function in `/services/ml-service/src/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("ML Service starting up...")

    # ... existing startup code ...

    # Initialize Auto-Promoter (Agent 44)
    try:
        from src.auto_promoter import initialize_auto_promoter
        from src.auto_promotion_scheduler import initialize_scheduler
        import os
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'titan-core', 'meta'))
        from marketing_api import RealMetaAdsManager

        # Get database session
        from shared.db.connection import get_session
        db_session = get_session()

        # Initialize Meta API manager (if credentials available)
        meta_api = None
        meta_token = os.getenv("META_ACCESS_TOKEN")
        meta_account = os.getenv("META_AD_ACCOUNT_ID")
        if meta_token and meta_account:
            meta_api = RealMetaAdsManager(
                access_token=meta_token,
                ad_account_id=meta_account
            )
            logger.info("Meta API manager initialized for auto-promotion")
        else:
            logger.warning("Meta API credentials not found - budget reallocation disabled")

        # Initialize AutoPromoter
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        promoter = initialize_auto_promoter(
            db_session=db_session,
            meta_api_manager=meta_api,
            anthropic_api_key=anthropic_key
        )

        # Initialize and start scheduler
        notification_webhook = os.getenv("PROMOTION_NOTIFICATION_WEBHOOK")
        check_interval = int(os.getenv("AUTO_PROMOTE_CHECK_INTERVAL_HOURS", "6"))

        scheduler = initialize_scheduler(
            auto_promoter=promoter,
            check_interval_hours=check_interval,
            notification_webhook=notification_webhook
        )

        logger.info("✓ Auto-Promotion System initialized and started")

    except Exception as e:
        logger.error(f"Failed to initialize Auto-Promotion System: {e}")
```

### Step 2: Register API routes

Add after the other route registrations in `main.py`:

```python
# Register Auto-Promotion routes (Agent 44)
from src.auto_promotion_endpoints import register_auto_promotion_routes
register_auto_promotion_routes(app)
```

### Step 3: Environment Variables

Add to `.env`:

```bash
# Auto-Promotion Configuration (Agent 44)
META_ACCESS_TOKEN=your-meta-access-token
META_AD_ACCOUNT_ID=act_123456789
ANTHROPIC_API_KEY=sk-ant-your-key
AUTO_PROMOTE_CHECK_INTERVAL_HOURS=6
PROMOTION_NOTIFICATION_WEBHOOK=https://your-webhook.com/promotions
```

### Step 4: Install Dependencies

Add to `requirements.txt`:

```txt
apscheduler>=3.10.0
anthropic>=0.18.0
facebook-business>=19.0.0
aiohttp>=3.9.0
scipy>=1.11.0
numpy>=1.24.0
```

Install:
```bash
cd /home/user/geminivideo/services/ml-service
pip install -r requirements.txt
```

## How It Works

### 1. Automatic Detection

Every 6 hours (configurable), the scheduler:
1. Queries all active A/B test experiments
2. Checks if they have enough data (min 100 samples/variant)
3. Runs statistical significance test (t-test)
4. Identifies winners with 95%+ confidence

### 2. Budget Reallocation

When a winner is detected:
1. Get current budgets from Meta API
2. Gradually shift budget to winner:
   - Phase 1: 60/40 split (immediate)
   - Phase 2: 70/30 split (1 hour later)
   - Phase 3: 80/20 split (2 hours later)
3. Loser keeps 20% for continued learning

### 3. Insight Extraction

Using Claude AI:
1. Analyze winner creative (hook, visuals, message)
2. Compare to loser performance
3. Extract patterns:
   - Hook formulas that worked
   - Visual elements that contributed
   - Specific winning factors
   - Replicable patterns
   - Audience resonance insights

### 4. Pattern Storage

Insights are stored in the knowledge base:
- Hook patterns → `knowledge_base_vectors` table
- Visual elements → Indexed for similarity search
- Best practices → Available for RAG-powered generation
- Confidence scores → Track success rates

### 5. Compound Learning

Each test improves the next:
```
Test 1: +15% improvement
Test 2: +12% improvement (using learnings from Test 1)
Test 3: +18% improvement (using learnings from Tests 1 & 2)

Compound Effect: (1.15 × 1.12 × 1.18) - 1 = 51.9% total improvement
```

## API Usage Examples

### Check Single Experiment

```bash
curl -X POST http://localhost:8003/api/ab/auto-promote/check \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "exp_12345",
    "force_promotion": false
  }'
```

Response:
```json
{
  "experiment_id": "exp_12345",
  "status": "promoted",
  "winner_ad_id": "ad_67890",
  "winner_metrics": {
    "ctr": 3.45,
    "impressions": 15000,
    "clicks": 518
  },
  "loser_ad_id": "ad_67891",
  "confidence": 0.97,
  "insights": {
    "hook_patterns": ["Question format", "Curiosity gap"],
    "visual_elements": ["Fast cuts", "Text overlays"],
    "winning_factors": [
      "Hook created immediate curiosity",
      "Visual pacing matched attention span",
      "CTA was clear and urgent"
    ]
  },
  "budget_reallocation": {
    "status": "completed",
    "winner_budget_pct": 0.80,
    "loser_budget_pct": 0.20
  },
  "message": "Winner promoted with 97.0% confidence",
  "promoted_at": "2025-12-05T10:30:00Z"
}
```

### Get Dashboard

```bash
curl http://localhost:8003/api/ab/auto-promote/dashboard
```

Response:
```json
{
  "summary": {
    "recent_promotions_7d": 5,
    "avg_confidence": 0.96,
    "avg_improvement_pct": 14.5,
    "total_experiments": 23,
    "compound_improvement_pct": 52.3
  },
  "recent_winners": [...],
  "compound_learning": {
    "total_experiments": 23,
    "compound_improvement_pct": 52.3,
    "avg_improvement_per_test": 14.2,
    "improvement_trend": [12.0, 15.5, 14.8, 13.2, 16.7]
  },
  "scheduler": {
    "is_running": true,
    "check_interval_hours": 6,
    "jobs": [
      {
        "id": "auto_promotion_check",
        "name": "Check and promote A/B test winners",
        "next_run": "2025-12-05T16:00:00Z"
      }
    ]
  }
}
```

### Check All Active Experiments

```bash
curl -X POST http://localhost:8003/api/ab/auto-promote/check-all
```

### Get Compound Learning Report

```bash
curl http://localhost:8003/api/ab/auto-promote/compound-report
```

### Manual Trigger

```bash
curl -X POST http://localhost:8003/api/ab/auto-promote/scheduler/trigger
```

## Database Schema

The system uses existing tables:
- `ab_tests` - Experiment definitions and results
- `performance_metrics` - Ad performance data
- `videos` - Creative content linked to ads
- `knowledge_base_vectors` - Winning patterns (to be added)

No migration needed - uses existing A/B test infrastructure!

## Configuration Options

### AutoPromoter Settings

```python
auto_promoter = AutoPromoter(
    db_session=db_session,
    meta_api_manager=meta_api,
    anthropic_api_key=anthropic_key,
    confidence_threshold=0.95,        # Require 95% confidence
    min_sample_size=100,              # Min 100 samples per variant
    winner_budget_pct=0.80,           # Winner gets 80%
    loser_budget_pct=0.20             # Loser gets 20%
)
```

### Scheduler Settings

```python
scheduler = AutoPromotionScheduler(
    auto_promoter=promoter,
    check_interval_hours=6,           # Check every 6 hours
    notification_webhook=webhook_url  # Slack/Discord webhook
)
```

## Monitoring

### Logs

The system logs all activities:
```
INFO: Checking experiment exp_12345 for promotion
INFO: Statistical test: confidence=0.973, winner=A
INFO: Winner: ad_67890 (CTR: 3.45%)
INFO: Budget reallocated: 80/20 split
INFO: Insights extracted: 5 winning factors identified
INFO: ✓ Experiment exp_12345 promoted successfully
```

### Metrics to Track

1. **Promotion Rate**: % of experiments promoted vs. continued
2. **Avg Confidence**: Average confidence of promotions
3. **Avg Improvement**: Average CTR improvement per test
4. **Compound Improvement**: Cumulative improvement over time
5. **Pattern Library Growth**: Number of patterns learned

## Benefits

### 1. Zero Manual Work
- Automatic winner detection
- Automatic budget reallocation
- No spreadsheets, no meetings

### 2. Compound Learning
- Each test improves the next
- Knowledge accumulates
- Performance compounds over time

### 3. Faster Iteration
- Winners promoted in hours, not days
- Budget optimized continuously
- Learning never stops

### 4. Data-Driven Decisions
- 95% statistical confidence
- Quantified improvements
- Reproducible patterns

### 5. Scale Efficiency
- Run 100+ experiments simultaneously
- All automatically optimized
- Human reviews only edge cases

## Testing

### Manual Test

1. Create test A/B experiment in database:
```sql
INSERT INTO ab_tests (test_id, model_type, model_a_id, model_b_id, status, start_date, end_date)
VALUES ('test_001', 'ctr_predictor', 'ad_001', 'ad_002', 'active', NOW(), NOW() + INTERVAL '7 days');
```

2. Add performance data for both variants

3. Trigger check:
```bash
curl -X POST http://localhost:8003/api/ab/auto-promote/check \
  -H "Content-Type: application/json" \
  -d '{"experiment_id": "test_001"}'
```

## Troubleshooting

### Auto-promoter not initialized
- Check database connection
- Verify Meta API credentials
- Check Anthropic API key

### Budget reallocation failing
- Verify Meta access token has ads_management permission
- Check ad account ID is correct
- Ensure ad sets exist and are active

### Insight extraction limited
- Requires Anthropic API key
- Falls back to basic metrics if unavailable
- Check API quota limits

## Next Steps

1. **Integrate with Frontend**: Add auto-promotion dashboard to UI
2. **Email Notifications**: Send weekly compound learning reports
3. **Pattern Recommendations**: Suggest patterns for new campaigns
4. **Multi-Objective**: Support ROAS, conversions, etc.
5. **A/A Testing**: Add baseline drift detection

## Support

For issues or questions:
- Check logs in `/services/ml-service/logs/`
- Review scheduler status: `GET /api/ab/auto-promote/scheduler/status`
- Force manual check: `POST /api/ab/auto-promote/scheduler/trigger`

---

**Agent 44 Complete** ✓

Auto-promotion creates COMPOUND LEARNING. Each test makes the next one better!
