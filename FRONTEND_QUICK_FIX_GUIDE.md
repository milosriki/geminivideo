# FRONTEND QUICK FIX GUIDE
**For Immediate Investor Demo Preparation**

## 🔥 CRITICAL FIXES (Do These First - 4 Hours)

### 1. Remove "TaxPal" Branding (15 mins)
```bash
# Find and replace all TaxPal references
cd /home/user/geminivideo/frontend/src
grep -r "TaxPal" .
# Files to fix:
# - pages/LandingPage.tsx: Lines 13-26, 39-47, 69
```

**Fix**: Replace with "GeminiVideo" or remove LandingPage from demo entirely

---

### 2. Fix Hardcoded Username (10 mins)
**File**: `frontend/src/pages/HomePage.tsx:216`

```tsx
// BEFORE (Line 216):
<Heading level={2} className="text-white">Welcome back, Milos 👋</Heading>

// AFTER:
const { user } = useAuth(); // or useUserStore()
<Heading level={2} className="text-white">Welcome back, {user?.name || 'User'} 👋</Heading>
```

---

### 3. Hide Fake AdSpyPage (5 mins)
**File**: `frontend/src/App.tsx`

```tsx
// Comment out or remove this route:
{/*
<Route path="spy" element={<Suspense fallback={<PageLoader />}><AdSpyPage /></Suspense>} />
*/}
```

Also remove from navigation/sidebar if present.

---

### 4. Fix Login/Register (30 mins)
**File**: `frontend/src/pages/auth/LoginPage.tsx:11-20`

```tsx
// BEFORE:
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  console.log('Login submitted', { email, password })
}

// AFTER:
const { login } = useAuth();
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    await login(email, password);
    navigate('/');
  } catch (error) {
    setError(error.message);
  }
}
```

**Repeat for**: `RegisterPage.tsx:66-80`

---

### 5. Fix Campaign Creation (45 mins)
**File**: `frontend/src/pages/campaigns/CreateCampaignPage.tsx:374`

```tsx
// BEFORE:
const handleNext = () => {
  // TODO: API call to create campaign
  resetWizard()
  navigate('/campaigns')
}

// AFTER:
const createCampaignMutation = useCreateCampaign();
const handleNext = async () => {
  try {
    const campaign = await createCampaignMutation.mutateAsync({
      name: wizardData.name,
      objective: wizardData.objective,
      // ... other fields
    });
    navigate(`/campaigns/${campaign.id}`);
  } catch (error) {
    toast.error('Failed to create campaign');
  }
}
```

---

### 6. Replace Mock HomePage Metrics (1 hour)
**File**: `frontend/src/pages/HomePage.tsx:182-186`

```tsx
// BEFORE:
const metrics = [
  { label: 'Total Spend', value: '$45,230', change: '+12%' },
  { label: 'ROAS', value: '4.2x', change: '+8%' },
  // ... hardcoded data
]

// AFTER:
const { data: overview, isLoading } = useQuery({
  queryKey: ['analytics', 'overview'],
  queryFn: () => apiClient.get('/analytics/overview')
});

const metrics = overview ? [
  { label: 'Total Spend', value: `$${overview.totalSpend}`, change: overview.spendChange },
  { label: 'ROAS', value: `${overview.roas}x`, change: overview.roasChange },
  // ... use real data
] : [];
```

**Backend Required**: Implement `GET /api/analytics/overview`

---

### 7. Fix Recent Jobs & Activity (1 hour)
**File**: `frontend/src/pages/HomePage.tsx:196-212`

```tsx
// BEFORE:
const recentJobs = [/* hardcoded array */];
const recentActivity = [/* hardcoded array */];

// AFTER:
const { data: recentJobs } = useQuery({
  queryKey: ['jobs', 'recent'],
  queryFn: () => apiClient.get('/jobs/recent?limit=5')
});

const { data: recentActivity } = useQuery({
  queryKey: ['activity', 'recent'],
  queryFn: () => apiClient.get('/activity/recent?limit=5')
});
```

**Backend Required**:
- `GET /api/jobs/recent`
- `GET /api/activity/recent`

---

## ⚡ HIGH PRIORITY FIXES (Next 8 Hours)

### 8. Add Missing Analytics Endpoints (Backend - 3 hours)

**Create**: `backend/src/routes/analytics.ts`

```typescript
// Minimum viable analytics endpoints
router.get('/analytics/overview', async (req, res) => {
  // Aggregate campaign metrics
  const overview = await getAnalyticsOverview(req.user.id);
  res.json(overview);
});

router.get('/analytics/chart', async (req, res) => {
  const { range } = req.query;
  const chartData = await getChartData(req.user.id, range);
  res.json({ chart: chartData });
});

router.get('/kpis', async (req, res) => {
  const kpis = await getKPIs(req.user.id, req.query.range);
  res.json({ kpis });
});

// Add stub endpoints for other missing routes
router.get('/analytics/trends', (req, res) => res.json([]));
router.get('/analytics/funnel', (req, res) => res.json([]));
router.get('/analytics/creatives', (req, res) => res.json([]));
```

---

### 9. Fix Studio Generate Button (1 hour)
**File**: `frontend/src/pages/studio/StudioPage.tsx:158`

**Current**: Calls `/api/generate` ✅

**Verify**: Backend endpoint exists and returns job_id

**If missing**, create stub:
```typescript
// backend/src/routes/video.ts
router.post('/generate', async (req, res) => {
  const { assets, target_audience } = req.body;
  const jobId = await enqueueVideoJob({
    userId: req.user.id,
    assets,
    targetAudience: target_audience
  });
  res.json({ job_id: jobId, status: 'queued' });
});
```

