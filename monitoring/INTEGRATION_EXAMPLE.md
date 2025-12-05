# Integration Example: Adding Monitoring to ML Service

This guide shows how to add comprehensive monitoring to an existing service.

## Example: ML Service

### Before (Current State)

```python
# /services/ml-service/src/main.py
import logging
from fastapi import FastAPI

# Basic logging only
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Service")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### After (With Monitoring)

```python
# /services/ml-service/src/main.py
import logging
import sys
from fastapi import FastAPI

# Add monitoring to path
sys.path.append('/home/user/geminivideo')

# Import monitoring
from monitoring.middleware.fastapi_middleware import setup_monitoring
from monitoring import (
    track_ai_call_with_cost,
    prediction_accuracy,
    campaigns_created_total,
    track_database_query,
)

app = FastAPI(
    title="ML Service",
    version="2.0.0"
)

# Setup monitoring (replaces basic logging)
setup_monitoring(
    app,
    service_name="ml-service",
    environment="production",
    version="2.0.0",
    log_level="INFO"
)

@app.post("/predict/ctr")
async def predict_ctr_enhanced(request: EnhancedCTRRequest):
    """
    Predict CTR using enhanced model with monitoring
    """
    # Track AI API call with automatic cost calculation
    cost = track_ai_call_with_cost(
        service="ml-service",
        provider="google",
        model="gemini-1.5-flash",
        input_tokens=features_size * 10,  # Estimate
        output_tokens=100
    )

    # Your existing prediction logic
    result = enhanced_ctr_predictor.predict(request.clip_data)

    # Update prediction accuracy metric
    prediction_accuracy.labels(
        service="ml-service",
        model_type="ctr_predictor",
        metric="r2"
    ).set(enhanced_ctr_predictor.training_metrics.get('test_r2', 0))

    return EnhancedCTRResponse(**result)


@app.post("/train/ctr")
async def train_enhanced_ctr_model(request: EnhancedTrainingRequest):
    """
    Train enhanced model with database query tracking
    """
    # Track database query
    with track_database_query("ml-service", "postgres", "SELECT"):
        data_loader = get_data_loader()
        X, y = data_loader.fetch_training_data(min_impressions=100)

    # Your existing training logic
    metrics = enhanced_ctr_predictor.train(historical_ads)

    # Update accuracy metric
    prediction_accuracy.labels(
        service="ml-service",
        model_type="ctr_predictor",
        metric="r2"
    ).set(metrics.get('test_r2', 0))

    return {
        "status": "success",
        "metrics": metrics
    }
```

## What You Get

### 1. Automatic HTTP Metrics

All endpoints automatically tracked:
- Request rate (req/s)
- Response latency (P50, P95, P99)
- Error rates
- Request/response sizes

### 2. Structured JSON Logs

```json
{
  "timestamp": "2025-12-05T12:00:00.000Z",
  "level": "INFO",
  "service": "ml-service",
  "environment": "production",
  "message": "HTTP Request: POST /predict/ctr",
  "correlation_id": "abc-123",
  "method": "POST",
  "path": "/predict/ctr",
  "duration_ms": 45.2
}
```

### 3. AI Cost Tracking

```python
# Before
response = openai.ChatCompletion.create(...)

# After
cost = track_ai_call_with_cost(
    service="ml-service",
    provider="openai",
    model="gpt-4",
    input_tokens=100,
    output_tokens=200
)
# Cost automatically calculated and tracked in Prometheus
```

### 4. Business Metrics

```python
# Track campaign creation
campaigns_created_total.labels(
    service="ml-service",
    user_id="user123",
    platform="meta"
).inc()

# Update prediction accuracy
prediction_accuracy.labels(
    service="ml-service",
    model_type="roas_predictor",
    metric="r2"
).set(0.87)
```

### 5. New Endpoints

Automatically added:
- `/metrics` - Prometheus metrics
- `/health` - Health check

## Step-by-Step Integration

### Step 1: Install Dependencies

```bash
cd /home/user/geminivideo/services/ml-service
pip install prometheus-client python-json-logger
```

### Step 2: Add Monitoring Import

```python
# At the top of your main.py
import sys
sys.path.append('/home/user/geminivideo')

