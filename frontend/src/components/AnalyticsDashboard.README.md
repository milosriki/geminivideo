# Analytics Dashboard - Agent 27

## Overview

The **Analytics Dashboard** is a comprehensive real-time performance tracking system that provides deep insights into campaign performance, creative analytics, HubSpot attribution, and predictive analytics. Built as Agent 27 of the ULTIMATE 30-agent production plan.

## Features

### 🎯 Core Features

1. **Real-time Metrics Tracking**
   - Live data from Meta API via Campaign Tracker (Agent 11)
   - WebSocket connection for instant updates
   - Auto-refresh with configurable intervals
   - Manual refresh capability

2. **Key Performance Indicators**
   - Total Spend
   - Total Revenue
   - ROAS (Return on Ad Spend)
   - CTR (Click-Through Rate)
   - CPA (Cost Per Acquisition)
   - Total Conversions
   - Impressions & Clicks

3. **Advanced Visualizations**
   - **ROAS Trend Chart**: Area chart showing ROAS over time
   - **Spend vs Revenue**: Line chart comparing spend and revenue
   - **CTR Trend**: Click-through rate over time
   - **Conversion Funnel**: Multi-stage funnel with drop-off analysis
   - **Attribution Pie Chart**: Deal distribution by source channel

4. **Creative Performance Analysis**
   - Side-by-side creative comparison table
   - Performance metrics per creative (ROAS, CTR, CVR, CPA)
   - Thumbnail previews
   - Hook type analysis
   - Format performance
   - Sortable columns

5. **HubSpot Deal Attribution**
   - Deal pipeline visualization
   - Source channel attribution
   - Deal value tracking
   - Campaign and creative attribution
   - Closed vs open deals

6. **Performance vs Prediction**
   - XGBoost model predictions (from Agent 16)
   - Actual vs predicted ROAS
   - Actual vs predicted conversions
   - Accuracy percentage
   - Variance analysis

7. **Alert Configuration**
   - ROAS drop alerts
   - Spend limit alerts
   - Conversion drop alerts
   - CTR drop alerts
   - Customizable thresholds
   - Multi-campaign support

8. **Scheduled Reports**
   - Daily/Weekly/Monthly reports
   - Email distribution
   - Customizable metrics
   - Multiple recipients

9. **Export Functionality**
   - Export campaigns to CSV
   - Export creatives to CSV
   - Export funnel data to CSV
   - Export HubSpot deals to CSV

10. **Date Range Control**
    - Custom date range picker
    - Quick presets (7d, 30d, 90d)
    - Date-based filtering

## Architecture

### Data Flow

```
┌─────────────────────┐
│  Analytics          │
│  Dashboard          │
│  (Agent 27)         │
└──────────┬──────────┘
           │
           ├──────────────────────────────────────────┐
           │                                          │
           ▼                                          ▼
┌──────────────────────┐                  ┌──────────────────────┐
│ Campaign Tracker     │                  │   WebSocket API      │
│ (Agent 11)           │◄─────────────────┤   /analytics/stream  │
│                      │                  │                      │
│ - Meta API Sync      │                  │   Real-time Updates  │
│ - Metrics Calc       │                  └──────────────────────┘
│ - ROAS, CTR, CPA     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Backend API         │
│                      │
│ GET /analytics/      │
│   - campaigns        │
│   - trends           │
│   - funnel           │
│   - creatives        │
│   - hubspot-deals    │
│   - prediction-      │
│     comparison       │
│                      │
│ POST /analytics/     │
│   - alerts           │
│   - scheduled-       │
│     reports          │
│   - export/csv       │
└──────────────────────┘
```

### Tech Stack

- **React** 18.2+ with TypeScript
- **Recharts** 2.10+ for data visualization
- **@tanstack/react-query** for data fetching & caching
- **Tailwind CSS** for styling
- **WebSocket** for real-time updates

## API Endpoints

### GET /analytics/campaigns
Fetch campaign-level metrics.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range

**Response:**
```typescript
{
  campaignId: string;
  campaignName: string;
  spend: number;
  revenue: number;
  roas: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  cvr: number;
  cpa: number;
  timestamp: number;
}[]
```

### GET /analytics/trends
Fetch time-series trend data.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range
- `granularity` (string): 'hour' | 'day' | 'week'

**Response:**
```typescript
{
  date: string;
  timestamp: number;
  roas: number;
  spend: number;
  revenue: number;
  conversions: number;
  ctr: number;
}[]
```

### GET /analytics/funnel
Fetch conversion funnel data.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range

**Response:**
```typescript
{
  stage: string;
  value: number;
  percentage: number;
  dropoff?: number;
}[]
```

### GET /analytics/creatives
Fetch creative-level performance.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range

**Response:**
```typescript
{
  creativeId: string;
  creativeName: string;
  campaignId: string;
  format: string;
  hookType: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  revenue: number;
  roas: number;
  ctr: number;
  cvr: number;
  cpa: number;
  thumbnailUrl?: string;
}[]
```

### GET /analytics/hubspot-deals
Fetch HubSpot deal attribution.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range

