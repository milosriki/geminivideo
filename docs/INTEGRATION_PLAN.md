# AdIntel OS - Integration & Testing Plan

> **Status**: Ready for Integration | **Est. Time**: 2-3 hours
> **Last Updated**: Dec 2024

## Quick Start Summary

```bash
# 1. Setup environment (5 min)
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# 2. Start infrastructure (2 min)
docker-compose up -d postgres redis typesense

# 3. Build & start AdIntel services (3 min)
docker-compose build intel-api intel-worker
docker-compose up -d intel-api intel-worker

# 4. Initialize database (1 min)
docker-compose exec intel-api python -c "from intel.orchestrator import AdIntelOrchestrator; import asyncio; asyncio.run(AdIntelOrchestrator().initialize())"

# 5. Verify (2 min)
curl http://localhost:8090/api/v1/health
curl http://localhost:8080/api/intel/winners
curl http://localhost:3000/discovery
```

---

## Prerequisites Checklist

Before starting integration, verify these items:

### Infrastructure
- [ ] Docker and Docker Compose installed (`docker --version`)
- [ ] Ports available: 5432, 6379, 8108, 8090, 8080, 3000
- [ ] Minimum 4GB RAM available (`docker stats`)
- [ ] At least 10GB disk space

### API Keys & Credentials
- [ ] Gemini API key obtained (https://makersuite.google.com/app/apikey)
- [ ] Meta credentials (optional, for production scraping)
  - [ ] META_APP_ID
  - [ ] META_ACCESS_TOKEN
  - [ ] META_AD_ACCOUNT_ID

### Code Verification
```bash
# Verify all required files exist
ls -la /home/user/geminivideo/services/intel/orchestrator.py
ls -la /home/user/geminivideo/services/intel/ad_library_scraper.py
ls -la /home/user/geminivideo/services/intel/ad_enrichment.py
ls -la /home/user/geminivideo/services/intel/search_engine.py
ls -la /home/user/geminivideo/services/intel/adintel_api.py
ls -la /home/user/geminivideo/frontend/src/components/DiscoveryDashboard.tsx
```

**Expected**: All files should exist (5 Python files, 1 TypeScript file)

---

## Phase 1: Infrastructure Setup (30 minutes)

### Step 1.1: Environment Configuration (5 min)

```bash
# Create .env from example
cd /home/user/geminivideo
cp .env.example .env
```

**Then edit .env and set**:
```bash
# Required
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Database (already configured in docker-compose)
DATABASE_URL=postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
REDIS_URL=redis://redis:6379

# Typesense
TYPESENSE_HOST=typesense
TYPESENSE_PORT=8108
TYPESENSE_API_KEY=adintel-key-change-in-prod

# Optional (for production)
META_ACCESS_TOKEN=your_meta_token_if_available
```

**Verify**:
```bash
grep "GEMINI_API_KEY" .env | grep -v "your_gemini_api_key"
```
**Expected**: Should show your actual API key, not placeholder

### Step 1.2: Start Core Infrastructure (10 min)

```bash
# Start PostgreSQL, Redis, Typesense
docker-compose up -d postgres redis typesense

# Wait for services to be healthy (30-60 seconds)
docker-compose ps postgres redis typesense
```

**Expected Output**:
```
NAME                      STATUS              PORTS
geminivideo-postgres      Up (healthy)        0.0.0.0:5432->5432/tcp
geminivideo-redis         Up (healthy)        0.0.0.0:6379->6379/tcp
geminivideo-typesense     Up (healthy)        0.0.0.0:8108->8108/tcp
```

**Verify Each Service**:
```bash
# PostgreSQL
docker-compose exec postgres psql -U geminivideo -d geminivideo -c "SELECT NOW();"

# Redis
docker-compose exec redis redis-cli ping

# Typesense
curl http://localhost:8108/health
```

**Expected**:
- PostgreSQL: Shows current timestamp
- Redis: Returns "PONG"
- Typesense: `{"ok":true}`

**If Fails**:
- PostgreSQL timeout: `docker-compose restart postgres && sleep 10`
- Redis not responding: `docker-compose logs redis` (check for errors)
- Typesense 404: `docker-compose logs typesense` (check startup)

### Step 1.3: Build AdIntel Services (10 min)

```bash
# Build intel services
docker-compose build intel-api intel-worker

# Check build success
docker images | grep geminivideo-intel
```

**Expected Output**:
```
geminivideo-intel-api        latest    <image-id>   X seconds ago   XXX MB
geminivideo-intel-worker     latest    <image-id>   X seconds ago   XXX MB
```

**If Build Fails**:

**Error: "playwright install failed"**
```bash
# Check Dockerfile
cat services/intel/Dockerfile | grep playwright
```
Solution: Ensure `RUN playwright install chromium --with-deps` is present

**Error: "requirements.txt not found"**
```bash
# Verify requirements file exists
ls -la services/intel/requirements.txt
```
Solution: File must exist in services/intel/

### Step 1.4: Initialize Database Schema (5 min)

```bash
# Start intel-api temporarily to initialize schema
docker-compose run --rm intel-api python -c "
import asyncio
from intel.orchestrator import AdIntelOrchestrator

async def init():
    orch = AdIntelOrchestrator()
    await orch.initialize()
    print('✅ Database schema initialized')
    await orch.shutdown()

asyncio.run(init())
"
```

**Expected Output**:
```
🚀 Initializing AdIntel Orchestrator...
✅ PostgreSQL connected
✅ Redis connected
✅ Typesense initialized
✅ Scraper ready
✅ Enrichment pipeline ready
🎉 AdIntel Orchestrator fully initialized!
✅ Database schema initialized
```

**Verify Schema Created**:
```bash
docker-compose exec postgres psql -U geminivideo -d geminivideo -c "\dt adintel*"
```

**Expected**:
```
             List of relations
 Schema |        Name         | Type  |   Owner
--------+---------------------+-------+------------
 public | adintel_ads         | table | geminivideo
 public | adintel_brands      | table | geminivideo
 public | adintel_collections | table | geminivideo
```

**If Fails**:
- Tables not created: Check orchestrator.py SCHEMA_SQL is correct
- Connection refused: Ensure postgres is healthy (`docker-compose ps postgres`)

---

## Phase 2: Backend Services (1 hour)

### Step 2.1: Start Intel Services (5 min)

```bash
# Start intel-api and intel-worker
docker-compose up -d intel-api intel-worker

# Wait for services to start (30 seconds)
sleep 30

# Check status
docker-compose ps intel-api intel-worker
```

**Expected**:
```
NAME                      STATUS              PORTS
geminivideo-intel-api     Up (healthy)        0.0.0.0:8090->8090/tcp
geminivideo-intel-worker  Up                  (no ports)
```

**Check Logs**:
```bash
# Intel API logs
docker-compose logs intel-api | tail -20

# Worker logs
docker-compose logs intel-worker | tail -20
```

**Expected in Logs**:
- API: "Application startup complete" or "Uvicorn running on http://0.0.0.0:8090"
- Worker: "🏃 Scrape worker started" and "🏃 Enrich worker started"

### Step 2.2: Health Check APIs (5 min)

```bash
# Test intel-api health
curl http://localhost:8090/api/v1/health

# Test gateway proxy
curl http://localhost:8080/api/intel/winners

# Test search engine stats
curl http://localhost:8090/api/v1/stats
```

**Expected Responses**:

**Intel API Health** (`/api/v1/health`):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-12-06T12:00:00"
}
```

**Gateway Proxy** (`/api/intel/winners`):
```json
{
  "winners": [],
  "total": 0,
  "remaining_credits": 10000
}
```
(Empty is OK - no data yet)

**Stats** (`/api/v1/stats`):
```json
{
  "total_ads_indexed": 0,
  "tracked_brands": 0,
  "active_scrapers": 1
}
```

**If Fails**:
- 502/503 errors: Intel-api not ready. Check `docker-compose logs intel-api`
- Connection refused: Check port 8090 is not blocked (`netstat -tlnp | grep 8090`)
- Typesense errors: Verify typesense health (`curl localhost:8108/health`)

### Step 2.3: Test Brand Tracking (10 min)

```bash
# Track a test brand (Nike)
curl -X POST http://localhost:8090/api/v1/spyder/track \
  -H "Authorization: Bearer test-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_name": "Nike",
    "platforms": ["meta"],
    "check_interval_hours": 24
  }'
