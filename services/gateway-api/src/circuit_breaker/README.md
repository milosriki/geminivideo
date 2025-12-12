# Circuit Breaker System for GeminiVideo Platform

**Agent 9: Circuit Breaker Builder**

A comprehensive circuit breaker implementation that protects the GeminiVideo platform from cascading failures when external APIs (OpenAI, Anthropic, Meta, Google) experience issues.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Components](#components)
- [Service-Specific Breakers](#service-specific-breakers)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Production Deployment](#production-deployment)

---

## Overview

The circuit breaker pattern prevents cascading failures by detecting when a service is unhealthy and temporarily blocking requests to that service. This gives the failing service time to recover while providing graceful degradation to users.

### Circuit Breaker States

```
┌─────────┐
│ CLOSED  │ ◄─── Normal operation, requests pass through
└────┬────┘
     │ Too many failures
     ▼
┌─────────┐
│  OPEN   │ ◄─── Service failing, requests blocked/fallback
└────┬────┘
     │ Timeout expires
     ▼
┌──────────┐
│HALF-OPEN │ ◄─── Testing recovery with limited requests
└────┬─────┘
     │ Success → CLOSED
     │ Failure → OPEN
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gateway API Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Circuit Breaker  │  │  Health Monitor  │                │
│  │   - State mgmt   │  │  - Periodic      │                │
│  │   - Metrics      │  │    checks        │                │
│  │   - Exponential  │  │  - Latency       │                │
│  │     backoff      │  │    tracking      │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                      │                           │
│           └──────────┬───────────┘                           │
│                      │                                       │
│           ┌──────────▼──────────┐                           │
│           │  Fallback Handler   │                           │
│           │  - Caching          │                           │
│           │  - Request queue    │                           │
│           │  - Retry logic      │                           │
│           └──────────┬──────────┘                           │
│                      │                                       │
└──────────────────────┼───────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  OpenAI     │ │ Anthropic   │ │    Meta     │
│  - GPT-4o   │ │ - Claude    │ │ - Ads API   │
│  - Failover │ │ - Failover  │ │ - Queueing  │
└─────────────┘ └─────────────┘ └─────────────┘
```

---

## Features

### Core Features
- ✅ **Circuit Breaker Pattern**: Closed → Open → Half-Open state machine
- ✅ **Exponential Backoff**: Automatic recovery with increasing timeouts
- ✅ **Health Monitoring**: Continuous health checks with latency tracking
- ✅ **Fallback Handling**: Graceful degradation strategies
- ✅ **Request Queueing**: Queue requests during outages for automatic retry
- ✅ **Metrics & Observability**: Detailed metrics for all operations

### Service-Specific Features
- ✅ **OpenAI Breaker**: Failover to Claude or Gemini
- ✅ **Anthropic Breaker**: Failover to GPT-4 or Gemini
- ✅ **Meta Breaker**: Request queueing for ad publishing

---

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis (optional, for distributed systems)

### Install Python Dependencies

```bash
cd /home/user/geminivideo/services/gateway-api/src/circuit_breaker
pip install -r requirements.txt
```

Create `requirements.txt`:
```
anthropic>=0.18.0
openai>=1.12.0
google-generativeai>=0.3.0
aiohttp>=3.9.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## Quick Start

### 1. Basic Circuit Breaker

```python
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig

# Create a circuit breaker
breaker = CircuitBreaker(
    name="my_api",
    config=CircuitBreakerConfig(
        failure_threshold=5,        # Open after 5 failures
        success_threshold=2,        # Close after 2 successes
        timeout_seconds=60.0,       # Try recovery after 1 minute
        exponential_backoff=True
    )
)

# Use as decorator
@breaker.protected
async def call_external_api():
    # Your API call here
    return await some_api_call()

# Or use as context manager
async with breaker:
    result = await some_api_call()

# Or use call method
result = await breaker.call(some_api_call)
```

### 2. With Fallback

```python
from circuit_breaker import CircuitBreaker

def fallback_handler(*args, **kwargs):
    return {"status": "degraded", "data": None}

breaker = CircuitBreaker(
    name="my_api",
    config=config,
    fallback=fallback_handler
)

# Fallback is automatically used when circuit is open
result = await breaker.call(risky_function)
```

### 3. Health Monitoring

```python
from health_monitor import HealthMonitor, HealthCheckConfig

monitor = HealthMonitor()

async def check_api_health():
    try:
        response = await api_client.ping()
        return response.ok
    except:
        return False

monitor.register_service(
    "my_api",
    check_api_health,
    config=HealthCheckConfig(
        check_interval_seconds=30.0,
        latency_warning_ms=1000.0,
        error_rate_critical=0.20
    )
)

# Start monitoring
await monitor.start()

# Get health status
health = monitor.get_service_health("my_api")
print(f"Status: {health.status}")
print(f"Error rate: {health.error_rate}")
print(f"P95 latency: {health.latency_p95}ms")
```

### 4. TypeScript/Express Integration

```typescript
import express from 'express';
import {
  registerCircuitBreakerRoutes,
  withCircuitBreaker
} from './circuit_breaker/middleware';

const app = express();

// Register monitoring endpoints
registerCircuitBreakerRoutes(app);

// Protect a route with circuit breaker
app.get('/api/generate', withCircuitBreaker(
  'openai_api',
  async (req, res) => {
    const result = await generateContent(req.body);
    res.json(result);
  }
));

// Access metrics
// GET /api/circuit-breaker/metrics
// GET /api/circuit-breaker/health
// GET /api/circuit-breaker/status
```

---

## Components

### 1. Circuit Breaker (`circuit_breaker.py`)

The core circuit breaker implementation with state management.

**Key Classes:**
- `CircuitBreaker`: Main circuit breaker class
- `CircuitBreakerConfig`: Configuration options
- `CircuitBreakerRegistry`: Global registry for managing multiple breakers

**Key Methods:**
- `call(func, *args, **kwargs)`: Execute function with protection
- `get_metrics()`: Get current metrics
- `reset()`: Reset circuit breaker state

### 2. Health Monitor (`health_monitor.py`)

Continuous health monitoring with alerts.

**Key Classes:**
- `HealthMonitor`: Main monitoring class
- `HealthCheckConfig`: Configuration for health checks
- `ServiceHealthMetrics`: Aggregated metrics per service

**Key Methods:**
- `register_service(name, health_check, config)`: Register a service
- `check_service_health(name)`: Perform health check
- `get_health_summary()`: Get overall health status
- `start()`: Start continuous monitoring

### 3. Fallback Handler (`fallback_handler.py`)

Graceful degradation with caching and queueing.

**Key Classes:**
- `FallbackHandler`: Main fallback handler
- `FallbackCache`: In-memory cache
- `RequestQueue`: Queue for retry requests

**Key Methods:**
- `register_fallback(service, func)`: Register fallback function
- `execute_with_fallback(service, func, ...)`: Execute with fallback
- `get_from_cache(service, key)`: Get cached response
- `queue_for_retry(service, func, ...)`: Queue for retry

---

## Service-Specific Breakers

### OpenAI Circuit Breaker

```python
from openai import AsyncOpenAI
from circuit_breaker.openai_breaker import OpenAICircuitBreaker

openai_client = AsyncOpenAI(api_key="...")
claude_client = Anthropic(api_key="...")  # Fallback

breaker = OpenAICircuitBreaker(
    openai_client=openai_client,
    claude_client=claude_client,  # Optional
    gemini_client=gemini_client   # Optional
)

# Use the breaker
result = await breaker.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4o-mini"
)

# If OpenAI fails, automatically fails over to Claude or Gemini
print(result["content"])
print(result.get("_fallback"))  # Shows which fallback was used
```

### Anthropic Circuit Breaker

```python
from anthropic import AsyncAnthropic
from circuit_breaker.anthropic_breaker import AnthropicCircuitBreaker

anthropic_client = AsyncAnthropic(api_key="...")
openai_client = AsyncOpenAI(api_key="...")  # Fallback

breaker = AnthropicCircuitBreaker(
    anthropic_client=anthropic_client,
    openai_client=openai_client,
    gemini_client=gemini_client
)

result = await breaker.create_message(
    messages=[{"role": "user", "content": "Hello"}],
    model="claude-3-5-sonnet-20241022"
)
```

### Meta Circuit Breaker

```python
from circuit_breaker.meta_breaker import MetaCircuitBreaker

breaker = MetaCircuitBreaker(
    meta_access_token="YOUR_META_TOKEN"
)

# Publish ad with automatic queueing on failure
result = await breaker.publish_ad(
    ad_account_id="act_123456",
    campaign_id="123456789",
    ad_creative={...},
    targeting={...},
    budget={...}
)

if result["queued"]:
    print(f"Ad queued for retry: {result['request_id']}")

# Check queued ads
queued = breaker.get_queued_ads()
print(f"{len(queued)} ads in queue")
```

---

## API Reference

### CircuitBreakerConfig

```python
CircuitBreakerConfig(
    failure_threshold: int = 5,              # Failures before opening
    success_threshold: int = 2,              # Successes to close
    timeout_seconds: float = 60.0,           # Recovery timeout
    half_open_max_calls: int = 3,           # Max calls in half-open
    exponential_backoff: bool = True,        # Enable backoff
    max_timeout_seconds: float = 300.0,      # Max backoff time
    backoff_multiplier: float = 2.0,         # Backoff multiplier
    rolling_window_seconds: int = 60,        # Failure window
    min_throughput: int = 10                 # Min requests before trigger
)
```

### HealthCheckConfig

```python
HealthCheckConfig(
    check_interval_seconds: float = 30.0,    # Check frequency
    check_timeout_seconds: float = 10.0,     # Check timeout
    latency_warning_ms: float = 1000.0,      # Warning threshold
    latency_critical_ms: float = 3000.0,     # Critical threshold
    error_rate_warning: float = 0.05,        # 5% warning
    error_rate_critical: float = 0.20,       # 20% critical
    history_size: int = 100,                 # History to keep
    alert_cooldown_seconds: int = 300        # Alert cooldown
)
```

### FallbackConfig

```python
FallbackConfig(
    cache_enabled: bool = True,              # Enable caching
    cache_ttl_seconds: int = 3600,          # Cache TTL
    queue_enabled: bool = True,              # Enable queueing
    max_queue_size: int = 1000,             # Max queue size
    queue_ttl_seconds: int = 300,           # Queue TTL
    auto_retry_enabled: bool = True,         # Auto retry
    max_retry_attempts: int = 3,            # Max retries
    retry_delay_seconds: float = 60.0,      # Initial retry delay
    retry_backoff_multiplier: float = 2.0,  # Retry backoff
    log_fallbacks: bool = True              # Log fallback events
)
```

---

## Configuration

### Environment Variables

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
META_ACCESS_TOKEN=...

# Circuit Breaker Settings
CIRCUIT_BREAKER_ENABLED=true
CB_FAILURE_THRESHOLD=5
CB_TIMEOUT_SECONDS=60
CB_EXPONENTIAL_BACKOFF=true

# Health Monitoring
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_ENABLED=true

# Fallback Settings
FALLBACK_CACHE_ENABLED=true
FALLBACK_QUEUE_ENABLED=true
```

---

## Monitoring

### Metrics Endpoints

#### GET `/api/circuit-breaker/metrics`
Returns metrics for all circuit breakers.

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "circuit_breakers": [
    {
      "name": "openai_api",
      "state": "closed",
      "total_requests": 1250,
      "successful_requests": 1200,
      "failed_requests": 50,
      "rejected_requests": 0,
      "success_rate": 96.0,
      "latency_p50_ms": 245.3,
      "latency_p95_ms": 892.1,
      "latency_p99_ms": 1523.8
    }
  ]
}
```

#### GET `/api/circuit-breaker/health`
Returns health status for all services.

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "openai_api": {
      "status": "healthy",
      "uptime": 99.8,
      "error_rate": 0.02,
      "latency_p95_ms": 892.1,
      "last_check": 1705318200
    }
  }
}
```

