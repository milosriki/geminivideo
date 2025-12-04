# Agent 11: Campaign Performance Tracker

## Overview

Real-time campaign performance tracking system that integrates with Meta Ads API to provide comprehensive analytics, anomaly detection, and creative-level insights.

## Implementation Details

**File:** `/home/user/geminivideo/services/ml-service/campaign_tracker.py`
**Lines of Code:** 1,302
**Status:** Production-ready

## Features Implemented

### 1. Real-time Metrics Sync
- **`sync_campaign_metrics(campaign_id, date_range)`**: Fetch latest metrics from Meta API
- **`sync_all_active_campaigns()`**: Batch sync all active campaigns
- Automatic database persistence
- Error handling and retry logic

### 2. ROAS Calculations
- **`calculate_roas(campaign_id, include_offline, attribution_window_days)`**: True ROAS with offline conversions
- **`calculate_blended_roas(campaign_ids)`**: Multi-campaign ROAS aggregation
- Configurable attribution windows (default: 7 days)
- Historical trend analysis

### 3. Performance Metrics
- **`calculate_ctr(campaign_id)`**: Click-Through Rate
- **`calculate_cpc(campaign_id)`**: Cost Per Click
- **`calculate_cpm(campaign_id)`**: Cost Per Mille (1000 impressions)
- **`calculate_cpa(campaign_id)`**: Cost Per Acquisition
- **`get_cost_per_result(campaign_id, result_type)`**: Custom result type costs

### 4. Prediction Validation
- **`compare_vs_prediction(prediction_id, campaign_id)`**: ML prediction accuracy
- **`get_prediction_accuracy(days_back)`**: Overall model performance
- Tracks ROAS and CTR prediction errors
- Accuracy scoring (0-100)

### 5. Anomaly Detection
- **`detect_anomalies(campaign_id, metrics, threshold_std)`**: Statistical anomaly detection
- **`alert_on_anomaly(campaign_id, alert_type, threshold)`**: Automated alerting
- Z-score based detection (configurable threshold)
- Multiple alert types:
  - Spend anomaly
  - CTR drop
  - ROAS below target
  - High frequency
  - Budget depleted

### 6. Creative-level Analysis
- **`aggregate_by_creative(campaign_id)`**: Performance breakdown by creative
- **`get_top_creatives(campaign_id, metric, limit)`**: Best performers
- **`get_creative_fatigue(creative_id)`**: Fatigue detection using CTR trends
- Creative rotation recommendations

### 7. Reporting & Export
- **`generate_daily_report(campaign_ids)`**: Daily performance summary
- **`export_metrics_csv(campaign_id, date_range, output_path)`**: CSV export
- Aggregated statistics across campaigns
- Top campaign identification

## Database Schema

### Tables Created

#### 1. `campaign_metrics`
```sql
- id (PK)
- campaign_id (indexed)
- impressions
- clicks
- spend
- conversions
- revenue
- ctr, cpc, cpm, cpa, roas
- frequency, reach
- date (indexed)
- synced_at
- metadata (JSON)
```

#### 2. `creative_metrics`
```sql
- id (PK)
- creative_id (indexed)
- campaign_id (indexed)
- impressions, clicks, conversions
- spend, ctr, conversion_rate, roas
- date
- synced_at
- metadata (JSON)
```

#### 3. `prediction_comparisons`
```sql
- id (PK)
- prediction_id (indexed)
- campaign_id (indexed)
- predicted_roas, actual_roas
- predicted_ctr, actual_ctr
- roas_error, ctr_error
- accuracy_score
- created_at
```

#### 4. `performance_alerts`
```sql
- id (PK)
- campaign_id (indexed)
- alert_type
- severity (info/warning/critical)
- message
- metric_name, threshold, actual_value
- created_at
- resolved
- metadata (JSON)
```

## Environment Variables Required

```bash
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=your_ad_account_id
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## Usage Examples

### Basic Metrics Sync

```python
from services.ml_service.campaign_tracker import campaign_tracker
import asyncio

async def sync_campaign():
    # Sync single campaign
    metrics = await campaign_tracker.sync_campaign_metrics("123456789")
    print(f"ROAS: {metrics.roas}, CTR: {metrics.ctr}%")

    # Sync all active campaigns
    all_metrics = await campaign_tracker.sync_all_active_campaigns()
    print(f"Synced {len(all_metrics)} campaigns")

asyncio.run(sync_campaign())
```

### ROAS Calculation

```python
# Calculate 7-day ROAS
roas = campaign_tracker.calculate_roas(
    campaign_id="123456789",
    include_offline=True,
    attribution_window_days=7
)
print(f"7-day ROAS: {roas}")

# Blended ROAS across campaigns
blended = campaign_tracker.calculate_blended_roas([
    "campaign_1",
    "campaign_2",
    "campaign_3"
])
print(f"Blended ROAS: {blended}")
```

### Anomaly Detection

```python
# Detect anomalies
anomalies = campaign_tracker.detect_anomalies(
    campaign_id="123456789",
    metrics=current_metrics,
    threshold_std=2.0  # 2 standard deviations
)

