# Winner Workflow - Quick Start Guide

## Installation

The workflow is already integrated into the gateway-api. No additional installation needed.

## Basic Usage

### 1. Import the workflow

```typescript
import { runFullWinnerWorkflow } from './workflows';
```

### 2. Run with defaults (approval mode)

```typescript
const result = await runFullWinnerWorkflow();

console.log('Workflow Complete!');
console.log(`Winners Found: ${result.winnersDetected}`);
console.log(`Replicas Created: ${result.replicasCreated}`);
console.log(`Awaiting Approval: ${result.replicasQueued}`);
```

### 3. Review and approve replicas

```typescript
import { getPendingApprovals, approveReplica } from './workflows';

const pending = await getPendingApprovals();

for (const { replica } of pending) {
  await approveReplica(replica.id, 'your-user-id', ['meta']);
  console.log(`✅ Approved and published: ${replica.id}`);
}
```

## Common Patterns

### Auto-Publish (No Approval)

```typescript
await runFullWinnerWorkflow({
  autoPublish: true,
  platforms: ['meta', 'google']
});
```

### Conservative Scaling

```typescript
await runFullWinnerWorkflow({
  autoPublish: false,
  minRoas: 5.0,              // Only ads with 5x+ ROAS
  minConfidence: 0.95,       // 95% confidence required
  maxReplicasPerWinner: 2,   // Just 2 variations
  budgetMultiplier: 1.2      // 20% budget increase
});
```

### Aggressive Scaling

```typescript
await runFullWinnerWorkflow({
  autoPublish: true,
  minRoas: 1.5,              // Lower threshold
  maxReplicasPerWinner: 5,   // More variations
  budgetMultiplier: 3.0,     // 3x budget
  platforms: ['meta', 'google', 'tiktok']
});
```

### Campaign-Specific

```typescript
const campaignId = 'campaign_abc123';

await runFullWinnerWorkflow({
  minRoas: 2.5,
  minConfidence: 0.9
}, campaignId);
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| autoPublish | boolean | false | Auto-publish without approval |
| maxReplicasPerWinner | number | 3 | Max variations per winner |
| budgetMultiplier | number | 1.5 | Budget increase (1.5 = +50%) |
| minRoas | number | 2.0 | Minimum ROAS threshold |
| minConfidence | number | 0.85 | Min statistical confidence |
| platforms | array | ['meta'] | Publishing platforms |

## Workflow Steps

1. **Detect Winners** - Find high-performing ads
2. **Index to RAG** - Store in AI learning system
3. **Select Top** - Pick best 5 winners
4. **Generate Replicas** - Create variations
5. **Queue/Publish** - Approve or auto-publish
6. **Track Status** - Monitor results

## Variation Types

The workflow creates these replica types:

- **Audience**: Lookalike expansion (+10%)
- **Hook**: Alternative hook styles
- **Budget**: Scale budget by multiplier
- **Placement**: Expand to Feed/Stories/Reels
- **Creative**: Color grading, format changes

## Approval Management

```typescript
// Get pending
const pending = await getPendingApprovals();

// Approve
await approveReplica(replicaId, userId, ['meta', 'google']);

// Reject
await rejectReplica(replicaId, userId, 'Reason here');
```

## Environment Setup

Required environment variables:

```bash
ML_SERVICE_URL=http://localhost:8003
META_PUBLISHER_URL=http://localhost:8001
GOOGLE_ADS_URL=http://localhost:8004
TIKTOK_ADS_URL=http://localhost:8005
```

## Error Handling

The workflow includes automatic fallbacks:

- ML service down → Use database
- RAG indexing fails → Continue workflow
- Publishing fails → Mark as failed, continue

## Monitoring

Check workflow results:

```typescript
const result = await runFullWinnerWorkflow();

console.log(`Status: ${result.status}`);
console.log(`Duration: ${result.duration}ms`);
console.log(`Winners: ${result.winnersDetected}`);
console.log(`Published: ${result.replicasPublished}`);

// Access details
result.details.winners      // All winners
result.details.topWinners   // Selected winners
result.details.replicas     // All replicas
```

## Examples

See `example-usage.ts` for 7 complete examples covering:
1. Default workflow
2. Auto-publish
3. Campaign-specific
4. Approval workflow
5. Manual approval
6. Conservative mode
7. Aggressive scaling

## Support

For detailed documentation, see:
- `README.md` - Complete documentation
- `example-usage.ts` - Usage examples
- `/home/user/geminivideo/AGENT_04_IMPLEMENTATION_SUMMARY.md` - Technical details

## Quick Test

```bash
# Navigate to gateway-api
cd /home/user/geminivideo/services/gateway-api

# Run examples (after uncommenting desired examples)
npx ts-node src/workflows/example-usage.ts
```

---

**That's it!** You now have a complete winner workflow system ready to use.
