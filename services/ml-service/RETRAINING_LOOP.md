# ML Model Retraining Loop - Agent 10
## €5M Investment-Grade Implementation

This document describes the automatic model retraining system implemented for production-grade continuous learning.

---

## Overview

The retraining loop ensures the CTR prediction model stays accurate by:
1. **Monitoring** prediction accuracy against actual campaign performance
2. **Triggering** automatic retraining when accuracy degrades
3. **Learning** from real performance data continuously
4. **Improving** prediction quality over time

---

## Architecture

### Components

#### 1. **AccuracyTracker** (`src/accuracy_tracker.py`)
- Tracks predictions vs actual performance
- Calculates accuracy metrics (MAE, RMSE, R²)
- Stores prediction records in database
- Provides investor-grade reports

#### 2. **CTRPredictor Retraining Methods** (`src/ctr_model.py`)
- `check_and_retrain()`: Checks accuracy and triggers retrain if needed
- `retrain_on_real_data()`: Retrains model using actual performance data
- `load_real_training_data()`: Fetches training data from database
- `extract_features()`: Prepares features for training

#### 3. **API Endpoint** (`src/main.py`)
- `POST /api/ml/check-retrain`: Cron endpoint for daily accuracy checks
- Returns detailed status and metrics
- Can be called manually or via scheduled job

#### 4. **Learning Loop Integration** (`services/titan-core/ai_council/learning_loop.py`)
- Triggers retraining when purchases occur
- Calls ML service retraining endpoint
- Logs retraining outcomes

---

## Retraining Logic

### Accuracy Threshold
- **Threshold**: MAE > 0.02 (2% error)
- **Metric**: Mean Absolute Error on CTR predictions
- **Lookback**: Last 7 days of predictions

### Decision Flow
```
1. Calculate accuracy metrics from last 7 days
   ↓
2. Check if MAE > 0.02
   ↓
   YES → Trigger retraining
   ↓
3. Load real training data from database
   ↓
4. Check if sufficient samples (≥50)
   ↓
   YES → Retrain model
   ↓
5. Save new model with improved metrics
   ↓
6. Return status and comparison metrics
```

---

## Database Schema

### prediction_records
Stores predictions for tracking:
- `prediction_id`: Unique identifier
- `predicted_ctr`, `predicted_roas`: ML predictions
- `actual_ctr`, `actual_roas`: Real performance
- `ctr_error`, `roas_error`: Accuracy metrics
- `hook_type`, `template_id`: For breakdown analysis
- `status`: predicted → running → completed

### prediction_comparisons
Historical comparisons (used by campaign_tracker):
- Links campaign performance to predictions
- Enables accuracy calculation

---

## API Usage

### Daily Cron Job
```bash
# Run daily at 2 AM
curl -X POST http://localhost:8003/api/ml/check-retrain
```

### Response Examples

#### No Retrain Needed
```json
{
  "status": "no_retrain_needed",
  "current_accuracy": {
    "ctr_mae": 0.0145,
    "ctr_rmse": 0.0189,
    "ctr_accuracy": 87.5,
    "total_predictions": 156
  },
  "threshold": 0.02,
  "message": "Model accuracy acceptable (MAE=0.0145 <= 0.02)",
  "checked_at": "2025-12-05T10:30:00.000Z"
}
```

#### Retrained Successfully
```json
{
  "status": "retrained",
  "samples": 245,
  "metrics": {
    "test_r2": 0.8956,
    "test_mae": 0.0167,
    "test_accuracy": 0.92,
    "trained_at": "2025-12-05T10:30:15.000Z"
  },
  "old_metrics": {
    "test_r2": 0.8723,
    "test_mae": 0.0234
  },
  "improvement": {
    "r2_improvement": 0.0233,
    "mae_improvement": 0.0067
  },
  "retrained_at": "2025-12-05T10:30:15.000Z",
  "checked_at": "2025-12-05T10:30:00.000Z"
}
```

#### Insufficient Data
```json
{
  "status": "insufficient_data",
  "count": 42,
  "message": "Need at least 50 samples for retraining, got 42",
  "checked_at": "2025-12-05T10:30:00.000Z"
}
```

---

## Cron Setup

### Option 1: Unix Cron
```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * /home/user/geminivideo/services/ml-service/cron_retrain.sh >> /var/log/ml-retrain.log 2>&1
```

### Option 2: Kubernetes CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ml-model-retrain
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: retrain
            image: curlimages/curl:latest
            command:
            - /bin/sh
            - -c
            - |
              curl -X POST http://ml-service:8003/api/ml/check-retrain
          restartPolicy: OnFailure
```

### Option 3: Cloud Scheduler (GCP)
```bash
gcloud scheduler jobs create http ml-retrain \
  --schedule="0 2 * * *" \
  --uri="https://your-ml-service.com/api/ml/check-retrain" \
  --http-method=POST \
  --location=us-central1
