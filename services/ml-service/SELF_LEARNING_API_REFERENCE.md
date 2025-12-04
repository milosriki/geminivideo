# Self-Learning Feedback Loop - API Reference

Quick reference for using the Self-Learning Engine.

## Quick Start

```python
from self_learning import SelfLearningEngine, ModelType

# Initialize
engine = SelfLearningEngine(database_service, model_registry)

# Register prediction
pred_id = engine.register_prediction(
    model_type=ModelType.ROAS_PREDICTOR,
    predicted_value=2.5,
    features={'ad_spend': 1000, 'ctr': 0.025}
)

# Record outcome
outcome = engine.record_outcome(pred_id, actual_value=2.7)

# Check performance
performance = engine.get_model_performance(ModelType.ROAS_PREDICTOR)
print(f"MAE: {performance.mae:.4f}, MAPE: {performance.mape:.2f}%")
```

## Core API Methods

### 1. Prediction Tracking

#### `register_prediction(model_type, predicted_value, features) -> str`
Register a new prediction for tracking.

**Parameters:**
- `model_type`: ModelType enum (ROAS_PREDICTOR, CTR_PREDICTOR, etc.)
- `predicted_value`: float - The model's prediction
- `features`: Dict[str, Any] - Feature values used for prediction

**Returns:** Prediction ID (str)

**Example:**
```python
pred_id = engine.register_prediction(
    model_type=ModelType.CTR_PREDICTOR,
    predicted_value=0.025,
    features={
        'ad_spend': 1000,
        'audience_size': 50000,
        'time_of_day': 14
    }
)
```

#### `record_outcome(prediction_id, actual_value) -> PredictionOutcome`
Record the actual outcome for a prediction.

**Parameters:**
- `prediction_id`: str - ID from register_prediction
- `actual_value`: float - The actual observed value

**Returns:** PredictionOutcome object

**Example:**
```python
outcome = engine.record_outcome(pred_id, actual_value=0.028)
print(f"Error: {outcome.error:.4f}")
print(f"Error %: {outcome.error_percentage:.2f}%")
```

### 2. Error Analysis

#### `analyze_error_distribution(model_type, days_back=30) -> Dict`
Get comprehensive error statistics.

**Returns:**
```python
{
    'sample_count': 150,
    'mean_error': -0.05,
    'median_error': -0.02,
    'std_error': 0.42,
    'mean_absolute_error': 0.35,
    'percentiles': {
        '25th': -0.25,
        '50th': -0.02,
        '75th': 0.18,
        '90th': 0.45,
        '95th': 0.72
    },
    'skewness': 0.15,
    'kurtosis': -0.32,
    'normality_test': {
        'test': 'Shapiro-Wilk',
        'p_value': 0.23,
        'is_normal': True
    }
}
```

#### `identify_systematic_errors(model_type) -> List[Dict]`
Find systematic biases in predictions.

**Returns:**
```python
[
    {
        'feature': 'ad_spend',
        'mean_error': -0.45,
        'std_error': 0.12,
        'sample_count': 75,
        't_statistic': -3.45,
        'p_value': 0.001,
        'bias_direction': 'overestimation',
        'severity': 'high'
    }
]
```

### 3. Drift Detection

#### `identify_feature_drift(model_type, reference_period_days=30, current_period_days=7) -> DriftReport`
Detect changes in feature distributions.

**Returns:** DriftReport with:
- `drift_type`: DriftType.DATA_DRIFT
- `severity`: 'low' | 'medium' | 'high' | 'critical'
- `affected_features`: List of drifted features
- `statistical_tests`: Dict with KS test results per feature
- `recommendation`: Action to take

**Example:**
```python
drift = engine.identify_feature_drift(ModelType.ROAS_PREDICTOR)
print(f"Severity: {drift.severity}")
print(f"Affected: {drift.affected_features}")
print(f"Action: {drift.recommendation}")
```

#### `detect_concept_drift(model_type) -> DriftReport`
Detect performance degradation (concept drift).

**Returns:** DriftReport with performance change statistics

