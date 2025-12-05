# Prediction Logging System - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Apply Database Migration

```bash
# Option A: Run Python script (recommended)
cd /home/user/geminivideo/services/ml-service
python apply_prediction_migration.py

# Option B: Direct SQL
psql $DATABASE_URL -f ../../database_migrations/005_prediction_logging.sql
```

### 2. Verify Installation

```python
python -c "
import asyncio
from shared.db.connection import get_db_context
from sqlalchemy import text

async def check():
    async with get_db_context() as session:
        result = await session.execute(
            text('SELECT COUNT(*) FROM information_schema.tables WHERE table_name = \\'predictions\\'')
        )
        count = result.scalar()
        print(f'✓ Predictions table exists: {count == 1}')

asyncio.run(check())
"
```

### 3. Run Demo

```bash
# Run integration example
python example_prediction_integration.py

# Run full test suite
pytest test_prediction_logger.py -v
```

## 📝 Basic Usage (3 Steps)

### Step 1: Log Prediction (When Model Predicts)

```python
from src.prediction_logger import log_prediction

prediction_id = await log_prediction(
    video_id="abc123",
    ad_id="fb_ad_456",
    predicted_ctr=0.045,
    predicted_roas=3.2,
    predicted_conversion=0.012,
    council_score=0.87,
    hook_type="problem_solution",
    template_type="ugc_style",
    platform="meta"
)

# Store prediction_id in your video/campaign metadata
video.metadata['prediction_id'] = prediction_id
```

### Step 2: Campaign Runs (7+ Days)

Wait for campaign to accumulate performance data on the platform.

### Step 3: Update with Actuals

```python
from src.prediction_logger import update_prediction_with_actuals

result = await update_prediction_with_actuals(
    prediction_id=prediction_id,
    actual_ctr=0.048,
    actual_roas=3.5,
    actual_conversion=0.013,
    impressions=10000,
    clicks=480,
    spend=150.00
)

print(f"Accuracy: {result['accuracy']['overall_accuracy']:.1f}%")
```

## 🔄 Automated Actuals Fetching (Scheduled Task)

Create `scheduled_actuals_update.py`:

```python
import asyncio
from src.prediction_logger import PredictionLogger
from your_campaign_tracker import CampaignTracker

async def update_pending():
    logger = PredictionLogger()
    tracker = CampaignTracker()

    # Get predictions needing actuals
    pending = await logger.get_pending_predictions(days_old=7)

    for pred in pending:
        # Fetch from platform
        perf = await tracker.get_ad_performance(pred['ad_id'])

        if perf and perf['impressions'] > 100:
            await logger.update_with_actuals(
                prediction_id=pred['id'],
                actual_ctr=perf['ctr'],
                actual_roas=perf['roas'],
                actual_conversion=perf['conversion_rate'],
                impressions=perf['impressions'],
                clicks=perf['clicks'],
                spend=perf['spend']
            )

asyncio.run(update_pending())
```

Add to crontab:

```bash
# Run daily at 2 AM
0 2 * * * cd /home/user/geminivideo/services/ml-service && python scheduled_actuals_update.py
```

## 📊 Key Analytical Queries

### Overall Model Accuracy

```sql
SELECT * FROM prediction_accuracy_summary;
```

### Platform Comparison

```sql
SELECT platform, avg_ctr_accuracy_pct, avg_roas_accuracy_pct
FROM prediction_accuracy_by_platform
ORDER BY total_predictions DESC;
```

### Find Problem Predictions

```sql
SELECT * FROM prediction_outliers LIMIT 20;
```

### Daily Accuracy Trend

```sql
SELECT prediction_date, avg_ctr_accuracy_pct, avg_roas_accuracy_pct
FROM prediction_accuracy_daily
WHERE prediction_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY prediction_date DESC;
```

## 🎯 Integration Examples

### With Enhanced CTR Model

```python
from src.enhanced_ctr_model import EnhancedCTRModel
from src.prediction_logger import log_prediction

model = EnhancedCTRModel()

# Get prediction
prediction = await model.predict(features)

# Log immediately
prediction_id = await log_prediction(
    video_id=video_id,
    ad_id=ad_id,
    predicted_ctr=prediction['ctr'],
    predicted_roas=prediction['roas'],
    predicted_conversion=prediction['conversion'],
    council_score=prediction['confidence'],
    hook_type=features['hook_type'],
    template_type=features['template_type'],
    platform=features['platform']
)
```

### With ROAS Predictor

