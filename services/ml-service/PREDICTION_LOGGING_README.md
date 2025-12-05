# Prediction Logging System - €5M Investment Validation

## Overview

The Prediction Logging System is a production-grade infrastructure for tracking all ML predictions and comparing them with actual campaign performance. This system is critical for:

- **Model Validation**: Measure and improve ML model accuracy over time
- **ROI Verification**: Validate predictions against real-world performance
- **Investor Confidence**: Provide transparent, auditable prediction tracking for €5M investment
- **Continuous Improvement**: Identify patterns in prediction errors to enhance models

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prediction Lifecycle                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. PREDICTION PHASE                                         │
│     ├─ ML Model generates predictions                       │
│     ├─ PredictionLogger.log_prediction()                    │
│     └─ Store: video_id, predicted_ctr, predicted_roas, etc. │
│                                                              │
│  2. CAMPAIGN RUNS (7+ days)                                  │
│     ├─ Ad platforms deliver impressions                     │
│     ├─ Real users click, convert                            │
│     └─ Actual performance data accumulates                  │
│                                                              │
│  3. VALIDATION PHASE                                         │
│     ├─ Fetch actual performance from platforms              │
│     ├─ PredictionLogger.update_with_actuals()               │
│     ├─ Calculate accuracy metrics                           │
│     └─ Store comparison results                             │
│                                                              │
│  4. ANALYSIS & IMPROVEMENT                                   │
│     ├─ Aggregate accuracy statistics                        │
│     ├─ Identify error patterns                              │
│     └─ Feed insights back to model training                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Database Migration

Apply the prediction logging schema to your database:

```bash
# From project root
psql $DATABASE_URL -f database_migrations/005_prediction_logging.sql
```

Or using Docker:

```bash
docker exec -i geminivideo-db psql -U geminivideo -d geminivideo < database_migrations/005_prediction_logging.sql
```

This creates:
- `predictions` table with full schema
- 7 analytical views for performance analysis
- Performance indexes for fast queries
- Helper functions for accuracy calculations

### 2. Verify Installation

Check that the table was created:

```sql
-- Check table exists
SELECT table_name FROM information_schema.tables
WHERE table_name = 'predictions';

-- Check views
SELECT table_name FROM information_schema.views
WHERE table_name LIKE 'prediction_%';
```

## Usage

### Basic Usage

```python
from src.prediction_logger import PredictionLogger

# Initialize logger
logger = PredictionLogger()

# Step 1: Log a prediction when model makes it
prediction_id = await logger.log_prediction(
    video_id="video_abc123",
    ad_id="fb_ad_789456",
    predicted_ctr=0.045,           # 4.5% predicted CTR
    predicted_roas=3.2,            # 3.2x predicted ROAS
    predicted_conversion=0.012,    # 1.2% predicted conversion
    council_score=0.87,            # 87% AI council confidence
    hook_type="problem_solution",  # Hook strategy used
    template_type="ugc_style",     # Template style
    platform="meta",               # Meta/Facebook platform
    metadata={
        "model_version": "v2.1",
        "feature_set": "full",
        "campaign_id": "campaign_xyz"
    }
)

# Save prediction_id for later (typically in your video/campaign record)
print(f"Logged prediction: {prediction_id}")
```

### Update with Actual Performance

After campaign runs (typically 7+ days):

```python
# Step 2: Update with actual performance from platform
result = await logger.update_with_actuals(
    prediction_id=prediction_id,
    actual_ctr=0.048,        # 4.8% actual CTR (better than predicted!)
    actual_roas=3.5,         # 3.5x actual ROAS
    actual_conversion=0.013, # 1.3% actual conversion
    impressions=10000,       # Total impressions delivered
    clicks=480,              # Total clicks received
    spend=150.00             # Total spend in USD
)

# Analyze accuracy
print(f"Overall Accuracy: {result['accuracy']['overall_accuracy']:.2f}%")
print(f"CTR Error: {result['errors']['ctr_error']:.4f}")
print(f"ROAS Error: {result['errors']['roas_error']:.2f}")
```

### Get Pending Predictions

Find predictions that need actual data:

```python
# Get predictions older than 7 days without actuals
pending = await logger.get_pending_predictions(
    days_old=7,
    platform="meta",           # Optional: filter by platform
    min_council_score=0.8      # Optional: only high-confidence predictions
)

print(f"Found {len(pending)} predictions needing actuals")

for pred in pending:
    print(f"  {pred['id']}: video {pred['video_id']}, created {pred['created_at']}")
```