```

**Expected Response**:
```json
{
  "brand_id": "abc123...",
  "brand_name": "Nike",
  "status": "tracking_started",
  "next_check": "2024-12-06T13:00:00"
}
```

**Verify in Database**:
```bash
docker-compose exec postgres psql -U geminivideo -d geminivideo -c \
  "SELECT brand_id, brand_name, is_tracked FROM adintel_brands;"
```

**Expected**:
```
  brand_id   | brand_name | is_tracked
-------------+------------+------------
 abc123...   | Nike       | t
```

**Check Worker Picked Up Job**:
```bash
# Check Redis queue
docker-compose exec redis redis-cli LLEN adintel:queue:scrape
```
**Expected**: 1 (one job queued)

**If Fails**:
- "Insufficient credits": Normal, credit system is in-memory for dev
- Job not queued: Check worker logs for errors
- Brand not saved: Check PostgreSQL connection

### Step 2.4: Test Search API (10 min)

```bash
# Search all ads
curl -X POST http://localhost:8090/api/v1/discovery/search \
  -H "Authorization: Bearer test-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "*",
    "page": 1,
    "per_page": 20
  }'
```

**Expected Response** (empty database):
```json
{
  "hits": [],
  "total": 0,
  "page": 1,
  "per_page": 20,
  "facets": {},
  "credits_used": 1,
  "remaining_credits": 9999
}
```

**Test with Filters**:
```bash
curl -X POST http://localhost:8090/api/v1/discovery/search \
  -H "Authorization: Bearer test-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fitness",
    "industry": "health",
    "winners_only": true,
    "page": 1,
    "per_page": 10
  }'
