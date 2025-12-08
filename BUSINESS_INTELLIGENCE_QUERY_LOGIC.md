# 🧠 BUSINESS INTELLIGENCE QUERY LOGIC
## How The System Answers: "Top 5 ROAS Campaigns Last Quarter"

**Question:** "What were our top 5 performing ad campaigns last quarter in terms of ROAS, and what was the primary audience segment for each?"

---

## 🔍 STEP 1: UNDERSTAND THE QUERY

**Query Breakdown:**
1. **Time Range:** Last quarter (3 months)
2. **Metric:** ROAS (Return on Ad Spend)
3. **Ranking:** Top 5 campaigns
4. **Additional Data:** Primary audience segment per campaign

**ROAS Calculation:**
```
ROAS = Total Revenue / Total Ad Spend
```

---

## 📊 STEP 2: DATA SOURCES AVAILABLE

### Data Source 1: Meta Insights API
**Location:** `services/meta-publisher/src/insights.ts`
**Data:**
- Campaign performance metrics
- Ad spend
- Conversions
- Revenue (for e-commerce)
- Audience demographics

### Data Source 2: HubSpot Attribution
**Location:** `services/ml-service/src/hubspot_attribution.py`
**Data:**
- Pipeline value (for service businesses)
- Deal stage changes
- Attribution to ad clicks

### Data Source 3: Synthetic Revenue
**Location:** `services/ml-service/src/synthetic_revenue.py`
**Data:**
- Calculated pipeline value per stage
- Service business revenue signals

### Data Source 4: Database Tables
**Tables:**
- `campaigns` - Campaign metadata
- `adsets` - Ad set targeting (audience segments)
- `ads` - Ad creative data
- `ad_change_history` - Performance history
- `attribution_tracking` - Click-to-conversion attribution

---

## 🔄 STEP 3: QUERY EXECUTION FLOW

### Phase 1: Fetch Campaign Performance Data

```python
# File: services/gateway-api/src/routes/analytics.ts

@app.get("/api/analytics/top-campaigns")
async def get_top_campaigns_roas(
    date_preset: str = "last_quarter",
    top_n: int = 5,
    tenant_id: str = None
):
    """
    Get top N campaigns by ROAS for a given time period.
    """
    # STEP 1: Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)  # Last quarter
    
    # STEP 2: Fetch from Meta Insights API
    meta_insights = await fetch_meta_insights(
        account_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        level="campaign"
    )
    
    # STEP 3: Fetch HubSpot pipeline data (for service businesses)
    hubspot_data = await fetch_hubspot_pipeline_value(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # STEP 4: Calculate ROAS for each campaign
    campaigns_with_roas = []
    
    for campaign in meta_insights:
        # Get direct revenue (e-commerce)
        direct_revenue = campaign.get('revenue', 0)
        
        # Get pipeline value (service business)
        pipeline_value = hubspot_data.get(campaign['id'], {}).get('pipeline_value', 0)
        
        # Total revenue = direct + pipeline
        total_revenue = direct_revenue + pipeline_value
        
        # Calculate ROAS
        total_spend = campaign.get('spend', 0)
        roas = total_revenue / max(total_spend, 1)
        
        campaigns_with_roas.append({
            'campaign_id': campaign['id'],
            'campaign_name': campaign['name'],
            'spend': total_spend,
            'revenue': total_revenue,
            'direct_revenue': direct_revenue,
            'pipeline_value': pipeline_value,
            'roas': roas,
            'impressions': campaign.get('impressions', 0),
            'clicks': campaign.get('clicks', 0),
            'conversions': campaign.get('conversions', 0)
        })
    
    # STEP 5: Sort by ROAS and get top N
    top_campaigns = sorted(
        campaigns_with_roas,
        key=lambda x: x['roas'],
        reverse=True
    )[:top_n]
    
    return {
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'top_campaigns': top_campaigns
    }
```

### Phase 2: Fetch Audience Segment Data