**Example:**
```python
drift = engine.detect_concept_drift(ModelType.CTR_PREDICTOR)
if drift.severity in ['high', 'critical']:
    print(f"Performance degraded by {drift.statistical_tests['performance_change_pct']:.1f}%")
```

#### `detect_prediction_drift(model_type) -> DriftReport`
Detect changes in prediction distributions.

### 4. Model Retraining

#### `should_retrain(model_type) -> Tuple[bool, str]`
Determine if model needs retraining.

**Returns:** (should_retrain: bool, reason: str)

**Example:**
```python
should_retrain, reason = engine.should_retrain(ModelType.ROAS_PREDICTOR)
if should_retrain:
    print(f"Retrain needed: {reason}")
```

#### `trigger_model_retrain(model_type, reason="scheduled") -> Dict`
Trigger model retraining.

**Returns:**
```python
{
    'retrain_id': 'uuid-string',
    'status': 'triggered',
    'reason': 'drift_detected',
    'sample_count': 150,
    'current_performance': {...}
}
```

#### `get_retraining_recommendation(model_type=None) -> Dict`
Get retraining recommendations for all or specific model.

**Returns:**
```python
{
    'roas_predictor': {
        'should_retrain': True,
        'reason': 'Feature drift detected: high',
        'priority': 'high',
        'checked_at': '2025-12-02T00:15:00'
    }
}
```

### 5. A/B Testing

#### `ab_test_model_versions(model_type, model_a_id, model_b_id, traffic_split=0.5, duration_days=7) -> Dict`
Start A/B test between two model versions.

**Parameters:**
- `traffic_split`: float (0-1) - Percentage for model A
- `duration_days`: int - Test duration

**Returns:**
```python
{
    'test_id': 'uuid-string',
    'status': 'active',
    'config': {
        'model_a_id': 'v1.0',
        'model_b_id': 'v1.1',
        'traffic_split': 0.5,
        'duration_days': 7
    }
}
```

#### `get_ab_test_results(test_id) -> Dict`
Get current results of A/B test.

**Returns:**
```python
{
    'test_id': 'uuid-string',
    'status': 'active',
    'results': {
        'model_a': {
            'sample_count': 150,
            'mae': 0.35,
            'rmse': 0.48,
            'mape': 14.2
        },
        'model_b': {
            'sample_count': 152,
            'mae': 0.28,
            'rmse': 0.39,
            'mape': 11.5
        },
        'comparison': {
            'winner': 'model_b',
            'mae_difference': 0.07,
            'statistically_significant': True,
            'p_value': 0.002,
            't_statistic': 3.45
        }
    }
}
```

#### `select_winning_model(test_id, min_confidence=0.95) -> Optional[str]`
Select winning model if statistically significant.

**Returns:** Model ID of winner or None

**Example:**
```python
winner = engine.select_winning_model(test_id, min_confidence=0.95)
if winner:
    print(f"Promote {winner} to production")
else:
    print("No significant winner, continue test")
```

### 6. Performance Monitoring

#### `get_model_performance(model_type, days_back=30) -> ModelPerformance`
Get current performance metrics.

**Returns:**
```python
ModelPerformance(
    model_type=ModelType.ROAS_PREDICTOR,
    mae=0.35,
    rmse=0.48,
    r2=0.85,
    mape=14.2,
    sample_count=150,
    last_updated=datetime.now()
)
```

**Example:**
```python
perf = engine.get_model_performance(ModelType.CTR_PREDICTOR)
print(f"MAE: {perf.mae:.4f}")
print(f"R²: {perf.r2:.4f}")
print(f"MAPE: {perf.mape:.2f}%")
print(f"Samples: {perf.sample_count}")
```

### 7. Feature Importance

#### `update_feature_weights(model_type, performance_data) -> Dict[str, float]`
Update feature importance based on performance.

**Parameters:**
- `performance_data`: pandas DataFrame with features and 'actual_value' column

**Returns:** Dict of feature -> normalized weight (0-1)

**Example:**
```python
import pandas as pd

data = pd.DataFrame({
    'ad_spend': [...],
    'ctr': [...],
    'engagement': [...],
    'actual_value': [...]
})

weights = engine.update_feature_weights(ModelType.ROAS_PREDICTOR, data)
for feature, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
    print(f"{feature}: {weight:.4f}")
```

