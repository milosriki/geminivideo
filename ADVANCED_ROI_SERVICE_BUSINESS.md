# Advanced ROI for Service Business
## Accounting for Service Delivery Costs

**Date:** 2025-12-09  
**Problem:** Service businesses have delivery costs (coaches, office, etc.) that must be included in ROI

---

## 🎯 THE REAL PROBLEM

### Service Business Economics:

**Example:**
- Customer pays: $3,000 (revenue)
- Ad spend: $1,000 (customer acquisition)
- Coach cost: $1,000 (service delivery)
- Office/overhead: $1,000 (operational costs)
- **Total costs: $3,000**
- **ROI = ($3,000 - $3,000) / $3,000 = 0%** ❌ Zero ROI!

**But ROAS would show:**
- ROAS = $3,000 / $1,000 = 3.0x ✅ Looks great!
- **This is misleading!**

---

## 📊 ADVANCED ROI CALCULATION

### Service Business Cost Structure:

```
Total Revenue = Customer Payment
Total Costs = 
  + Ad Spend (customer acquisition)
  + Service Delivery Cost (coaches, materials)
  + Operational Overhead (office, admin, support)
  + Platform Fees (10-15% of revenue)
  + Production Costs (video creation)
  + Other Variable Costs
```

### ROI Formula for Service Business:

```
ROI = (Revenue - Total Costs) / Total Costs × 100%

Where:
  Revenue = Customer payment
  Total Costs = Ad Spend + Service Delivery + Overhead + Fees + Production
```

---

## 🔧 IMPLEMENTATION

### 1. Cost Tracking Structure

```typescript
interface ServiceBusinessCosts {
  // Customer Acquisition
  ad_spend: number;              // Ad spend to acquire customer
  production_cost: number;        // Video creation cost
  
  // Service Delivery
  coach_cost: number;             // Cost to deliver service (per customer)
  materials_cost: number;         // Materials/tools needed
  service_delivery_cost: number;  // Total service delivery cost
  
  // Operational Overhead
  office_cost: number;            // Office rent, utilities (allocated)
  admin_cost: number;             // Admin, support staff (allocated)
  overhead_allocation: number;     // Total overhead allocation
  
  // Platform & Fees
  platform_fees: number;          // Meta/Google fees (10-15% of revenue)
  payment_processing: number;    // Stripe/PayPal fees (2-3%)
  
  // Total
  total_cost: number;             // Sum of all above
}

interface CustomerEconomics {
  customer_id: string;
  revenue: number;                // What customer pays
  costs: ServiceBusinessCosts;
  profit: number;                 // Revenue - Total Costs
  roi: number;                    // (Profit / Total Costs) × 100%
  roas: number;                   // Revenue / Ad Spend (for comparison)
}
```

---

### 2. ROI Calculation Function

```typescript
function calculateServiceBusinessROI(
  revenue: number,
  costs: ServiceBusinessCosts
): {
  profit: number;
  roi: number;
  roas: number;
  cost_breakdown: {
    acquisition_pct: number;
    delivery_pct: number;
    overhead_pct: number;
    fees_pct: number;
  };
} {
  const totalCost = costs.total_cost;
  const profit = revenue - totalCost;
  const roi = totalCost > 0 ? (profit / totalCost) * 100 : 0;
  const roas = costs.ad_spend > 0 ? revenue / costs.ad_spend : 0;
  
  return {
    profit,
    roi,
    roas,
    cost_breakdown: {
      acquisition_pct: (costs.ad_spend / totalCost) * 100,
      delivery_pct: (costs.service_delivery_cost / totalCost) * 100,
      overhead_pct: (costs.overhead_allocation / totalCost) * 100,
      fees_pct: ((costs.platform_fees + costs.payment_processing) / totalCost) * 100,
    }
  };
}
```

---

### 3. Database Schema Updates

```sql
-- Add cost tracking to campaigns table
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS service_delivery_cost DECIMAL(10,2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS overhead_allocation DECIMAL(10,2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS platform_fees DECIMAL(10,2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS production_cost DECIMAL(10,2) DEFAULT 0;

-- Add cost tracking to conversions/customers
CREATE TABLE IF NOT EXISTS customer_economics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id VARCHAR(255) NOT NULL,
  campaign_id UUID REFERENCES campaigns(id),
  revenue DECIMAL(10,2) NOT NULL,
  ad_spend DECIMAL(10,2) NOT NULL,
  service_delivery_cost DECIMAL(10,2) NOT NULL,
  overhead_allocation DECIMAL(10,2) NOT NULL,
  platform_fees DECIMAL(10,2) NOT NULL,
  production_cost DECIMAL(10,2) NOT NULL,
  total_cost DECIMAL(10,2) NOT NULL,
  profit DECIMAL(10,2) NOT NULL,
  roi DECIMAL(5,2) NOT NULL,
  roas DECIMAL(5,2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_customer_economics_campaign ON customer_economics(campaign_id);
CREATE INDEX idx_customer_economics_roi ON customer_economics(roi DESC);
```

---

### 4. Advanced ROI Dashboard