```python
from roas_predictor import ROASPredictor
from src.prediction_logger import log_prediction

predictor = ROASPredictor()

# Get comprehensive predictions
predictions = await predictor.predict_comprehensive(video_features)

# Log for validation
prediction_id = await log_prediction(
    video_id=video_id,
    ad_id=ad_id,
    predicted_ctr=predictions['ctr'],
    predicted_roas=predictions['roas'],
    predicted_conversion=predictions['conversion_rate'],
    council_score=predictions['confidence_score'],
    hook_type=video_features['hook_type'],
    template_type=video_features['template_type'],
    platform=video_features['platform'],
    metadata={'roas_model_version': predictor.version}
)
```

## 📈 Performance Monitoring

### Python API

```python
from src.prediction_logger import get_model_accuracy

stats = await get_model_accuracy(days=30)
print(f"Average Accuracy: {stats['avg_overall_accuracy']:.1f}%")
print(f"CTR Error: {stats['avg_ctr_error']:.5f}")
print(f"ROAS Error: {stats['avg_roas_error']:.2f}")
```

### SQL Dashboard Query

```sql
-- Comprehensive dashboard
SELECT
    'Overall' as metric,
    COUNT(*) as predictions,
    COUNT(actual_ctr) as with_actuals,
    ROUND(AVG(CASE WHEN actual_ctr IS NOT NULL THEN
        (metadata->>'overall_accuracy')::float
    END), 2) as avg_accuracy
FROM predictions
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'

UNION ALL

SELECT
    platform as metric,
    COUNT(*) as predictions,
    COUNT(actual_ctr) as with_actuals,
    ROUND(AVG(CASE WHEN actual_ctr IS NOT NULL THEN
        (metadata->>'overall_accuracy')::float
    END), 2) as avg_accuracy
FROM predictions
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY platform

ORDER BY metric;
```

## ⚠️ Common Issues

### Predictions Not Updating

**Problem:** Predictions remain without actuals after 14+ days

**Solution:**
1. Check if ad_id matches platform identifier exactly
2. Verify platform API credentials for fetching performance
3. Ensure campaign ran long enough (minimum 7 days, 100+ impressions)
4. Check scheduled task is running (cron job)

```python
# Debug specific prediction
logger = PredictionLogger()
pred = await logger.get_prediction_by_id(prediction_id)
print(f"Ad ID: {pred['ad_id']}")
print(f"Platform: {pred['platform']}")
print(f"Created: {pred['created_at']}")
```

### Low Accuracy Scores

**Problem:** Model showing <70% average accuracy

**Solution:**
1. Investigate outliers: `SELECT * FROM prediction_outliers;`
2. Check if certain platforms/hook types perform worse
3. Review feature engineering - missing critical features?
4. Consider retraining with recent data

```python
# Find error patterns
stats_by_hook = await logger.get_model_performance_stats(
    days=30,
    hook_type="problem_solution"
)
# Compare across different hook types
```

## 📚 Documentation

- **Full Documentation:** `PREDICTION_LOGGING_README.md`
- **API Reference:** See docstrings in `src/prediction_logger.py`
- **Test Examples:** `test_prediction_logger.py`
- **Integration Guide:** `example_prediction_integration.py`
- **SQL Schema:** `database_migrations/005_prediction_logging.sql`

## 🎓 Key Concepts

### Prediction Lifecycle

```
1. PREDICTION → Log when model makes prediction
2. CAMPAIGN RUNS → 7-14 days for statistically significant data
3. FETCH ACTUALS → Retrieve performance from ad platforms
4. UPDATE RECORD → Compare predicted vs actual
5. ANALYZE → Track accuracy trends, improve models
```

### Accuracy Calculation

- **CTR Accuracy:** `100 - (|predicted - actual| / actual × 100)`
- **ROAS Accuracy:** `100 - (|predicted - actual| / actual × 100)`
- **Overall Accuracy:** `0.4 × CTR_acc + 0.4 × ROAS_acc + 0.2 × Conv_acc`

### Council Score

AI council confidence (0-1) representing how confident the models are.
High council score should correlate with high accuracy.

## 🔗 Integration Checklist

- [ ] Database migration applied
- [ ] Prediction logging added to ML model endpoints
- [ ] Prediction IDs stored in video/campaign metadata
- [ ] Scheduled task for actuals fetching configured
- [ ] Dashboard or monitoring for accuracy metrics
- [ ] Alert thresholds set (e.g., accuracy < 80%)
- [ ] Documentation updated for team

## 🆘 Support

**Issues:** Check test suite and example integration

**Questions:** Review full documentation in `PREDICTION_LOGGING_README.md`

**Database Schema:** See `database_migrations/005_prediction_logging.sql`

---

**Built for €5M Investment Validation**
Production-grade prediction tracking and model validation system.
