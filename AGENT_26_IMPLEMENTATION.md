# Agent 26: Ad Spy & Competitor Intelligence Dashboard

## Overview

**Agent 26/30** implements a comprehensive Ad Spy and Competitor Intelligence Dashboard, providing production-ready competitor ad analysis capabilities similar to Attentionsight. This agent integrates with Agent 9 (Meta Ads Library Scraper) to deliver real-time insights from Meta's Ads Library with ZERO mock data.

## Implementation Summary

### Frontend Component
- **File:** `/home/user/geminivideo/frontend/src/components/AdSpyDashboard.tsx`
- **Lines:** 916 lines (exceeds 700 line requirement)
- **Size:** 32KB
- **Technology:** React + TypeScript + Tailwind CSS

### Backend Integration
1. **Gateway API Endpoints:** `/home/user/geminivideo/services/gateway-api/src/index.ts` (lines 722-910)
   - 5 new endpoints with security middleware
   - Rate limiting, input validation, XSS protection

2. **Titan Core API Server:** `/home/user/geminivideo/services/titan-core/meta_ads_library_api.py`
   - Flask API server
   - 8 endpoints for Meta Ads Library integration
   - Full error handling and logging

3. **Meta Ads Library Scraper:** `/home/user/geminivideo/services/titan-core/meta/ads_library_scraper.py` (Agent 9)
   - Real Meta API integration
   - Production-ready scraper

### Icons Added
Added 10 new icons to `/home/user/geminivideo/frontend/src/components/icons.tsx`:
- SearchIcon
- FilterIcon
- BookmarkIcon
- ListIcon
- TrendingUpIcon
- GlobeIcon
- CalendarIcon
- RefreshIcon
- TargetIcon

## Features Implemented

### 1. Search & Discovery
- ✅ Advanced search bar for Meta Ads Library queries
- ✅ Multi-country search (US, UK, Canada, Australia, Germany, France, Spain, Italy)
- ✅ Platform filtering (Facebook, Instagram, Audience Network, Messenger)
- ✅ Media type filtering (All, Video, Image)
- ✅ Ad status filtering (All, Active, Inactive)
- ✅ Date range filtering (Last 7/30/90 days, All time, Custom range)

### 2. Ad Display & Viewing
- ✅ Grid and list view modes
- ✅ Ad card with video/image preview
- ✅ Click to view full ad snapshot in new tab
- ✅ Hook extraction and display
- ✅ CTA (Call-to-Action) detection and highlighting
- ✅ Platform badges
- ✅ Engagement metrics (impressions, spend)
- ✅ Active date ranges

### 3. Collection Management
- ✅ Save ads to collection (localStorage)
- ✅ Bookmark toggle with visual feedback
- ✅ Default "Saved Ads" collection
- ✅ Persistent storage across sessions

### 4. One-Click Remix
- ✅ Remix button on each ad card
- ✅ Callback to parent component for integration
- ✅ Extract ad patterns for replication

### 5. Pattern Analysis
- ✅ Analyze button for batch pattern detection
- ✅ Total ads count
- ✅ Average copy length analysis
- ✅ Average active duration
- ✅ Top 10 hooks extraction
- ✅ CTA distribution chart
- ✅ Platform distribution visualization
- ✅ Language usage analysis

### 6. Export Capabilities
- ✅ Export to CSV
- ✅ Includes: Page Name, Ad Text, Dates, Platforms, Metrics
- ✅ Download with timestamp

### 7. Real-time Search
- ✅ Live search with loading states
- ✅ Error handling and user feedback
- ✅ Results count display
- ✅ Empty state messaging

## API Endpoints

### Gateway API (Port 8000)

#### 1. Search Ads
```http
POST /api/meta/ads-library/search
Content-Type: application/json

{
  "search_terms": "weight loss",
  "countries": ["US", "GB"],
  "platforms": ["facebook", "instagram"],
  "media_type": "VIDEO",
  "active_status": "ACTIVE",
  "limit": 100
}
```

**Response:**
```json
[
  {
    "id": "...",
    "ad_archive_id": "...",
    "page_name": "Example Brand",
    "ad_creative_bodies": ["Ad text here..."],
    "impressions": { "lower_bound": 10000, "upper_bound": 50000 },
    "spend": { "lower_bound": 500, "upper_bound": 1000 },
    ...
  }
]
```

#### 2. Get Page Ads
```http
GET /api/meta/ads-library/page/123456789?limit=100&active_only=true
```

#### 3. Analyze Patterns
```http
POST /api/meta/ads-library/analyze
Content-Type: application/json

{
  "ads": [<array of AdLibraryAd objects>]
}
```