```typescript
// GET /api/roi/dashboard - Advanced ROI dashboard for service business
router.get('/dashboard', async (req: Request, res: Response) => {
  try {
    const { range = '7d' } = req.query;
    
    // Get all customer economics
    const query = `
      SELECT 
        ce.*,
        c.name as campaign_name,
        c.status as campaign_status
      FROM customer_economics ce
      LEFT JOIN campaigns c ON ce.campaign_id = c.id
      WHERE ce.created_at >= NOW() - INTERVAL '${range} days'
      ORDER BY ce.roi DESC
    `;
    
    const result = await pgPool.query(query);
    
    // Calculate aggregate metrics
    const totalRevenue = result.rows.reduce((sum, r) => sum + parseFloat(r.revenue), 0);
    const totalCosts = result.rows.reduce((sum, r) => sum + parseFloat(r.total_cost), 0);
    const totalProfit = totalRevenue - totalCosts;
    const overallROI = totalCosts > 0 ? (totalProfit / totalCosts) * 100 : 0;
    
    // Cost breakdown
    const totalAdSpend = result.rows.reduce((sum, r) => sum + parseFloat(r.ad_spend), 0);
    const totalServiceDelivery = result.rows.reduce((sum, r) => sum + parseFloat(r.service_delivery_cost), 0);
    const totalOverhead = result.rows.reduce((sum, r) => sum + parseFloat(r.overhead_allocation), 0);
    const totalFees = result.rows.reduce((sum, r) => sum + parseFloat(r.platform_fees), 0);
    
    const costBreakdown = {
      ad_spend: {
        amount: totalAdSpend,
        percentage: (totalAdSpend / totalCosts) * 100
      },
      service_delivery: {
        amount: totalServiceDelivery,
        percentage: (totalServiceDelivery / totalCosts) * 100
      },
      overhead: {
        amount: totalOverhead,
        percentage: (totalOverhead / totalCosts) * 100
      },
      fees: {
        amount: totalFees,
        percentage: (totalFees / totalCosts) * 100
      }
    };
    
    // Campaign-level ROI
    const campaignROI = result.rows.reduce((acc, row) => {
      const campaignId = row.campaign_id || 'unknown';
      if (!acc[campaignId]) {
        acc[campaignId] = {
          campaign_id: campaignId,
          campaign_name: row.campaign_name,
          revenue: 0,
          total_cost: 0,
          profit: 0,
          customers: 0
        };
      }
      acc[campaignId].revenue += parseFloat(row.revenue);
      acc[campaignId].total_cost += parseFloat(row.total_cost);
      acc[campaignId].profit += parseFloat(row.profit);
      acc[campaignId].customers += 1;
      return acc;
    }, {});
    
    Object.keys(campaignROI).forEach(campaignId => {
      const campaign = campaignROI[campaignId];
      campaign.roi = campaign.total_cost > 0 
        ? (campaign.profit / campaign.total_cost) * 100 
        : 0;
      campaign.roas = campaign.total_cost > 0 
        ? campaign.revenue / (campaign.total_cost * 0.33) // Assuming 33% is ad spend
        : 0;
    });
    
    res.json({
      metrics: {
        total_revenue: totalRevenue,
        total_costs: totalCosts,
        total_profit: totalProfit,
        overall_roi: overallROI,
        customer_count: result.rows.length,
        avg_revenue_per_customer: totalRevenue / result.rows.length,
        avg_cost_per_customer: totalCosts / result.rows.length,
        avg_profit_per_customer: totalProfit / result.rows.length
      },
      cost_breakdown: costBreakdown,
      campaigns: Object.values(campaignROI),
      customers: result.rows.map(row => ({
        customer_id: row.customer_id,
        revenue: parseFloat(row.revenue),
        total_cost: parseFloat(row.total_cost),
        profit: parseFloat(row.profit),
        roi: parseFloat(row.roi),
        roas: parseFloat(row.roas),
        campaign_name: row.campaign_name
      })),
      timestamp: new Date().toISOString()
    });
    
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});
```

---

### 5. Update Battle-Hardened Sampler for ROI