```

**Verify Typesense Collection**:
```bash
curl -H "X-TYPESENSE-API-KEY: adintel-key-change-in-prod" \
  http://localhost:8108/collections/ads
```

**Expected**: Collection schema or 404 if not created yet (normal for empty DB)

### Step 2.5: Test Gateway Proxy Routes (5 min)

```bash
# Test all gateway proxy routes

# 1. Search
curl -X POST http://localhost:8080/api/intel/search \
  -H "Content-Type: application/json" \
  -d '{"query": "*", "per_page": 10}'

# 2. Winners
curl http://localhost:8080/api/intel/winners

# 3. Track brand
curl -X POST http://localhost:8080/api/intel/track-brand \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "TestBrand"}'

# 4. Trends
curl http://localhost:8080/api/intel/trends
```

**Expected**: All should return JSON responses (may be empty data)

**If Fails**:
- 404 errors: Gateway routes not wired. Check `services/gateway-api/src/index.ts` lines 2272-2343
- 500 errors: Intel service down. Check `docker-compose ps intel-api`

### Step 2.6: Test Enrichment Pipeline (15 min)

**Note**: This requires a real video URL. For testing, we'll use a placeholder.

```bash
# Test enrichment (will fail without real video, but tests the pipeline)
curl -X POST http://localhost:8090/api/v1/enrich \
  -H "Authorization: Bearer test-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ad_id": "test-ad-123",
    "video_url": "https://example.com/test.mp4",
    "force_refresh": false
  }'
```

**Expected Response** (may error without GEMINI_API_KEY):
```json
{
  "error": "Gemini API key not configured"
}
```
OR (if key configured):
```json
{
  "ad_id": "test-ad-123",
  "transcription": null,
  "winner_score": 0,
  "credits_used": 5
}
```

**Verify Gemini Configuration**:
```bash
docker-compose exec intel-api python -c "
import os
key = os.getenv('GEMINI_API_KEY', '')
print(f'Gemini API Key: {key[:10]}...' if key else 'NOT SET')
"
```

---

## Phase 3: Frontend Integration (30 minutes)

### Step 3.1: Start Gateway & Frontend (5 min)

```bash
# Start gateway if not running
docker-compose up -d gateway-api

