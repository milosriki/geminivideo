# Analytics Dashboard Architecture

## Agent 27: Real-time Performance Tracking System

### Executive Summary

The Analytics Dashboard is a production-grade, real-time performance tracking system that integrates with multiple backend agents to provide comprehensive campaign analytics, creative performance insights, HubSpot attribution, and predictive analytics. Built with TypeScript, React, and Recharts, it delivers a responsive, data-rich interface for monitoring and optimizing advertising campaigns.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANALYTICS DASHBOARD                          │
│                        (Agent 27)                                │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Overview   │  │  Creatives  │  │ Attribution │             │
│  │     Tab     │  │     Tab     │  │     Tab     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │   Alerts    │  │   Reports   │                               │
│  │     Tab     │  │     Tab     │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                   │
│  Components:                                                      │
│  • MetricCard      • TrendChart      • FunnelChart              │
│  • CreativeTable   • AttributionPie  • DateRangePicker          │
│  • AlertConfig     • ReportScheduler                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP / WebSocket
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌──────────────────┐                    ┌──────────────────────┐
│  Analytics API   │                    │  WebSocket Server    │
│  (Backend)       │                    │  /analytics/stream   │
│                  │                    │                      │
│  REST Endpoints  │                    │  Real-time Updates   │
│  • campaigns     │                    │  • Campaign metrics  │
│  • trends        │                    │  • Alert triggers    │
│  • funnel        │                    │  • Live data push    │
│  • creatives     │                    └──────────────────────┘
│  • hubspot-deals │
│  • predictions   │
│  • alerts        │
│  • reports       │
└─────────┬────────┘
          │
          │ Integrates with:
          │
    ┌─────┴─────────────────────────────────────┐
    │                                             │
    ▼                                             ▼
┌──────────────────┐                    ┌──────────────────────┐
│  Agent 11:       │                    │  Agent 16:           │
│  Campaign        │                    │  ROAS Predictor      │
│  Tracker         │                    │                      │
│                  │                    │  XGBoost Model       │
│  • Meta API Sync │                    │  • Predictions       │
│  • Metrics Calc  │                    │  • Accuracy Tracking │
│  • ROAS, CTR     │                    └──────────────────────┘
└──────────────────┘
    │
    ├──────────────────────────────────────────┐
    │                                          │
    ▼                                          ▼
┌──────────────────┐                ┌──────────────────────┐
│  Agent 12:       │                │  Agent 13:           │
│  Creative        │                │  HubSpot Sync        │
│  Attribution     │                │                      │
│                  │                │  • Deal Attribution  │
│  • Hook Analysis │                │  • Pipeline Tracking │
│  • Visual Metrics│                │  • CRM Integration   │
└──────────────────┘                └──────────────────────┘
```

---

## Component Architecture

### React Component Tree

```
AnalyticsDashboard
│
├── DateRangePicker
│   ├── StartDateInput
│   ├── EndDateInput
│   └── QuickRangeButtons (7d, 30d, 90d)
│
├── TabNavigation
│   ├── OverviewTab
│   ├── CreativesTab
│   ├── AttributionTab
│   ├── AlertsTab
│   └── ReportsTab
│
├── OverviewTab
│   ├── MetricCards (x5)
│   │   ├── TotalSpend
│   │   ├── TotalRevenue
│   │   ├── ROAS
│   │   ├── CTR
│   │   └── CPA
│   │
│   ├── RoasTrendChart (AreaChart)
│   ├── SpendVsRevenueChart (LineChart)
│   ├── CtrTrendChart (LineChart)
│   ├── ConversionFunnel (ProgressBars)
│   └── PredictionComparison
│
├── CreativesTab
│   ├── ExportButton
│   └── CreativePerformanceTable
│       ├── SortableHeaders
│       ├── CreativeRows (with thumbnails)
│       └── PerformanceMetrics
│
├── AttributionTab
│   ├── ExportButton
│   ├── AttributionSummary (MetricCards x4)
│   ├── DealsByChannelChart (PieChart)
│   └── DealsTable
│
├── AlertsTab
│   ├── CreateAlertForm
│   │   ├── AlertTypeSelect
│   │   ├── ThresholdInput
│   │   └── EnableToggle
│   └── ActiveAlertsList
│
└── ReportsTab
    ├── CreateReportForm
    │   ├── ReportNameInput
    │   ├── FrequencySelect
    │   ├── RecipientsManager
    │   └── MetricsSelector
    └── ActiveReportsList
