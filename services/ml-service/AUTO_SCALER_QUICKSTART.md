# Auto-Scaler Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Initialize Database (One-time)

```bash
cd /home/user/geminivideo/services/ml-service

# Create database tables
python3 -c "from src.auto_scaler import create_tables; create_tables()"
```

### Step 2: Set Environment Variables

```bash
export META_ACCESS_TOKEN="your_meta_access_token"
export META_AD_ACCOUNT_ID="act_123456789"
export DATABASE_URL="postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
```

### Step 3: Create Your First Scaling Rule

```bash
curl -X POST http://localhost:8003/api/auto-scaler/rules \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "act_123456789",
    "rule_name": "Default Auto-Scaling",
    "enabled": true,
    "roas_scale_up_aggressive": 4.0,
    "roas_scale_up": 3.0,
    "roas_scale_down": 1.5,
    "roas_pause": 1.0,
    "ctr_threshold": 0.03,
    "min_impressions": 1000,
    "multiplier_aggressive_up": 1.5,
    "multiplier_up": 1.2,
    "multiplier_down": 0.7,
    "max_daily_budget": 1000.00,
    "min_daily_budget": 10.00,
    "require_approval_threshold": 500.00,
    "auto_approve_up_to": 100.00
  }'
```

### Step 4: Test with a Single Campaign

```bash
curl -X POST http://localhost:8003/api/auto-scaler/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "YOUR_CAMPAIGN_ID",
    "account_id": "act_123456789"
  }'
```

Response:
```json
{
  "success": true,
  "campaign_id": "123456789",
  "action_type": "scale_up",
  "budget_before": 100.00,
  "budget_after": 120.00,
  "budget_change_pct": 20.0,
  "multiplier": 1.2,
  "reasoning": "Strong performance: ROAS 3.45x (>3.0x)",
  "requires_approval": false,
  "executed": true,
  "metrics": {
    "roas": 3.45,
    "ctr": 0.025,
    "spend": 85.50,
    "revenue": 295.00,
    "impressions": 12500,
    "clicks": 312,
    "conversions": 15
  }
}
```

### Step 5: View Dashboard

```bash
curl http://localhost:8003/api/auto-scaler/dashboard?days=7
```

### Step 6: Set Up Automated Hourly Runs

```bash
# Make script executable
chmod +x /home/user/geminivideo/services/ml-service/cron_auto_scaler.sh

# Test manual run
./cron_auto_scaler.sh

# Add to crontab (runs every hour)
crontab -e

# Add this line:
0 * * * * /home/user/geminivideo/services/ml-service/cron_auto_scaler.sh
```

## 📊 Common Operations

### View Pending Approvals

```bash
curl http://localhost:8003/api/auto-scaler/actions/pending?limit=20
```

### Approve an Action

```bash
curl -X POST http://localhost:8003/api/auto-scaler/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": 42,
    "approved_by": "john@example.com",
    "approved": true
  }'
```

### Reject an Action

```bash
curl -X POST http://localhost:8003/api/auto-scaler/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": 43,
    "approved_by": "john@example.com",
    "approved": false,
    "rejection_reason": "Budget too aggressive for this campaign"
  }'
```

### View Action History

```bash
curl "http://localhost:8003/api/auto-scaler/actions/history?campaign_id=123&days=30&limit=100"
```

### Learn Optimal Hours for Campaign

```bash
curl -X POST "http://localhost:8003/api/auto-scaler/time-optimization/learn?campaign_id=123&min_samples=24"
```

### Get Time-Based Performance Report

```bash
curl http://localhost:8003/api/auto-scaler/time-optimization/report/123456789
```

Response:
```json
{
  "campaign_id": "123456789",
  "peak_hours": [9, 10, 11, 16, 17, 18, 19],
  "valley_hours": [1, 2, 3, 4, 5],
  "confidence_score": 0.85,
  "hourly_breakdown": [
    {
      "hour": 0,
      "hour_label": "00:00",
      "status": "normal",
      "avg_roas": 2.1,
      "avg_ctr": 0.018,
      "samples": 45
    },
    ...
  ]
}
```

### Get Recommended Budget Schedule

```bash
curl "http://localhost:8003/api/auto-scaler/time-optimization/schedule/123?base_daily_budget=240&peak_multiplier=1.3"
```

