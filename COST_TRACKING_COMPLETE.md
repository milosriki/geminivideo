# Cost Tracking System - Implementation Complete

## Summary

A comprehensive cost tracking and reporting system has been successfully implemented for the Gateway API. The system monitors AI API costs, provides detailed analytics, and projects future spending.

---

## Files Created

### 1. Cost Tracker Service
**File:** `/home/user/geminivideo/services/gateway-api/src/services/cost-tracker.ts`

**Features:**
- `recordCost()` - Log API calls to database with cost calculation
- `getDailyCosts()` - Query daily cost breakdown from view
- `getModelCosts()` - Per-model cost analysis
- `getTotalSpend()` - Aggregate spend summary
- `getCostProjection()` - Forecast future costs based on trends
- `getModelPricing()` - Get pricing information
- `estimateCost()` - Estimate cost for token count

**Model Pricing (per 1K tokens):**
- gemini-2.0-flash: $0.00075
- gemini-3-pro: $0.00125
- gpt-4o-mini: $0.00015
- claude-3.5-sonnet: $0.003
- gpt-4o: $0.005

---

## API Endpoints Added

All endpoints are in `/home/user/geminivideo/services/gateway-api/src/index.ts` (lines 1607-1709)

### GET /api/costs/daily?days=30
Get daily cost breakdown for the last N days.

**Response:**
```json
{
  "days": 30,
  "total_entries": 45,
  "daily_costs": [
    {
      "date": "2025-12-03",
      "model_name": "gemini-2.0-flash-exp",
      "calls": 125,
      "total_cost": 0.234,
      "avg_latency": 1250.5,
      "cache_hit_rate": 0.15
    }
  ]
}
```

### GET /api/costs/by-model?days=30&model=gemini-2.0-flash
Get costs by model with optional filtering.

**Response:**
```json
{
  "days": 30,
  "model": "gemini-2.0-flash-exp",
  "total_models": 3,
  "model_costs": [
    {
      "model_name": "gemini-2.0-flash-exp",
      "calls": 453,
      "total_cost": 2.45,
      "avg_cost_per_call": 0.0054,
      "total_tokens": 123456,
      "avg_latency": 1234.5
    }
  ]
}
```

### GET /api/costs/total?days=30
Get total spend summary across all models.

**Response:**
```json
{
  "days": 30,
  "total_cost": 15.67,
  "total_calls": 1234,
  "total_tokens": 567890,
  "avg_cost_per_call": 0.0127,
  "models_used": 4,
  "date_range": {
    "start": "2025-11-03T00:00:00Z",
    "end": "2025-12-03T23:59:59Z"
  }
}
```

### GET /api/costs/projection?days=30
Get cost projection and trend analysis.

**Response:**
```json
{
  "based_on_days": 30,
  "current_daily_average": 0.52,
  "projected_weekly": 3.64,
  "projected_monthly": 15.60,
  "projected_annual": 189.80,
  "trend": "increasing",
  "trend_percentage": 12.5,
  "generated_at": "2025-12-03T10:30:00Z"
}
```

### GET /api/costs/pricing
Get model pricing information.

**Response:**
```json
{
  "pricing_per_1k_tokens": {
    "gemini-2.0-flash": 0.00075,
    "gemini-3-pro": 0.00125,
    "gpt-4o-mini": 0.00015,
    "claude-3.5-sonnet": 0.003,
    "gpt-4o": 0.005
  },
  "note": "Prices shown are approximate blended rates for input/output tokens"
}
```

---

## Cost Recording Integration

Cost tracking has been integrated into the following AI endpoints:

### 1. POST /api/analyze (Line 191-263)
**Status:** ✅ INTEGRATED (Line 244)

Tracks:
- Model: gemini-2.0-flash-exp
- Operation: analysis
- Tokens: Estimated from prompt + response
- Latency: Measured from start to completion

### 2. GET /api/insights/ai (Line 1264-1328)
**Status:** ✅ INTEGRATED (Line 1308)

Tracks:
- Model: gemini-2.0-flash-exp
- Operation: insights
- Tokens: Estimated from prompt + response
- Latency: Measured from start to completion

### 3. POST /api/generate (Line ~330)
**Status:** ⚠️ PROXIED TO TITAN CORE

This endpoint proxies to Titan Core service, which internally uses multiple models.
Cost tracking should be added directly in Titan Core service.

---

## Database Schema

Uses `api_costs` table from migration `/home/user/geminivideo/database_migrations/002_feedback_and_knowledge.sql`:

```sql
CREATE TABLE IF NOT EXISTS api_costs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50),  -- evaluation, generation, embedding

    input_tokens INT,
    output_tokens INT,
    total_tokens INT,

    cost_usd FLOAT,
    latency_ms FLOAT,

    cache_hit BOOLEAN DEFAULT FALSE,
    early_exit BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_costs_model ON api_costs(model_name);
CREATE INDEX idx_costs_created ON api_costs(created_at DESC);

-- Aggregated view for reporting
CREATE OR REPLACE VIEW daily_costs AS
SELECT
    DATE(created_at) as date,
    model_name,
    COUNT(*) as calls,
    SUM(cost_usd) as total_cost,
    AVG(latency_ms) as avg_latency,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as cache_hit_rate
FROM api_costs
GROUP BY DATE(created_at), model_name
ORDER BY date DESC, total_cost DESC;
```

---

## Testing

### 1. Test Cost Recording

```bash
# Trigger an analysis (will record cost)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_uri": "gs://your-video.mp4"}'

# Get AI insights (will record cost)
curl http://localhost:8000/api/insights/ai
```

### 2. Check Costs Were Recorded