#### `get_feature_importance_trends(model_type, days_back=90) -> Dict[str, List[float]]`
Get feature importance history.

### 8. Reporting

#### `generate_learning_report(period_days=7) -> Dict`
Generate comprehensive learning report.

**Returns:**
```python
{
    'period_days': 7,
    'generated_at': '2025-12-02T00:15:00',
    'models': {
        'roas_predictor': {
            'performance': {...},
            'error_distribution': {...},
            'drift_detection': {
                'feature_drift': {...},
                'concept_drift': {...}
            },
            'systematic_errors': [...],
            'retraining': {
                'recommended': True,
                'reason': '...'
            }
        }
    }
}
```

### 9. Scheduled Jobs

#### `run_daily_learning_job() -> Dict`
Run automated daily analysis.

**Performs:**
1. Feature drift detection for all models
2. Concept drift detection for all models
3. Performance metric updates
4. Alert creation for critical issues

**Example:**
```python
results = engine.run_daily_learning_job()
print(f"Analyzed {len(results['tasks'])} models")
```

#### `run_weekly_learning_job() -> Dict`
Run comprehensive weekly analysis.

**Performs:**
1. Generate learning report
2. Get retraining recommendations
3. Check and conclude A/B tests
4. Select winning models

### 10. Alerts

#### `check_alerts() -> List[Dict]`
Get recent alerts (last 24 hours).

**Returns:**
```python
[
    {
        'alert_id': 'uuid-string',
        'alert_type': 'feature_drift',
        'model_type': 'roas_predictor',
        'severity': 'high',
        'details': {...},
        'created_at': '2025-12-02T00:15:00',
        'status': 'active'
    }
]
```

#### `create_alert(alert_type, model_type, details) -> str`
Manually create an alert.

## Statistical Tests

### Kolmogorov-Smirnov Test
**Usage:** Feature drift, prediction drift
**Interpretation:** p-value < 0.05 → distributions differ
**Method:** `run_ks_test(reference, current)`

### T-Test (Independent)
**Usage:** Concept drift, A/B testing
**Interpretation:** p-value < 0.05 → significant difference
**Auto-applied in:** `detect_concept_drift()`, `select_winning_model()`

### One-Sample T-Test
**Usage:** Systematic error detection
**Interpretation:** p-value < 0.05 → systematic bias exists
**Auto-applied in:** `identify_systematic_errors()`

### Shapiro-Wilk Test
**Usage:** Error normality check
**Interpretation:** p-value > 0.05 → normally distributed
**Auto-applied in:** `analyze_error_distribution()`

## Enums

### ModelType
```python
ModelType.ROAS_PREDICTOR
ModelType.HOOK_CLASSIFIER
ModelType.VISUAL_PATTERN
ModelType.CTR_PREDICTOR
```

### DriftType
```python
DriftType.DATA_DRIFT        # Feature distributions changed
DriftType.CONCEPT_DRIFT     # Model-target relationships changed
DriftType.PREDICTION_DRIFT  # Prediction distributions changed
```

## Severity Levels

All drift reports use consistent severity:
- **low**: Monitor, no action needed
- **medium**: Increased monitoring, consider retraining
- **high**: Schedule retraining soon
- **critical**: Immediate retraining required

## Common Workflows

### Complete Prediction Lifecycle
```python
# 1. Make and register prediction
pred_id = engine.register_prediction(
    ModelType.ROAS_PREDICTOR,
    predicted_value=2.5,
    features={'ad_spend': 1000}
)

# 2. Later, record actual outcome
outcome = engine.record_outcome(pred_id, actual_value=2.7)

# 3. Periodically check performance
perf = engine.get_model_performance(ModelType.ROAS_PREDICTOR)

# 4. Check for drift
feature_drift = engine.identify_feature_drift(ModelType.ROAS_PREDICTOR)
concept_drift = engine.detect_concept_drift(ModelType.ROAS_PREDICTOR)

# 5. Retrain if needed
if feature_drift.severity == 'critical':
    engine.trigger_model_retrain(
        ModelType.ROAS_PREDICTOR,
        reason=feature_drift.recommendation
    )
```