### Model Performance Statistics

```python
# Get aggregate performance stats
stats = await logger.get_model_performance_stats(
    days=30,              # Last 30 days
    platform="meta",      # Optional: filter by platform
    hook_type="problem_solution"  # Optional: filter by hook type
)

print(f"Total Predictions: {stats['total_predictions']}")
print(f"With Actuals: {stats['predictions_with_actuals']}")
print(f"Average Accuracy: {stats['avg_overall_accuracy']:.2f}%")
print(f"Avg CTR Error: {stats['avg_ctr_error']:.5f}")
print(f"Avg ROAS Error: {stats['avg_roas_error']:.2f}")
```

### Convenience Functions

For simpler usage:

```python
from src.prediction_logger import (
    log_prediction,
    update_prediction_with_actuals,
    get_model_accuracy
)

# Log prediction
prediction_id = await log_prediction(video_id="...", ad_id="...", ...)

# Update with actuals
result = await update_prediction_with_actuals(
    prediction_id=prediction_id,
    actual_ctr=0.048,
    ...
)

# Get accuracy stats
stats = await get_model_accuracy(days=30)
```

## Analytical Queries

The migration creates several views for analysis:

### Overall Model Accuracy

```sql
SELECT * FROM prediction_accuracy_summary;
```

Returns:
- Total predictions
- Predictions with actuals
- Average CTR error, ROAS error, conversion error
- Accuracy percentages
- Council score correlation

### Platform Comparison

```sql
SELECT * FROM prediction_accuracy_by_platform;
```

Compare model performance across Meta, TikTok, Google, etc.

### Hook Type Performance

```sql
SELECT * FROM prediction_accuracy_by_hook
ORDER BY avg_actual_ctr DESC;
```

See which hook types perform best and where predictions are most accurate.

### Daily Trends

```sql
SELECT * FROM prediction_accuracy_daily
WHERE prediction_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY prediction_date DESC;
```

Track model accuracy improvement over time.

### Outlier Investigation

```sql
SELECT * FROM prediction_outliers
LIMIT 20;
```

Find predictions with large errors for investigation and model improvement.

### High Confidence Predictions

```sql
SELECT * FROM high_confidence_predictions
LIMIT 20;
```

Validate that high council scores correlate with high accuracy.

## Integration Examples

### With CTR Model

```python
from src.enhanced_ctr_model import EnhancedCTRModel
from src.prediction_logger import log_prediction

model = EnhancedCTRModel()

# Get prediction from model
prediction = await model.predict({
    "hook_type": "problem_solution",
    "template_type": "ugc_style",
    "platform": "meta",
    # ... other features
})

# Log it immediately
prediction_id = await log_prediction(
    video_id=video_id,
    ad_id=ad_id,
    predicted_ctr=prediction['ctr'],
    predicted_roas=prediction['roas'],
    predicted_conversion=prediction['conversion'],
    council_score=prediction['confidence'],
    hook_type="problem_solution",
    template_type="ugc_style",
    platform="meta"
)

# Store prediction_id in video metadata for later
video.metadata['prediction_id'] = prediction_id
```

### With Campaign Tracker

```python
from campaign_tracker import CampaignTracker
from src.prediction_logger import update_prediction_with_actuals

tracker = CampaignTracker()

# Fetch actual performance
performance = await tracker.get_ad_performance(ad_id)

# Update prediction with actuals
if video.metadata.get('prediction_id'):
    await update_prediction_with_actuals(
        prediction_id=video.metadata['prediction_id'],
        actual_ctr=performance['ctr'],
        actual_roas=performance['roas'],
        actual_conversion=performance['conversion_rate'],
        impressions=performance['impressions'],
        clicks=performance['clicks'],
        spend=performance['spend']
    )
```

### Scheduled Actuals Fetching

