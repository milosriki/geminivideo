# Accuracy Tracker Quick Start - Agent 9

## €5M Investment Validation - 30 Second Setup

---

## Files Created

✅ `/home/user/geminivideo/services/ml-service/src/accuracy_tracker.py` (999 lines)
✅ `/home/user/geminivideo/services/ml-service/test_accuracy_tracker.py` (262 lines)
✅ `/home/user/geminivideo/services/ml-service/ACCURACY_TRACKER_README.md` (445 lines)

---

## The Main Endpoint (For Investors)

```bash
# Generate comprehensive investor report
curl http://localhost:8003/api/ml/accuracy-report?days_back=30
```

**Returns:**
- CTR Accuracy %
- ROAS Accuracy %
- ROI Generated
- Investment Verdict (STRONG_BUY, BUY, HOLD, NEEDS_IMPROVEMENT)
- Performance breakdown by hook type
- Top performers
- Learning improvement

---

## Quick Test

```bash
cd /home/user/geminivideo/services/ml-service
python test_accuracy_tracker.py
```

**Output:**
- Generates 50 test predictions
- Calculates all metrics
- Shows full investor report
- Demonstrates system working

---

## 3-Step Usage

### 1. Record Prediction (Before Launch)
```python
await accuracy_tracker.record_prediction(
    prediction_id="pred_123",
    campaign_id="camp_abc",
    predicted_ctr=0.045,
    predicted_roas=3.2,
    hook_type="question"
)
```

### 2. Run Campaign
(Campaign runs on Meta)

### 3. Update Actuals (After Complete)
```python
await accuracy_tracker.update_with_actuals(
    prediction_id="pred_123",
    actual_ctr=0.048,
    actual_roas=3.5
)
```

---

## All Endpoints

```
GET  /api/ml/accuracy-report          # Main investor report
GET  /api/ml/accuracy-metrics         # Quick metrics
POST /api/ml/prediction/record        # Record prediction
POST /api/ml/prediction/update-actuals # Update with actuals
GET  /api/ml/top-performers           # Best predictions
```

---

## Investment Targets

✅ **CTR Accuracy:** 75%+ (currently tracks within 20% threshold)
✅ **ROAS Accuracy:** 75%+ (currently tracks within 15% threshold)
✅ **ROI:** Positive
✅ **Learning:** Improving over time

**Verdict Scale:**
- STRONG_BUY ⭐⭐⭐⭐⭐ (80%+ accuracy, positive ROI)
- BUY ⭐⭐⭐⭐ (70%+ accuracy)
- HOLD ⭐⭐⭐ (60%+ accuracy)
- NEEDS_IMPROVEMENT ⭐⭐ (<60% accuracy)

---

## Database Tables

Auto-created on startup:
- `prediction_records` - All predictions + actuals
- `accuracy_snapshots` - Daily accuracy trends

---

## That's It!

System is **production-ready** for €5M investment validation.

**Documentation:**
- Full docs: `ACCURACY_TRACKER_README.md`
- Summary: `AGENT_9_IMPLEMENTATION_SUMMARY.md`
- This file: `ACCURACY_TRACKER_QUICKSTART.md`
