# Frontend Testing Guide

## Overview
Guide for testing the newly implemented frontend infrastructure with React Query hooks.

## Manual Testing Checklist

### 1. Campaign Management

#### Create Campaign Flow
- [ ] Navigate to `/campaigns/create`
- [ ] Fill out campaign form
- [ ] Verify loading spinner shows during creation
- [ ] Verify success toast appears
- [ ] Verify redirect to campaigns list
- [ ] Verify new campaign appears in list

#### List Campaigns
- [ ] Navigate to `/campaigns`
- [ ] Verify loading spinner on initial load
- [ ] Verify campaigns are displayed
- [ ] Verify empty state shows when no campaigns
- [ ] Click on campaign to view details
- [ ] Verify campaign detail modal opens

#### Update Campaign
- [ ] Open campaign detail modal
- [ ] Click "Edit Campaign"
- [ ] Make changes
- [ ] Verify loading state on save
- [ ] Verify success toast
- [ ] Verify changes reflected immediately (optimistic update)

#### Delete Campaign
- [ ] Click "Delete" on a campaign
- [ ] Verify confirmation dialog appears
- [ ] Confirm deletion
- [ ] Verify loading state on button
- [ ] Verify success toast
- [ ] Verify campaign removed from list immediately

#### Pause/Resume Campaign
- [ ] Click "Pause" on active campaign
- [ ] Verify loading state
- [ ] Verify status changes to "paused"
- [ ] Verify success toast
- [ ] Click "Resume"
- [ ] Verify status changes back to "active"

#### Launch Campaign
- [ ] Create draft campaign
- [ ] Click "Launch"
- [ ] Verify confirmation dialog
- [ ] Confirm launch
- [ ] Verify loading state
- [ ] Verify success toast
- [ ] Verify status changes to "active"

### 2. Analytics Dashboard

#### Overview Metrics
- [ ] Navigate to analytics page
- [ ] Verify loading spinner on initial load
- [ ] Verify all metric cards display data
- [ ] Verify numbers are formatted correctly
- [ ] Verify trend indicators show
- [ ] Click "Refresh" button
- [ ] Verify data refreshes

#### Time Range Selection
- [ ] Change time range to "Last 7 days"
- [ ] Verify data updates
- [ ] Change to "Last 90 days"
- [ ] Verify data updates
- [ ] Verify loading state during fetch

#### Campaign Analytics
- [ ] Select a specific campaign
- [ ] Verify campaign-specific metrics load
- [ ] Verify charts display correctly
- [ ] Verify data matches campaign

### 3. A/B Testing

#### Create A/B Test
- [ ] Navigate to A/B tests page
- [ ] Click "Create Test"
- [ ] Fill out test form
- [ ] Configure variants A and B
- [ ] Submit form
- [ ] Verify loading state
- [ ] Verify success toast
- [ ] Verify test appears in list

#### Start Test
- [ ] Click "Start" on a draft test
- [ ] Verify loading state
- [ ] Verify status changes to "running"
- [ ] Verify success toast

#### View Results
- [ ] Open running test
- [ ] Verify results update in real-time
- [ ] Verify variant metrics displayed
- [ ] Verify statistical significance shown
- [ ] Verify winner indicated when determined

#### Promote Winner
- [ ] Wait for test to complete (or use mock)
- [ ] Click "Promote Winner"
- [ ] Verify confirmation dialog
- [ ] Confirm promotion
- [ ] Verify loading state
- [ ] Verify success toast
- [ ] Verify campaign updated with winning variant

### 4. Multi-Platform Publishing

#### Publish to Meta
- [ ] Select campaign
- [ ] Click "Publish to Meta"
- [ ] Verify loading state
- [ ] Verify publish job created
- [ ] Verify job ID shown
- [ ] Verify status polling starts
- [ ] Wait for completion
- [ ] Verify external ID shown

#### Publish to Multiple Platforms
- [ ] Select Meta, Google, and TikTok
- [ ] Click "Publish to All"
- [ ] Verify multiple jobs created
- [ ] Verify all jobs show in progress list
- [ ] Verify each job polls independently
- [ ] Verify completion status for each

#### Publishing Progress Tracking
- [ ] Verify progress bars show
- [ ] Verify percentage updates
- [ ] Verify status messages update
- [ ] Verify completion/failure states
- [ ] Verify error messages for failures