from monitoring.middleware.fastapi_middleware import setup_monitoring
from monitoring import track_ai_call_with_cost, prediction_accuracy
```

### Step 3: Setup Monitoring

```python
# After creating FastAPI app
app = FastAPI(title="ML Service")

# Add this line
setup_monitoring(
    app,
    service_name="ml-service",
    environment=os.getenv("ENVIRONMENT", "production"),
    version="2.0.0"
)
```

### Step 4: Add Business Metrics

```python
# In your prediction endpoints
from monitoring import prediction_accuracy

@app.post("/predict/ctr")
async def predict_ctr(request):
    result = model.predict(...)

    # Track accuracy
    prediction_accuracy.labels(
        service="ml-service",
        model_type="ctr",
        metric="r2"
    ).set(model.metrics['r2'])

    return result
```

### Step 5: Track AI Calls

```python
# In endpoints that use AI APIs
from monitoring import track_ai_call_with_cost

@app.post("/generate")
async def generate(request):
    # Track AI call
    cost = track_ai_call_with_cost(
        service="ml-service",
        provider="google",
        model="gemini-pro",
        input_tokens=request.input_size,
        output_tokens=response.output_size
    )

    return {"result": result, "cost": cost}
```

### Step 6: Update Prometheus Config

```yaml
# In /monitoring/prometheus.yml
scrape_configs:
  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8003']  # Your service port
    metrics_path: '/metrics'
```

### Step 7: Reload Prometheus

```bash
curl -X POST http://localhost:9090/-/reload
```

## Verification

### Check Metrics Endpoint

```bash
curl http://localhost:8003/metrics

# Should see:
# http_requests_total{service="ml-service",method="POST",endpoint="/predict/ctr",status="200"} 42
# ai_api_cost_total{service="ml-service",provider="google",model="gemini-pro"} 1.23
# prediction_accuracy{service="ml-service",model_type="ctr",metric="r2"} 0.87
```

### Check Logs

```bash
docker logs ml-service --tail=10

# Should see JSON format:
# {"timestamp":"2025-12-05T12:00:00.000Z","level":"INFO","service":"ml-service",...}
```

### Check Grafana

1. Open http://localhost:3000
2. Import dashboards from `/monitoring/dashboards/`
3. View ML service metrics

## Minimal Integration (Quick Start)

If you only want basic monitoring:

```python
from monitoring.middleware.fastapi_middleware import setup_monitoring

app = FastAPI()
setup_monitoring(app, service_name="ml-service")

# That's it! You now have:
# - HTTP metrics
# - Structured logging
# - /metrics endpoint
# - /health endpoint
```

## Advanced: Custom Metrics

```python
from prometheus_client import Counter, Histogram

# Custom metric
model_predictions = Counter(
    'model_predictions_total',
    'Total model predictions',
    ['model_type', 'accuracy_band']
)

@app.post("/predict")
async def predict(request):
    result = model.predict(...)

    # Track custom metric
    model_predictions.labels(
        model_type='ctr',
        accuracy_band='high' if result.confidence > 0.8 else 'low'
    ).inc()

    return result
```

## Common Issues

### Import Error

```
ModuleNotFoundError: No module named 'monitoring'
```

**Solution**: Add parent directory to path:
```python
import sys
sys.path.append('/home/user/geminivideo')
```

### Metrics Not Showing

**Solution**:
1. Check `/metrics` endpoint is accessible
2. Verify Prometheus is scraping: http://localhost:9090/targets
3. Check service name matches dashboard queries

### Duplicate Metrics

```
ValueError: Duplicated timeseries in CollectorRegistry
```

**Solution**: Only call `setup_monitoring()` once per service

## Next Steps

1. Add alerting rules for your service
2. Create custom Grafana dashboard
3. Set up log aggregation
4. Configure PagerDuty for critical alerts

## Full Example

See `/monitoring/examples/ml_service_integration.py` for complete working example.