Response:
```json
{
  "campaign_id": "123",
  "base_daily_budget": 240,
  "peak_multiplier": 1.3,
  "schedule": [
    {"hour": 0, "hour_label": "00:00", "budget": 8.5, "multiplier": 1.0, "status": "normal"},
    {"hour": 1, "hour_label": "01:00", "budget": 6.5, "multiplier": 0.77, "status": "valley"},
    ...
    {"hour": 9, "hour_label": "09:00", "budget": 11.0, "multiplier": 1.3, "status": "peak"},
    ...
  ]
}
```

## 🎯 Understanding Scaling Actions

### Scale Up Aggressive (50% increase)
**Trigger:** ROAS > 4x AND CTR > 3%
```
Before: $200/day → After: $300/day
Reasoning: "Exceptional performance: ROAS 4.50x (>4.0x) and CTR 3.20% (>3%)"
```

### Scale Up (20% increase)
**Trigger:** ROAS > 3x
```
Before: $200/day → After: $240/day
Reasoning: "Strong performance: ROAS 3.25x (>3.0x)"
```

### Scale Down (30% decrease)
**Trigger:** ROAS < 1.5x
```
Before: $200/day → After: $140/day
Reasoning: "Underperforming: ROAS 1.30x (<1.5x)"
```

### Pause
**Trigger:** ROAS < 1x
```
Before: $200/day → After: $0 (PAUSED)
Reasoning: "Critical underperformance: ROAS 0.80x (<1.0x) - pausing to stop losses"
```

### Maintain
**Trigger:** Everything else
```
Before: $200/day → After: $200/day
Reasoning: "Performance within normal range: ROAS 2.10x"
```

## 🔒 Safety Features

### 1. Budget Limits
```json
{
  "max_daily_budget": 1000.00,  // Never exceed $1000/day
  "min_daily_budget": 10.00      // Never below $10/day
}
```

### 2. Approval Thresholds
```json
{
  "require_approval_threshold": 500.00,  // Budgets > $500 need approval
  "auto_approve_up_to": 100.00           // Auto-approve increases up to $100
}
```

### 3. Minimum Data Requirements
```json
{
  "min_impressions": 1000  // Need 1000+ impressions before making decisions
}
```

### 4. Complete Audit Trail
Every action is logged with:
- ✅ Before/after budgets
- ✅ Performance metrics
- ✅ Reasoning
- ✅ Approval status
- ✅ Execution timestamp
- ✅ Who approved/rejected

## 📈 Monitoring

### Check Cron Logs
```bash
tail -f /var/log/geminivideo/auto_scaler.log
```

### Dashboard API
```bash
curl http://localhost:8003/api/auto-scaler/dashboard?days=7
```

Returns:
- Total actions
- Execution rate
- Action breakdown
- Budget impact
- Performance metrics
- Recent actions

## 🎓 Best Practices

### Week 1: Conservative Start
```json
{
  "roas_scale_up": 3.5,
  "multiplier_up": 1.1,
  "require_approval_threshold": 200.00
}
```

### Week 2: Increase Automation
```json
{
  "roas_scale_up": 3.0,
  "multiplier_up": 1.2,
  "require_approval_threshold": 500.00
}
```

### Week 3+: Full Automation
```json
{
  "roas_scale_up": 3.0,
  "multiplier_up": 1.2,
  "require_approval_threshold": 1000.00
}
```

## 🚨 Troubleshooting

### "Meta API not initialized"
```bash
export META_ACCESS_TOKEN="your_token"
export META_AD_ACCOUNT_ID="act_123456789"
```

### "No enabled scaling rules found"
```bash
# Create a rule first
curl -X POST http://localhost:8003/api/auto-scaler/rules ...
```

### "Insufficient data"
Wait for campaign to accumulate at least 1000 impressions.

### "Action requires approval"
```bash
# View pending
curl http://localhost:8003/api/auto-scaler/actions/pending

# Approve
curl -X POST http://localhost:8003/api/auto-scaler/approve -d '{"action_id": 42, "approved_by": "me", "approved": true}'
```

## 🎯 Success Checklist

- [x] Database tables created
- [x] Meta API credentials configured
- [x] At least one scaling rule created
- [x] Test evaluation successful
- [x] Cron job scheduled
- [x] Dashboard accessible
- [x] Monitoring logs

**You're ready! The auto-scaler will now run hourly and automatically optimize your campaigns.**

---

**Need help?** Check the full documentation: `AGENT47_AUTO_SCALER_COMPLETE.md`