#### GET `/api/circuit-breaker/status`
Returns overall system status.

```json
{
  "status": "healthy",
  "summary": {
    "total_services": 4,
    "healthy_services": 3,
    "degraded_services": 1,
    "unhealthy_services": 0,
    "open_circuits": 0,
    "half_open_circuits": 0
  }
}
```

### Dashboard Integration

The circuit breaker system exposes metrics in Prometheus format:

```
# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)
# TYPE circuit_breaker_state gauge
circuit_breaker_state{name="openai_api"} 0

# HELP circuit_breaker_requests_total Total requests
# TYPE circuit_breaker_requests_total counter
circuit_breaker_requests_total{name="openai_api",result="success"} 1200
circuit_breaker_requests_total{name="openai_api",result="failure"} 50

# HELP circuit_breaker_latency_seconds Request latency
# TYPE circuit_breaker_latency_seconds histogram
circuit_breaker_latency_seconds_bucket{name="openai_api",le="0.1"} 300
circuit_breaker_latency_seconds_bucket{name="openai_api",le="0.5"} 850
```

---

## Testing

### Run Tests

```bash
# Run all tests
cd /home/user/geminivideo/services/gateway-api/src/circuit_breaker
pytest test_circuit_breaker.py -v

# Run specific test
pytest test_circuit_breaker.py::test_circuit_breaker_opens_after_failures -v

# Run with coverage
pytest test_circuit_breaker.py --cov=. --cov-report=html
```

