# Frontend Quick Start Guide

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend services running

### Installation

```bash
cd /home/user/geminivideo/frontend
npm install
```

### Environment Setup

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000/api
VITE_GATEWAY_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open http://localhost:5173

## Using the New API Hooks

### 1. Simple Data Fetching

```typescript
import { useCampaignsList } from '@/hooks';

function CampaignsList() {
  const { data, isLoading, error } = useCampaignsList();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data.map(campaign => (
        <li key={campaign.id}>{campaign.name}</li>
      ))}
    </ul>
  );
}
```

### 2. Creating Resources

```typescript
import { useCreateCampaign } from '@/hooks';
import { useToastStore } from '@/stores/toastStore';

function CreateCampaignButton() {
  const createCampaign = useCreateCampaign();
  const { addToast } = useToastStore();

  const handleCreate = async () => {
    try {
      await createCampaign.mutateAsync({
        name: 'New Campaign',
        objective: 'sales',
        // ... other fields
      });

      addToast({
        title: 'Success',
        message: 'Campaign created!',
        variant: 'success',
      });
    } catch (error) {
      addToast({
        title: 'Error',
        message: error.message,
        variant: 'error',
      });
    }
  };

  return (
    <button
      onClick={handleCreate}
      disabled={createCampaign.isPending}
    >
      {createCampaign.isPending ? 'Creating...' : 'Create Campaign'}
    </button>
  );
}
```

### 3. Real-time Updates

```typescript
import { usePublishStatus } from '@/hooks';

function PublishProgress({ jobId }) {
  // Automatically polls every 5 seconds
  const { data: status } = usePublishStatus(jobId);

  return (
    <div>
      <p>Status: {status?.status}</p>
      <p>Progress: {status?.progress}%</p>
    </div>
  );
}
```

### 4. Combined Hooks

```typescript
import { useAnalyticsDashboard } from '@/hooks';

function Analytics() {
  const {
    overview,
    trends,
    isLoading,
    refetch
  } = useAnalyticsDashboard('last_30d');

  return (
    <div>
      {overview.data && <MetricsCard data={overview.data} />}
      {trends.data && <TrendsChart data={trends.data} />}
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}
```

## Common Patterns

### Loading States

```typescript
const { data, isLoading, isError, error } = useCampaignsList();

if (isLoading) {
  return <LoadingSpinner />;
}

if (isError) {
  return <ErrorMessage error={error} />;
}

return <CampaignsList campaigns={data} />;
```

### Optimistic Updates

```typescript
const updateCampaign = useUpdateCampaign();

// UI updates immediately, rolls back on error
updateCampaign.mutate({
  id: campaignId,
  updates: { name: 'New Name' }
});
```

### Manual Refetch

```typescript
const { data, refetch } = useCampaignsList();

<button onClick={() => refetch()}>
  Refresh
</button>
```

### Dependent Queries

```typescript
const { data: campaign } = useCampaign(campaignId);
const { data: analytics } = useCampaignAnalytics(
  campaignId,
  'last_30d',
  { enabled: !!campaign } // Only fetch if campaign exists
);
```

## File Locations

### API Client
- `/home/user/geminivideo/frontend/src/lib/api.ts`

### Hooks
- `/home/user/geminivideo/frontend/src/hooks/useCampaigns.ts`
- `/home/user/geminivideo/frontend/src/hooks/useAnalytics.ts`
- `/home/user/geminivideo/frontend/src/hooks/useABTests.ts`
- `/home/user/geminivideo/frontend/src/hooks/usePublishing.ts`

### Components
- `/home/user/geminivideo/frontend/src/components/ui/LoadingSpinner.tsx`

### Examples
- `/home/user/geminivideo/frontend/src/examples/AnalyticsDashboardExample.tsx`
- `/home/user/geminivideo/frontend/src/examples/PublishingFlowExample.tsx`

## Debugging

### React Query DevTools

Already installed! Open in browser:
- Toggle with keyboard shortcut
- View all queries
- See cache state
- Manual refetch
- Inspect query details

### Console Logging

All API errors are logged to console with:
- Request URL
- Request method
- Error message
- Full error object

### Toast Notifications

All user actions show toasts:
- Success (green)
- Error (red)
- Warning (yellow)
- Info (blue)

## Next Steps

1. Read `/home/user/geminivideo/frontend/FRONTEND_WIRING_COMPLETE.md` for complete documentation
2. Check `/home/user/geminivideo/frontend/TESTING_GUIDE.md` for testing instructions
3. Review examples in `/home/user/geminivideo/frontend/src/examples/`
4. Start building your features!

## Need Help?

- Check React Query docs: https://tanstack.com/query/latest
- Check TypeScript docs: https://www.typescriptlang.org/
- Check component examples in `/examples/`
- Check existing implementations in `/pages/`