# Start frontend
docker-compose up -d frontend

# Wait for startup
sleep 30

# Check status
docker-compose ps gateway-api frontend
```

**Expected**:
```
NAME                      STATUS              PORTS
geminivideo-gateway-api   Up (healthy)        0.0.0.0:8080->8080/tcp
geminivideo-frontend      Up (healthy)        0.0.0.0:3000->80/tcp
```

### Step 3.2: Verify Frontend Routes (5 min)

```bash
# Test frontend is serving
curl -I http://localhost:3000

# Test discovery route (should return HTML)
curl http://localhost:3000/discovery | head -20
```

**Expected**:
- Status: 200 OK
- Content-Type: text/html
- HTML contains "AdIntel" or "Discovery"

**Open in Browser**:
```
http://localhost:3000/discovery
```

**Expected UI Elements**:
- [ ] Three tabs: Discovery, Brand Tracker, Trends
- [ ] Search bar with filters
- [ ] Empty state message ("No ads found")
- [ ] Filter sidebar (Industry, Emotion, Hook Type)

### Step 3.3: Test Frontend API Integration (10 min)

**Open Browser DevTools (F12) → Network Tab**

**Test 1: Search Functionality**
1. Go to http://localhost:3000/discovery
2. Type "fitness" in search bar
3. Click "Search"

**Expected Network Requests**:
```
POST http://localhost:8080/api/intel/search
Status: 200
Response: {"hits": [], "total": 0, ...}
```

**Test 2: Winners Tab**
1. Click "Winners" filter checkbox
2. Click "Search"

**Expected Network Request**:
```
POST http://localhost:8080/api/intel/search
Payload: {"winners_only": true, ...}
```

**Test 3: Brand Tracker**
1. Click "Brand Tracker" tab
2. Enter "Nike" in brand input
3. Click "Start Tracking"

**Expected Network Request**:
```
POST http://localhost:8080/api/intel/track-brand
Payload: {"brand_name": "Nike"}
Status: 200
```

**Test 4: Trends Tab**
1. Click "Trends" tab

**Expected Network Request**:
```
GET http://localhost:8080/api/intel/trends
Status: 200
Response: {"by_industry": [], "by_emotion": [], ...}
```

**If Frontend Tests Fail**:
- CORS errors: Check gateway CORS config in `services/gateway-api/src/index.ts`
- 404 errors: Routes not wired. Verify lines 2272-2343 in gateway
- Network errors: Gateway not running or wrong port

### Step 3.4: Check React Hook Integration (5 min)

**Open Browser Console**

```javascript
// Test if useAdIntel hook is loaded
console.log(window.__REACT_DEVTOOLS_GLOBAL_HOOK__)
```

**In React DevTools**:
1. Open Components tab
2. Find `<DiscoveryDashboard>`
3. Check hooks: `useAdIntel`, `useState`, `useEffect`

**Expected Hook State**:
```javascript
{
  loading: false,
  error: null,
  results: null,
  trends: null,
  trackedBrands: []
}
```

**If Hook Fails**:
- Check `/home/user/geminivideo/frontend/src/hooks/useAdIntel.ts` exists
- Verify import in DiscoveryDashboard.tsx
- Check browser console for errors

---

## Minimal End-to-End Test

**This is the SIMPLEST test to verify the entire stack works:**

### 1. Track a Brand & Search (3 minutes)

```bash
# 1. Track Nike
curl -X POST http://localhost:8080/api/intel/track-brand \
  -H "Content-Type: application/json" \
  -d '{"brand_name": "Nike"}' | jq

# 2. Check it was tracked
curl http://localhost:8090/api/v1/spyder/brands | jq

# 3. Search for ads (will be empty until scraper runs)
curl -X POST http://localhost:8080/api/intel/search \
  -H "Content-Type: application/json" \
  -d '{"query": "*"}' | jq
