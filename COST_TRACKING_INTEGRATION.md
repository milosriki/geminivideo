# Cost Tracking Integration Guide

This document describes the changes needed to integrate cost tracking into AI endpoints.

## Files Created

1. **`/home/user/geminivideo/services/gateway-api/src/services/cost-tracker.ts`** - Cost tracking service (✅ CREATED)
2. **Cost tracking endpoints in index.ts** (✅ ADDED):
   - `GET /api/costs/daily?days=30` - Daily cost breakdown
   - `GET /api/costs/by-model?days=30` - Per-model cost analysis
   - `GET /api/costs/total?days=30` - Total spend summary
   - `GET /api/costs/projection?days=30` - Cost forecasting
   - `GET /api/costs/pricing` - Model pricing information

## Integration Points for AI Endpoints

The following endpoints need cost tracking integrated:

### 1. `/api/analyze` (Line ~191)

**Current state:** Has `startTime` added ✅

**Still needs:** Add cost tracking before `res.json(analysis)`

Add this code after line ~233 (`console.log('Gemini analysis completed...')`):

```typescript
// Record cost (estimate tokens: ~4 chars per token)
const latency = Date.now() - startTime;
const promptText = `Analyze this video ad at ${video_uri}...`; // Use the actual prompt text
const estimatedInputTokens = Math.ceil(promptText.length / 4);
const estimatedOutputTokens = Math.ceil(analysisText.length / 4);
const totalTokens = estimatedInputTokens + estimatedOutputTokens;

await costTracker.recordCost(
  'gemini-2.0-flash-exp',
  totalTokens,
  latency,
  'analysis',
  {
    inputTokens: estimatedInputTokens,
    outputTokens: estimatedOutputTokens
  }
);
```

### 2. `/api/insights/ai` (Line ~1245)

**Needs:**
1. Add `const startTime = Date.now();` at the beginning of the function (after line 1245)
2. Add cost tracking before `res.json({...})` (before line 1284)

```typescript
// Record cost
const latency = Date.now() - startTime;
const responseText = result.response.text();
const estimatedTokens = Math.ceil((prompt.length + responseText.length) / 4);

await costTracker.recordCost(
  'gemini-2.0-flash-exp',
  estimatedTokens,
  latency,
  'insights'
);
```

### 3. `/api/generate` (Line ~330)

This endpoint proxies to Titan Core, which internally uses multiple models.
Cost tracking should be added in Titan Core service, not in the gateway.

## Manual Integration Instructions

Since the file is being modified by a linter, here's how to manually integrate:

1. **Open `/home/user/geminivideo/services/gateway-api/src/index.ts`**

2. **For `/api/analyze`:**
   - Find the line with `console.log(\`Gemini analysis completed for \${video_uri}\`);`
   - Extract the prompt text into a variable before the API call
   - Add the cost tracking code shown above before `res.json(analysis)`

3. **For `/api/insights/ai`:**
   - Add `const startTime = Date.now();` right after the `try {` on line ~1246
   - Save the response text: `const responseText = result.response.text();`
   - Add cost tracking before the `res.json({...})` call
   - Use `responseText` instead of calling `result.response.text()` again

## Testing the Integration

Once integrated, test with:

```bash
# Run an analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_uri": "gs://your-video.mp4"}'

# Check costs were recorded
curl http://localhost:8000/api/costs/total?days=1

# View daily breakdown
curl http://localhost:8000/api/costs/daily?days=7

# Check model-specific costs
curl http://localhost:8000/api/costs/by-model?days=30

# View projections
curl http://localhost:8000/api/costs/projection?days=30
```

## Database Schema

The system uses the `api_costs` table from migration `/home/user/geminivideo/database_migrations/002_feedback_and_knowledge.sql`:

```sql
CREATE TABLE IF NOT EXISTS api_costs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50),
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    cost_usd FLOAT,
    latency_ms FLOAT,
    cache_hit BOOLEAN DEFAULT FALSE,
    early_exit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Model Pricing (per 1K tokens)

- `gemini-2.0-flash`: $0.00075
- `gemini-3-pro`: $0.00125
- `gpt-4o-mini`: $0.00015
- `claude-3.5-sonnet`: $0.003
- `gpt-4o`: $0.005

## Summary

**Created:**
- ✅ `/home/user/geminivideo/services/gateway-api/src/services/cost-tracker.ts`
- ✅ Cost tracking endpoints in index.ts (lines 1220-1322)
- ✅ CostTracker initialization (line 118)

**Needs manual integration:**
- ⚠️ `/api/analyze` - Add cost recording (need to extract prompt to variable)
- ⚠️ `/api/insights/ai` - Add startTime and cost recording

The file keeps being modified by a linter/formatter, making automated edits difficult.
Follow the manual integration instructions above to complete the integration.