```python
def calculate_roi_score(
    ad_state: AdState,
    service_delivery_cost: float,
    overhead_allocation: float,
    platform_fees: float,
    production_cost: float
) -> float:
    """
    Calculate ROI for service business accounting for all costs.
    
    Args:
        ad_state: Ad performance state
        service_delivery_cost: Cost to deliver service per customer
        overhead_allocation: Overhead cost allocation per customer
        platform_fees: Platform fees (10-15% of revenue)
        production_cost: Video production cost
    
    Returns:
        ROI percentage
    """
    revenue = ad_state.pipeline_value + ad_state.cash_revenue
    
    # Calculate total costs
    ad_spend = ad_state.spend
    total_cost = (
        ad_spend +
        service_delivery_cost +
        overhead_allocation +
        platform_fees +
        production_cost
    )
    
    if total_cost <= 0:
        return 0.0
    
    profit = revenue - total_cost
    roi = (profit / total_cost) * 100
    
    return roi

# Update blended score to use ROI
def calculate_blended_score(
    ad_state: AdState,
    age_hours: float,
    costs: ServiceBusinessCosts
) -> float:
    """
    Calculate blended score using ROI instead of ROAS.
    """
    # Calculate ROI
    roi = calculate_roi_score(
        ad_state,
        costs.service_delivery_cost,
        costs.overhead_allocation,
        costs.platform_fees,
        costs.production_cost
    )
    
    # Normalize ROI to 0-1 scale (assuming max ROI of 500%)
    roi_normalized = min(roi / 500.0, 1.0)
    
    # Calculate CTR
    ctr = ad_state.clicks / max(ad_state.impressions, 1)
    
    # Calculate decay
    decay = math.exp(-costs.decay_constant * age_hours)
    
    # Blended score: CTR (early) → ROI (later)
    if age_hours < 6:
        # Hours 0-6: Trust CTR 100%
        return ctr * decay
    elif age_hours < 24:
        # Hours 6-24: Trust CTR 70%, ROI 30%
        return (ctr * 0.7 + roi_normalized * 0.3) * decay
    elif age_hours < 72:
        # Hours 24-72: Trust CTR 30%, ROI 70%
        return (ctr * 0.3 + roi_normalized * 0.7) * decay
    else:
        # Days 3+: Trust ROI 100%
        return roi_normalized * decay
```

---

## 📊 EXAMPLE CALCULATIONS

### Scenario 1: Zero ROI (Your Example)

**Input:**
- Customer pays: $3,000
- Ad spend: $1,000
- Coach cost: $1,000
- Office/overhead: $1,000
- Platform fees: $450 (15% of $3,000)
- Production cost: $0 (assumed)

**Calculation:**
- Total costs: $1,000 + $1,000 + $1,000 + $450 = $3,450
- Profit: $3,000 - $3,450 = -$450 ❌
- **ROI = (-$450 / $3,450) × 100 = -13%** ❌ Negative ROI!

**ROAS would show:**
- ROAS = $3,000 / $1,000 = 3.0x ✅ (misleading!)

---

### Scenario 2: Profitable Service Business

**Input:**
- Customer pays: $5,000
- Ad spend: $1,000
- Coach cost: $1,500
- Office/overhead: $500
- Platform fees: $750 (15% of $5,000)
- Production cost: $250

**Calculation:**
- Total costs: $1,000 + $1,500 + $500 + $750 + $250 = $4,000
- Profit: $5,000 - $4,000 = $1,000 ✅
- **ROI = ($1,000 / $4,000) × 100 = 25%** ✅ Positive ROI!

**ROAS:**
- ROAS = $5,000 / $1,000 = 5.0x ✅

---

### Scenario 3: High-Margin Service

**Input:**
- Customer pays: $10,000
- Ad spend: $2,000
- Coach cost: $2,000
- Office/overhead: $1,000
- Platform fees: $1,500 (15% of $10,000)
- Production cost: $500

**Calculation:**
- Total costs: $2,000 + $2,000 + $1,000 + $1,500 + $500 = $7,000
- Profit: $10,000 - $7,000 = $3,000 ✅
- **ROI = ($3,000 / $7,000) × 100 = 43%** ✅ Excellent ROI!

**ROAS:**
- ROAS = $10,000 / $2,000 = 5.0x ✅

---

## 🎯 ROI TARGETS FOR SERVICE BUSINESS

### Minimum Viable ROI:
- **100% ROI** = Double your money (2x return)
- **200% ROI** = Triple your money (3x return)
- **500% ROI** = 5x return (excellent)

### Cost Structure Targets:
- **Ad spend:** 20-30% of revenue
- **Service delivery:** 30-40% of revenue
- **Overhead:** 10-15% of revenue
- **Fees:** 10-15% of revenue
- **Production:** 5-10% of revenue
- **Total costs:** 75-110% of revenue
- **Target profit margin:** 10-25%

---

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Add cost tracking fields to database
- [ ] Create customer_economics table
- [ ] Update ROI calculation to include all costs
- [ ] Create advanced ROI dashboard endpoint
- [ ] Update Battle-Hardened Sampler to use ROI
- [ ] Add cost breakdown visualization
- [ ] Track service delivery costs per customer
- [ ] Allocate overhead costs per customer
- [ ] Calculate platform fees automatically
- [ ] Show ROI vs ROAS comparison

---

## 🚀 NEXT STEPS

1. **Add Cost Tracking:**
   - Service delivery cost per customer
   - Overhead allocation per customer
   - Platform fees calculation
   - Production cost tracking

2. **Update ROI Calculation:**
   - Include all costs in ROI formula
   - Show cost breakdown
   - Track ROI per customer
   - Track ROI per campaign

3. **Optimize for ROI:**
   - Update Battle-Hardened Sampler
   - Use ROI for budget allocation
   - Set ROI targets (200%+)

4. **ROI Dashboard:**
   - Create advanced ROI dashboard
   - Show cost breakdown
   - Compare ROI vs ROAS
   - Track ROI trends

---

**Advanced ROI = True Profitability for Service Business!** 🎯