### Manual Testing

```python
# Test circuit breaker manually
import asyncio
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig

async def test():
    breaker = CircuitBreaker(
        "test",
        config=CircuitBreakerConfig(failure_threshold=3)
    )

    # Simulate failures
    async def failing():
        raise Exception("API error")

    for i in range(5):
        try:
            await breaker.call(failing)
        except Exception as e:
            print(f"Call {i+1}: {e}")
            print(f"Circuit state: {breaker.state.value}")

    # Check metrics
    print("\nMetrics:", breaker.get_metrics())

asyncio.run(test())
```

---

## Production Deployment

### 1. Enable Circuit Breakers

Update your main application file:

```typescript
// src/index.ts
import { registerCircuitBreakerRoutes } from './circuit_breaker/middleware';

// Register circuit breaker routes
registerCircuitBreakerRoutes(app);

// Protect API routes
import { withCircuitBreaker } from './circuit_breaker/middleware';

app.post('/api/generate-content', withCircuitBreaker(
  'openai_api',
  async (req, res) => {
    // Your handler
  }
));
```

### 2. Start Health Monitoring

Create a startup script:

```python
# startup.py
import asyncio
from circuit_breaker import global_monitor
from circuit_breaker.openai_breaker import setup_openai_health_check
from circuit_breaker.anthropic_breaker import setup_anthropic_health_check
from circuit_breaker.meta_breaker import setup_meta_health_check

async def main():
    # Initialize breakers (your actual clients)
    openai_breaker = ...
    anthropic_breaker = ...
    meta_breaker = ...

    # Setup health checks
    await setup_openai_health_check(openai_breaker, global_monitor)
    await setup_anthropic_health_check(anthropic_breaker, global_monitor)
    await setup_meta_health_check(meta_breaker, global_monitor)

    # Start monitoring
    await global_monitor.start()

    # Keep running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Configure Alerts

```python
from circuit_breaker import global_monitor