### 5. Error Handling

#### Network Errors
- [ ] Disconnect network
- [ ] Try to load campaigns
- [ ] Verify error message shows
- [ ] Verify "Retry" button appears
- [ ] Reconnect network
- [ ] Click "Retry"
- [ ] Verify data loads

#### API Errors
- [ ] Trigger 404 error (invalid ID)
- [ ] Verify error toast appears
- [ ] Verify user-friendly message
- [ ] Trigger 500 error
- [ ] Verify error toast appears

#### Validation Errors
- [ ] Submit form with invalid data
- [ ] Verify validation messages show
- [ ] Verify form doesn't submit
- [ ] Fix errors
- [ ] Verify form submits successfully

### 6. Loading States

#### Initial Load
- [ ] Clear cache
- [ ] Reload page
- [ ] Verify skeleton loaders show
- [ ] Verify spinners display
- [ ] Verify content loads smoothly

#### Subsequent Loads
- [ ] Navigate away
- [ ] Navigate back
- [ ] Verify cached data shows immediately
- [ ] Verify no loading state (using cache)
- [ ] Wait 30 seconds
- [ ] Navigate back
- [ ] Verify background refresh (stale data)

#### Optimistic Updates
- [ ] Pause a campaign
- [ ] Verify UI updates immediately
- [ ] Verify status changes before API response
- [ ] If API fails, verify rollback

### 7. Toast Notifications

#### Success Toasts
- [ ] Create campaign → verify success toast
- [ ] Delete campaign → verify success toast
- [ ] Launch campaign → verify success toast
- [ ] Verify toasts auto-dismiss after 5 seconds

#### Error Toasts
- [ ] Trigger error → verify error toast
- [ ] Verify error message is user-friendly
- [ ] Verify toast stays until dismissed

#### Warning Toasts
- [ ] Trigger warning → verify warning toast
- [ ] Verify warning icon and color

#### Info Toasts
- [ ] Trigger info → verify info toast
- [ ] Verify info icon and color

## Automated Testing

### Unit Tests

#### API Client Tests
```typescript
// Test API client methods
describe('ApiClient', () => {
  it('should set auth token', () => {
    apiClient.setAuthToken('test-token');
    expect(apiClient.getAuthToken()).toBe('test-token');
  });

  it('should make GET request', async () => {
    const data = await apiClient.getCampaigns();
    expect(data).toBeInstanceOf(Array);
  });

  it('should handle errors', async () => {
    await expect(apiClient.getCampaignById('invalid')).rejects.toThrow();
  });
});
```

#### Hook Tests
```typescript
// Test React Query hooks
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCampaignsList } from '@/hooks';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useCampaignsList', () => {
  it('should fetch campaigns', async () => {
    const { result } = renderHook(() => useCampaignsList(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
  });

  it('should handle errors', async () => {
    // Mock API to return error
    const { result } = renderHook(() => useCampaignsList(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
```

### Integration Tests

#### Campaign Flow Test
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CampaignsPage from '@/pages/campaigns/CampaignsPage';