```python
# File: services/gateway-api/src/routes/analytics.ts

@app.get("/api/analytics/campaign-audience")
async def get_campaign_audience_segments(
    campaign_ids: List[str],
    tenant_id: str
):
    """
    Get primary audience segment for each campaign.
    """
    # STEP 1: Fetch ad set targeting data from Meta
    meta_ad_sets = await fetch_meta_ad_sets(
        campaign_ids=campaign_ids,
        account_id=tenant_id
    )
    
    # STEP 2: Extract audience segments
    campaign_audiences = {}
    
    for campaign_id in campaign_ids:
        ad_sets = meta_ad_sets.get(campaign_id, [])
        
        # Find primary audience (largest budget allocation)
        primary_adset = max(
            ad_sets,
            key=lambda x: x.get('daily_budget', 0)
        ) if ad_sets else None
        
        if primary_adset:
            # Extract audience targeting
            targeting = primary_adset.get('targeting', {})
            
            # Determine primary segment
            audience_segment = determine_primary_segment(targeting)
            
            campaign_audiences[campaign_id] = {
                'primary_segment': audience_segment,
                'targeting_details': targeting,
                'adset_name': primary_adset.get('name'),
                'budget': primary_adset.get('daily_budget', 0)
            }
    
    return campaign_audiences

def determine_primary_segment(targeting: dict) -> str:
    """
    Determine primary audience segment from targeting data.
    """
    # Check custom audiences
    if targeting.get('custom_audiences'):
        return f"Custom: {targeting['custom_audiences'][0].get('name', 'Unknown')}"
    
    # Check lookalike audiences
    if targeting.get('lookalike_audiences'):
        return f"Lookalike: {targeting['lookalike_audiences'][0].get('name', 'Unknown')}"
    
    # Check demographics
    age_min = targeting.get('age_min', 18)
    age_max = targeting.get('age_max', 65)
    genders = targeting.get('genders', ['all'])
    
    # Check interests
    interests = targeting.get('interests', [])
    if interests:
        return f"Interest: {interests[0].get('name', 'Unknown')}"
    
    # Check behaviors
    behaviors = targeting.get('behaviors', [])
    if behaviors:
        return f"Behavior: {behaviors[0].get('name', 'Unknown')}"
    
    # Default: Broad targeting
    return f"Broad: {age_min}-{age_max}, {', '.join(genders)}"
```

### Phase 3: Combine Data and Format Response

```python
# File: services/gateway-api/src/routes/analytics.ts

@app.get("/api/analytics/top-campaigns-with-audience")
async def get_top_campaigns_with_audience(
    date_preset: str = "last_quarter",
    top_n: int = 5,
    tenant_id: str = None
):
    """
    Complete query: Top campaigns by ROAS + primary audience segment.
    """
    # STEP 1: Get top campaigns by ROAS
    top_campaigns_response = await get_top_campaigns_roas(
        date_preset=date_preset,
        top_n=top_n,
        tenant_id=tenant_id
    )
    
    top_campaigns = top_campaigns_response['top_campaigns']
    campaign_ids = [c['campaign_id'] for c in top_campaigns]
    
    # STEP 2: Get audience segments
    audience_data = await get_campaign_audience_segments(
        campaign_ids=campaign_ids,
        tenant_id=tenant_id
    )
    
    # STEP 3: Combine data
    result = []
    for campaign in top_campaigns:
        campaign_id = campaign['campaign_id']
        audience_info = audience_data.get(campaign_id, {})
        
        result.append({
            'rank': len(result) + 1,
            'campaign_id': campaign_id,
            'campaign_name': campaign['campaign_name'],
            'roas': round(campaign['roas'], 2),
            'revenue': round(campaign['revenue'], 2),
            'spend': round(campaign['spend'], 2),
            'direct_revenue': round(campaign['direct_revenue'], 2),
            'pipeline_value': round(campaign['pipeline_value'], 2),
            'primary_audience_segment': audience_info.get('primary_segment', 'Unknown'),
            'targeting_details': audience_info.get('targeting_details', {}),
            'impressions': campaign['impressions'],
            'clicks': campaign['clicks'],
            'conversions': campaign['conversions']
        })
    
    return {
        'query': {
            'date_preset': date_preset,
            'top_n': top_n,
            'tenant_id': tenant_id
        },
        'date_range': top_campaigns_response['date_range'],
        'results': result,
        'summary': {
            'total_campaigns_analyzed': len(top_campaigns),
            'average_roas': round(
                sum(c['roas'] for c in top_campaigns) / len(top_campaigns),
                2
            ) if top_campaigns else 0,
            'total_revenue': round(
                sum(c['revenue'] for c in top_campaigns),
                2
            ),
            'total_spend': round(
                sum(c['spend'] for c in top_campaigns),
                2
            )
        }
    }
```

---

## 🎯 STEP 4: EXAMPLE RESPONSE

