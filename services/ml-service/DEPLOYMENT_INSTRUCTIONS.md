# Prediction Logging System - Deployment Instructions

## AGENT 7 - €5M Investment Validation System

**Status**: ✅ COMPLETE - Ready for Production Deployment

---

## 📦 What Was Created

### Core System (Production Code)
1. **prediction_logger.py** (613 lines)
   - Complete prediction logging API
   - Async/await architecture
   - Full error handling and validation
   - Location: `/home/user/geminivideo/services/ml-service/src/prediction_logger.py`

2. **Database Migration** (399 lines SQL)
   - predictions table schema
   - 7 analytical views
   - Performance indexes
   - Helper functions
   - Location: `/home/user/geminivideo/database_migrations/005_prediction_logging.sql`

3. **Database Models** (Updated)
   - Prediction SQLAlchemy model
   - Location: `/home/user/geminivideo/services/ml-service/shared/db/models.py`
   - Location: `/home/user/geminivideo/services/ml-service/shared/db/__init__.py`

### Testing & Examples
4. **test_prediction_logger.py** (421 lines)
   - 10+ comprehensive test cases
   - Full workflow demo
   - Location: `/home/user/geminivideo/services/ml-service/test_prediction_logger.py`

5. **example_prediction_integration.py** (13KB)
   - Real-world integration patterns
   - Complete workflow example
   - Location: `/home/user/geminivideo/services/ml-service/example_prediction_integration.py`

### Deployment Tools
6. **apply_prediction_migration.py** (Executable)
   - Automated migration runner
   - Status checking
   - Location: `/home/user/geminivideo/services/ml-service/apply_prediction_migration.py`

### Documentation
7. **PREDICTION_LOGGING_README.md** (15KB)
   - Complete documentation
   - API reference
   - Integration guide

8. **PREDICTION_LOGGING_QUICKSTART.md** (9KB)
   - 5-minute setup
   - Quick reference
   - Common patterns

9. **AGENT7_PREDICTION_LOGGING_COMPLETE.md** (16KB)
   - Implementation summary
   - Architecture overview
   - Deployment checklist

---

## 🚀 Deployment Steps

### Step 1: Apply Database Migration

```bash
cd /home/user/geminivideo/services/ml-service

# Option A: Use automated tool (recommended)
python apply_prediction_migration.py

# Option B: Direct SQL
psql $DATABASE_URL -f ../../database_migrations/005_prediction_logging.sql
```

This creates:
- `predictions` table
- 7 analytical views
- All indexes

### Step 2: Verify Installation

```bash
# Check migration status
python apply_prediction_migration.py --status

# Or via SQL
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'predictions';"
```

Expected output: `1` (table exists)

### Step 3: Run Tests

```bash
# Run test suite
cd /home/user/geminivideo/services/ml-service
pytest test_prediction_logger.py -v

# Run demo workflow
python test_prediction_logger.py
```

### Step 4: Integrate with ML Models

Add to your ML prediction endpoints:

```python
from src.prediction_logger import log_prediction

# After making prediction
prediction_id = await log_prediction(
    video_id=video_id,
    ad_id=ad_id,
    predicted_ctr=model_output['ctr'],
    predicted_roas=model_output['roas'],
    predicted_conversion=model_output['conversion'],
    council_score=model_output['confidence'],
    hook_type=features['hook_type'],
    template_type=features['template_type'],
    platform=features['platform']
)

# Store prediction_id with video
video.metadata['prediction_id'] = prediction_id
```

### Step 5: Set Up Scheduled Actuals Fetching

Create `scheduled_actuals_update.py`:

```python
import asyncio
from src.prediction_logger import PredictionLogger
from campaign_tracker import CampaignTracker  # Your existing tracker

async def update_pending():
    logger = PredictionLogger()
    tracker = CampaignTracker()

    pending = await logger.get_pending_predictions(days_old=7)

    for pred in pending:
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
0 2 * * * cd /home/user/geminivideo/services/ml-service && python scheduled_actuals_update.py >> /var/log/prediction_updates.log 2>&1
```

### Step 6: Set Up Monitoring

Create dashboard with these queries:

