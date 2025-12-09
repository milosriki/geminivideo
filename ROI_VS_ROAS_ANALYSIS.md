# ROI vs ROAS Analysis
## Which Metric Should Be The Northstar?

**Date:** 2025-12-09  
**Question:** Should we optimize for ROAS or ROI?

---

## 📊 KEY DIFFERENCES

### ROAS (Return on Ad Spend)
**Formula:** `ROAS = Revenue / Ad Spend`

**What it measures:**
- Revenue generated per dollar spent on ads
- **Does NOT account for:**
  - Production costs (video creation, editing)
  - Platform fees (Meta, Google take ~10-15%)
  - Overhead costs (team, infrastructure)
  - Cost of goods sold (COGS)
  - Other operational costs

**Example:**
- Ad Spend: $1,000
- Revenue: $3,000
- **ROAS = 3.0x** ✅ Looks great!

**But:**
- Production costs: $500
- Platform fees: $150 (5% of revenue)
- Overhead: $200
- **Actual Profit = $3,000 - $1,000 - $500 - $150 - $200 = $1,150**
- **ROI = ($1,150) / ($1,000 + $500 + $150 + $200) = 62%**

---

### ROI (Return on Investment)
**Formula:** `ROI = (Revenue - Total Costs) / Total Costs`

**What it measures:**
- Actual profit per dollar invested
- **Accounts for ALL costs:**
  - Ad spend
  - Production costs
  - Platform fees
  - Overhead
  - COGS
  - Infrastructure costs

**Example:**
- Total Investment: $1,850 (ad spend + production + fees + overhead)
- Revenue: $3,000
- Profit: $1,150
- **ROI = $1,150 / $1,850 = 62%** ✅ Shows true profitability

---

## 🎯 WHICH ONE MATTERS MORE?

### For Business Decisions: **ROI** ✅

**Why:**
1. **True Profitability:** ROI shows actual profit, not just revenue
2. **Cost Awareness:** Accounts for all costs, not just ad spend
3. **Scalability:** Know if you can actually scale profitably
4. **Investor Perspective:** Investors care about ROI, not ROAS

### For Ad Optimization: **ROAS** (But with ROI context)

**Why:**
1. **Faster Feedback:** ROAS available immediately, ROI takes time
2. **Ad-Level Optimization:** Can optimize individual ads by ROAS
3. **Platform Standard:** Meta, Google optimize for ROAS
4. **Quick Decisions:** Need fast budget allocation decisions

---

## 🔍 CURRENT SYSTEM ANALYSIS

### What We're Currently Tracking:

#### 1. ROAS Dashboard
**File:** `services/gateway-api/src/routes/roas-dashboard.ts`

**Tracks:**
- `predicted_roas` - Predicted ROAS
- `actual_roas` - Actual ROAS
- `revenue` - Revenue generated
- `spend` - Ad spend

**Missing:**
- ❌ Production costs
- ❌ Platform fees
- ❌ Overhead allocation
- ❌ True ROI calculation

#### 2. Battle-Hardened Sampler
**File:** `services/ml-service/src/battle_hardened_sampler.py`

**Optimizes for:**
- `pipeline_value` - Synthetic revenue from pipeline
- `cash_revenue` - Actual closed deals
- `spend` - Ad spend

**Blended Score:**
- CTR (early) → Pipeline ROAS (later)
- **Still ROAS-based, not ROI-based**

#### 3. Revenue Attribution
**File:** `services/gateway-api/src/webhooks/hubspot.ts`

**Tracks:**
- Synthetic revenue (pipeline value)
- Attribution to ad clicks
- **No cost tracking beyond ad spend**

---

## 💡 RECOMMENDATION: **ROI as Northstar**

### Why ROI Should Be The Northstar:

1. **Business Reality:**
   - Production costs matter (video creation, editing)
   - Platform fees matter (10-15% of revenue)
   - Overhead matters (team, infrastructure)
   - **ROAS ignores these costs**

2. **True Profitability:**
   - ROAS 3.0x might look great
   - But if production costs are high, ROI might be negative
   - **ROI shows actual profit**

3. **Scalability:**
   - Can't scale if ROI is negative
   - Need to know true profitability to scale
   - **ROI shows if scaling is profitable**

4. **Investor Perspective:**
   - Investors care about ROI, not ROAS
   - Need to show true profitability
   - **ROI is what matters to investors**

---

## 🔧 HOW TO IMPLEMENT ROI AS NORTHSTAR

### 1. Track All Costs

**Add Cost Tracking:**
```typescript
interface CampaignCosts {
  ad_spend: number;           // Already tracked
  production_cost: number;     // NEW: Video creation cost
  platform_fees: number;      // NEW: Meta/Google fees (10-15%)
  overhead_allocation: number; // NEW: Team/infrastructure cost
  cogs: number;               // NEW: Cost of goods sold
  total_cost: number;         // Sum of all above
}
```

### 2. Calculate ROI

**ROI Calculation:**
```typescript
function calculateROI(revenue: number, costs: CampaignCosts): number {
  const profit = revenue - costs.total_cost;
  const roi = (profit / costs.total_cost) * 100;
  return roi;
}
```

### 3. Optimize for ROI