```

---

## Data Flow Architecture

### 1. Initial Data Load

```
User opens Dashboard
        │
        ▼
React Component Mounts
        │
        ▼
React Query Hooks Execute
        │
        ├──► useQuery('campaignMetrics')
        ├──► useQuery('trendData')
        ├──► useQuery('funnelData')
        ├──► useQuery('creativePerformance')
        ├──► useQuery('hubspotDeals')
        └──► useQuery('predictionComparison')
        │
        ▼
Parallel API Calls
        │
        ▼
Backend Processing
        │
        ├──► Campaign Tracker (Agent 11)
        ├──► Creative Attribution (Agent 12)
        ├──► HubSpot Sync (Agent 13)
        └──► ROAS Predictor (Agent 16)
        │
        ▼
Data Aggregation
        │
        ▼
Response to Frontend
        │
        ▼
React Query Cache Update
        │
        ▼
Component Re-renders
        │
        ▼
Charts & Tables Update
```

### 2. Real-time Updates

```
WebSocket Connection
        │
        ▼
Subscribe to Campaign IDs
        │
        ▼
Backend Event Stream
        │
        ├──► Meta API Webhook
        ├──► Scheduled Sync (every 5min)
        └──► Manual Trigger
        │
        ▼
Metrics Update Detected
        │
        ▼
Push Update via WebSocket
        │
        ▼
Frontend Receives Update
        │
        ▼
Invalidate React Query Cache
        │
        ▼
Automatic Refetch
        │
        ▼
UI Updates in Real-time
```

### 3. User Interaction Flow

```
User Changes Date Range
        │
        ▼
State Update (setDateRange)
        │
        ▼
Query Key Changes
        │
        ▼
React Query Detects Change
        │
        ▼
Refetch with New Parameters
        │
        ▼
Loading State
        │
        ▼
New Data Arrives
        │
        ▼
Charts Re-render
```

---

## State Management

### React State

```typescript
// Local Component State
const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);
const [dateRange, setDateRange] = useState<DateRange>({ ... });
const [autoRefresh, setAutoRefresh] = useState(true);
const [refreshInterval, setRefreshInterval] = useState(30000);
const [activeTab, setActiveTab] = useState('overview');
const [sortColumn, setSortColumn] = useState('roas');
const [sortDirection, setSortDirection] = useState('desc');
```

### Server State (React Query)

```typescript
// Cached API Data
const campaignMetrics = useQuery({
  queryKey: ['campaignMetrics', selectedCampaigns, dateRange],
  queryFn: () => AnalyticsAPI.getCampaignMetrics(...),
  refetchInterval: autoRefresh ? refreshInterval : false,
});

const trendData = useQuery({
  queryKey: ['trendData', selectedCampaigns, dateRange],
  queryFn: () => AnalyticsAPI.getTrendData(...),
  refetchInterval: autoRefresh ? refreshInterval : false,
});

// ... more queries
```

### Cache Strategy

```typescript
// Query Client Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      cacheTime: 10 * 60 * 1000,     // 10 minutes
      refetchOnWindowFocus: true,     // Refetch on tab focus
      refetchOnReconnect: true,       // Refetch on network reconnect
      retry: 3,                       // Retry failed requests 3 times
    },
  },
});
```

---

## API Integration

### REST API Endpoints

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `/analytics/campaigns` | GET | Campaign metrics | 100/min |
| `/analytics/trends` | GET | Time-series data | 100/min |
| `/analytics/funnel` | GET | Conversion funnel | 100/min |
| `/analytics/creatives` | GET | Creative performance | 100/min |
| `/analytics/hubspot-deals` | GET | Deal attribution | 50/min |
| `/analytics/prediction-comparison` | GET | Predictions vs actual | 50/min |
| `/analytics/alerts` | GET/POST | Alert configs | 50/min |
| `/analytics/scheduled-reports` | GET/POST | Report configs | 50/min |
| `/analytics/export/csv` | GET | CSV export | 10/min |

### WebSocket Protocol

```json
// Client → Server (Subscribe)
{
  "type": "subscribe",
  "campaignIds": ["campaign_1", "campaign_2"]
}