### A/B Test New Model
```python
# 1. Start test
test = engine.ab_test_model_versions(
    model_type=ModelType.CTR_PREDICTOR,
    model_a_id="current_v1.0",
    model_b_id="candidate_v1.1",
    traffic_split=0.5,
    duration_days=7
)

test_id = test['test_id']

# 2. Record predictions and outcomes for both models
# (Application logic routes 50% traffic to each)

# 3. Check results after test period
results = engine.get_ab_test_results(test_id)
if results['results']['comparison']['statistically_significant']:
    winner = engine.select_winning_model(test_id)
    print(f"Promote {winner} to production")
```

### Daily Monitoring Job
```python
def daily_ml_monitoring():
    """Run as cron job every day"""
    results = engine.run_daily_learning_job()

    # Check for critical alerts
    alerts = engine.check_alerts()
    critical = [a for a in alerts if a['severity'] == 'critical']

    if critical:
        send_alert_to_team(critical)

    return results
```

### Weekly Analysis
```python
def weekly_ml_analysis():
    """Run as cron job every week"""
    results = engine.run_weekly_learning_job()

    # Get retraining recommendations
    recommendations = results['retraining_recommendations']
    high_priority = {
        model: rec for model, rec in recommendations.items()
        if rec['priority'] == 'high'
    }

    # Trigger retraining for high priority
    for model_type_str in high_priority:
        model_type = ModelType[model_type_str.upper()]
        engine.trigger_model_retrain(model_type, reason="weekly_review")

    # Generate report email
    send_weekly_report(results['report'])
```

## Error Handling

All methods include try/except blocks and return informative errors:

```python
try:
    outcome = engine.record_outcome(pred_id, actual_value)
except ValueError as e:
    # Prediction ID not found
    logger.error(f"Invalid prediction: {e}")
except Exception as e:
    # Unexpected error
    logger.error(f"Error recording outcome: {e}")
```

## Best Practices

1. **Minimum Sample Sizes**: Wait for 10+ samples before drift detection
2. **Regular Monitoring**: Run daily jobs for drift, weekly for comprehensive analysis
3. **Alert Thresholds**: Act on 'high' and 'critical' alerts immediately
4. **A/B Test Duration**: Run for at least 7 days for statistical power
5. **Retraining Cadence**: Retrain when drift detected, not on schedule alone
6. **Feature Tracking**: Update feature weights monthly to track importance shifts

## Performance Tips

1. Use numpy arrays for bulk operations
2. Filter outcomes by date before processing
3. Batch prediction registrations if possible
4. Cache performance calculations
5. Run heavy analysis jobs off-peak hours

## Integration Examples

### With FastAPI
```python
from fastapi import FastAPI
from self_learning import SelfLearningEngine, ModelType

app = FastAPI()
engine = SelfLearningEngine(db_service, model_registry)

@app.post("/predict")
async def predict(request: PredictRequest):
    # Make prediction
    prediction = model.predict(request.features)

    # Register with learning engine
    pred_id = engine.register_prediction(
        ModelType.ROAS_PREDICTOR,
        prediction,
        request.features
    )

    return {"prediction": prediction, "tracking_id": pred_id}

@app.post("/outcome")
async def record_outcome(pred_id: str, actual: float):
    outcome = engine.record_outcome(pred_id, actual)
    return {"status": "recorded", "error": outcome.error}

@app.get("/health/models")
async def model_health():
    report = engine.generate_learning_report(period_days=7)
    return report
```

## Troubleshooting

**Q: "Insufficient data" errors in drift detection?**
A: Need minimum 10 samples in both reference and current periods

**Q: A/B test shows no winner?**
A: Either not statistically significant or sample size too small. Run longer.

**Q: All features showing drift?**
A: Likely data pipeline change. Investigate upstream data sources.

**Q: Performance metrics look wrong?**
A: Check that actual_value is being recorded correctly for all predictions.

## Next Steps

- Integrate with production prediction pipeline
- Set up scheduled jobs (cron/Airflow)
- Configure alert routing (email/Slack)
- Add database persistence
- Implement model registry integration
- Set up monitoring dashboards