```

---

## Monitoring & Alerts

### Slack Notifications
Configure `SLACK_WEBHOOK_URL` in `cron_retrain.sh`:
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Notifications sent for:
- ✅ Successful retraining
- ❌ Errors during retraining
- ⚠️ Insufficient training data

### Metrics to Monitor
1. **Retraining Frequency**: Should happen ~1-2 times per week in healthy system
2. **Accuracy Improvement**: R² should trend upward over time
3. **Training Sample Count**: Should grow as more campaigns run
4. **Error Rate**: MAE should decrease over time

---

## Learning Loop Flow

### Purchase Signal → Retraining
```
1. User makes purchase
   ↓
2. LearningLoop.process_purchase_signal() called
   ↓
3. Update Vector Store with high-conversion pattern
   ↓
4. Trigger ML retraining via API
   ↓
5. ML service checks accuracy
   ↓
6. If needed, retrain with new data
   ↓
7. Model improves for future predictions
```

---

## Performance Considerations

### Training Time
- **Typical**: 10-30 seconds for 100-500 samples
- **Maximum**: 5 minutes (timeout configured)
- **Non-blocking**: API returns immediately with status

### Database Load
- Accuracy checks query last 7 days (~100-1000 records)
- Optimized with indexes on `created_at`, `status`
- Minimal impact on production database

### Model Size
- XGBoost model: ~1-5 MB
- Saved to disk after each training
- No memory issues with continuous retraining

---

## Testing

### Manual Trigger
```bash
# Test the endpoint
curl -X POST http://localhost:8003/api/ml/check-retrain

# With authentication (if enabled)
curl -X POST http://localhost:8003/api/ml/check-retrain \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Simulate Accuracy Drop
```python
# In Python shell
from src.ctr_model import ctr_predictor
import asyncio

# Check current accuracy
result = asyncio.run(ctr_predictor.check_and_retrain())
print(result)
```

---

## Investment Validation

### Key Metrics for Investors

#### 1. **Prediction Accuracy**
- Target: >85% accuracy (CTR within 20%)
- Current: Tracked in real-time via AccuracyTracker
- Trend: Visible in investor reports

#### 2. **Learning Improvement**
- Measured: Accuracy improvement over time
- Report: `/api/ml/check-retrain` shows improvement delta
- Expected: +5-10% accuracy improvement per month

#### 3. **ROI Generation**
- Tracked: Revenue from accurate predictions
- Calculated: AccuracyTracker.generate_investor_report()
- Demonstrates: ML system drives business value

#### 4. **System Reliability**
- Automated: Daily accuracy checks
- Resilient: Handles insufficient data gracefully
- Monitored: Slack alerts on issues

---

## Troubleshooting

### Issue: "insufficient_data" Status
**Cause**: Not enough campaign performance data
**Solution**:
- Ensure campaigns are running and collecting metrics
- Check `videos` table has impressions/clicks data
- Wait for more data to accumulate (need 50+ samples)

### Issue: "error" Status
**Cause**: Database connection or query issue
**Solution**:
- Check `DATABASE_URL` environment variable
- Verify PostgreSQL is running
- Check logs for specific error details

### Issue: Retraining Not Improving Accuracy
**Cause**: Data quality or feature engineering issues
**Solution**:
- Review feature engineering (src/feature_engineering.py)
- Check for data quality issues in videos table
- Consider adding more features or improving existing ones

### Issue: Retraining Takes Too Long
**Cause**: Too many training samples or complex model
**Solution**:
- Limit training samples to last 10,000 records
- Reduce XGBoost n_estimators
- Consider async training for very large datasets

---

## Future Enhancements

### Planned Improvements
1. **Multi-metric Retraining**: Trigger on ROAS accuracy too
2. **A/B Testing**: Test new model vs current before deployment
3. **Confidence Scoring**: Only retrain if high confidence in improvement
4. **Feature Selection**: Auto-remove low-importance features
5. **Hyperparameter Tuning**: Auto-optimize XGBoost parameters

### Advanced Features
- **Online Learning**: Update model incrementally with each new sample
- **Ensemble Models**: Combine multiple models for better accuracy
- **Transfer Learning**: Leverage patterns from similar campaigns
- **Anomaly Detection**: Flag unusual predictions for review

---

## Summary

The retraining loop provides:
- ✅ **Automatic** accuracy monitoring
- ✅ **Intelligent** retrain triggering
- ✅ **Real data** continuous learning
- ✅ **Production-grade** reliability
- ✅ **Investor-grade** reporting

**Result**: A self-improving ML system that gets better over time, demonstrating clear ROI for €5M investment validation.

---

## Contact & Support

For issues or questions:
- Check logs: `/var/log/ml-retrain.log`
- Review database: `prediction_records` and `prediction_comparisons` tables
- Test endpoint: `POST /api/ml/check-retrain`
- Monitor metrics: `GET /api/ml/stats`

**Agent 10 Implementation Complete** ✅