// Server → Client (Update)
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

// Server → Client (Alert)
{
  "type": "alert_triggered",
  "alertId": "alert_1",
  "campaignId": "campaign_1",
  "alertType": "roas_drop",
  "threshold": 2.0,
  "currentValue": 1.8,
  "message": "ROAS dropped below threshold"
}
```

---

## Data Models

### Campaign Metrics

```typescript
interface CampaignMetrics {
  campaignId: string;        // Unique campaign identifier
  campaignName: string;      // Human-readable name
  spend: number;             // Total spend in USD
  revenue: number;           // Total revenue in USD
  roas: number;              // Return on Ad Spend (revenue / spend)
  impressions: number;       // Total ad impressions
  clicks: number;            // Total clicks
  conversions: number;       // Total conversions
  ctr: number;               // Click-through rate (clicks / impressions)
  cvr: number;               // Conversion rate (conversions / clicks)
  cpa: number;               // Cost per acquisition (spend / conversions)
  timestamp: number;         // Unix timestamp
}
```

### Trend Data Point

```typescript
interface TrendDataPoint {
  date: string;              // ISO date string (YYYY-MM-DD)
  timestamp: number;         // Unix timestamp
  roas: number;              // ROAS for this period
  spend: number;             // Spend for this period
  revenue: number;           // Revenue for this period
  conversions: number;       // Conversions for this period
  ctr: number;               // CTR for this period
}
```

### Creative Performance

```typescript
interface CreativePerformance {
  creativeId: string;        // Unique creative identifier
  creativeName: string;      // Human-readable name
  campaignId: string;        // Parent campaign ID
  format: string;            // 'video' | 'image' | 'carousel'
  hookType: string;          // Hook classification from Agent 17
  impressions: number;       // Total impressions
  clicks: number;            // Total clicks
  conversions: number;       // Total conversions
  spend: number;             // Total spend
  revenue: number;           // Total revenue
  roas: number;              // ROAS
  ctr: number;               // CTR
  cvr: number;               // CVR
  cpa: number;               // CPA
  thumbnailUrl?: string;     // Preview thumbnail
}
```

---

## Performance Optimization

### 1. Code Splitting

```typescript
// Lazy load charts
const RoasChart = React.lazy(() => import('./charts/RoasChart'));
const FunnelChart = React.lazy(() => import('./charts/FunnelChart'));
```

### 2. Memoization

```typescript
// Memoize expensive calculations
const aggregateMetrics = useMemo(() => {
  // Heavy computation only when campaignMetrics changes
  return calculateAggregates(campaignMetrics);
}, [campaignMetrics]);

// Memoize sorted data
const sortedCreatives = useMemo(() => {
  return [...creativePerformance].sort(compareFn);
}, [creativePerformance, sortColumn, sortDirection]);
```

### 3. Virtual Scrolling

For large creative tables, implement virtualization:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const rowVirtualizer = useVirtualizer({
  count: sortedCreatives.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 64, // Row height in pixels
});
```

### 4. Debounced Inputs

```typescript
import { useDebouncedValue } from '@mantine/hooks';

const [searchTerm, setSearchTerm] = useState('');
const [debouncedSearch] = useDebouncedValue(searchTerm, 300);
```

### 5. Request Deduplication

React Query automatically deduplicates identical requests:

```typescript
// These will only fire one request
const query1 = useQuery({ queryKey: ['campaigns', id] });
const query2 = useQuery({ queryKey: ['campaigns', id] }); // Deduped
```

---

## Security Considerations

### 1. API Authentication