```json
{
  "query": {
    "date_preset": "last_quarter",
    "top_n": 5,
    "tenant_id": "tenant_123"
  },
  "date_range": {
    "start": "2024-09-01T00:00:00Z",
    "end": "2024-11-30T23:59:59Z"
  },
  "results": [
    {
      "rank": 1,
      "campaign_id": "campaign_001",
      "campaign_name": "Fitness Transformation Q3",
      "roas": 4.75,
      "revenue": 47500.00,
      "spend": 10000.00,
      "direct_revenue": 25000.00,
      "pipeline_value": 22500.00,
      "primary_audience_segment": "Interest: Fitness & Wellness, Age 25-45",
      "targeting_details": {
        "age_min": 25,
        "age_max": 45,
        "genders": ["all"],
        "interests": [
          {"id": "6003107902433", "name": "Fitness and wellness"}
        ]
      },
      "impressions": 1250000,
      "clicks": 12500,
      "conversions": 250
    },
    {
      "rank": 2,
      "campaign_id": "campaign_002",
      "campaign_name": "Service Business Leads Q3",
      "roas": 4.20,
      "revenue": 42000.00,
      "spend": 10000.00,
      "direct_revenue": 0.00,
      "pipeline_value": 42000.00,
      "primary_audience_segment": "Lookalike: High-Value Customers 1%",
      "targeting_details": {
        "lookalike_audiences": [
          {"id": "123456", "name": "High-Value Customers 1%"}
        ]
      },
      "impressions": 980000,
      "clicks": 9800,
      "conversions": 140
    },
    {
      "rank": 3,
      "campaign_id": "campaign_003",
      "campaign_name": "E-commerce Holiday Q3",
      "roas": 3.85,
      "revenue": 38500.00,
      "spend": 10000.00,
      "direct_revenue": 38500.00,
      "pipeline_value": 0.00,
      "primary_audience_segment": "Custom: Previous Purchasers",
      "targeting_details": {
        "custom_audiences": [
          {"id": "789012", "name": "Previous Purchasers"}
        ]
      },
      "impressions": 1500000,
      "clicks": 15000,
      "conversions": 385
    },
    {
      "rank": 4,
      "campaign_id": "campaign_004",
      "campaign_name": "Brand Awareness Q3",
      "roas": 3.50,
      "revenue": 35000.00,
      "spend": 10000.00,
      "direct_revenue": 20000.00,
      "pipeline_value": 15000.00,
      "primary_audience_segment": "Behavior: Frequent Online Shoppers",
      "targeting_details": {
        "behaviors": [
          {"id": "6003107902433", "name": "Frequent online shoppers"}
        ]
      },
      "impressions": 2000000,
      "clicks": 20000,
      "conversions": 200
    },
    {
      "rank": 5,
      "campaign_id": "campaign_005",
      "campaign_name": "Retargeting Q3",
      "roas": 3.25,
      "revenue": 32500.00,
      "spend": 10000.00,
      "direct_revenue": 32500.00,
      "pipeline_value": 0.00,
      "primary_audience_segment": "Custom: Website Visitors (Last 30 Days)",
      "targeting_details": {
        "custom_audiences": [
          {"id": "345678", "name": "Website Visitors (Last 30 Days)"}
        ]
      },
      "impressions": 800000,
      "clicks": 8000,
      "conversions": 325
    }
  ],
  "summary": {
    "total_campaigns_analyzed": 5,
    "average_roas": 3.91,
    "total_revenue": 195500.00,
    "total_spend": 50000.00
  }
}
```

---

## 🔧 STEP 5: IMPLEMENTATION DETAILS

### Endpoint to Create

```typescript
// File: services/gateway-api/src/routes/analytics.ts

import { Router, Request, Response } from 'express';
import axios from 'axios';

const router = Router();

const META_API_URL = process.env.META_API_URL;
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://ml-service:8003';

/**
 * GET /api/analytics/top-campaigns-with-audience
 * 
 * Query Parameters:
 * - date_preset: "last_quarter" | "last_month" | "last_7d" | custom date range
 * - top_n: number (default: 5)
 * - tenant_id: string (required)
 */
router.get('/top-campaigns-with-audience', async (req: Request, res: Response) => {
  try {
    const { date_preset = 'last_quarter', top_n = 5, tenant_id } = req.query;
    
    if (!tenant_id) {
      return res.status(400).json({ error: 'tenant_id is required' });
    }
    
    // Call internal endpoint
    const response = await axios.get(
      `${ML_SERVICE_URL}/api/analytics/top-campaigns-with-audience`,
      {
        params: { date_preset, top_n, tenant_id }
      }
    );
    
    res.json(response.data);
    
  } catch (error: any) {
    console.error('Error fetching top campaigns:', error);
    res.status(500).json({ error: error.message });
  }
});
```

### Database Query (Alternative Approach)