```

**Expected**:
- Step 1: `{"brand_id": "...", "status": "tracking_started"}`
- Step 2: `{"brands": [{"brand_name": "Nike", ...}]}`
- Step 3: `{"hits": [], "total": 0}` (empty until scraper completes)

### 2. Frontend Test (2 minutes)

```
1. Open: http://localhost:3000/discovery
2. Click "Brand Tracker" tab
3. See "Nike" in tracked brands list
4. Click "Trends" tab
5. See empty charts (normal - no data yet)
```

**Pass Criteria**: All steps complete without errors

---

## Validation Commands

### Quick Health Check (30 seconds)

```bash
# All-in-one health check
docker-compose ps | grep -E "intel-api|intel-worker|typesense|postgres|redis"
curl -s http://localhost:8090/api/v1/health | jq
curl -s http://localhost:8080/api/intel/winners | jq
curl -s http://localhost:3000 -I | grep "200 OK"
```

**Expected**: All services "Up", all curls return valid JSON/200 OK

### Database Verification

```bash
# Check all AdIntel tables exist
docker-compose exec postgres psql -U geminivideo -d geminivideo -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_name LIKE 'adintel%';
"
```

**Expected**:
```
    table_name
--------------------
 adintel_ads
 adintel_brands
 adintel_collections
```

### Typesense Verification

```bash
# Check collections
curl -H "X-TYPESENSE-API-KEY: adintel-key-change-in-prod" \
  http://localhost:8108/collections | jq
```

**Expected**: Empty array `[]` or ads collection if created

### Redis Queue Verification

```bash
# Check queue lengths
docker-compose exec redis redis-cli LLEN adintel:queue:scrape
docker-compose exec redis redis-cli LLEN adintel:queue:enrich
```

**Expected**: Numbers (could be 0 if queue is empty)

### API Route Verification

```bash
# Test all API routes return 200 or valid responses
for route in health winners trends; do
  echo "Testing /api/v1/${route}..."
  curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:8090/api/v1/${route} || \
    http://localhost:8090/api/v1/discovery/${route}
  echo
done
```

**Expected**: All 200 or 401 (auth required, but route exists)

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| **intel-api won't start** | Missing dependencies | `docker-compose logs intel-api` → Check for import errors. Rebuild: `docker-compose build intel-api` |
| **Database connection refused** | PostgreSQL not ready | `docker-compose restart postgres && sleep 10`, then try again |
| **Typesense 404 errors** | Service not initialized | `curl localhost:8108/health` - Should return `{"ok":true}`. Restart: `docker-compose restart typesense` |
| **"Gemini API key not configured"** | Missing env var | Check `.env` has `GEMINI_API_KEY=your_key`. Restart services: `docker-compose restart intel-api intel-worker` |
| **Worker not processing jobs** | Redis connection issue | `docker-compose logs intel-worker` - Look for Redis errors. Check: `docker-compose exec redis redis-cli ping` |
| **Frontend shows CORS error** | Gateway CORS misconfigured | Check `services/gateway-api/src/index.ts` line 39-48. Should allow `http://localhost:3000` |
| **Scraper fails to run** | Playwright not installed | Check Dockerfile has `RUN playwright install chromium --with-deps`. Rebuild intel services |
| **Search returns 500 error** | Typesense not running | `docker-compose ps typesense` should be "Up (healthy)". Restart if needed |
| **Gateway proxy 502** | Intel-api down or wrong URL | Check `INTEL_API_URL` env var in gateway. Should be `http://intel-api:8090` (Docker network) |
| **Frontend 404 on /discovery** | Route not configured | Check frontend routing. May need `/#/discovery` instead. Check React Router config |

---

## Common Failure Scenarios & Solutions

### Scenario 1: "Cannot connect to Docker daemon"

```bash
# Check Docker is running
sudo systemctl status docker

# Start Docker
sudo systemctl start docker
```

### Scenario 2: "Port 8090 already in use"

```bash
# Find process using port
sudo lsof -i :8090

# Kill process (replace PID)
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

### Scenario 3: "intel-api unhealthy"

```bash
# Check logs
docker-compose logs intel-api --tail=50

