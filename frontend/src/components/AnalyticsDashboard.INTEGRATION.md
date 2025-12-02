# Analytics Dashboard Integration Guide

## Quick Start

### 1. Install Dependencies

The Analytics Dashboard requires the following dependencies (already in package.json):

```bash
npm install react@^18.2.0 react-dom@^18.2.0
npm install recharts@^2.10.3
npm install @tanstack/react-query@^5.17.0
npm install axios@^1.6.2
```

### 2. Basic Integration

```typescript
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AnalyticsDashboard campaignIds={['campaign_1', 'campaign_2']} />
    </QueryClientProvider>
  );
}
```

### 3. Environment Setup

Create a `.env` file:

```bash
VITE_API_URL=http://localhost:8080/api
```

---

## Backend Integration Requirements

### Required API Endpoints

The Analytics Dashboard expects these endpoints to be available:

#### 1. Campaign Metrics
```
GET /api/analytics/campaigns?campaignIds=xxx&startDate=xxx&endDate=xxx
```

**Expected Response:**
```json
[
  {
    "campaignId": "campaign_1",
    "campaignName": "Summer Sale 2024",
    "spend": 5000,
    "revenue": 15000,
    "roas": 3.0,
    "impressions": 100000,
    "clicks": 5000,
    "conversions": 300,
    "ctr": 0.05,
    "cvr": 0.06,
    "cpa": 16.67,
    "timestamp": 1704240000000
  }
]
```

#### 2. Trend Data
```
GET /api/analytics/trends?campaignIds=xxx&startDate=xxx&endDate=xxx&granularity=day
```

**Expected Response:**
```json
[
  {
    "date": "2024-01-01",
    "timestamp": 1704067200000,
    "roas": 2.8,
    "spend": 1000,
    "revenue": 2800,
    "conversions": 50,
    "ctr": 0.045
  }
]
```

#### 3. Funnel Data
```
GET /api/analytics/funnel?campaignIds=xxx&startDate=xxx&endDate=xxx
```

**Expected Response:**
```json
[
  {
    "stage": "Impressions",
    "value": 100000,
    "percentage": 100,
    "dropoff": 0
  },
  {
    "stage": "Clicks",
    "value": 5000,
    "percentage": 5,
    "dropoff": 95
  }
]
```

#### 4. Creative Performance
```
GET /api/analytics/creatives?campaignIds=xxx&startDate=xxx&endDate=xxx
```

**Expected Response:**
```json
[
  {
    "creativeId": "creative_1",
    "creativeName": "Summer Video Ad",
    "campaignId": "campaign_1",
    "format": "video",
    "hookType": "problem_agitate",
    "impressions": 50000,
    "clicks": 2500,
    "conversions": 150,
    "spend": 2500,
    "revenue": 7500,
    "roas": 3.0,
    "ctr": 0.05,
    "cvr": 0.06,
    "cpa": 16.67,
    "thumbnailUrl": "https://example.com/thumb.jpg"
  }
]
```

#### 5. HubSpot Deals
```
GET /api/analytics/hubspot-deals?campaignIds=xxx&startDate=xxx&endDate=xxx
```

**Expected Response:**
```json
[
  {
    "dealId": "deal_1",
    "dealName": "Enterprise Deal",
    "amount": 50000,
    "stage": "Closed Won",
    "campaignId": "campaign_1",
    "creativeId": "creative_1",
    "sourceChannel": "Facebook",
    "createdAt": 1704067200000,
    "closedAt": 1704240000000
  }
]
```

#### 6. Prediction Comparison
```
GET /api/analytics/prediction-comparison?campaignIds=xxx&startDate=xxx&endDate=xxx
```

**Expected Response:**
```json
{
  "predictedRoas": 2.8,
  "actualRoas": 3.0,
  "predictedConversions": 280,
  "actualConversions": 300,
  "accuracy": 93.3,
  "variance": 7.1
}
```

#### 7. Export CSV
```
GET /api/analytics/export/csv?campaignIds=xxx&startDate=xxx&endDate=xxx&dataType=campaigns
```

**Expected Response:** CSV file blob

#### 8. Alerts (GET)
```
GET /api/analytics/alerts?campaignIds=xxx
```

**Expected Response:**
```json
[
  {
    "id": "alert_1",
    "type": "roas_drop",
    "threshold": 2.0,
    "enabled": true,
    "campaignIds": ["campaign_1"]
  }
]
```

#### 9. Alerts (POST)
```
POST /api/analytics/alerts
Content-Type: application/json

{
  "type": "roas_drop",
  "threshold": 2.0,
  "enabled": true,
  "campaignIds": ["campaign_1"]
}
```

#### 10. Scheduled Reports (GET)
```
GET /api/analytics/scheduled-reports
```