```sql
-- File: database/queries/top_campaigns_roas.sql

WITH campaign_performance AS (
  SELECT
    c.id AS campaign_id,
    c.name AS campaign_name,
    SUM(ach.spend) AS total_spend,
    SUM(ach.revenue) AS direct_revenue,
    SUM(COALESCE(sr.calculated_value, 0)) AS pipeline_value,
    SUM(ach.impressions) AS total_impressions,
    SUM(ach.clicks) AS total_clicks,
    SUM(ach.conversions) AS total_conversions
  FROM campaigns c
  LEFT JOIN ad_change_history ach ON c.id = ach.campaign_id
  LEFT JOIN attribution_tracking at ON ach.ad_id = at.ad_id
  LEFT JOIN synthetic_revenue_config src ON at.tenant_id = src.tenant_id
  LEFT JOIN hubspot_deals hd ON at.contact_email = hd.contact_email
  LEFT JOIN synthetic_revenue_calculations sr ON hd.deal_id = sr.deal_id
  WHERE ach.created_at >= NOW() - INTERVAL '3 months'
    AND c.tenant_id = $1
  GROUP BY c.id, c.name
),
campaign_roas AS (
  SELECT
    campaign_id,
    campaign_name,
    total_spend,
    direct_revenue,
    pipeline_value,
    (direct_revenue + pipeline_value) AS total_revenue,
    CASE
      WHEN total_spend > 0 THEN (direct_revenue + pipeline_value) / total_spend
      ELSE 0
    END AS roas,
    total_impressions,
    total_clicks,
    total_conversions
  FROM campaign_performance
)
SELECT
  cr.*,
  a.targeting AS primary_audience_segment
FROM campaign_roas cr
LEFT JOIN (
  SELECT DISTINCT ON (campaign_id)
    campaign_id,
    targeting
  FROM adsets
  WHERE tenant_id = $1
  ORDER BY campaign_id, daily_budget DESC
) a ON cr.campaign_id = a.campaign_id
ORDER BY roas DESC
LIMIT $2;
```

---

## 🎨 STEP 6: FRONTEND INTEGRATION

```typescript
// File: frontend/src/components/TopCampaignsReport.tsx

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

interface TopCampaign {
  rank: number;
  campaign_id: string;
  campaign_name: string;
  roas: number;
  revenue: number;
  spend: number;
  primary_audience_segment: string;
}

export const TopCampaignsReport: React.FC = () => {
  const [campaigns, setCampaigns] = useState<TopCampaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [datePreset, setDatePreset] = useState('last_quarter');

  useEffect(() => {
    loadTopCampaigns();
  }, [datePreset]);

  const loadTopCampaigns = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/analytics/top-campaigns-with-audience', {
        params: {
          date_preset: datePreset,
          top_n: 5,
          tenant_id: getTenantId()
        }
      });
      setCampaigns(response.data.results);
    } catch (error) {
      console.error('Failed to load top campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">
        Top 5 Campaigns by ROAS - Last Quarter
      </h2>
      
      <div className="mb-4">
        <select
          value={datePreset}
          onChange={(e) => setDatePreset(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="last_quarter">Last Quarter</option>
          <option value="last_month">Last Month</option>
          <option value="last_7d">Last 7 Days</option>
        </select>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2">Rank</th>
              <th className="border p-2">Campaign</th>
              <th className="border p-2">ROAS</th>
              <th className="border p-2">Revenue</th>
              <th className="border p-2">Spend</th>
              <th className="border p-2">Primary Audience</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((campaign) => (
              <tr key={campaign.campaign_id}>
                <td className="border p-2">{campaign.rank}</td>
                <td className="border p-2">{campaign.campaign_name}</td>
                <td className="border p-2 font-bold">
                  {campaign.roas.toFixed(2)}x
                </td>
                <td className="border p-2">
                  ${campaign.revenue.toLocaleString()}
                </td>
                <td className="border p-2">
                  ${campaign.spend.toLocaleString()}
                </td>
                <td className="border p-2 text-sm">
                  {campaign.primary_audience_segment}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
```

---

## 📋 SUMMARY: HOW THE SYSTEM ANSWERS

**Step 1:** Parse query → Extract: time range, metric (ROAS), top N, additional data (audience)

**Step 2:** Fetch data from multiple sources:
- Meta Insights API (spend, impressions, clicks)
- HubSpot Attribution (pipeline value for service businesses)
- Database (campaign metadata, audience targeting)

**Step 3:** Calculate ROAS:
```
ROAS = (Direct Revenue + Pipeline Value) / Total Spend
```

**Step 4:** Rank campaigns by ROAS (descending)

**Step 5:** Fetch primary audience segment for each campaign:
- Find ad set with largest budget
- Extract targeting data
- Determine primary segment (custom, lookalike, interest, behavior, or broad)

**Step 6:** Combine and format response

**Step 7:** Return structured JSON with:
- Rank, campaign name, ROAS, revenue, spend
- Primary audience segment
- Additional metrics (impressions, clicks, conversions)

---

## ✅ CURRENT STATUS

**What Exists:**
- ✅ Meta Insights API integration (partial)
- ✅ HubSpot Attribution system
- ✅ Synthetic Revenue calculator
- ✅ Database schema (campaigns, adsets, ads)

**What Needs to Be Built:**
- ⚠️ `/api/analytics/top-campaigns-with-audience` endpoint
- ⚠️ Audience segment extraction logic
- ⚠️ Frontend component for display

**Estimated Time:** 4-6 hours to implement complete solution

---

**This demonstrates how the system would logically answer business intelligence questions by combining multiple data sources and calculating derived metrics.**

