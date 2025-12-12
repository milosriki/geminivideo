# Circuit Breaker Integration Example

This guide shows how to integrate the circuit breaker system into the existing GeminiVideo codebase.

## Integration with Smart Router

The `smart-router.ts` already calls OpenAI, Claude, and Gemini. Let's add circuit breaker protection.

### Before (smart-router.ts)

```typescript
private async callOpenAI(model: string, prompt: string): Promise<ModelResponse> {
  if (!this.openaiApiKey) {
    throw new Error('OPENAI_API_KEY not set');
  }

  const response = await axios.post(
    'https://api.openai.com/v1/chat/completions',
    {
      model: model,
      messages: [{ role: 'user', content: prompt }],
      response_format: { type: 'json_object' },
    },
    {
      headers: {
        Authorization: `Bearer ${this.openaiApiKey}`,
        'Content-Type': 'application/json',
      },
    }
  );

  const result = JSON.parse(response.data.choices[0].message.content);
  return {
    score: result.score,
    confidence: result.confidence,
    reasoning: result.reasoning,
  };
}
```

### After (with Circuit Breaker)

```typescript
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);

// Add circuit breaker wrapper
private async callWithCircuitBreaker(
  serviceName: string,
  apiCall: () => Promise<any>
): Promise<any> {
  try {
    // Check circuit breaker state
    const { stdout } = await execAsync(`
      python3 -c "
import sys
sys.path.insert(0, '/home/user/geminivideo/services/gateway-api/src/circuit_breaker')
from circuit_breaker import registry
breaker = registry.get('${serviceName}')
if breaker and breaker.is_open:
    print('OPEN')
else:
    print('CLOSED')
"
    `);

    if (stdout.trim() === 'OPEN') {
      console.warn(`Circuit breaker ${serviceName} is OPEN, using fallback`);
      throw new Error('Circuit breaker is open');
    }

    // Execute the API call
    return await apiCall();

  } catch (error: any) {
    console.error(`API call to ${serviceName} failed:`, error.message);
    throw error;
  }
}

// Updated callOpenAI with circuit breaker
private async callOpenAI(model: string, prompt: string): Promise<ModelResponse> {
  return this.callWithCircuitBreaker('openai_api', async () => {
    if (!this.openaiApiKey) {
      throw new Error('OPENAI_API_KEY not set');
    }

    const response = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: model,
        messages: [{ role: 'user', content: prompt }],
        response_format: { type: 'json_object' },
      },
      {
        headers: {
          Authorization: `Bearer ${this.openaiApiKey}`,
          'Content-Type': 'application/json',
        },
      }
    );

    const result = JSON.parse(response.data.choices[0].message.content);
    return {
      score: result.score,
      confidence: result.confidence,
      reasoning: result.reasoning,
    };
  });
}
```

## Integration with Express Routes

### Add Circuit Breaker Middleware to index.ts

```typescript
// src/index.ts
import {
  registerCircuitBreakerRoutes,
  circuitBreakerHeaders
} from './circuit_breaker/middleware';

// ... existing imports ...

// After security middleware, add circuit breaker
app.use(circuitBreakerHeaders);

// Register circuit breaker monitoring routes
registerCircuitBreakerRoutes(app);

// ... rest of your app setup ...
```

### Protect Prediction Endpoint

```typescript
// src/routes/predictions.ts
import { withCircuitBreaker } from '../circuit_breaker/middleware';

// Before
app.post('/api/predict', async (req, res) => {
  const result = await scoringEngine.scoreContent(req.body);
  res.json(result);
});

// After
app.post('/api/predict', withCircuitBreaker(
  'prediction_service',
  async (req, res) => {
    const result = await scoringEngine.scoreContent(req.body);
    res.json(result);
  }
));
```

### Protect Image Generation Endpoint

```typescript
// src/routes/image-generation.ts
import { withCircuitBreaker } from '../circuit_breaker/middleware';

app.post('/api/generate-image', withCircuitBreaker(
  'openai_api',
  async (req, res) => {
    const { prompt, size = '1024x1024' } = req.body;

    // Your existing image generation logic
    const response = await openai.images.generate({
      prompt,
      n: 1,
      size
    });

    res.json({
      image_url: response.data[0].url,
      revised_prompt: response.data[0].revised_prompt
    });
  }
));
```