# Common issues:
# - Missing dependencies → Rebuild
# - Database not ready → Wait 30s and restart
# - Typesense down → Start typesense first
```

### Scenario 4: "Worker not processing jobs"

```bash
# Check worker logs
docker-compose logs intel-worker --tail=50

# Verify Redis queue
docker-compose exec redis redis-cli LLEN adintel:queue:scrape

# If queue has items but worker isn't processing:
docker-compose restart intel-worker
```

### Scenario 5: "Frontend can't reach backend"

```bash
# Check gateway is up
docker-compose ps gateway-api

# Test proxy directly
curl http://localhost:8080/api/intel/health

# Check browser console for CORS errors
# If CORS error: Restart gateway-api
docker-compose restart gateway-api
```

---

## Future Integration Points

### Adding New Scrapers

**Location**: `/home/user/geminivideo/services/intel/`

1. Create new scraper class in `ad_library_scraper.py`:
```python
class TikTokScraper:
    async def scrape_by_advertiser(self, brand_name: str):
        # Implementation
        pass
```

2. Add to orchestrator.py:
```python
self.tiktok_scraper = TikTokScraper()
```

3. Update API endpoint in `adintel_api.py`:
```python
@app.post("/api/v1/spyder/track")
async def track_brand(request: BrandTrackRequest):
    platforms = request.platforms  # ['meta', 'tiktok']
    # Route to appropriate scraper
```

### Adding New AI Models

**Location**: `/home/user/geminivideo/services/intel/ad_enrichment.py`

1. Create new analyzer class:
```python
class Claude4Analyzer:
    async def analyze(self, video_data):
        # Claude API call
        pass
```

2. Update EnrichmentPipeline:
```python
self.claude_analyzer = Claude4Analyzer()
enriched.claude_analysis = await self.claude_analyzer.analyze(video)
```

3. Update database schema in `orchestrator.py`:
```sql
ALTER TABLE adintel_ads ADD COLUMN claude_insights JSONB;
```

### Adding New UI Features

**Location**: `/home/user/geminivideo/frontend/src/components/DiscoveryDashboard.tsx`

**Example: Add "Collections" Feature**

1. Add new tab:
```typescript
const tabs = [
  { id: 'discovery', ... },
  { id: 'spyder', ... },
  { id: 'trends', ... },
  { id: 'collections', label: 'My Collections', icon: BookmarkIcon }
];
```

2. Add state:
```typescript
const [collections, setCollections] = useState([]);
```

3. Add API hook method in `useAdIntel.ts`:
```typescript
const createCollection = async (name: string, adIds: string[]) => {
  const res = await axios.post('/api/intel/collections', { name, adIds });
  return res.data;
};
```

4. Add backend endpoint in `adintel_api.py`:
```python
@app.post("/api/v1/collections")
async def create_collection(request: CollectionRequest):
    # Save to adintel_collections table
    pass
```

---

## Performance Benchmarks

**Expected Performance** (after full integration):

| Operation | Target Time | Acceptable Range |
|-----------|-------------|------------------|
| Startup (all services) | 60 seconds | 30-120 seconds |
| Database init | 5 seconds | 2-10 seconds |
| API health check | < 100ms | 50-200ms |
| Search query (empty DB) | < 500ms | 200-1000ms |
| Search query (10K ads) | < 2 seconds | 1-5 seconds |
| Brand tracking (queue job) | < 1 second | 500ms-2s |
| Scrape 50 ads | 30-60 seconds | 20s-2min |
| Enrich 1 ad (Gemini) | 3-10 seconds | 2-15s |
| Frontend page load | < 2 seconds | 1-5 seconds |

**Monitoring Commands**:
```bash
# Check API response time
time curl http://localhost:8090/api/v1/health

# Check search performance
time curl -X POST http://localhost:8080/api/intel/search \
  -H "Content-Type: application/json" \
  -d '{"query": "*"}'

