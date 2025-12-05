# Accuracy Tracker - Agent 9

## €5M Investment Validation System

**Purpose:** Track and report prediction accuracy to demonstrate that ML predictions match reality for investor validation.

---

## Overview

The Accuracy Tracker is a production-grade system that:

1. **Records predictions** before campaigns launch
2. **Updates with actual results** after campaigns run
3. **Calculates accuracy metrics** (CTR, ROAS)
4. **Generates investor reports** with comprehensive analysis
5. **Tracks learning improvement** over time

---

## Database Schema

### Tables Created

#### `prediction_records`
Stores all predictions with their features and actuals:
- `prediction_id` - Unique identifier
- `campaign_id` - Meta campaign ID
- `creative_id` - Creative/ad ID
- `predicted_ctr` - Predicted CTR (0-1)
- `predicted_roas` - Predicted ROAS
- `actual_ctr` - Actual CTR (filled later)
- `actual_roas` - Actual ROAS (filled later)
- `ctr_error`, `roas_error`, `accuracy_score` - Calculated metrics
- `hook_type` - Hook type used (question, number, emotion, etc.)
- `template_id` - Template identifier
- `features` - JSON with all features used
- `demographic_target` - JSON with target demographics
- `status` - predicted | running | completed

#### `accuracy_snapshots`
Daily snapshots for trend analysis:
- `date` - Date of snapshot
- `total_predictions` - Number of predictions
- `ctr_mae`, `ctr_rmse`, `ctr_accuracy` - CTR metrics
- `roas_mae`, `roas_rmse`, `roas_accuracy` - ROAS metrics
- `roi_generated` - Total ROI from predictions

---

## API Endpoints

### 1. GET /api/ml/accuracy-report

**THE MAIN INVESTOR ENDPOINT**

Generates comprehensive validation report for investors.

**Parameters:**
- `days_back` (int, default: 30) - Days to analyze

**Response:**
```json
{
  "report_generated_at": "2025-12-05 14:30:00",
  "period_analyzed": "2025-11-05 to 2025-12-05",

  "summary": {
    "total_predictions": 150,
    "ctr_accuracy": 82.5,
    "roas_accuracy": 78.3,
    "predictions_above_threshold": 85,
    "roi_generated": 45000.00,
    "model_confidence_score": 80.4
  },

  "detailed_metrics": {
    "ctr_mae": 0.0145,
    "ctr_rmse": 0.0198,
    "ctr_mape": 18.2,
    "roas_mae": 0.35,
    "roas_rmse": 0.48,
    "roas_mape": 15.8,
    "total_revenue": 245000.00,
    "total_spend": 150000.00
  },

  "by_hook_type": {
    "hook_types": {
      "question": {
        "count": 45,
        "ctr_mae": 0.0132,
        "roas_mae": 0.28,
        "avg_actual_roas": 3.2
      },
      "number": {
        "count": 38,
        "ctr_mae": 0.0156,
        "roas_mae": 0.41,
        "avg_actual_roas": 2.8
      }
    },
    "best_performing": "question"
  },

  "by_template": {
    "templates": {
      "template_001": {
        "count": 52,
        "avg_actual_roas": 3.5
      }
    }
  },

  "top_performers": [
    {
      "prediction_id": "pred_abc123",
      "predicted_ctr": 0.0450,
      "actual_ctr": 0.0478,
      "predicted_roas": 3.2,
      "actual_roas": 3.5,
      "accuracy_score": 94.5
    }
  ],

  "learning_improvement": {
    "ctr_improvement": 5.2,
    "roas_improvement": 3.8,
    "learning_status": "improving"
  },

  "revenue_impact": {
    "total_revenue": 245000.00,
    "total_spend": 150000.00,
    "roi_generated": 95000.00,
    "avg_roas": 2.85,
    "cost_savings": 22500.00
  },

  "model_confidence": {
    "overall_score": 80.4,
    "ctr_confidence": "high",
    "roas_confidence": "high",
    "reliability_grade": "B"
  },

  "investment_validation": {
    "accuracy_target_met": true,
    "roi_positive": true,
    "learning_improving": true,
    "overall_verdict": "BUY"
  }
}
```

**Verdicts:**
- `STRONG_BUY` - CTR > 80%, ROAS > 80%, ROI > 0, Confidence > 75%
- `BUY` - CTR > 70%, ROAS > 70%, ROI > 0 or improving
- `HOLD` - CTR > 60%, ROAS > 60%
- `NEEDS_IMPROVEMENT` - Below thresholds

---

### 2. GET /api/ml/accuracy-metrics

Get quick accuracy metrics without full report.

**Parameters:**
- `days_back` (int, default: 30)

**Response:**
```json
{
  "total_predictions": 150,
  "ctr_mae": 0.0145,
  "ctr_rmse": 0.0198,
  "ctr_accuracy": 82.5,
  "roas_mae": 0.35,
  "roas_rmse": 0.48,
  "roas_accuracy": 78.3,
  "predictions_above_threshold": 85,
  "roi_generated": 45000.00
}
```

---

### 3. POST /api/ml/prediction/record

Record a new prediction (call BEFORE launching campaign).

**Request:**
```json
{
  "prediction_id": "pred_unique_123",
  "campaign_id": "camp_abc",
  "creative_id": "creative_xyz",
  "predicted_ctr": 0.0450,
  "predicted_roas": 3.2,
  "hook_type": "question",
  "template_id": "template_001",
  "features": {
    "psychology_score": 0.85,
    "hook_strength": 0.92,
    "technical_score": 0.88
  },
  "demographic_target": {
    "age_range": "25-45",
    "interests": ["fitness", "wellness"]
  }
}
```