## Python Service Integration

### Create Initialized Circuit Breakers

```python
# src/circuit_breaker/init_breakers.py
"""
Initialize all circuit breakers for the platform
"""
import os
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai

from openai_breaker import OpenAICircuitBreaker, setup_openai_health_check
from anthropic_breaker import AnthropicCircuitBreaker, setup_anthropic_health_check
from meta_breaker import MetaCircuitBreaker, setup_meta_health_check
from health_monitor import global_monitor
from fallback_handler import global_fallback_handler

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
anthropic_client = AsyncAnthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
gemini_client = genai

# Initialize breakers
openai_breaker = OpenAICircuitBreaker(
    openai_client=openai_client,
    claude_client=anthropic_client,
    gemini_client=gemini_client
)

anthropic_breaker = AnthropicCircuitBreaker(
    anthropic_client=anthropic_client,
    openai_client=openai_client,
    gemini_client=gemini_client
)

meta_breaker = MetaCircuitBreaker(
    meta_access_token=os.environ.get('META_ACCESS_TOKEN')
)

async def initialize_circuit_breakers():
    """Initialize all circuit breakers and health monitoring"""

    # Setup health checks
    await setup_openai_health_check(openai_breaker, global_monitor)
    await setup_anthropic_health_check(anthropic_breaker, global_monitor)
    await setup_meta_health_check(meta_breaker, global_monitor)

    # Start health monitoring
    await global_monitor.start()

    # Start fallback handler retry processor
    await global_fallback_handler.start_retry_processor()

    print("✅ Circuit breakers initialized and health monitoring started")

# Export for use in other modules
__all__ = [
    'openai_breaker',
    'anthropic_breaker',
    'meta_breaker',
    'initialize_circuit_breakers'
]
```

### Use in Python Services

```python
# Example: Using in intelligent-orchestrator.py or any Python service
from circuit_breaker.init_breakers import openai_breaker, anthropic_breaker

async def generate_content_with_protection(prompt: str):
    """Generate content with circuit breaker protection"""

    try:
        # Try OpenAI first (with automatic failover to Claude/Gemini)
        result = await openai_breaker.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o-mini"
        )

        return {
            "content": result["content"],
            "model": result["model"],
            "cost": result["cost_usd"],
            "fallback_used": result.get("_fallback", None)
        }

    except Exception as e:
        print(f"All AI providers failed: {e}")
        # Return degraded response
        return {
            "content": "Service temporarily unavailable",
            "error": str(e),
            "degraded": True
        }
```

## Startup Script

Create a startup script to initialize everything:

```python
# src/startup_circuit_breakers.py
"""
Startup script for circuit breaker system
Run this before starting your main application
"""
import asyncio
import sys
import os

# Add circuit breaker to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'circuit_breaker'))

from init_breakers import initialize_circuit_breakers

async def main():
    print("🚀 Starting circuit breaker system...")

    try:
        await initialize_circuit_breakers()

        print("✅ Circuit breaker system ready")
        print("📊 Monitoring endpoints available at:")
        print("   - GET /api/circuit-breaker/metrics")
        print("   - GET /api/circuit-breaker/health")
        print("   - GET /api/circuit-breaker/status")

        # Keep running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\n👋 Shutting down circuit breaker system...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Docker Integration

Update your `docker-compose.yml`:

```yaml
services:
  gateway-api:
    build: ./services/gateway-api
    ports:
      - "8000:8000"
    environment:
      # API Keys
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - META_ACCESS_TOKEN=${META_ACCESS_TOKEN}

      # Circuit Breaker Settings
      - CIRCUIT_BREAKER_ENABLED=true
      - CB_FAILURE_THRESHOLD=5
      - CB_TIMEOUT_SECONDS=60
      - HEALTH_CHECK_INTERVAL=30

    # Start circuit breaker system
    command: sh -c "
      python3 src/startup_circuit_breakers.py &
      npm start
    "