```typescript
// Add auth token to all requests
const API_BASE = process.env.VITE_API_URL;
const AUTH_TOKEN = localStorage.getItem('auth_token');

fetch(`${API_BASE}/analytics/campaigns`, {
  headers: {
    'Authorization': `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json',
  },
});
```

### 2. Input Validation

```typescript
// Validate date ranges
const isValidDateRange = (start: Date, end: Date): boolean => {
  if (end < start) return false;
  if (end > new Date()) return false;
  const daysDiff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (daysDiff > 365) return false; // Max 1 year
  return true;
};
```

### 3. XSS Prevention

```typescript
// Sanitize user inputs
import DOMPurify from 'dompurify';

const sanitizedInput = DOMPurify.sanitize(userInput);
```

### 4. CSRF Protection

```typescript
// Include CSRF token
fetch(`${API_BASE}/analytics/alerts`, {
  method: 'POST',
  headers: {
    'X-CSRF-Token': getCsrfToken(),
  },
});
```

---

## Error Handling

### 1. API Error Handling

```typescript
try {
  const data = await AnalyticsAPI.getCampaignMetrics(...);
} catch (error) {
  if (error instanceof NetworkError) {
    // Show offline message
  } else if (error instanceof AuthError) {
    // Redirect to login
  } else {
    // Show generic error
  }
}
```

### 2. React Error Boundaries

```typescript
class AnalyticsErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

### 3. Query Error Handling

```typescript
const { data, error, isError } = useQuery({
  queryKey: ['campaigns'],
  queryFn: fetchCampaigns,
  onError: (error) => {
    toast.error('Failed to load campaigns');
  },
});

if (isError) {
  return <ErrorMessage error={error} />;
}
```

---

## Testing Strategy

### 1. Unit Tests

```typescript
describe('AnalyticsDashboard', () => {
  it('should calculate aggregate metrics correctly', () => {
    const metrics = calculateAggregates(mockData);
    expect(metrics.totalSpend).toBe(8000);
    expect(metrics.avgRoas).toBe(3.0);
  });
});
```

### 2. Integration Tests

```typescript
describe('API Integration', () => {
  it('should fetch campaign metrics', async () => {
    const data = await AnalyticsAPI.getCampaignMetrics(...);
    expect(data).toHaveLength(2);
    expect(data[0].campaignId).toBe('campaign_1');
  });
});
```

### 3. E2E Tests (Playwright)

```typescript
test('should display analytics dashboard', async ({ page }) => {
  await page.goto('/analytics');
  await expect(page.locator('h1')).toContainText('Analytics Dashboard');
  await expect(page.locator('[data-testid="roas-metric"]')).toBeVisible();
});
```

### 4. Performance Tests

```typescript
import { measurePerformance } from '@testing-library/react';

test('should render within performance budget', async () => {
  const { renderTime } = await measurePerformance(
    () => render(<AnalyticsDashboard />)
  );
  expect(renderTime).toBeLessThan(1000); // 1 second
});
```

---

## Deployment

### Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'recharts': ['recharts'],
          'react-query': ['@tanstack/react-query'],
        },
      },
    },
  },
});
```

### Environment Variables

```bash
# .env.production
VITE_API_URL=https://api.geminivideo.com
VITE_WS_URL=wss://api.geminivideo.com
VITE_ENABLE_ANALYTICS=true
```

---

## Future Enhancements

1. **Advanced Filtering**
   - Multi-dimensional filtering
   - Saved filter presets
   - Dynamic segmentation

2. **Custom Dashboards**
   - Drag-and-drop widgets
   - Customizable layouts
   - User preferences

3. **AI Insights**
   - Automated anomaly detection
   - Recommendation engine
   - Predictive alerts

4. **Collaboration**
   - Shared dashboards
   - Comments and annotations
   - Team notifications

5. **Mobile App**
   - React Native implementation
   - Push notifications
   - Offline support

---

## Conclusion

The Analytics Dashboard (Agent 27) is a production-ready, scalable solution for real-time campaign performance tracking. It seamlessly integrates with multiple backend agents to provide comprehensive insights, enabling data-driven decision-making and campaign optimization.

For support, consult the README.md or contact the development team.