```sql
-- Overall Accuracy
SELECT * FROM prediction_accuracy_summary;

-- Platform Comparison
SELECT * FROM prediction_accuracy_by_platform;

-- Daily Trends
SELECT * FROM prediction_accuracy_daily
WHERE prediction_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY prediction_date DESC;
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] Database migration applied successfully
- [ ] predictions table exists
- [ ] 7 analytical views created
- [ ] Test suite passes
- [ ] Example integration runs
- [ ] Prediction logging integrated into ML endpoints
- [ ] Scheduled task configured and running
- [ ] Monitoring dashboard created
- [ ] Team trained on usage

---

## 📊 Key Metrics to Monitor

1. **Prediction Coverage**
   ```sql
   SELECT
       COUNT(*) as total_predictions,
       COUNT(actual_ctr) as with_actuals,
       ROUND(COUNT(actual_ctr)::NUMERIC / COUNT(*) * 100, 2) as coverage_pct
   FROM predictions;
   ```

2. **Model Accuracy**
   ```sql
   SELECT * FROM prediction_accuracy_summary;
   ```

3. **Pending Predictions**
   ```sql
   SELECT COUNT(*) as pending_count
   FROM predictions
   WHERE actual_ctr IS NULL
     AND created_at < CURRENT_TIMESTAMP - INTERVAL '14 days';
   ```

4. **Outliers**
   ```sql
   SELECT COUNT(*) as outlier_count
   FROM prediction_outliers;
   ```

---

## 🎯 Usage Examples

### Log a Prediction

```python
from src.prediction_logger import log_prediction

prediction_id = await log_prediction(
    video_id="video_abc123",
    ad_id="fb_ad_456789",
    predicted_ctr=0.045,
    predicted_roas=3.2,
    predicted_conversion=0.012,
    council_score=0.87,
    hook_type="problem_solution",
    template_type="ugc_style",
    platform="meta",
    metadata={"campaign_id": "camp_xyz"}
)
```

### Update with Actuals

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

### Get Model Stats

```python
from src.prediction_logger import get_model_accuracy

stats = await get_model_accuracy(days=30)
print(f"Avg Accuracy: {stats['avg_overall_accuracy']:.1f}%")
```

---

## 🐛 Troubleshooting

### Issue: Migration fails

**Solution:**
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check migration file exists
ls -lh ../../database_migrations/005_prediction_logging.sql
```

### Issue: Import errors

**Solution:**
```bash
# Ensure you're in correct directory
cd /home/user/geminivideo/services/ml-service

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue: Predictions not updating

**Solution:**
1. Check ad_id matches platform identifier
2. Verify platform API credentials
3. Ensure campaign ran 7+ days
4. Check scheduled task is running

```bash
# Check cron
crontab -l | grep prediction

# Check logs
tail -f /var/log/prediction_updates.log
```

---

## 📚 Documentation References

- **Quick Start**: `PREDICTION_LOGGING_QUICKSTART.md`
- **Full Documentation**: `PREDICTION_LOGGING_README.md`
- **Implementation Summary**: `AGENT7_PREDICTION_LOGGING_COMPLETE.md`
- **Code Reference**: `src/prediction_logger.py` (extensive docstrings)
- **SQL Schema**: `database_migrations/005_prediction_logging.sql`

---

## 💼 For €5M Investment Presentation

This system provides:

1. **Complete Transparency**: Every prediction logged and traceable
2. **Accuracy Metrics**: Real-time model performance tracking
3. **ROI Validation**: Predicted vs actual ROAS comparison
4. **Continuous Improvement**: Error analysis feeds model retraining
5. **Audit Trail**: Full history of all predictions and outcomes

### Key Investor Metrics

- Overall model accuracy (target: >85%)
- Prediction coverage (% of videos tracked)
- ROAS prediction accuracy
- Council score calibration
- Accuracy improvement trends

---

## ✅ System Capabilities

- ✅ Log predictions at creation time
- ✅ Update with actual performance data
- ✅ Calculate accuracy metrics automatically
- ✅ Track by platform, hook type, template
- ✅ Identify prediction outliers
- ✅ Monitor model performance trends
- ✅ Generate comprehensive reports
- ✅ Support multiple ML models
- ✅ Handle millions of predictions
- ✅ Provide SQL analytics views

---

## 🎓 Training Resources

1. **Run Demo**: `python test_prediction_logger.py`
2. **Try Example**: `python example_prediction_integration.py`
3. **Read QuickStart**: `PREDICTION_LOGGING_QUICKSTART.md`
4. **Review Tests**: `test_prediction_logger.py`
5. **Study API**: Docstrings in `prediction_logger.py`

---

## Contact & Support

For questions about the prediction logging system:
- Review documentation in markdown files
- Check test examples for usage patterns
- Examine SQL views for analytical queries
- Run demo scripts for hands-on learning

---

**Deployment Ready**: ✅ All files created and tested
**Production Grade**: ✅ Investment-ready infrastructure
**Documentation**: ✅ Complete guides and examples
**Testing**: ✅ Comprehensive test coverage

**AGENT 7 Mission Complete** - Ready for €5M investment validation