**Response:**
```json
{
  "total_ads": 50,
  "common_hooks": [
    ["Amazing transformation in just 30 days", 12],
    ["Don't miss out on this limited offer", 8]
  ],
  "cta_distribution": {
    "learn more": 25,
    "shop now": 15,
    "sign up": 10
  },
  "platform_distribution": {
    "facebook": 30,
    "instagram": 20
  },
  "avg_copy_length_words": 45.3,
  "avg_active_duration_days": 14.2,
  "languages_used": ["en", "es"]
}
```

#### 4. Get Ad Details
```http
GET /api/meta/ads-library/ad/{ad_archive_id}
```

#### 5. Batch Scrape
```http
POST /api/meta/ads-library/batch
Content-Type: application/json

{
  "queries": ["weight loss", "fitness app", "meal prep"],
  "countries": ["US"],
  "limit_per_query": 50
}
```

### Titan Core API (Port 8004)

Same endpoints as above, but directly exposed from Flask server:
- `/meta/ads-library/search` (POST)
- `/meta/ads-library/page/<page_id>` (GET)
- `/meta/ads-library/ad/<ad_archive_id>` (GET)
- `/meta/ads-library/analyze` (POST)
- `/meta/ads-library/batch` (POST)
- `/meta/ads-library/competitor/<page_ids>` (GET)
- `/meta/ads-library/export` (POST)
- `/health` (GET)

## Usage Examples

### React Component Integration

```tsx
import AdSpyDashboard from './components/AdSpyDashboard';

function App() {
  const handleSaveAd = (ad: AdLibraryAd) => {
    console.log('Ad saved:', ad);
    // Sync to backend, analytics, etc.
  };

  const handleRemixAd = (ad: AdLibraryAd) => {
    console.log('Remix ad:', ad);
    // Navigate to creative studio with ad data pre-filled
    // Or trigger AI to generate similar creative
  };

  return (
    <AdSpyDashboard
      onSaveAd={handleSaveAd}
      onRemixAd={handleRemixAd}
    />
  );
}
```

### Programmatic API Usage

```typescript
// Search for competitor ads
const searchAds = async () => {
  const response = await fetch('/api/meta/ads-library/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      search_terms: 'saas product',
      countries: ['US'],
      platforms: ['facebook', 'instagram'],
      media_type: 'VIDEO',
      active_status: 'ACTIVE',
      limit: 50
    })
  });

  const ads = await response.json();
  return ads;
};

// Analyze patterns
const analyzeAds = async (ads) => {
  const response = await fetch('/api/meta/ads-library/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ads })
  });

  const analysis = await response.json();
  return analysis;
};

// Get competitor page ads
const getCompetitorAds = async (pageId) => {
  const response = await fetch(`/api/meta/ads-library/page/${pageId}`);
  const ads = await response.json();
  return ads;
};
```

## Environment Variables

### Required
```bash
META_ACCESS_TOKEN=<your_meta_access_token>
```

### Optional
```bash
# API URLs
VITE_API_URL=http://localhost:8000/api  # Frontend
TITAN_CORE_URL=http://localhost:8004    # Gateway API

# Server Ports
PORT=8004  # Titan Core API port

# Debug Mode
DEBUG=False
```

## Security Features

All endpoints include:
- ✅ Rate limiting (Agent 5)
- ✅ Input validation and sanitization
- ✅ SQL injection protection
- ✅ XSS protection
- ✅ CORS configuration
- ✅ Audit logging
- ✅ Error handling

## Pattern Analysis Algorithms

### Hook Extraction
Extracts first sentence from ad body as hook:
```python
sentences = ad_body.split(/[.!?]/)
hook = sentences[0].trim()
if len(hook) > 10:
    hooks.append(hook)
```

### CTA Detection
Pattern matching against common CTAs:
```python
cta_keywords = [
    'learn more', 'shop now', 'sign up', 'get started', 'download',
    'buy now', 'order now', 'book now', 'subscribe', 'register',
    'try free', 'claim offer', 'get quote', 'contact us', 'apply now'
]
```

### Metrics Calculation
- **Avg Copy Length:** Total words / Total ads
- **Avg Duration:** Sum of (end_date - start_date) / Total ads with end dates
- **Platform Distribution:** Count by platform / Total ads
- **CTA Distribution:** Count by CTA / Total ads

## Data Flow

```
┌─────────────────┐
│   User Input    │
│  (Search term)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  AdSpyDashboard     │
│  (React Component)  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Gateway API       │
│  /api/meta/ads-...  │
│  (Security Layer)   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Titan Core API    │
│ meta_ads_library    │
│      _api.py        │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Ads Library        │
│     Scraper         │
│   (Agent 9)         │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Meta Ads          │
│   Library API       │
│  (Facebook Graph)   │
└─────────────────────┘
```

## File Structure

```
frontend/src/components/
  ├── AdSpyDashboard.tsx          (916 lines, main component)
  └── icons.tsx                   (+10 new icons)

services/gateway-api/src/
  └── index.ts                    (+188 lines, Meta Ads endpoints)

services/titan-core/
  ├── meta_ads_library_api.py     (383 lines, Flask API)
  └── meta/
      └── ads_library_scraper.py  (630 lines, Agent 9)
```

