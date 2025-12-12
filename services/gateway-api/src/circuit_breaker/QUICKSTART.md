# Circuit Breaker Quick Start Guide

**Get up and running with circuit breakers in 5 minutes!**

## Install Dependencies

```bash
pip install anthropic openai google-generativeai aiohttp pytest pytest-asyncio
```

## Basic Usage (Python)

### 1. Simple Circuit Breaker

```python
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig

# Create breaker
breaker = CircuitBreaker(
    name="my_api",
    config=CircuitBreakerConfig(
        failure_threshold=5,
        timeout_seconds=60
    )
)

# Use it!
@breaker.protected
async def call_api():
    return await some_api_call()

result = await call_api()
```

### 2. With Automatic Failover

```python
from circuit_breaker.openai_breaker import OpenAICircuitBreaker
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Initialize
openai_client = AsyncOpenAI(api_key="sk-...")
claude_client = AsyncAnthropic(api_key="sk-ant-...")

breaker = OpenAICircuitBreaker(
    openai_client=openai_client,
    claude_client=claude_client  # Fallback
)

# Call - automatically fails over to Claude if OpenAI is down
result = await breaker.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4o-mini"
)

print(result["content"])
if "_fallback" in result:
    print(f"Used fallback: {result['_fallback']}")
```

## Basic Usage (TypeScript/Express)

### 1. Register Routes

```typescript
import { registerCircuitBreakerRoutes } from './circuit_breaker/middleware';

const app = express();
registerCircuitBreakerRoutes(app);

// Access monitoring at:
// GET /api/circuit-breaker/metrics
// GET /api/circuit-breaker/health
```

### 2. Protect Routes

```typescript
import { withCircuitBreaker } from './circuit_breaker/middleware';

app.post('/api/generate', withCircuitBreaker(
  'openai_api',
  async (req, res) => {
    const result = await generateContent(req.body);
    res.json(result);
  }
));
```

## Check Status

### Via API

```bash
# Get metrics
curl http://localhost:8000/api/circuit-breaker/metrics

# Get health
curl http://localhost:8000/api/circuit-breaker/health

# Reset if stuck
curl -X POST http://localhost:8000/api/circuit-breaker/reset/openai_api
```

### Via Python

```python
from circuit_breaker import registry

# Get all metrics
metrics = registry.get_all_metrics()
for m in metrics:
    print(f"{m['name']}: {m['state']} - {m['success_rate']}%")
```

## Common Scenarios

### Scenario 1: OpenAI Rate Limited

**Without Circuit Breaker:**
```python
# Every request fails → cascading failures → user sees errors
result = await openai_client.chat.completions.create(...)  # 429 Error
```

**With Circuit Breaker:**
```python
# After 5 failures, circuit opens → automatically uses Claude
result = await openai_breaker.chat_completion(...)
# Returns response from Claude, user doesn't notice
```

### Scenario 2: Meta API Down

**Without Circuit Breaker:**
```python
# Ad publish fails → lost opportunity → manual retry needed
await publish_ad(...)  # Error
```

**With Circuit Breaker:**
```python
# Ad automatically queued for retry when service recovers
result = await meta_breaker.publish_ad(...)
if result["queued"]:
    print("Ad will be published when Meta recovers")
```

### Scenario 3: High Latency

**Without Circuit Breaker:**
```python
# Every request waits 10s → timeouts → bad UX
result = await slow_api_call()  # Takes 10s
```

**With Circuit Breaker:**
```python
# Health monitor detects high latency → alerts → you can investigate
# Meanwhile, requests are monitored and latency tracked
result = await breaker.call(slow_api_call)
print(f"P95 latency: {breaker.get_metrics()['latency_p95_ms']}ms")
```

## Configuration Presets

### Fast Recovery (Non-Critical Services)
```python
CircuitBreakerConfig(
    failure_threshold=3,
    timeout_seconds=30,
    success_threshold=1,
    exponential_backoff=False
)
```

### Balanced (Recommended)
```python
CircuitBreakerConfig(
    failure_threshold=5,
    timeout_seconds=60,
    success_threshold=2,
    exponential_backoff=True
)
```

### Stable (Critical Services)
```python
CircuitBreakerConfig(
    failure_threshold=10,
    timeout_seconds=120,
    success_threshold=5,
    exponential_backoff=True,
    max_timeout_seconds=600
)
```

## Testing Your Setup

### Test 1: Circuit Opens

```python
import asyncio
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig

async def test():
    breaker = CircuitBreaker(
        "test",
        CircuitBreakerConfig(failure_threshold=3, min_throughput=1)
    )

    async def failing():
        raise Exception("API down")

    # Trigger failures
    for i in range(5):
        try:
            await breaker.call(failing)
        except:
            print(f"Call {i+1}: {breaker.state.value}")

asyncio.run(test())
```

Expected output:
```
Call 1: closed
Call 2: closed
Call 3: closed
Call 4: open
Call 5: open
```

### Test 2: Health Check

```python
from circuit_breaker import global_monitor
from circuit_breaker.health_monitor import HealthCheckConfig

async def check_health():
    return True  # Service is healthy

global_monitor.register_service(
    "test_service",
    check_health,
    HealthCheckConfig(check_interval_seconds=10)
)

await global_monitor.start()

# Wait and check
await asyncio.sleep(15)
health = global_monitor.get_service_health("test_service")
print(f"Status: {health.status.value}")
```

## Troubleshooting

### Circuit Won't Close
**Problem**: Circuit stays open even after service recovers.

**Solution**:
```bash
# Check timeout setting
curl http://localhost:8000/api/circuit-breaker/metrics | jq '.circuit_breakers[] | select(.name=="openai_api")'

# Reset manually
curl -X POST http://localhost:8000/api/circuit-breaker/reset/openai_api
```

### High Rejection Rate
**Problem**: Too many requests being rejected.

**Solution**:
```python
# Increase failure threshold
config = CircuitBreakerConfig(
    failure_threshold=10,  # Was 5
    timeout_seconds=60
)
```

### Fallback Not Working
**Problem**: Fallback not being called when circuit opens.

**Check**:
```python
# Verify fallback is registered
breaker = CircuitBreaker("test", config, fallback=my_fallback)

# Or register separately
fallback_handler.register_fallback("service_name", my_fallback)
```

## Next Steps

1. ✅ Read full documentation: `README.md`
2. ✅ See integration examples: `INTEGRATION_EXAMPLE.md`
3. ✅ Run tests: `pytest test_circuit_breaker.py -v`
4. ✅ Set up monitoring dashboard
5. ✅ Configure alerts

## Need Help?

- **Full Docs**: See `README.md` for comprehensive guide
- **Integration**: See `INTEGRATION_EXAMPLE.md` for step-by-step integration
- **Tests**: Run `pytest test_circuit_breaker.py -v` to see examples

---

**Agent 9: Circuit Breaker Builder** ⚡
