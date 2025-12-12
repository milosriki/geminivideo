# Drift Detection Quick Start Guide

**5-Minute Setup** for monitoring your ML models for drift.

## What You Get

Automatic monitoring that alerts you when:
- 📊 **Feature distributions change** (input data shifts)
- 🎯 **Model predictions drift** (output patterns change)
- 📉 **Accuracy degrades** (model performance drops)
- 🎲 **Calibration fails** (confidence scores become unreliable)

## Quick Setup (3 Steps)

### Step 1: Configure Slack Alerts

```bash
# Get your Slack webhook URL from:
# https://api.slack.com/messaging/webhooks

export SLACK_DRIFT_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Step 2: Start Celery Workers

```bash
# Terminal 1: Start drift monitoring worker
celery -A src.celery_app worker \
    --queue=drift-monitoring \
    --loglevel=info \
    --concurrency=2

# Terminal 2: Start beat scheduler
celery -A src.celery_app beat --loglevel=info
```

### Step 3: Integrate with Your Model

#### Option A: Use Mixin (Easiest)

```python
from src.drift.model_integrations import DriftIntegrationMixin

class YourModel(DriftIntegrationMixin):
    def __init__(self):
        self.init_drift_monitoring('your_model_name')

    def train(self, X, y, feature_names):
        # ... train your model ...
        self.set_training_baseline(X, y, feature_names)

    def predict(self, X, feature_names):
        predictions = self.model.predict(X)
        for i, pred in enumerate(predictions):
            self.track_prediction(X[i], pred, feature_names)
        return predictions
```

#### Option B: Manual Integration

```python
from src.drift.feature_monitor import get_feature_monitor
from src.drift.prediction_monitor import get_prediction_monitor

# After training
feature_monitor = get_feature_monitor()
prediction_monitor = get_prediction_monitor()

# Set baselines
for i, feature_name in enumerate(feature_names):
    feature_monitor.set_baseline(feature_name, X_train[:, i])
prediction_monitor.set_baseline('your_model', y_train)

# Track during prediction
feature_monitor.track_features({
    name: value for name, value in zip(feature_names, features)
})
prediction_monitor.track_prediction('your_model', prediction)
```

## What Happens Next

### Automatic Monitoring

- ⏰ **Every Hour**: Prediction snapshots created
- ⏰ **Every Day at 4am**: Full drift check across all models
- ⏰ **Every Monday at 5am**: Comprehensive weekly analysis

### Slack Alerts

When drift detected, you'll get:

```
🔥 Model Drift Alert - CRITICAL

Model: ctr_model
Drift Type: feature
Metric: click_through_rate
Drift Score: 0.350

Message:
Feature drift detected in ctr_model: click_through_rate has drifted
(score=0.350, mean_shift=2.5σ, std_shift=30%)

Recommendation:
Retrain model immediately. Feature distribution changed drastically.
```

## Manual Drift Check

```python
from src.drift.model_integrations import check_model_drift

# Quick check any time
status = check_model_drift('your_model_name')
print(status['recommendation'])
# Output: "Model is stable" or "WARNING: Monitor closely"
```

## Common Use Cases

### Check if Model Needs Retraining

```python
from src.drift.prediction_monitor import get_prediction_monitor

monitor = get_prediction_monitor()
report = monitor.check_prediction_drift('ctr_model')

if report and report.is_drifting:
    if report.drift_magnitude > 0.8:
        print("🚨 CRITICAL: Retrain NOW")
    else:
        print("⚠️ WARNING: Schedule retraining")
else:
    print("✅ Model is healthy")
```

### Find Which Features Drifted

```python
from src.drift.feature_monitor import get_feature_monitor

monitor = get_feature_monitor()
top_drifting = monitor.get_top_drifting_features(n=5)

for report in top_drifting:
    if report.is_drifting:
        print(f"⚠️ {report.feature_name}: "
              f"mean shifted by {report.mean_shift:.1f}σ")
```

### Check Model Calibration

```python
from src.drift.prediction_monitor import get_prediction_monitor

monitor = get_prediction_monitor()
calibration = monitor.check_calibration('ctr_model')

print(f"Calibration Error: {calibration.expected_calibration_error:.3f}")
if calibration.drift_detected:
    print(f"⚠️ {calibration.recommendation}")
```

## Understanding Drift Scores

### PSI (Population Stability Index)

- **< 0.1**: ✅ No drift
- **0.1 - 0.25**: ⚠️ Monitor
- **> 0.25**: 🔥 Retrain

### Mean Shift

- **< 2σ**: ✅ Normal variation
- **2-3σ**: ⚠️ Watch closely
- **> 3σ**: 🔥 Investigate

### Accuracy Drop

- **< 5%**: ✅ Acceptable
- **5-10%**: ⚠️ Concerning
- **> 10%**: 🔥 Critical

## Testing

```bash
# Run tests to verify setup
pytest test_drift_detection.py -v

# Quick test
pytest test_drift_detection.py::test_end_to_end_drift_detection -v
```

## Troubleshooting

### No Alerts Received

1. Check Slack webhook:
   ```bash
   echo $SLACK_DRIFT_WEBHOOK_URL
   ```

2. Check Celery workers running:
   ```bash
   celery -A src.celery_app inspect active
   ```

3. Check logs:
   ```bash
   tail -f logs/celery.log | grep drift
   ```

### Too Many Alerts

Adjust thresholds in code:

```python
from src.drift.drift_detector import DriftDetector

detector = DriftDetector(
    psi_warning_threshold=0.15,  # Increase from 0.1
    psi_critical_threshold=0.30,  # Increase from 0.25
)
```

Or adjust alert cooldown:

```python
from src.drift.alert_manager import AlertManager

manager = AlertManager(
    alert_cooldown_minutes=120  # Increase from 60
)
```

## Advanced Features

### Set Baseline from Database

```python
from src.drift.model_integrations import set_model_baseline_from_db

set_model_baseline_from_db(
    model_name='ctr_model',
    training_data_query='SELECT * FROM training_data WHERE date >= NOW() - INTERVAL 30 days',
    feature_columns=['ctr', 'spend', 'impressions'],
    target_column='actual_ctr'
)
```

### Get Drift Trends

```python
from src.drift.feature_monitor import get_feature_monitor

monitor = get_feature_monitor()
trend = monitor.get_feature_trend('ctr', hours=24)

for snapshot in trend:
    print(f"{snapshot.timestamp}: mean={snapshot.mean:.3f}")
```

### Custom Alerts

```python
from src.drift.drift_tasks import alert_on_drift

alert_on_drift.delay(
    model_name='custom_model',
    drift_type='feature',
    metric_name='custom_metric',
    drift_score=0.35,
    severity='warning',
    details={'custom': 'data'}
)
```

## Next Steps

1. ✅ Monitor alerts for 1 week
2. 📊 Set up Grafana dashboard (optional)
3. 🔄 Add automatic retraining triggers
4. 📚 Review drift patterns monthly

---

**Questions?** Check full docs: `AGENT10_DRIFT_DETECTION_COMPLETE.md`

**Status**: 🟢 You're all set! Models are being monitored 24/7.