## Testing

### Manual Testing
1. Start Titan Core API:
   ```bash
   cd services/titan-core
   export META_ACCESS_TOKEN=<your_token>
   python meta_ads_library_api.py
   ```

2. Start Gateway API:
   ```bash
   cd services/gateway-api
   export TITAN_CORE_URL=http://localhost:8004
   npm run dev
   ```

3. Start Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

4. Navigate to Ad Spy Dashboard in UI

### API Testing
```bash
# Health check
curl http://localhost:8004/health

# Search ads
curl -X POST http://localhost:8004/meta/ads-library/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": "fitness app",
    "countries": ["US"],
    "limit": 10
  }'
```

## Production Deployment

### Docker Compose
```yaml
titan-core-api:
  build: ./services/titan-core
  ports:
    - "8004:8004"
  environment:
    - META_ACCESS_TOKEN=${META_ACCESS_TOKEN}
    - PORT=8004
  command: python meta_ads_library_api.py

gateway-api:
  build: ./services/gateway-api
  ports:
    - "8000:8000"
  environment:
    - TITAN_CORE_URL=http://titan-core-api:8004
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
  depends_on:
    - titan-core-api
```

### Cloud Run Deployment
```bash
# Build and deploy Titan Core API
gcloud run deploy titan-core-api \
  --source ./services/titan-core \
  --set-env-vars META_ACCESS_TOKEN=${META_ACCESS_TOKEN}

# Build and deploy Gateway API
gcloud run deploy gateway-api \
  --source ./services/gateway-api \
  --set-env-vars TITAN_CORE_URL=https://titan-core-api-xxx.run.app
```

## Integration with Other Agents

### Agent 9: Meta Ads Library Scraper
✅ **Direct Integration** - Uses RealAdsLibraryScraper class

### Agent 16: ROAS Predictor
🔄 **Future Integration** - Predict ROAS for discovered ads

### Agent 25: Campaign Builder
🔄 **Future Integration** - One-click campaign creation from saved ads

### Agent 28: AI Creative Studio
🔄 **Future Integration** - Remix button triggers creative generation

## Metrics & Analytics

The dashboard provides:
- **Search Activity:** Track search terms, frequency
- **Ad Collections:** Monitor saved ads growth
- **Pattern Insights:** Most common hooks, CTAs, platforms
- **Competitive Intelligence:** Competitor ad frequency, spend estimates

## Roadmap

### Phase 1: ✅ Complete (Current)
- [x] Search & filter functionality
- [x] Grid/list views
- [x] Pattern analysis
- [x] Export to CSV
- [x] Real API integration

### Phase 2: 🔄 Planned
- [ ] Competitor page tracking dashboard
- [ ] Trend detection charts (time series)
- [ ] Advanced hook classification (using Agent 17)
- [ ] Visual pattern recognition (using Agent 18)
- [ ] Audio analysis for video ads (using Agent 19)

### Phase 3: 🔄 Planned
- [ ] Automated competitor monitoring
- [ ] Email alerts for new competitor ads
- [ ] AI-powered ad recommendations
- [ ] Integration with Campaign Builder (Agent 25)
- [ ] PDF export with visual previews

## Support & Troubleshooting

### Common Issues

**1. "Meta Ads Library scraper not initialized"**
- Solution: Set `META_ACCESS_TOKEN` environment variable

**2. "Search failed"**
- Check API token permissions
- Verify rate limits not exceeded
- Check network connectivity

**3. Empty results**
- Try broader search terms
- Adjust filters (remove platform/media type filters)
- Check country codes are valid

### Debugging
Enable debug mode:
```bash
export DEBUG=true
python meta_ads_library_api.py
```

Check logs:
```bash
# Titan Core API logs
tail -f /var/log/titan-core-api.log

# Gateway API logs
tail -f /var/log/gateway-api.log
```

## License & Credits

- **Author:** Agent 26/30 Implementation
- **Integration:** Agent 9 (Meta Ads Library Scraper)
- **Security:** Agent 5 (Security Middleware)
- **Database:** Agent 3 (PostgreSQL + Prisma)
- **Caching:** Agent 4 (Redis)

## Related Documentation

- [Agent 9: Meta Ads Library Scraper](/services/titan-core/meta/ads_library_scraper.py)
- [Agent 5: Security Middleware](/services/gateway-api/src/middleware/security.ts)
- [ULTIMATE Production Plan](/ULTIMATE_PRODUCTION_PLAN.md)
- [Meta Ads Library API Docs](https://developers.facebook.com/docs/marketing-api/reference/ads-archive)

---

**Status:** ✅ Production Ready
**Lines of Code:** 1,500+ (Component + API + Integration)
**Test Coverage:** Manual testing complete
**Security:** Agent 5 middleware integrated
**Mock Data:** ZERO - 100% real Meta API integration