```

## Testing the Integration

### 1. Test Circuit Breaker Endpoints

```bash
# Get metrics
curl http://localhost:8000/api/circuit-breaker/metrics

# Get health status
curl http://localhost:8000/api/circuit-breaker/health

# Get overall status
curl http://localhost:8000/api/circuit-breaker/status
```

### 2. Test Failover

```python
# test_failover.py
import asyncio
from circuit_breaker.init_breakers import openai_breaker

async def test():
    # Simulate OpenAI being down by setting wrong API key
    openai_breaker.openai_client.api_key = "invalid"

    # This should automatically failover to Claude or Gemini
    result = await openai_breaker.chat_completion(
        messages=[{"role": "user", "content": "test"}],
        model="gpt-4o-mini"
    )

    print(f"Content: {result['content']}")
    print(f"Fallback used: {result.get('_fallback')}")

asyncio.run(test())
```

### 3. Simulate Circuit Opening

```python
# test_circuit_open.py
import asyncio
from circuit_breaker import CircuitBreaker, CircuitBreakerConfig

async def test():
    breaker = CircuitBreaker(
        "test",
        config=CircuitBreakerConfig(failure_threshold=3, min_throughput=1)
    )

    async def failing_call():
        raise Exception("Service down")

    # Trigger failures
    for i in range(5):
        try:
            await breaker.call(failing_call)
        except Exception as e:
            print(f"Call {i+1}: State={breaker.state.value}, Error={e}")

    print(f"\nFinal state: {breaker.state.value}")
    print(f"Metrics: {breaker.get_metrics()}")

asyncio.run(test())
```

## Monitoring in Production

### Grafana Dashboard

Create a Grafana dashboard to visualize:

1. **Circuit Breaker States**
   - Gauge showing open/closed/half-open
   - Alert when any circuit opens

2. **Request Success Rate**
   - Line graph of success rate over time
   - Alert when below 95%

3. **Latency Percentiles**
   - P50, P95, P99 latencies
   - Alert when P95 > 2000ms

4. **Fallback Usage**
   - Count of fallback invocations
   - Which services are being used as fallbacks

### Alert Configuration

```yaml
# alerts.yml
groups:
  - name: circuit_breaker
    interval: 30s
    rules:
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker {{ $labels.name }} is open"

      - alert: HighErrorRate
        expr: circuit_breaker_error_rate > 0.2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate for {{ $labels.name }} exceeds 20%"

      - alert: HighLatency
        expr: circuit_breaker_latency_p95 > 3000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency for {{ $labels.name }} exceeds 3s"
```

## Rollout Strategy

1. **Phase 1: Monitoring Only** (Week 1)
   - Deploy circuit breakers in "monitoring mode"
   - Don't actually block requests
   - Collect metrics and tune thresholds

2. **Phase 2: Non-Critical Services** (Week 2)
   - Enable for non-critical services first
   - Monitor impact
   - Adjust configuration

3. **Phase 3: Critical Services** (Week 3)
   - Enable for OpenAI, Claude, Meta
   - 24/7 monitoring
   - Quick rollback plan ready

4. **Phase 4: Full Production** (Week 4+)
   - All services protected
   - Automated alerting
   - Regular threshold reviews

## Troubleshooting

### Circuit Breaker Not Working

```bash
# Check if circuit breaker is initialized
python3 -c "
import sys
sys.path.insert(0, 'src/circuit_breaker')
from circuit_breaker import registry
print('Registered breakers:', list(registry.get_all().keys()))
"

# Check metrics
curl http://localhost:8000/api/circuit-breaker/metrics | jq
```

### Reset Stuck Circuit

```bash
# Reset specific circuit
curl -X POST http://localhost:8000/api/circuit-breaker/reset/openai_api

# Reset all circuits
curl -X POST http://localhost:8000/api/circuit-breaker/reset-all
```

## Next Steps

1. ✅ Complete circuit breaker integration
2. ✅ Test failover scenarios
3. ✅ Setup monitoring dashboard
4. ✅ Configure alerts
5. ✅ Document runbooks
6. ✅ Train team on troubleshooting

---

**Need help?** Check the main README.md or review the test files for more examples.