for anomaly in anomalies:
    print(f"Anomaly: {anomaly['metric']} - {anomaly['severity']}")

# Set up alerts
alert = campaign_tracker.alert_on_anomaly(
    campaign_id="123456789",
    alert_type=AlertType.ROAS_BELOW_TARGET,
    threshold=2.5  # Alert if ROAS < 2.5
)

if alert:
    print(f"Alert triggered: {alert['message']}")
```

### Creative Analysis

```python
# Get top performing creatives
top_creatives = campaign_tracker.get_top_creatives(
    campaign_id="123456789",
    metric="roas",
    limit=10
)

for creative in top_creatives:
    print(f"Creative {creative.creative_id}: ROAS={creative.roas}")

# Check for creative fatigue
fatigue = campaign_tracker.get_creative_fatigue("creative_123")
if fatigue['fatigued']:
    print(f"Creative is fatigued! Score: {fatigue['fatigue_score']}")
    print(f"Recommendation: {fatigue['recommendation']}")
```

### Daily Reporting

```python
# Generate daily report
report = campaign_tracker.generate_daily_report()
print(f"Total Spend: ${report['total_spend']}")
print(f"Total Revenue: ${report['total_revenue']}")
print(f"Average ROAS: {report['avg_roas']}")
print(f"Top Campaigns: {report['top_campaigns']}")

# Export to CSV
csv_path = campaign_tracker.export_metrics_csv(
    campaign_id="123456789",
    date_range=("2025-01-01", "2025-01-31"),
    output_path="/tmp/campaign_metrics.csv"
)
print(f"Exported to: {csv_path}")
```

### Prediction Validation

```python
# Compare prediction vs actual
comparison = campaign_tracker.compare_vs_prediction(
    prediction_id="pred_123",
    campaign_id="123456789"
)

print(f"Predicted ROAS: {comparison.predicted_roas}")
print(f"Actual ROAS: {comparison.actual_roas}")
print(f"Accuracy: {comparison.accuracy_score}%")

# Overall prediction accuracy
accuracy = campaign_tracker.get_prediction_accuracy(days_back=30)
print(f"30-day prediction accuracy: {accuracy['avg_accuracy']}%")
print(f"ROAS prediction accuracy: {accuracy['roas_accuracy']}%")
print(f"CTR prediction accuracy: {accuracy['ctr_accuracy']}%")
```

## Integration Points

### 1. Meta Ads API (v19.0)
- Campaign Insights endpoint
- Ad-level metrics
- Real-time data sync

### 2. Database (PostgreSQL)
- SQLAlchemy ORM
- Automatic schema creation
- Transaction management

### 3. ML Service Integration
- Prediction comparison
- Accuracy tracking
- Model performance monitoring

## Error Handling

- **API Failures**: Graceful degradation, returns empty metrics
- **Database Errors**: Continues operation, logs warnings
- **Missing Credentials**: Clear warning messages
- **Rate Limiting**: Implements timeout and retry logic

## Performance Considerations

- **Batch Operations**: `sync_all_active_campaigns()` for efficiency
- **Database Indexing**: Optimized queries on `campaign_id` and `date`
- **Connection Pooling**: SQLAlchemy session management
- **Caching**: Historical data cached for anomaly detection

## Testing

```python
# Run basic tests
python3 /home/user/geminivideo/services/ml-service/campaign_tracker.py
```

## Monitoring & Logging

All operations logged with Python `logging` module:
- INFO: Successful operations
- WARNING: Non-critical issues (missing credentials, no data)
- ERROR: Critical failures with stack traces

## Next Steps

1. **Integration with Agent 12**: Creative Performance Attribution
2. **Integration with Agent 16**: ROAS Predictor for validation
3. **Dashboard UI**: Real-time metrics visualization
4. **Alert System**: Slack/email notifications for anomalies
5. **Automated Actions**: Auto-pause campaigns on poor performance

## Production Checklist

- [x] Real Meta API integration (no mocks)
- [x] Database persistence with SQLAlchemy
- [x] Comprehensive error handling
- [x] Type hints throughout
- [x] Logging infrastructure
- [x] Anomaly detection algorithms
- [x] Creative-level analysis
- [x] CSV export functionality
- [x] Daily reporting
- [x] Prediction validation
- [x] Documentation

## Key Metrics Tracked

| Metric | Description | Calculation |
|--------|-------------|-------------|
| ROAS | Return on Ad Spend | Revenue / Spend |
| CTR | Click-Through Rate | (Clicks / Impressions) × 100 |
| CPC | Cost Per Click | Spend / Clicks |
| CPM | Cost Per Mille | (Spend / Impressions) × 1000 |
| CPA | Cost Per Acquisition | Spend / Conversions |
| Frequency | Avg impressions per user | Impressions / Reach |

## Author

Agent 11 of 30 - ULTIMATE Production Plan

## License

Part of the GeminiVideo production system