async def alert_to_slack(service: str, alert_type: str, details: dict):
    # Send to Slack, PagerDuty, etc.
    webhook_url = "https://hooks.slack.com/..."
    message = f"🚨 Alert for {service}: {alert_type}\n{details['message']}"
    # Post to webhook...

global_monitor.register_alert_handler(alert_to_slack)
```

### 4. Monitoring Dashboard

Access the monitoring endpoints:
- Metrics: `GET /api/circuit-breaker/metrics`
- Health: `GET /api/circuit-breaker/health`
- Status: `GET /api/circuit-breaker/status`

### 5. Operations

**Reset a circuit breaker:**
```bash
curl -X POST http://localhost:8000/api/circuit-breaker/reset/openai_api
```

**Reset all circuit breakers:**
```bash
curl -X POST http://localhost:8000/api/circuit-breaker/reset-all
```

---

## Best Practices

1. **Tune Thresholds**: Start conservative and adjust based on your SLAs
2. **Monitor Metrics**: Set up alerts for circuit state changes
3. **Test Failovers**: Regularly test your failover strategies
4. **Cache Aggressively**: Cache successful responses when appropriate
5. **Log Everything**: Log all circuit state changes and fallback usage
6. **Gradual Rollout**: Enable circuit breakers gradually in production
7. **Set Appropriate Timeouts**: Balance recovery speed vs. load

---

## Troubleshooting

### Circuit Breaker Won't Close

**Problem**: Circuit stays open even after service recovers.

**Solutions**:
- Check `timeout_seconds` - may be too long
- Verify health checks are passing
- Check if exponential backoff is too aggressive
- Reset manually if needed

### Too Many False Positives

**Problem**: Circuit opens unnecessarily.

**Solutions**:
- Increase `failure_threshold`
- Increase `min_throughput`
- Adjust `rolling_window_seconds`
- Check if health checks are too sensitive

### Fallback Not Working

**Problem**: Fallback function not being called.

**Solutions**:
- Verify fallback is registered
- Check circuit breaker is actually open
- Verify fallback function signature matches
- Check logs for fallback errors

---

## Contributing

This circuit breaker system was built by Agent 9. For issues or improvements:

1. Check existing circuit breaker metrics
2. Review logs for patterns
3. Test changes thoroughly
4. Update documentation

---

## License

Copyright 2024 GeminiVideo Platform. All rights reserved.