describe('Campaign Flow', () => {
  it('should create and launch campaign', async () => {
    const queryClient = new QueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <CampaignsPage />
      </QueryClientProvider>
    );

    // Wait for campaigns to load
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Click "New Campaign" button
    fireEvent.click(screen.getByText('New Campaign'));

    // Fill out form (implementation depends on form structure)
    // ...

    // Submit form
    fireEvent.click(screen.getByText('Create Campaign'));

    // Verify success toast
    await waitFor(() => {
      expect(screen.getByText(/Campaign Created/i)).toBeInTheDocument();
    });

    // Verify campaign appears in list
    await waitFor(() => {
      expect(screen.getByText('My Test Campaign')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests (Playwright/Cypress)

#### Complete Campaign Lifecycle
```typescript
test('complete campaign lifecycle', async ({ page }) => {
  // Navigate to campaigns
  await page.goto('/campaigns');

  // Create campaign
  await page.click('text=New Campaign');
  await page.fill('input[name="name"]', 'E2E Test Campaign');
  await page.selectOption('select[name="objective"]', 'sales');
  await page.click('text=Next');
  // ... fill remaining steps
  await page.click('text=Create Campaign');

  // Verify creation
  await expect(page.locator('text=Campaign Created')).toBeVisible();

  // Launch campaign
  await page.click('text=E2E Test Campaign');
  await page.click('text=Launch');
  await page.click('text=Confirm');

  // Verify launch
  await expect(page.locator('text=Campaign Launched')).toBeVisible();

  // Verify status changed
  await expect(page.locator('text=active')).toBeVisible();

  // Publish to platforms
  await page.click('text=Publish');
  await page.click('text=Meta');
  await page.click('text=Google');
  await page.click('text=Publish to 2 Platforms');

  // Wait for publishing to complete
  await expect(page.locator('text=Publishing Complete')).toBeVisible({
    timeout: 30000,
  });
});
```

## Performance Testing

### Load Testing
- [ ] Open campaigns list with 100+ campaigns
- [ ] Verify list renders smoothly
- [ ] Verify pagination works
- [ ] Verify filtering works
- [ ] Measure time to interactive

### Cache Testing
- [ ] Load campaigns list
- [ ] Navigate away
- [ ] Navigate back
- [ ] Verify instant load (cached)
- [ ] Wait for stale time (30s)
- [ ] Verify background refetch

### Polling Testing
- [ ] Start publish job
- [ ] Verify polling every 5 seconds
- [ ] Verify polling stops when complete
- [ ] Open multiple publish jobs
- [ ] Verify all poll independently

## Browser Testing

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Browsers
- [ ] iOS Safari
- [ ] Android Chrome
- [ ] Mobile responsive design

## Accessibility Testing

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Verify focus indicators visible
- [ ] Verify Enter/Space activate buttons
- [ ] Verify Escape closes modals

### Screen Reader
- [ ] Test with NVDA/JAWS
- [ ] Verify all content readable
- [ ] Verify button labels clear
- [ ] Verify error messages announced

## Test Data Setup

### Mock Data
Create test campaigns:
```typescript
const testCampaigns = [
  {
    name: 'Test Campaign 1',
    objective: 'sales',
    status: 'active',
    budget: { type: 'daily', amount: 100 },
    creatives: [],
  },
  // ... more test campaigns
];
```

### API Mocking
Use MSW (Mock Service Worker):
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/campaigns', (req, res, ctx) => {
    return res(ctx.json(testCampaigns));
  }),
  rest.post('/api/campaigns', (req, res, ctx) => {
    return res(ctx.json({ id: '123', ...req.body }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Common Issues and Solutions

### Issue: "Cannot read property of undefined"
**Solution:** Ensure proper null checking and optional chaining
```typescript
// Bad
const name = campaign.name;

// Good
const name = campaign?.name || 'Untitled';
```

### Issue: Infinite refetch loop
**Solution:** Check dependency arrays and query keys
```typescript
// Bad - creates new object every render
const { data } = useQuery({ queryKey: ['campaigns', { status: 'active' }] });

// Good - stable reference
const filters = useMemo(() => ({ status: 'active' }), []);
const { data } = useQuery({ queryKey: ['campaigns', filters] });
```

### Issue: Stale data shown
**Solution:** Adjust staleTime or force refetch
```typescript
const { data, refetch } = useQuery({
  queryKey: ['campaigns'],
  staleTime: 0, // Always refetch
});

// Or manually refetch
<button onClick={() => refetch()}>Refresh</button>
```

### Issue: Memory leak warning
**Solution:** Cleanup subscriptions and abort requests
```typescript
useEffect(() => {
  const controller = new AbortController();

  fetchData({ signal: controller.signal });

  return () => controller.abort();
}, []);
```

## Continuous Testing

### GitHub Actions Workflow
```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'

      - run: npm ci
      - run: npm run test
      - run: npm run test:e2e

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Coverage Goals

- Unit tests: > 80% coverage
- Integration tests: All critical paths
- E2E tests: Primary user flows
- Performance: Load time < 3s
- Accessibility: WCAG 2.1 AA

## Reporting Issues

When reporting bugs, include:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Browser and version
5. Console errors
6. Network tab screenshots
7. React Query DevTools state

## Resources

- [React Query DevTools](https://tanstack.com/query/latest/docs/react/devtools)
- [Testing Library](https://testing-library.com/)
- [MSW](https://mswjs.io/)
- [Playwright](https://playwright.dev/)
