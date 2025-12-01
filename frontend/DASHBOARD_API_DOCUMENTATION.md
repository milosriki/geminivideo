# Dashboard API Client & Context - Implementation Documentation

**Agent 11: Frontend Dashboard Integration Engineer**

This document describes the unified dashboard API client and React context provider that connects all backend services.

## Table of Contents

- [Overview](#overview)
- [Files Created](#files-created)
- [Features](#features)
- [Installation](#installation)
- [API Client](#api-client)
- [React Context](#react-context)
- [Usage Examples](#usage-examples)
- [Type Definitions](#type-definitions)
- [Error Handling](#error-handling)
- [Caching Strategy](#caching-strategy)
- [Best Practices](#best-practices)

## Overview

The Dashboard API integration provides:

1. **Unified API Client** (`dashboardAPI.ts`) - Type-safe HTTP client with axios
2. **React Context Provider** (`DashboardContext.tsx`) - Global state management for API calls
3. **Usage Examples** (`DashboardUsageExample.tsx`) - Real-world component examples

## Files Created

### 1. `/home/user/geminivideo/frontend/src/services/dashboardAPI.ts`

Complete TypeScript API client with:
- 30+ type definitions for all API responses
- Axios-based HTTP client with interceptors
- Automatic retry logic for failed requests
- Request timeout handling
- Authentication header support
- Comprehensive error transformation

**Size:** ~19KB | **Lines:** ~690

### 2. `/home/user/geminivideo/frontend/src/contexts/DashboardContext.tsx`

React context provider with:
- Loading state management
- Error state management
- Intelligent caching system
- Custom React hook (`useDashboard`)
- Automatic cache cleanup

**Size:** ~19KB | **Lines:** ~670

### 3. `/home/user/geminivideo/frontend/src/contexts/DashboardUsageExample.tsx`

6 complete component examples demonstrating:
- Video analysis
- Approval workflows
- Meta insights
- Render job monitoring
- Metrics dashboards
- Drive folder analysis

**Size:** ~11KB | **Lines:** ~350+

## Features

### API Client Features

 **Video Analysis**
- Upload and analyze videos
- Poll analysis status
- Get detailed results

 **Council of Titans**
- Get AI council scores
- Submit videos for review
- Multi-titan consensus

 **Meta Learning**
- Get performance insights
- Trigger data refresh
- Get top performers

 **Render Jobs**
- Create render jobs
- Monitor progress
- Cancel jobs
- Download results

 **Approval Workflow**
- Get approval queue
- Approve/reject ads
- Submit for approval

 **Metrics**
- Diversification metrics
- Reliability metrics
- Prediction accuracy

 **Drive Integration**
- Analyze entire folders
- Track progress
- Get results

### Context Features

 **Smart Caching**
- Configurable TTL
- Automatic expiration
- Cache invalidation

 **Loading States**
- Per-request loading tracking
- Global loading state
- Loading indicators

 **Error Management**
- Typed error objects
- Per-request error tracking
- Error clearing

 **Performance**
- Request deduplication
- Parallel requests
- Automatic retry

## Installation

### Step 1: Install Dependencies

```bash
cd /home/user/geminivideo/frontend
npm install axios
```

### Step 2: Environment Configuration

Add to your `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

### Step 3: Wrap Your App

In your `main.tsx` or `App.tsx`:

```typescript
import { DashboardProvider } from './contexts/DashboardContext';

function App() {
  return (
    <DashboardProvider cacheTTL={5 * 60 * 1000}>
      {/* Your app components */}
    </DashboardProvider>
  );
}
```

## API Client

### Direct Usage (Without Context)

```typescript
import { dashboardAPI } from './services/dashboardAPI';

// Set authentication
dashboardAPI.setAuthToken('your-jwt-token');

// Analyze a video
const analyzeVideo = async (file: File) => {
  try {
    const result = await dashboardAPI.analyzeVideo(file);
    console.log('Analysis ID:', result.asset_id);
  } catch (error) {
    console.error('Failed:', error.message);
  }
};

// Get approval queue
const getQueue = async () => {
  const items = await dashboardAPI.getApprovalQueue();
  return items;
};
```

### Available Methods

#### Video Analysis
```typescript
dashboardAPI.analyzeVideo(file: File)
dashboardAPI.getAnalysisStatus(analysisId: string)
dashboardAPI.getAnalysisResults(analysisId: string)
```

#### Council of Titans
```typescript
dashboardAPI.getCouncilScore(videoId: string)
dashboardAPI.submitForCouncilReview(videoId: string)
```

#### Meta Learning
```typescript
dashboardAPI.getMetaInsights()
dashboardAPI.triggerMetaRefresh()
dashboardAPI.getTopPerformers(limit: number)
```

#### Render Jobs
```typescript
dashboardAPI.createRenderJob(config: RenderConfig)
dashboardAPI.getRenderStatus(jobId: string)
dashboardAPI.cancelRenderJob(jobId: string)
dashboardAPI.downloadRenderedVideo(jobId: string)
```

#### Approval Workflow
```typescript
dashboardAPI.getApprovalQueue()
dashboardAPI.submitForApproval(adId: string)
dashboardAPI.approveAd(adId: string, notes?: string)
dashboardAPI.rejectAd(adId: string, reason: string)
```

#### Metrics
```typescript
dashboardAPI.getDiversificationMetrics()
dashboardAPI.getReliabilityMetrics()
dashboardAPI.getPredictionAccuracy()
```

#### Drive Integration
```typescript
dashboardAPI.analyzeDriveFolder(folderId: string, maxVideos: number)
dashboardAPI.getDriveAnalysisStatus(jobId: string)
```

## React Context

### Using the Hook

```typescript
import { useDashboard } from './contexts/DashboardContext';

function MyComponent() {
  const {
    // Methods
    analyzeVideo,
    getApprovalQueue,

    // State
    isLoading,
    getError,

    // Cache
    clearCache,
  } = useDashboard();

  // Use the methods...
}
```

### Context Benefits

1. **Automatic Loading States**
   - No need to manually track loading
   - Per-request loading indicators
   - Global loading state

2. **Error Management**
   - Typed errors
   - Per-request error tracking
   - Easy error display

3. **Smart Caching**
   - Reduce API calls
   - Configurable TTL
   - Automatic cleanup

4. **Cache Invalidation**
   - Auto-clear on mutations
   - Manual cache clearing
   - Selective invalidation

## Usage Examples

### Example 1: Video Upload & Analysis

```typescript
function VideoUploader() {
  const { analyzeVideo, isLoading, getError } = useDashboard();
  const [result, setResult] = useState(null);

  const handleUpload = async (file: File) => {
    const analysis = await analyzeVideo(file);
    setResult(analysis);
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      {isLoading('analyzeVideo_*') && <p>Analyzing...</p>}
      {getError('analyzeVideo_*') && <p>Error: {getError('analyzeVideo_*').message}</p>}
      {result && <p>Analysis ID: {result.asset_id}</p>}
    </div>
  );
}
```

### Example 2: Approval Queue

```typescript
function ApprovalQueue() {
  const { getApprovalQueue, approveAd, rejectAd } = useDashboard();
  const [items, setItems] = useState([]);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    const queue = await getApprovalQueue();
    setItems(queue);
  };

  return (
    <div>
      {items.map(item => (
        <div key={item.ad_id}>
          <h3>{item.ad_id}</h3>
          <p>CTR: {item.predicted_ctr}</p>
          <button onClick={() => approveAd(item.ad_id)}>Approve</button>
          <button onClick={() => rejectAd(item.ad_id, 'Needs work')}>Reject</button>
        </div>
      ))}
    </div>
  );
}
```

### Example 3: Metrics Dashboard

```typescript
function MetricsDashboard() {
  const { getDiversificationMetrics, getReliabilityMetrics, isLoading } = useDashboard();
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    const [div, rel] = await Promise.all([
      getDiversificationMetrics(true), // Use cache
      getReliabilityMetrics(true),
    ]);
    setMetrics({ diversification: div, reliability: rel });
  };

  if (isLoading('diversificationMetrics')) return <div>Loading...</div>;

  return (
    <div>
      <h2>Diversification: {metrics?.diversification?.diversity_score}</h2>
      <h2>Accuracy: {metrics?.reliability?.accuracy}</h2>
    </div>
  );
}
```

## Type Definitions

All API responses are fully typed. Key types include:

```typescript
interface VideoAnalysis {
  asset_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  hook_style?: string;
  pacing?: string;
  emotional_trigger?: string;
  visual_elements?: string[];
}

interface CouncilScore {
  video_id: string;
  overall_score: number;
  titan_scores: TitanScore[];
  consensus: string;
}

interface RenderJob {
  job_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number;
  output_path?: string;
}

interface ApprovalItem {
  ad_id: string;
  predicted_ctr: number;
  predicted_roas: number;
  status: string;
}
```

See `/home/user/geminivideo/frontend/src/services/dashboardAPI.ts` for all types.

## Error Handling

### Error Structure

```typescript
interface DashboardAPIError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}
```

### Handling Errors

```typescript
// Using context
const { getApprovalQueue, getError } = useDashboard();

const loadQueue = async () => {
  await getApprovalQueue();

  const error = getError('approvalQueue');
  if (error) {
    console.error(`Error ${error.code}: ${error.message}`);
  }
};

// Using API directly
try {
  const result = await dashboardAPI.getApprovalQueue();
} catch (error) {
  console.error('API Error:', error.message);
}
```

### Retry Logic

The API client automatically retries:
- Network errors (no response)
- 5xx server errors
- 429 rate limit errors

Max retries: **3 attempts**
Retry delay: **1s, 2s, 3s** (exponential backoff)

## Caching Strategy

### How Caching Works

1. **TTL-based**: Cache entries expire after `cacheTTL` (default: 5 minutes)
2. **Automatic cleanup**: Expired entries removed every 60 seconds
3. **Smart invalidation**: Cache cleared after mutations

### Cache Control

```typescript
const { getMetaInsights, setCache, clearCache, getFromCache } = useDashboard();

// Use cache (default)
const insights = await getMetaInsights(true);

// Skip cache
const freshInsights = await getMetaInsights(false);

// Manual cache control
setCache('myKey', myData, 10 * 60 * 1000); // 10 minute TTL
const cached = getFromCache('myKey');
clearCache('myKey'); // Clear specific
clearCache(); // Clear all
```

### When Cache is Invalidated

- After `approveAd()` ’ clears approval queue cache
- After `rejectAd()` ’ clears approval queue cache
- After `triggerMetaRefresh()` ’ clears meta insights cache
- After `submitForCouncilReview()` ’ clears council score cache

## Best Practices

### 1. Use Context for Components

```typescript
//  Good - Uses context
function MyComponent() {
  const { analyzeVideo } = useDashboard();
  // ...
}

// L Avoid - Direct API calls lose state management
function MyComponent() {
  import { dashboardAPI } from '../services/dashboardAPI';
  // ...
}
```

### 2. Handle Loading States

```typescript
//  Good
if (isLoading('approvalQueue')) {
  return <Spinner />;
}

// L Avoid - No loading indicator
const items = await getApprovalQueue();
```

### 3. Use Cache Appropriately

```typescript
//  Good - Cache stable data
const metrics = await getDiversificationMetrics(true);

//  Good - Skip cache for dynamic data
const queue = await getApprovalQueue(false);
```

### 4. Clear Errors

```typescript
//  Good - Clear errors before retry
clearError('approvalQueue');
await getApprovalQueue();

//  Good - Clear all errors on logout
clearAllErrors();
```

### 5. Poll Status Correctly

```typescript
//  Good - Poll with cleanup
useEffect(() => {
  const interval = setInterval(async () => {
    const status = await getRenderStatus(jobId);
    if (status.status === 'COMPLETED') {
      clearInterval(interval);
    }
  }, 2000);

  return () => clearInterval(interval);
}, [jobId]);
```

## Testing

### Test API Client

```typescript
import { DashboardAPIClass } from './services/dashboardAPI';

describe('DashboardAPI', () => {
  let api: DashboardAPIClass;

  beforeEach(() => {
    api = new DashboardAPIClass();
  });

  it('should analyze video', async () => {
    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' });
    const result = await api.analyzeVideo(file);
    expect(result.asset_id).toBeDefined();
  });
});
```

### Test Context

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import { useDashboard, DashboardProvider } from './contexts/DashboardContext';

describe('DashboardContext', () => {
  it('should provide dashboard methods', () => {
    const wrapper = ({ children }) => (
      <DashboardProvider>{children}</DashboardProvider>
    );

    const { result } = renderHook(() => useDashboard(), { wrapper });

    expect(result.current.analyzeVideo).toBeDefined();
    expect(result.current.getApprovalQueue).toBeDefined();
  });
});
```

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Analyze video |
| GET | `/api/analysis/status/:id` | Get analysis status |
| GET | `/api/analysis/results/:id` | Get analysis results |
| GET | `/api/council/score/:id` | Get council score |
| POST | `/api/council/review` | Submit for review |
| GET | `/api/insights` | Get meta insights |
| POST | `/api/trigger/refresh-meta-metrics` | Trigger refresh |
| GET | `/api/top-performers` | Get top performers |
| POST | `/api/render/remix` | Create render job |
| GET | `/api/render/status/:id` | Get render status |
| DELETE | `/api/render/job/:id` | Cancel render job |
| GET | `/api/render/download/:id` | Download video |
| GET | `/api/approval/queue` | Get approval queue |
| POST | `/api/approval/submit` | Submit for approval |
| POST | `/api/approval/approve/:id` | Approve ad |
| GET | `/api/metrics/diversification` | Get diversification metrics |
| GET | `/api/metrics/reliability` | Get reliability metrics |
| GET | `/api/metrics/accuracy` | Get accuracy metrics |
| POST | `/api/trigger/analyze-drive-folder` | Analyze Drive folder |
| GET | `/api/drive/analysis/:id` | Get Drive analysis status |

## Troubleshooting

### Issue: "useDashboard must be used within a DashboardProvider"

**Solution:** Wrap your app with `<DashboardProvider>`:

```typescript
<DashboardProvider>
  <App />
</DashboardProvider>
```

### Issue: Requests timing out

**Solution:** Increase timeout in `dashboardAPI.ts`:

```typescript
const DEFAULT_TIMEOUT = 60000; // 60 seconds
```

### Issue: Cache not working

**Solution:** Ensure you're passing `useCache: true`:

```typescript
const data = await getMetaInsights(true); // Enable cache
```

### Issue: CORS errors

**Solution:** Configure backend CORS headers or update API base URL:

```env
VITE_API_URL=http://your-backend-url.com
```

## Performance Tips

1. **Use caching** for stable data (metrics, insights)
2. **Batch requests** using `Promise.all()`
3. **Clear cache** after mutations
4. **Debounce** frequent API calls
5. **Poll efficiently** with cleanup

## Security Considerations

1. **Authentication**: Use `setAuthToken()` for JWT tokens
2. **HTTPS**: Always use HTTPS in production
3. **Token storage**: Store tokens securely (httpOnly cookies)
4. **Error messages**: Don't expose sensitive data in errors
5. **Rate limiting**: Respect API rate limits

## Support

For issues or questions:
- Check this documentation
- Review usage examples in `DashboardUsageExample.tsx`
- Check TypeScript types in `dashboardAPI.ts`
- Refer to backend API documentation

---

**Created by Agent 11: Frontend Dashboard Integration Engineer**
**Date:** 2025-12-01
**Version:** 1.0.0