# Monitor Docker resource usage
docker stats --no-stream
```

---

## Production Readiness Checklist

**Before deploying to production**:

### Security
- [ ] Change Typesense API key from default
- [ ] Add real authentication (replace test-api-key)
- [ ] Enable HTTPS for all services
- [ ] Add rate limiting to API endpoints
- [ ] Encrypt sensitive data in database

### Scaling
- [ ] Add Redis persistence for job queues
- [ ] Configure PostgreSQL connection pooling
- [ ] Add multiple worker instances
- [ ] Set up Typesense cluster (3+ nodes)
- [ ] Configure CDN for frontend assets

### Monitoring
- [ ] Add Sentry for error tracking
- [ ] Set up Prometheus metrics
- [ ] Configure logging to centralized service
- [ ] Add uptime monitoring (Pingdom, etc.)
- [ ] Set up alerting for failures

### Data
- [ ] Seed database with sample ads
- [ ] Set up automated backups
- [ ] Configure data retention policies
- [ ] Add data validation rules
- [ ] Set up ETL for analytics

### Testing
- [ ] Write integration tests
- [ ] Add E2E tests with Playwright
- [ ] Performance load testing
- [ ] Security penetration testing
- [ ] User acceptance testing

---

## Success Criteria

**Integration is COMPLETE when all these pass**:

### Infrastructure (15/15 points)
- [ ] All 5 core services running (postgres, redis, typesense, intel-api, intel-worker)
- [ ] All health checks return 200 OK
- [ ] Database schema created with 3 tables
- [ ] Typesense accepting requests
- [ ] Redis queues operational

### Backend API (20/20 points)
- [ ] `/api/v1/health` returns healthy status
- [ ] `/api/v1/discovery/search` returns search results
- [ ] `/api/v1/discovery/winners` returns winners
- [ ] `/api/v1/spyder/track` accepts brand tracking
- [ ] `/api/v1/analytics/trends` returns trends data
- [ ] Gateway proxy routes working
- [ ] Credit system tracking usage
- [ ] Worker processing jobs from queue

### Frontend (15/15 points)
- [ ] Discovery tab renders without errors
- [ ] Brand Tracker tab renders
- [ ] Trends tab renders
- [ ] Search functionality works
- [ ] Brand tracking button works
- [ ] API calls succeed from frontend
- [ ] Error states display correctly

### End-to-End (10/10 points)
- [ ] Can track a brand via UI
- [ ] Can search ads via UI
- [ ] Can view trends via UI
- [ ] Data flows: UI → Gateway → Intel API → Database
- [ ] Real-time updates work (if implemented)

**Total Score**: 60/60 = **PRODUCTION READY** ✅

---

## Next Steps After Integration

1. **Seed Sample Data**
   - Run scraper for 5-10 popular brands
   - Import sample ads from JSON
   - Generate test analytics data

2. **Performance Testing**
   - Load test with 10,000+ ads
   - Stress test search with concurrent users
   - Benchmark enrichment pipeline

3. **User Testing**
   - Internal team testing
   - Beta user feedback
   - UI/UX improvements

4. **Documentation**
   - API documentation (Swagger/OpenAPI)
   - User guide for Discovery Dashboard
   - Developer onboarding guide

5. **Production Deployment**
   - Set up staging environment
   - Configure CI/CD pipeline
   - Deploy to production infrastructure

---

## Support & Resources

- **Architecture Doc**: `/home/user/geminivideo/docs/ADINTEL_ARCHITECTURE.md`
- **Docker Compose**: `/home/user/geminivideo/docker-compose.yml`
- **Backend Code**: `/home/user/geminivideo/services/intel/`
- **Frontend Code**: `/home/user/geminivideo/frontend/src/components/DiscoveryDashboard.tsx`
- **Gateway Routes**: `/home/user/geminivideo/services/gateway-api/src/index.ts` (lines 2272-2343)

**For Issues**:
1. Check logs: `docker-compose logs <service-name>`
2. Review troubleshooting guide above
3. Verify prerequisites checklist
4. Check common failure scenarios

---

**Created by**: Agent 5 (Integration Planner)
**Last Updated**: December 6, 2024
**Version**: 1.0