**Response:**
```json
{
  "status": "recorded",
  "prediction_id": "pred_unique_123",
  "message": "Prediction recorded successfully"
}
```

---

### 4. POST /api/ml/prediction/update-actuals

Update prediction with actual results (call AFTER campaign completes).

**Request:**
```json
{
  "prediction_id": "pred_unique_123",
  "actual_ctr": 0.0478,
  "actual_roas": 3.5,
  "actual_conversions": 45
}
```

**Response:**
```json
{
  "status": "updated",
  "prediction_id": "pred_unique_123",
  "message": "Actuals recorded successfully"
}
```

---

### 5. GET /api/ml/top-performers

Get top performing predictions.

**Parameters:**
- `limit` (int, default: 10)

**Response:**
```json
{
  "top_performers": [
    {
      "prediction_id": "pred_abc",
      "campaign_id": "camp_123",
      "hook_type": "question",
      "predicted_ctr": 0.0450,
      "actual_ctr": 0.0478,
      "predicted_roas": 3.2,
      "actual_roas": 3.5,
      "accuracy_score": 94.5
    }
  ],
  "count": 10
}
```

---

## Usage Workflow

### 1. When Making a Prediction

```python
# In your prediction service
prediction_result = await ml_service.predict_ctr(clip_data)

# Record the prediction
await accuracy_tracker.record_prediction(
    prediction_id=f"pred_{uuid.uuid4().hex}",
    campaign_id=campaign_id,
    creative_id=creative_id,
    predicted_ctr=prediction_result['predicted_ctr'],
    predicted_roas=prediction_result['predicted_roas'],
    hook_type=clip_data.get('hook_type'),
    template_id=clip_data.get('template_id'),
    features=prediction_result['features']
)
```

### 2. After Campaign Runs

```python
# Fetch actual metrics from Meta API
actual_metrics = await meta_api.get_campaign_metrics(campaign_id)

# Update with actuals
await accuracy_tracker.update_with_actuals(
    prediction_id=prediction_id,
    actual_ctr=actual_metrics['ctr'],
    actual_roas=actual_metrics['roas'],
    actual_conversions=actual_metrics['conversions']
)
```

### 3. Generate Investor Report

```python
# Generate report for last 30 days
report = await accuracy_tracker.generate_investor_report(days_back=30)

# Present to investors
print(f"Model Accuracy: {report['summary']['ctr_accuracy']}%")
print(f"Investment Verdict: {report['investment_validation']['overall_verdict']}")
```

---

## Accuracy Metrics Explained

### CTR Metrics

- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and actual CTR
  - Good: < 0.02 (2%)
  - Acceptable: 0.02 - 0.03
  - Needs improvement: > 0.03

- **RMSE (Root Mean Squared Error)**: Penalizes larger errors more
  - Good: < 0.025
  - Acceptable: 0.025 - 0.04
  - Needs improvement: > 0.04

- **MAPE (Mean Absolute Percentage Error)**: Percentage-based error
  - Good: < 15%
  - Acceptable: 15% - 25%
  - Needs improvement: > 25%

- **Accuracy**: % of predictions within 20% of actual
  - Excellent: > 85%
  - Good: 75% - 85%
  - Acceptable: 65% - 75%
  - Needs improvement: < 65%

### ROAS Metrics

- **MAE**: Average absolute difference
  - Good: < 0.3
  - Acceptable: 0.3 - 0.5
  - Needs improvement: > 0.5

- **Accuracy**: % within 15% of actual
  - Excellent: > 85%
  - Good: 75% - 85%
  - Acceptable: 65% - 75%
  - Needs improvement: < 65%

---

## Testing

Run the test suite:

```bash
cd /home/user/geminivideo/services/ml-service
python test_accuracy_tracker.py
```

This will:
1. Generate 50 test predictions
2. Simulate actual results
3. Calculate all metrics
4. Generate full investor report

---

## Integration with ML Service

The accuracy tracker is fully integrated with the ML service:

1. **Automatic Database Setup**: Tables created on startup
2. **API Endpoints**: Accessible via `/api/ml/accuracy-*`
3. **Health Check**: Status included in `/health`
4. **Documentation**: Listed in `/` root endpoint

---

## Cron Jobs (Recommended)

### Daily Accuracy Snapshot

```bash
# Create daily snapshot at 2 AM
0 2 * * * curl -X POST http://localhost:8003/api/ml/accuracy-snapshot
```

### Weekly Investor Report

```bash
# Generate weekly report and email to investors
0 9 * * 1 curl http://localhost:8003/api/ml/accuracy-report?days_back=7 | mail -s "Weekly ML Performance" investors@company.com
```

---

## Production Checklist

- [ ] Database tables created
- [ ] Environment variables set (DATABASE_URL)
- [ ] ML Service running
- [ ] Test predictions recorded
- [ ] Actuals being updated
- [ ] Daily snapshots scheduled
- [ ] Investor reports accessible
- [ ] Monitoring alerts configured

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs ml-service`
2. Test database: `psql $DATABASE_URL`
3. Verify predictions: `SELECT COUNT(*) FROM prediction_records;`
4. Check accuracy: `GET /api/ml/accuracy-metrics`

---

## Investment Validation

**Key Metrics for Investors:**

1. **Accuracy > 75%** ✅ Shows model reliability
2. **ROI > 0** ✅ Demonstrates profitability
3. **Learning Status = "improving"** ✅ Shows continuous improvement
4. **Confidence Grade B+** ✅ Investment-grade reliability

**Verdict: BUY** means the system is performing at investment-grade level for €5M validation.