```python
# scheduled_task.py
import asyncio
from src.prediction_logger import PredictionLogger
from campaign_tracker import CampaignTracker

async def fetch_pending_actuals():
    """
    Scheduled task to fetch actuals for predictions older than 7 days.
    Run this daily via cron or scheduler.
    """
    logger = PredictionLogger()
    tracker = CampaignTracker()

    # Get pending predictions
    pending = await logger.get_pending_predictions(days_old=7)

    print(f"Processing {len(pending)} pending predictions...")

    for pred in pending:
        try:
            # Fetch actual performance from platform
            performance = await tracker.get_ad_performance(pred['ad_id'])

            if performance and performance['impressions'] > 100:  # Minimum threshold
                # Update with actuals
                await logger.update_with_actuals(
                    prediction_id=pred['id'],
                    actual_ctr=performance['ctr'],
                    actual_roas=performance['roas'],
                    actual_conversion=performance['conversion_rate'],
                    impressions=performance['impressions'],
                    clicks=performance['clicks'],
                    spend=performance['spend']
                )
                print(f"  ✓ Updated {pred['id']}")
            else:
                print(f"  ⊘ Insufficient data for {pred['id']}")

        except Exception as e:
            print(f"  ✗ Failed to update {pred['id']}: {e}")

    print(f"Completed processing {len(pending)} predictions")

# Run daily
asyncio.run(fetch_pending_actuals())
```

## Testing

### Run Tests

```bash
# Full test suite
pytest services/ml-service/test_prediction_logger.py -v

# Run demo workflow
python services/ml-service/test_prediction_logger.py
```

### Manual Testing

```python
# Test in Python REPL
import asyncio
from src.prediction_logger import PredictionLogger

async def test():
    logger = PredictionLogger()

    # Log test prediction
    pred_id = await logger.log_prediction(
        video_id="test_video",
        ad_id="test_ad",
        predicted_ctr=0.045,
        predicted_roas=3.2,
        predicted_conversion=0.012,
        council_score=0.87,
        hook_type="problem_solution",
        template_type="ugc_style",
        platform="meta"
    )
    print(f"Created: {pred_id}")

    # Retrieve it
    pred = await logger.get_prediction_by_id(pred_id)
    print(f"Retrieved: {pred}")

asyncio.run(test())
```

## Performance Considerations

- **Indexes**: All common query patterns are indexed (video_id, platform, hook_type, created_at)
- **Async Operations**: All database operations are async for high throughput
- **Batch Updates**: For bulk actuals updates, use transactions
- **View Materialization**: For very large datasets, consider materializing views

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Prediction Coverage**: % of predictions with actuals
2. **Average Accuracy**: Overall model accuracy trend
3. **Error Patterns**: Systematic over/under-prediction
4. **Council Calibration**: High council score → high accuracy correlation
5. **Platform Performance**: Accuracy variations by platform

### Recommended Alerts

```sql
-- Alert if average accuracy drops below 80%
SELECT avg_overall_accuracy
FROM prediction_accuracy_summary
WHERE avg_overall_accuracy < 80;

-- Alert if many pending predictions (> 100 older than 14 days)
SELECT COUNT(*) as pending_count
FROM predictions
WHERE actual_ctr IS NULL
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '14 days';
```

## Troubleshooting

### Issue: Predictions not updating with actuals

**Check:**
1. Verify prediction_id is stored with video/ad record
2. Check ad_id matches platform ad identifier
3. Ensure campaign has run long enough (7+ days recommended)
4. Verify platform API access for fetching performance

### Issue: Low accuracy scores

**Investigate:**
1. Query `prediction_outliers` view for systematic errors
2. Check if certain hook types or platforms have lower accuracy
3. Review feature engineering - are critical features missing?
4. Examine high confidence but low accuracy predictions

### Issue: Database performance

**Optimize:**
1. Ensure indexes are present (check with `\d predictions`)
2. Consider partitioning by created_at for large datasets (>1M rows)
3. Materialize views if queries are slow
4. Archive old predictions (>1 year) to separate table

## Future Enhancements

- [ ] Automated scheduled actuals fetching
- [ ] Real-time accuracy dashboard
- [ ] Email alerts for accuracy drops
- [ ] Model retraining triggers based on accuracy thresholds
- [ ] Multi-model prediction tracking (A/B test different models)
- [ ] Prediction explanation storage (SHAP values, feature importance)

## Support

For issues or questions:
- Check test suite: `test_prediction_logger.py`
- Review SQL views for analytical queries
- Examine `prediction_outliers` for problematic predictions

## License

This system is part of the GeminiVideo platform - €5M Investment Grade Infrastructure.