**Response:**
```typescript
{
  dealId: string;
  dealName: string;
  amount: number;
  stage: string;
  campaignId?: string;
  creativeId?: string;
  sourceChannel: string;
  createdAt: number;
  closedAt?: number;
}[]
```

### GET /analytics/prediction-comparison
Compare predictions vs actual performance.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range

**Response:**
```typescript
{
  predictedRoas: number;
  actualRoas: number;
  predictedConversions: number;
  actualConversions: number;
  accuracy: number;
  variance: number;
}
```

### GET /analytics/export/csv
Export data to CSV.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs
- `startDate` (ISO string): Start of date range
- `endDate` (ISO string): End of date range
- `dataType` (string): 'campaigns' | 'creatives' | 'funnel' | 'hubspot'

**Response:** Blob (CSV file)

### POST /analytics/alerts
Save alert configuration.

**Body:**
```typescript
{
  id?: string;
  type: 'roas_drop' | 'spend_limit' | 'conversion_drop' | 'ctr_drop';
  threshold: number;
  enabled: boolean;
  campaignIds: string[];
}
```

### GET /analytics/alerts
Get alert configurations.

**Query Parameters:**
- `campaignIds` (string): Comma-separated campaign IDs

**Response:**
```typescript
{
  id: string;
  type: 'roas_drop' | 'spend_limit' | 'conversion_drop' | 'ctr_drop';
  threshold: number;
  enabled: boolean;
  campaignIds: string[];
}[]
```

### POST /analytics/scheduled-reports
Save scheduled report configuration.

**Body:**
```typescript
{
  id?: string;
  name: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  metrics: string[];
  enabled: boolean;
}
```

### GET /analytics/scheduled-reports
Get scheduled report configurations.

**Response:**
```typescript
{
  id: string;
  name: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  metrics: string[];
  enabled: boolean;
}[]
```

### WebSocket /analytics/stream
Real-time updates stream.

**Subscribe Message:**
```json
{
  "type": "subscribe",
  "campaignIds": ["campaign_1", "campaign_2"]
}
```

**Update Message:**
```json
{
  "type": "metrics_update",
  "campaignId": "campaign_1",
  "data": { /* updated metrics */ }
}
```

## Usage

### Basic Usage

```typescript
import { AnalyticsDashboard } from './components/AnalyticsDashboard';

function App() {
  return (
    <AnalyticsDashboard
      campaignIds={['campaign_1', 'campaign_2']}
    />
  );
}
```

### With Query Client Provider

The dashboard internally manages its own queries, but you can wrap it in your app's QueryClientProvider:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AnalyticsDashboard />
    </QueryClientProvider>
  );
}
```

### Environment Variables

Set the API base URL:

```bash
VITE_API_URL=https://your-api.com/api
```

## Integration with Other Agents

### Agent 11: Campaign Performance Tracker
- Provides real-time campaign metrics
- Syncs data from Meta API
- Calculates ROAS, CTR, CPA, CVR

### Agent 16: ROAS Predictor
- XGBoost model predictions
- Supplies prediction comparison data
- Accuracy and variance metrics

### Agent 12: Creative Performance Attribution
- Creative-level insights
- Hook type analysis
- Visual element performance

### Agent 13: HubSpot Sync Agent
- Deal pipeline data
- Attribution tracking
- CRM integration

## Performance Optimization

1. **React Query Caching**
   - 5-minute stale time for most queries
   - Automatic background refetching
   - Query invalidation on updates

2. **WebSocket Connection**
   - Single connection for all campaigns
   - Automatic reconnection on failure
   - Selective query invalidation

3. **Lazy Loading**
   - Charts render only when tabs are active
   - Data fetched on-demand per tab
   - Efficient re-renders with useMemo

4. **Auto-refresh Control**
   - Toggle auto-refresh on/off
   - Configurable refresh intervals
   - Pauses when tab is inactive

## Testing

### Unit Tests

```bash
npm test AnalyticsDashboard.test.tsx
```

### Integration Tests

```bash
npm test AnalyticsDashboard.integration.test.tsx
```

### E2E Tests

```bash
npm run test:e2e
```

## Troubleshooting

### WebSocket Connection Issues

If real-time updates aren't working:

1. Check the WebSocket URL in browser console
2. Verify backend WebSocket server is running
3. Check firewall/proxy settings
4. Try manual refresh as fallback

### Missing Data

If charts show "No data available":

1. Verify campaigns are selected
2. Check date range is valid
3. Ensure backend API is returning data
4. Check browser console for API errors

### Export Fails

If CSV export doesn't work:

1. Check browser allows downloads
2. Verify API endpoint is accessible
3. Check date range and campaign selection
4. Ensure sufficient data exists

## Future Enhancements

- [ ] PDF export support
- [ ] Custom dashboard layouts
- [ ] Drag-and-drop widget arrangement
- [ ] More chart types (scatter, heatmap)
- [ ] Advanced filtering and segmentation
- [ ] Annotation support on charts
- [ ] Comparison mode (A vs B campaigns)
- [ ] Mobile-responsive optimizations
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts

## License

Part of the GeminiVideo ULTIMATE Production System.

## Support

For issues or questions, contact the development team or file an issue in the repository.