**Expected Response:**
```json
[
  {
    "id": "report_1",
    "name": "Weekly Performance",
    "frequency": "weekly",
    "recipients": ["user@example.com"],
    "metrics": ["roas", "spend", "revenue"],
    "enabled": true
  }
]
```

#### 11. Scheduled Reports (POST)
```
POST /api/analytics/scheduled-reports
Content-Type: application/json

{
  "name": "Weekly Performance",
  "frequency": "weekly",
  "recipients": ["user@example.com"],
  "metrics": ["roas", "spend", "revenue"],
  "enabled": true
}
```

### WebSocket Endpoint

```
WS /api/analytics/stream
```

**Subscribe Message (Client → Server):**
```json
{
  "type": "subscribe",
  "campaignIds": ["campaign_1", "campaign_2"]
}
```

**Update Message (Server → Client):**
```json
{
  "type": "metrics_update",
  "campaignId": "campaign_1",
  "timestamp": 1704240000000,
  "data": {
    "spend": 5200,
    "revenue": 15600,
    "roas": 3.0,
    "conversions": 312
  }
}
```

---

## Integration with Other Agents

### Agent 11: Campaign Performance Tracker

The Campaign Tracker provides the core metrics data:

```python
# services/ml-service/campaign_tracker.py

class CampaignTracker:
    async def get_campaign_metrics(
        self,
        campaign_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[CampaignMetrics]:
        """
        Called by GET /api/analytics/campaigns
        Returns real-time metrics from Meta API
        """
        metrics = []
        for campaign_id in campaign_ids:
            # Fetch from Meta API
            meta_data = await self.meta_client.get_insights(campaign_id)

            # Calculate metrics
            metrics.append({
                'campaignId': campaign_id,
                'spend': meta_data['spend'],
                'revenue': self.calculate_revenue(campaign_id),
                'roas': meta_data['revenue'] / meta_data['spend'],
                # ... more metrics
            })

        return metrics
```

### Agent 16: ROAS Predictor

The ROAS Predictor provides prediction comparison data:

```python
# services/ml-service/roas_predictor.py

class ROASPredictor:
    async def get_prediction_comparison(
        self,
        campaign_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> PredictionComparison:
        """
        Called by GET /api/analytics/prediction-comparison
        Compares XGBoost predictions with actual performance
        """
        predictions = []
        actuals = []

        for campaign_id in campaign_ids:
            # Get prediction from XGBoost model
            pred = self.model.predict(campaign_features)
            predictions.append(pred)

            # Get actual performance
            actual = await self.tracker.get_actual_roas(campaign_id)
            actuals.append(actual)

        return self.calculate_accuracy(predictions, actuals)
```

### Agent 12: Creative Performance Attribution

Provides creative-level insights:

```python
# services/ml-service/creative_attribution.py

class CreativeAttribution:
    async def get_creative_performance(
        self,
        campaign_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[CreativePerformance]:
        """
        Called by GET /api/analytics/creatives
        Analyzes hook types, visual elements, and copy patterns
        """
        creatives = await self.get_creatives_for_campaigns(campaign_ids)

        performances = []
        for creative in creatives:
            # Analyze hook type (from Agent 17)
            hook_type = await self.hook_detector.classify(creative)

            # Get performance metrics
            metrics = await self.get_creative_metrics(creative.id)

            performances.append({
                'creativeId': creative.id,
                'hookType': hook_type,
                'roas': metrics.roas,
                # ... more data
            })

        return performances
```

### Agent 13: HubSpot Sync Agent

Provides deal attribution:

```python
# services/ml-service/hubspot_sync.py

class HubSpotSync:
    async def get_deal_attribution(
        self,
        campaign_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[HubSpotDeal]:
        """
        Called by GET /api/analytics/hubspot-deals
        Returns deals attributed to campaigns
        """
        deals = await self.hubspot_client.get_deals(
            created_after=start_date,
            created_before=end_date
        )

        # Attribute deals to campaigns
        attributed_deals = []
        for deal in deals:
            campaign_id = self.attribute_deal_to_campaign(deal)
            if campaign_id in campaign_ids:
                attributed_deals.append({
                    'dealId': deal.id,
                    'campaignId': campaign_id,
                    'amount': deal.amount,
                    # ... more data
                })

        return attributed_deals
```

---

## Backend Implementation Example

Here's a complete Flask/FastAPI endpoint example:

