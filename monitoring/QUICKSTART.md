# Monitoring Quick Start Guide

Get monitoring up and running in 5 minutes.

## Step 1: Deploy Monitoring Stack (2 minutes)

```bash
# Navigate to monitoring directory
cd /home/user/geminivideo/monitoring

# Copy environment configuration
cp .env.example .env

# Edit .env and set required values (at minimum):
# - GRAFANA_ADMIN_PASSWORD
# - SLACK_WEBHOOK_URL (optional but recommended)

# Deploy with Docker
./setup.sh docker
```

This will start:
- Prometheus (metrics): http://localhost:9090
- Grafana (dashboards): http://localhost:3000
- AlertManager (alerts): http://localhost:9093
- Node Exporter (system metrics)
- Redis Exporter
- PostgreSQL Exporter

## Step 2: Integrate Services (3 minutes)

### Python Service (FastAPI)

1. Install dependencies:
```bash
pip install prometheus-client python-json-logger
```

2. Add to your service (e.g., `/services/titan-core/main.py`):
```python
from fastapi import FastAPI
import sys
sys.path.append('/home/user/geminivideo')
from monitoring.middleware.fastapi_middleware import setup_monitoring

app = FastAPI(title="Titan Core")

# Add this line
setup_monitoring(
    app,
    service_name="titan-core",
    environment="production",
    version="1.0.0"
)

# Your existing routes...
```

3. Update Prometheus config to scrape your service:
```yaml
# Add to monitoring/prometheus.yml under scrape_configs
- job_name: 'titan-core'
  static_configs:
    - targets: ['titan-core:8080']
  metrics_path: '/metrics'
```

4. Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

### Node.js Service (Express)

1. Install dependencies:
```bash
npm install prom-client winston uuid
```

2. Add to your service (e.g., `/services/gateway-api/src/index.ts`):
```typescript
import express from 'express';
import { setupMonitoring } from '../../monitoring/middleware/express_middleware';

const app = express();

// Add this line
const logger = setupMonitoring(app, {
  serviceName: 'gateway-api',
  environment: 'production',
  version: '1.0.0'
});

// Your existing routes...
```

3. Update Prometheus config (same as Python above)

## Step 3: View Dashboards

1. Open Grafana: http://localhost:3000
   - Username: `admin`
   - Password: (from your .env file)

2. Import dashboards:
   - Go to Dashboards → Import
   - Upload files from `/monitoring/dashboards/`:
     - `api-performance.json`
     - `ai-costs.json`
     - `business-metrics.json`
     - `system-health.json`

3. View metrics:
   - Select a dashboard
   - Set time range (last 1 hour)
   - Refresh to see live data

## Step 4: Test Alerting

Send a test alert:

```python
# Test script: test_alert.py
import sys
sys.path.append('/home/user/geminivideo')
from monitoring.alerting import setup_alerting_from_env, Severity

manager = setup_alerting_from_env("test-service")

manager.create_and_send_alert(
    title="Test Alert",
    message="This is a test alert from the monitoring system",
    severity=Severity.WARNING
)

print("Test alert sent! Check your email/Slack")
```

Run it:
```bash
python test_alert.py
```

## Step 5: Track Business Metrics

Add business metrics to your services:

```python
from monitoring.metrics import (
    campaigns_created_total,
    ads_published_total,
    roas_value
)

# When a campaign is created
campaigns_created_total.labels(
    service="my-service",
    user_id=user_id,
    platform="meta"
).inc()

# When an ad is published
ads_published_total.labels(
    service="my-service",
    platform="google",
    format="video"
).inc()

# Update ROAS
roas_value.labels(
    service="my-service",
    campaign_id=campaign_id,
    platform="meta"
).set(4.5)
```

## Verification Checklist

- [ ] Prometheus is running and accessible
- [ ] Grafana is running and accessible
- [ ] Services are instrumented and exposing `/metrics`
- [ ] Prometheus is scraping service metrics
- [ ] Dashboards show live data
- [ ] Alerts are configured and tested
- [ ] Logs are in JSON format with correlation IDs

## Common Issues

### Metrics not appearing

**Problem**: Service metrics don't show up in Prometheus

**Solution**:
1. Check service is exposing `/metrics`: `curl http://localhost:8080/metrics`
2. Verify Prometheus config: `docker-compose -f docker-compose.monitoring.yml config`
3. Check Prometheus targets: http://localhost:9090/targets
4. Ensure service is reachable from Prometheus container

### Dashboards empty

**Problem**: Grafana dashboards show no data

**Solution**:
1. Check Prometheus datasource: Configuration → Data Sources
2. Verify metrics are in Prometheus: http://localhost:9090/graph
3. Check time range in dashboard (try "Last 1 hour")
4. Ensure service names in dashboard match your config

### Alerts not sending

**Problem**: Alerts configured but not received

**Solution**:
1. Check environment variables in `.env`
2. Test SMTP connection: `telnet smtp.gmail.com 587`
3. Verify Slack webhook: `curl -X POST -d '{"text":"test"}' YOUR_WEBHOOK_URL`
4. Check AlertManager logs: `docker logs alertmanager`

## Next Steps

1. **Configure custom thresholds** for your SLOs
2. **Set up log aggregation** (ELK, Datadog, etc.)
3. **Create custom dashboards** for your specific metrics
4. **Set up SLA monitoring** for critical endpoints
5. **Configure retention policies** for metrics and logs
6. **Enable backup** for Prometheus and Grafana data

## Production Deployment

For production, update `docker-compose.monitoring.yml`:

1. **Use persistent volumes**:
```yaml
volumes:
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/prometheus-data
```

2. **Configure retention**:
```yaml
command:
  - '--storage.tsdb.retention.time=90d'
  - '--storage.tsdb.retention.size=50GB'
```

3. **Enable authentication**:
```yaml
environment:
  - GF_AUTH_BASIC_ENABLED=true
  - GF_AUTH_ANONYMOUS_ENABLED=false
```

4. **Use secrets** instead of environment variables

5. **Set up backup** cron jobs

## Support

For detailed documentation, see [README.md](README.md)

For issues:
1. Check service logs
2. Check Prometheus targets
3. Verify AlertManager status
4. Review environment configuration
