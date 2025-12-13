# Monitoring & Observability

This module provides comprehensive monitoring and observability features for the Gateway API service, including Prometheus metrics, health checks, and distributed tracing.

## Features

### 1. Prometheus Metrics (`metrics.ts`)

Collect and expose metrics in Prometheus format, compatible with Grafana dashboards.

#### Available Metrics

**HTTP Metrics:**
- `http_request_duration_seconds` - Histogram of HTTP request durations
- `http_requests_total` - Counter of total HTTP requests
- `active_connections` - Gauge of active connections

**Business Metrics:**
- `ads_processed_total` - Counter of ads processed (by status and account)
- `video_generation_total` - Counter of video generation requests
- `cache_operations_total` - Counter of cache operations (hits/misses)
- `database_query_duration_seconds` - Histogram of database query durations
- `active_jobs` - Gauge of active background jobs
- `errors_total` - Counter of errors by type and endpoint

**System Metrics:**
- Node.js default metrics (memory, CPU, event loop, GC, etc.)

#### Usage

```typescript
import { metricsMiddleware, recordAdProcessed } from './monitoring/metrics';

// Add middleware to Express app
app.use(metricsMiddleware);

// Record business metrics
recordAdProcessed('success', 'account-123');
recordVideoGeneration('completed', 'gemini-1.5');
recordCacheOperation('get', 'hit');

// Record database queries with timing
await recordDatabaseQuery('select_ads', async () => {
  return await db.query('SELECT * FROM ads');
});
```

### 2. Health Checks (`health.ts`)

Comprehensive health checking for the service and its dependencies.

#### Endpoints

- **`/health`** - Overall health status of the service
- **`/health/ready`** - Readiness probe (is the service ready to accept traffic?)
- **`/health/live`** - Liveness probe (is the service alive?)

#### Health Check Components

The health check system monitors:
- Database connectivity (PostgreSQL)
- Redis connectivity (optional)
- Meta API configuration
- Gemini API configuration
- System resources (memory, CPU)

#### Response Format

```json
{
  "status": "healthy",
  "timestamp": "2025-12-13T10:30:00.000Z",
  "uptime": 3600,
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "latency": 15,
      "details": {
        "type": "postgresql",
        "connected": true
      }
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency": 5
    }
  ],
  "version": "1.0.0"
}
```

#### Health Status Codes

- `200` - Healthy or degraded (service is operational)
- `503` - Unhealthy (service is not operational)

### 3. Distributed Tracing (`tracing.ts`)

OpenTelemetry-based distributed tracing for request tracking and debugging.

#### Features

- Automatic HTTP request tracing
- Manual span creation for custom instrumentation
- Trace context propagation
- Basic tracing without OpenTelemetry packages (fallback mode)

#### Usage

```typescript
import {
  initTracing,
  tracingMiddleware,
  traceAsync
} from './monitoring/tracing';

// Initialize tracing
initTracing({
  serviceName: 'gateway-api',
  enabled: true,
  exporterUrl: 'http://localhost:4318/v1/traces'
});

// Add middleware
app.use(tracingMiddleware);

// Trace async operations
await traceAsync('process_video', async () => {
  // Your code here
  return result;
}, { videoId: '123' });
```

#### OpenTelemetry Setup

To enable full OpenTelemetry support, install the required packages:

```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

Then set environment variables:

```bash
export TRACING_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

## Environment Variables

```bash
# Tracing Configuration
TRACING_ENABLED=true|false          # Enable/disable distributed tracing
SERVICE_NAME=gateway-api             # Service name for tracing
OTEL_EXPORTER_OTLP_ENDPOINT=url     # OpenTelemetry collector endpoint

# Database (required for health checks)
DATABASE_URL=postgresql://...        # PostgreSQL connection string

# Redis (optional)
REDIS_URL=redis://localhost:6379    # Redis connection string
REDIS_ENABLED=true|false            # Enable/disable Redis
```

## Grafana Integration

### Prometheus Data Source

Add the Gateway API metrics endpoint as a Prometheus data source in Grafana:

1. Navigate to Configuration → Data Sources
2. Add new Prometheus data source
3. Set URL to: `http://gateway-api:8000/metrics`
4. Save & Test

### Sample Queries

**Request Rate:**
```promql
rate(http_requests_total[5m])
```

**Request Duration (p95):**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error Rate:**
```promql
rate(errors_total[5m])
```

**Active Connections:**
```promql
active_connections
```

## Kubernetes Integration

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Metrics Scraping

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

## Testing

### Test Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Test Health Endpoints

```bash
# Overall health
curl http://localhost:8000/health | jq

# Readiness
curl http://localhost:8000/health/ready | jq

# Liveness
curl http://localhost:8000/health/live | jq
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Gateway API                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Metrics    │  │    Health    │  │   Tracing    │ │
│  │  Middleware  │  │    Checks    │  │  Middleware  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │          │
│         v                 v                  v          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Express Application                   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                 │                  │
         v                 v                  v
   ┌──────────┐     ┌────────────┐    ┌──────────────┐
   │Prometheus│     │   K8s      │    │ OpenTelemetry│
   │ & Grafana│     │ Health     │    │  Collector   │
   └──────────┘     └────────────┘    └──────────────┘
```

## Best Practices

1. **Metrics Cardinality**: Avoid high-cardinality labels (e.g., user IDs) in metrics
2. **Health Check Timeout**: Keep health checks fast (< 1 second)
3. **Tracing Sampling**: In production, use sampling to reduce overhead
4. **Error Tracking**: Always record errors in both metrics and traces
5. **Dashboard Organization**: Group related metrics in Grafana dashboards

## Troubleshooting

### Metrics not appearing

1. Verify the `/metrics` endpoint is accessible
2. Check Prometheus scrape configuration
3. Ensure middleware is loaded correctly

### Health checks failing

1. Check database connectivity
2. Verify Redis configuration (if enabled)
3. Review service logs for errors

### Tracing not working

1. Verify `TRACING_ENABLED=true`
2. Check OpenTelemetry collector endpoint
3. Install required OpenTelemetry packages

## Future Enhancements

- [ ] Add custom dashboards for Grafana
- [ ] Implement alerting rules
- [ ] Add distributed tracing correlation with logs
- [ ] Implement SLO/SLI tracking
- [ ] Add performance profiling integration