```python
# backend/app/routes/analytics.py

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/analytics")

@router.get("/campaigns")
async def get_campaign_metrics(
    campaignIds: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...)
):
    """Get campaign metrics for Analytics Dashboard"""
    campaign_ids = campaignIds.split(',')
    start = datetime.fromisoformat(startDate)
    end = datetime.fromisoformat(endDate)

    # Call Agent 11: Campaign Tracker
    tracker = CampaignTracker()
    metrics = await tracker.get_campaign_metrics(
        campaign_ids=campaign_ids,
        start_date=start,
        end_date=end
    )

    return metrics

@router.get("/trends")
async def get_trend_data(
    campaignIds: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...),
    granularity: str = Query("day")
):
    """Get time-series trend data"""
    campaign_ids = campaignIds.split(',')
    start = datetime.fromisoformat(startDate)
    end = datetime.fromisoformat(endDate)

    tracker = CampaignTracker()
    trends = await tracker.get_trend_data(
        campaign_ids=campaign_ids,
        start_date=start,
        end_date=end,
        granularity=granularity
    )

    return trends

@router.get("/creatives")
async def get_creative_performance(
    campaignIds: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...)
):
    """Get creative-level performance"""
    campaign_ids = campaignIds.split(',')
    start = datetime.fromisoformat(startDate)
    end = datetime.fromisoformat(endDate)

    # Call Agent 12: Creative Attribution
    attribution = CreativeAttribution()
    creatives = await attribution.get_creative_performance(
        campaign_ids=campaign_ids,
        start_date=start,
        end_date=end
    )

    return creatives

@router.get("/hubspot-deals")
async def get_hubspot_deals(
    campaignIds: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...)
):
    """Get HubSpot deal attribution"""
    campaign_ids = campaignIds.split(',')
    start = datetime.fromisoformat(startDate)
    end = datetime.fromisoformat(endDate)

    # Call Agent 13: HubSpot Sync
    hubspot = HubSpotSync()
    deals = await hubspot.get_deal_attribution(
        campaign_ids=campaign_ids,
        start_date=start,
        end_date=end
    )

    return deals

@router.get("/prediction-comparison")
async def get_prediction_comparison(
    campaignIds: str = Query(...),
    startDate: str = Query(...),
    endDate: str = Query(...)
):
    """Get performance vs prediction comparison"""
    campaign_ids = campaignIds.split(',')
    start = datetime.fromisoformat(startDate)
    end = datetime.fromisoformat(endDate)

    # Call Agent 16: ROAS Predictor
    predictor = ROASPredictor()
    comparison = await predictor.get_prediction_comparison(
        campaign_ids=campaign_ids,
        start_date=start,
        end_date=end
    )

    return comparison

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()

    try:
        while True:
            # Receive subscribe message
            data = await websocket.receive_json()

            if data['type'] == 'subscribe':
                campaign_ids = data['campaignIds']

                # Start streaming updates
                async for update in campaign_tracker.stream_updates(campaign_ids):
                    await websocket.send_json({
                        'type': 'metrics_update',
                        'campaignId': update.campaign_id,
                        'data': update.metrics
                    })
    except WebSocketDisconnect:
        pass
```

---

## Testing the Integration

### 1. Test API Endpoints

```bash
# Test campaign metrics
curl "http://localhost:8080/api/analytics/campaigns?campaignIds=campaign_1&startDate=2024-01-01T00:00:00Z&endDate=2024-01-31T23:59:59Z"

# Test trend data
curl "http://localhost:8080/api/analytics/trends?campaignIds=campaign_1&startDate=2024-01-01T00:00:00Z&endDate=2024-01-31T23:59:59Z&granularity=day"

# Test creative performance
curl "http://localhost:8080/api/analytics/creatives?campaignIds=campaign_1&startDate=2024-01-01T00:00:00Z&endDate=2024-01-31T23:59:59Z"
```

### 2. Test WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8080/api/analytics/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    campaignIds: ['campaign_1', 'campaign_2']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received update:', data);
};
```

---

## Troubleshooting

### Issue: Dashboard shows "Loading..." forever

**Solution:**
1. Check API endpoints are running: `curl http://localhost:8080/health`
2. Check CORS configuration allows frontend origin
3. Check browser console for errors
4. Verify environment variables are set correctly

### Issue: Real-time updates not working

**Solution:**
1. Verify WebSocket endpoint is accessible
2. Check firewall/proxy allows WebSocket connections
3. Ensure auto-refresh is enabled
4. Check browser console for WebSocket errors

### Issue: Charts show "No data available"

**Solution:**
1. Verify campaigns are selected
2. Check date range is valid
3. Ensure backend returns data in correct format
4. Check React Query cache in React DevTools

---

## Production Checklist

- [ ] All API endpoints implemented and tested
- [ ] WebSocket server configured and running
- [ ] CORS configured for production domain
- [ ] Rate limiting configured (per API docs)
- [ ] Authentication/authorization implemented
- [ ] Error monitoring set up (Sentry, etc.)
- [ ] Performance monitoring enabled
- [ ] CDN configured for static assets
- [ ] SSL/TLS certificates installed
- [ ] Database indexes optimized
- [ ] Cache layer configured (Redis)
- [ ] Load balancing configured
- [ ] Backup and recovery tested

---

## Support

For issues or questions:
1. Check the README.md for usage examples
2. Review the ARCHITECTURE.md for technical details
3. Check example files in AnalyticsDashboard.example.tsx
4. Contact the development team