```bash
# View today's costs
curl http://localhost:8000/api/costs/total?days=1

# View daily breakdown for last week
curl http://localhost:8000/api/costs/daily?days=7

# View per-model costs
curl http://localhost:8000/api/costs/by-model?days=30

# View specific model costs
curl "http://localhost:8000/api/costs/by-model?days=30&model=gemini-2.0-flash-exp"
```

### 3. Check Projections

```bash
# Get cost projection
curl http://localhost:8000/api/costs/projection?days=30

# Get pricing info
curl http://localhost:8000/api/costs/pricing
```

### 4. Query Database Directly

```bash
# View recent cost records
psql $DATABASE_URL -c "SELECT * FROM api_costs ORDER BY created_at DESC LIMIT 10;"

# View daily summary
psql $DATABASE_URL -c "SELECT * FROM daily_costs LIMIT 10;"

# View total spend
psql $DATABASE_URL -c "SELECT SUM(cost_usd) as total_cost, COUNT(*) as total_calls FROM api_costs WHERE created_at >= NOW() - INTERVAL '7 days';"
```

---

## Dashboard Integration

The cost tracking data can be visualized in a dashboard using the following endpoints:

1. **Cost Overview Widget**: Use `/api/costs/total?days=30`
2. **Daily Trend Chart**: Use `/api/costs/daily?days=30`
3. **Model Breakdown Pie Chart**: Use `/api/costs/by-model?days=30`
4. **Cost Projection Card**: Use `/api/costs/projection?days=30`

### Example Dashboard Data Flow

```javascript
// Fetch all cost data for dashboard
const [totalSpend, dailyCosts, modelCosts, projection] = await Promise.all([
  fetch('/api/costs/total?days=30').then(r => r.json()),
  fetch('/api/costs/daily?days=30').then(r => r.json()),
  fetch('/api/costs/by-model?days=30').then(r => r.json()),
  fetch('/api/costs/projection?days=30').then(r => r.json())
]);

// Display metrics
console.log(`Total Spend (30 days): $${totalSpend.total_cost.toFixed(2)}`);
console.log(`Projected Monthly: $${projection.projected_monthly.toFixed(2)}`);
console.log(`Trend: ${projection.trend} (${projection.trend_percentage}%)`);
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gateway API                             │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │ /api/analyze │────▶│ CostTracker  │────▶│ PostgreSQL   │  │
│  └──────────────┘     │              │     │              │  │
│                       │ recordCost() │     │  api_costs   │  │
│  ┌──────────────┐     │              │     │  table       │  │
│  │/api/insights │────▶│ getDailyCosts│◀────│              │  │
│  │    /ai       │     │              │     │  daily_costs │  │
│  └──────────────┘     │ getModelCosts│     │  view        │  │
│                       │              │     └──────────────┘  │
│  ┌──────────────┐     │getTotalSpend │                       │
│  │ /api/costs/* │────▶│              │                       │
│  └──────────────┘     │getProjection │                       │
│                       └──────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Paths Summary

### Created Files
- `/home/user/geminivideo/services/gateway-api/src/services/cost-tracker.ts` - Cost tracking service
- `/home/user/geminivideo/COST_TRACKING_COMPLETE.md` - This documentation
- `/home/user/geminivideo/COST_TRACKING_INTEGRATION.md` - Integration guide

### Modified Files
- `/home/user/geminivideo/services/gateway-api/src/index.ts`:
  - Line 52: Added CostTracker import
  - Line 118: Initialized CostTracker service
  - Line 244: Added cost recording to /api/analyze
  - Line 1308: Added cost recording to /api/insights/ai
  - Lines 1607-1709: Added cost tracking endpoints

### Database Migration (Already Exists)
- `/home/user/geminivideo/database_migrations/002_feedback_and_knowledge.sql`
  - Lines 144-176: api_costs table and daily_costs view

---

## Monitoring & Alerts

### Set Up Cost Alerts

```sql
-- Create alert trigger for high daily spend
CREATE OR REPLACE FUNCTION check_daily_spend()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT SUM(cost_usd) FROM api_costs WHERE DATE(created_at) = CURRENT_DATE) > 5.00 THEN
    RAISE WARNING 'Daily spend exceeded $5.00';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER daily_spend_alert
AFTER INSERT ON api_costs
FOR EACH ROW
EXECUTE FUNCTION check_daily_spend();
```

### Cost Optimization Tips

1. **Enable Caching**: Set `cache_hit=true` for repeated queries
2. **Use Early Exit**: Set `early_exit=true` when sufficient confidence reached
3. **Monitor Trends**: Check projections weekly to avoid surprises
4. **Optimize Prompts**: Shorter prompts = fewer input tokens = lower costs
5. **Model Selection**: Use gemini-2.0-flash for low-cost operations

---

## Next Steps

1. **Add to Frontend Dashboard**:
   - Create cost visualization widgets
   - Add cost alerts/notifications
   - Show real-time spend tracking

2. **Extend to Other Services**:
   - Add cost tracking to Titan Core
   - Add cost tracking to ML Service
   - Track Meta Ads API costs

3. **Advanced Features**:
   - Budget limits and throttling
   - Per-user cost tracking
   - Cost optimization recommendations
   - Automated cost reports via email

---

## Support

For issues or questions:
1. Check logs: `docker logs gateway-api`
2. Query database: `psql $DATABASE_URL -c "SELECT * FROM api_costs LIMIT 10;"`
3. Test endpoints: Use curl examples above
4. Review code: `/home/user/geminivideo/services/gateway-api/src/services/cost-tracker.ts`

---

**Status: ✅ COMPLETE**
- Cost Tracker Service: ✅ Created
- API Endpoints: ✅ Added (5 endpoints)
- Integration: ✅ Added to 2 AI endpoints
- Database: ✅ Using existing schema
- Documentation: ✅ Complete