---

### 10. Fix Broken onClick Handlers (2 hours)

**Quick fix for all broken buttons**:

```tsx
// Pattern 1: Simple navigation
<Button onClick={() => navigate('/destination')}>Click Me</Button>

// Pattern 2: With toast notification
<Button onClick={() => {
  toast.info('Feature coming soon');
}}>Feature</Button>

// Pattern 3: Disable for demo
<Button disabled title="Available post-demo">Premium Feature</Button>
```

**Files to update**:
- `HomePage.tsx`: Lines 278, 292, 328, 332
- `AnalyticsPage.tsx`: Lines 221, 360
- `StudioPage.tsx`: Lines 202, 258, 313, 416
- `AdSpyPage.tsx`: Lines 137, 145, 172, 198
- `SettingsPage.tsx`: Lines 96, 129, 130, 138, 152

---

### 11. Fix Pagination (30 mins)

**Pattern for all pages**:

```tsx
const [currentPage, setCurrentPage] = useState(1);
const totalPages = Math.ceil(totalItems / itemsPerPage);

<Pagination>
  <PaginationPrevious
    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
    disabled={currentPage === 1}
  />
  <PaginationList>
    {Array.from({ length: totalPages }).map((_, i) => (
      <PaginationPage
        key={i}
        onClick={() => setCurrentPage(i + 1)}
        current={currentPage === i + 1}
      >
        {i + 1}
      </PaginationPage>
    ))}
  </PaginationList>
  <PaginationNext
    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
    disabled={currentPage === totalPages}
  />
</Pagination>
```

**Apply to**:
- `AnalyticsPage.tsx:407`
- `AssetsPage.tsx:190`

---

### 12. Fix React Hooks Violation (15 mins)
**File**: `frontend/src/hooks/usePublishing.ts:174-176`

```tsx
// BEFORE:
const statusQueries = (activeJobs || []).map((job) =>
  usePublishStatus(job.jobId)  // ❌ WRONG
);

// AFTER:
// Option 1: Pre-fetch all job IDs
const jobIds = activeJobs?.map(j => j.jobId) || [];
const statusQueries = jobIds.map(id =>
  useQuery({
    queryKey: ['publishStatus', id],
    queryFn: () => apiClient.getPublishStatus(id),
    enabled: !!id
  })
);

// Option 2: Remove dynamic hooks, fetch in single query
const { data: allStatuses } = useQuery({
  queryKey: ['publishStatuses', jobIds],
  queryFn: () => apiClient.getBatchPublishStatuses(jobIds),
  enabled: jobIds.length > 0
});
```

---

## 🛠 MEDIUM PRIORITY (Post-Core Fixes)

### 13. Verify Component Imports (1 hour)

**Check if these exist** (use Glob tool):
```bash
frontend/src/layouts/DashboardLayout.tsx
frontend/src/components/catalyst/empty-state.tsx
frontend/src/components/compass/video-player.tsx
frontend/src/components/compass/video-card.tsx
frontend/src/components/onboarding/*.tsx
frontend/src/components/predictions/index.ts
frontend/src/types/index.ts
```

**If missing**, create minimal stubs or fix imports.

---

### 14. Add Error Boundaries (30 mins)

**File**: `frontend/src/App.tsx:123` (already has ErrorBoundary ✅)

**Add to problematic pages**:
```tsx
<ErrorBoundary fallback={<ErrorFallback />}>
  <AnalyticsDashboard />
</ErrorBoundary>
```

---

### 15. Add Loading States (30 mins)

**Pattern**:
```tsx
if (isLoading) return <LoadingSpinner />;
if (isError) return <ErrorMessage error={error} />;
if (!data) return <EmptyState />;

return <ActualContent data={data} />;
```

**Apply everywhere**: HomePage, AnalyticsPage, CampaignsPage, AssetsPage

---

## 📋 PRE-DEMO CHECKLIST

### Visual Inspection (15 mins before demo):
- [ ] No "TaxPal" visible on any page
- [ ] No "Milos" hardcoded (should show actual logged-in user)
- [ ] No console errors on page load
- [ ] All navigation links work (or are hidden)
- [ ] Login/register works
- [ ] Can create a campaign
- [ ] Analytics page loads without 404s
- [ ] Studio page can generate a video

### Backend Health Check (10 mins before demo):
- [ ] `GET /api/analytics/overview` returns data
- [ ] `GET /api/analytics/chart` returns data
- [ ] `GET /api/kpis` returns data
- [ ] `POST /api/generate` returns job_id
- [ ] `GET /api/jobs/recent` returns jobs
- [ ] Auth endpoints work

### Fallback Strategy:
**If time runs out**, disable broken features:
```tsx
// Hide from navigation
const DEMO_HIDDEN_ROUTES = ['spy', 'projects', 'settings'];

// Or show "Coming Soon" banner
{!isFeatureReady && <ComingSoonBanner />}
```

---

## 🚀 DEPLOYMENT NOTES

**Environment Variables Required**:
```env
VITE_API_BASE_URL=https://api.geminivideo.com
VITE_FIREBASE_API_KEY=...
VITE_ENABLE_DEMO_MODE=true
```

**Demo Mode Features**:
- Auto-login with demo account
- Hide unfinished features
- Show sample data if API fails
- Disable destructive actions

---

## 📞 EMERGENCY CONTACTS

**If stuck, escalate to**:
- Backend Team: Fix missing API endpoints
- DevOps: Deployment issues
- Design: Replace placeholder content

**Last Resort**:
- Switch to pre-recorded demo video
- Use staging environment with mock data
- Present slides instead of live demo

---

**Good luck with the €5M investor demo! 🚀**