**Update Battle-Hardened Sampler:**
```python
# Instead of: blended_score = ctr * roas * decay
# Use: blended_score = ctr * roi * decay

def calculate_roi_score(ad_state: AdState, costs: CampaignCosts) -> float:
    revenue = ad_state.pipeline_value + ad_state.cash_revenue
    total_cost = costs.ad_spend + costs.production_cost + costs.platform_fees
    profit = revenue - total_cost
    roi = profit / total_cost if total_cost > 0 else 0
    return roi
```

### 4. ROI Dashboard

**Add ROI Dashboard:**
```typescript
// GET /api/roi/dashboard
router.get('/dashboard', async (req: Request, res: Response) => {
  // Calculate ROI for all campaigns
  // Show ROI trends
  // Optimize for ROI, not ROAS
});
```

---

## 📊 ROI vs ROAS COMPARISON

### Scenario 1: High Production Costs

**Campaign A:**
- Ad Spend: $1,000
- Production Cost: $800 (high-quality video)
- Platform Fees: $150
- Revenue: $3,000
- **ROAS = 3.0x** ✅ Looks great!
- **ROI = ($3,000 - $1,950) / $1,950 = 54%** ⚠️ Decent

**Campaign B:**
- Ad Spend: $1,000
- Production Cost: $200 (template-based)
- Platform Fees: $150
- Revenue: $2,500
- **ROAS = 2.5x** ⚠️ Lower than A
- **ROI = ($2,500 - $1,350) / $1,350 = 85%** ✅ Better!

**Winner by ROAS:** Campaign A (3.0x > 2.5x)  
**Winner by ROI:** Campaign B (85% > 54%) ✅

---

### Scenario 2: Scaling Decision

**Current State:**
- Ad Spend: $10,000/day
- Production Cost: $2,000/day
- Platform Fees: $1,500/day
- Revenue: $30,000/day
- **ROAS = 3.0x** ✅
- **ROI = ($30,000 - $13,500) / $13,500 = 122%** ✅

**Scale to 10x:**
- Ad Spend: $100,000/day
- Production Cost: $20,000/day (scales linearly)
- Platform Fees: $15,000/day
- Revenue: $300,000/day (assumes same ROAS)
- **ROAS = 3.0x** ✅ Still looks great!
- **ROI = ($300,000 - $135,000) / $135,000 = 122%** ✅ Same ROI

**But what if production costs don't scale?**
- Production Cost: $50,000/day (fixed costs + variable)
- **ROI = ($300,000 - $165,000) / $165,000 = 82%** ⚠️ Lower ROI

**ROAS doesn't show this problem!**

---

## 🎯 RECOMMENDED APPROACH

### Hybrid: ROI as Northstar, ROAS as Leading Indicator

**Strategy:**
1. **Northstar Metric:** ROI (true profitability)
2. **Leading Indicator:** ROAS (fast feedback)
3. **Optimization:** Optimize for ROI, use ROAS for quick decisions

**Implementation:**
```python
# Quick decisions (budget allocation): Use ROAS
if roas > threshold:
    allocate_budget()

# Strategic decisions (campaign selection): Use ROI
if roi > target_roi:
    scale_campaign()
```

---

## 📈 ROI TARGETS

### Industry Benchmarks:

**Good ROI:**
- **100%+ ROI** = Double your money
- **200%+ ROI** = Triple your money
- **500%+ ROI** = 5x return (excellent)

**Your System Goals:**
- **Target ROI: 200%+** (3x return)
- **Minimum ROI: 100%** (2x return)
- **Excellent ROI: 500%+** (5x return)

### ROAS vs ROI Conversion:

**ROAS 2.0x:**
- If costs = 50% of ad spend → ROI = 100%
- If costs = 30% of ad spend → ROI = 133%
- If costs = 70% of ad spend → ROI = 43%

**ROAS 3.0x:**
- If costs = 50% of ad spend → ROI = 200%
- If costs = 30% of ad spend → ROI = 233%
- If costs = 70% of ad spend → ROI = 129%

**ROAS 5.0x:**
- If costs = 50% of ad spend → ROI = 400%
- If costs = 30% of ad spend → ROI = 433%
- If costs = 70% of ad spend → ROI = 329%

---

## ✅ FINAL RECOMMENDATION

### **ROI Should Be The Northstar** ✅

**Why:**
1. Shows true profitability
2. Accounts for all costs
3. Enables smart scaling decisions
4. What investors care about

**But:**
- Keep ROAS as leading indicator
- Use ROAS for quick decisions
- Use ROI for strategic decisions

**Implementation:**
1. Track all costs (production, fees, overhead)
2. Calculate ROI for all campaigns
3. Optimize Battle-Hardened Sampler for ROI
4. Add ROI dashboard
5. Set ROI targets (200%+)

---

## 🚀 NEXT STEPS

1. **Add Cost Tracking:**
   - Production costs per campaign
   - Platform fees calculation
   - Overhead allocation

2. **Calculate ROI:**
   - Add ROI calculation to ROAS dashboard
   - Show ROI alongside ROAS
   - Track ROI trends

3. **Optimize for ROI:**
   - Update Battle-Hardened Sampler
   - Use ROI in budget allocation
   - Set ROI targets

4. **ROI Dashboard:**
   - Create ROI dashboard
   - Show ROI by campaign
   - Track ROI improvements

---

**ROI = True Profitability. ROAS = Revenue Efficiency. Both matter, but ROI is the northstar!** 🎯

