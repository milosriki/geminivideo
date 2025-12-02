# Database Service Documentation

Complete guide for using the PostgreSQL database with Prisma ORM in Gateway API.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Schema Overview](#schema-overview)
4. [Usage Examples](#usage-examples)
5. [Best Practices](#best-practices)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Setup Database

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres redis

# Or use your own PostgreSQL instance
# Update DATABASE_URL in .env
```

### 2. Initialize Database

```bash
# Run setup script (interactive)
./scripts/setup-db.sh

# Or manually
npm install
npm run db:generate
npm run db:migrate
npm run db:seed
```

### 3. Use Database Service

```typescript
import { db } from './services/database';

// Connect to database
await db.connect();

// Create a user
const user = await db.createUser({
  email: 'user@example.com',
  name: 'John Doe',
  role: 'USER',
});

// Get user
const foundUser = await db.getUserById(user.id);

// Disconnect when done
await db.disconnect();
```

## Architecture

### Connection Pooling

The DatabaseService uses Prisma's built-in connection pooling:

```typescript
// Configured via DATABASE_URL
postgresql://user:pass@host:port/db?connection_limit=10&pool_timeout=20
```

**Pool Settings:**
- `connection_limit`: Maximum number of database connections (default: 10)
- `pool_timeout`: Time to wait for connection in seconds (default: 20)
- `connect_timeout`: Connection establishment timeout (default: 10)

### Singleton Pattern

The service uses a singleton pattern to ensure only one Prisma client instance:

```typescript
const db = DatabaseService.getInstance();
```

## Schema Overview

### Core Models

#### User
Manages user accounts and authentication.

**Fields:**
- `id`: UUID primary key
- `email`: Unique email address
- `name`: User display name
- `role`: USER | ADMIN | ENTERPRISE
- `apiKey`: Unique API key for authentication
- `settings`: JSON configuration

**Relationships:**
- Has many `Assets`
- Has many `Campaigns`

#### Asset
Uploaded video files stored in GCS.

**Fields:**
- `id`: UUID primary key
- `userId`: Foreign key to User
- `filename`: Generated filename
- `gcsUrl`: Google Cloud Storage URL
- `duration`: Video duration in seconds
- `status`: PENDING | PROCESSING | READY | FAILED

**Relationships:**
- Belongs to `User`
- Has many `Clips`

#### Clip
Extracted video segments with AI analysis.

**Fields:**
- `id`: UUID primary key
- `assetId`: Foreign key to Asset
- `startTime`, `endTime`: Timestamps in seconds
- `features`: JSON with detected features
- `score`: Overall quality score (0-1)
- `rank`: Ranking within asset

**Relationships:**
- Belongs to `Asset`
- Has many `Predictions`

#### Campaign
Ad campaign on Meta/Google platforms.

**Fields:**
- `id`: UUID primary key
- `userId`: Foreign key to User
- `name`: Campaign name
- `objective`: AWARENESS | CONVERSIONS | etc.
- `budget`: Total budget (Decimal)
- `status`: DRAFT | ACTIVE | PAUSED | COMPLETED

**Relationships:**
- Belongs to `User`
- Has many `Experiments`
- Has many `Conversions`

## Usage Examples

### User Management

```typescript
// Create user with API key
const user = await db.createUser({
  email: 'enterprise@example.com',
  name: 'Enterprise User',
  role: 'ENTERPRISE',
  apiKey: 'ent_key_12345',
  settings: {
    notifications: true,
    theme: 'dark',
  },
});

// Authenticate by API key
const authenticatedUser = await db.getUserByApiKey('ent_key_12345');

// Update user settings
await db.updateUser(user.id, {
  settings: {
    ...user.settings,
    language: 'es',
  },
});

// Soft delete user
await db.deleteUser(user.id, true);
```

### Asset & Clip Processing

```typescript
// Create asset
const asset = await db.createAsset({
  userId: user.id,
  filename: 'video_123.mp4',
  originalName: 'My Video.mp4',
  mimeType: 'video/mp4',
  fileSize: BigInt(52428800),
  gcsUrl: 'gs://bucket/videos/video_123.mp4',
  gcsBucket: 'bucket',
  gcsPath: 'videos/video_123.mp4',
  duration: 120.5,
  width: 1920,
  height: 1080,
});

// Update processing status
await db.updateAssetStatus(asset.id, 'PROCESSING');

// Create clips
const clip = await db.createClip({
  assetId: asset.id,
  startTime: 0,
  endTime: 15,
  duration: 15,
  features: {
    hasLogo: true,
    hasFaces: 2,
    emotion: 'happy',
  },
  hasText: true,
  hasSpeech: true,
});

// Update clip scores
await db.updateClipScoring(clip.id, {
  score: 0.85,
  viralScore: 0.75,
  engagementScore: 0.90,
  rank: 1,
  status: 'SCORED',
});

// Get top clips
const topClips = await db.getTopClips({
  assetId: asset.id,
  limit: 10,
  minScore: 0.7,
});
```

### Campaign Management

```typescript
// Create campaign
const campaign = await db.createCampaign({
  userId: user.id,
  name: 'Summer Sale 2025',
  objective: 'CONVERSIONS',
  budget: 5000,
  dailyBudget: 200,
  metaCampaignId: 'meta_123456',
  targetAudience: {
    age: [25, 45],
    interests: ['technology', 'business'],
  },
  startDate: new Date('2025-06-01'),
  endDate: new Date('2025-08-31'),
});

// Update metrics from Meta
await db.updateCampaignMetrics(campaign.id, {
  totalSpend: 1250.50,
  totalImpressions: BigInt(125000),
  totalClicks: BigInt(3500),
  totalConversions: BigInt(175),
});

// Create A/B test
const experiment = await db.createExperiment({
  campaignId: campaign.id,
  name: 'Headline Test',
  variants: [
    { id: 'a', headline: 'Buy Now' },
    { id: 'b', headline: 'Shop Today' },
  ],
});

// Select winner
await db.selectExperimentWinner(experiment.id, 'variant-b', 0.95);
```

### ML Predictions

```typescript
// Store prediction
const prediction = await db.createPrediction({
  clipId: clip.id,
  modelVersion: 'v1.2.3',
  predictedRoas: 2.5,
  predictedCtr: 0.035,
  predictedCpc: 0.75,
  features: {
    clipScore: 0.85,
    duration: 15,
    hasFaces: true,
  },
  confidence: 0.92,
});

// Update with actual results
await db.updatePredictionActuals(prediction.id, {
  actualRoas: 2.8,
  actualCtr: 0.042,
  actualCpc: 0.68,
  predictionError: 0.12,
});
```

### Conversion Tracking

```typescript
// Record conversion from Meta
const conversion = await db.createConversion({
  campaignId: campaign.id,
  source: 'META',
  externalId: 'meta_conv_789',
  value: 99.99,
  currency: 'USD',
  attributedClipId: clip.id,
  timestamp: new Date(),
});

// Get conversions for date range
const conversions = await db.listConversions({
  campaignId: campaign.id,
  startDate: new Date('2025-06-01'),
  endDate: new Date('2025-06-30'),
});
```

### Transactions

```typescript
// Execute multiple operations atomically
const result = await db.transaction(async (tx) => {
  // Create user
  const user = await tx.user.create({
    data: {
      email: 'new@example.com',
      name: 'New User',
    },
  });

  // Create asset for user
  const asset = await tx.asset.create({
    data: {
      userId: user.id,
      filename: 'video.mp4',
      // ... other fields
    },
  });

  return { user, asset };
});

// If any operation fails, all are rolled back
```

### Advanced Queries

```typescript
// Get Prisma client for custom queries
const prisma = db.getClient();

// Complex query with relations
const assetsWithClips = await prisma.asset.findMany({
  where: {
    userId: user.id,
    status: 'READY',
  },
  include: {
    clips: {
      where: {
        score: { gte: 0.8 },
      },
      orderBy: { score: 'desc' },
      take: 5,
    },
    user: {
      select: {
        name: true,
        email: true,
      },
    },
  },
});

// Aggregations
const stats = await prisma.campaign.aggregate({
  where: { userId: user.id },
  _sum: {
    totalSpend: true,
    totalConversions: true,
  },
  _avg: {
    totalSpend: true,
  },
});
```

## Best Practices

### 1. Always Use Transactions for Related Operations

```typescript
// ✅ Good
await db.transaction(async (tx) => {
  await tx.campaign.update({ ... });
  await tx.conversion.create({ ... });
});

// ❌ Bad
await db.updateCampaign(...);
await db.createConversion(...);
```

### 2. Use Soft Deletes by Default

```typescript
// ✅ Good
await db.deleteUser(id, true); // Soft delete

// ⚠️ Use carefully
await db.deleteUser(id, false); // Hard delete
```

### 3. Always Filter Out Soft-Deleted Records

The service handles this automatically:

```typescript
// Automatically excludes deletedAt != null
const user = await db.getUserById(id);
```

### 4. Use Pagination for Large Lists

```typescript
// ✅ Good
const clips = await db.listClips({
  skip: 0,
  take: 100,
});

// ❌ Bad - loads everything
const allClips = await prisma.clip.findMany();
```

### 5. Select Only Needed Fields

```typescript
// ✅ Good
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    email: true,
  },
});

// ❌ Bad - loads all fields
const users = await prisma.user.findMany();
```

## Performance Optimization

### 1. Connection Pooling

```env
# Development
DATABASE_URL="postgresql://...?connection_limit=10"

# Production (adjust based on load)
DATABASE_URL="postgresql://...?connection_limit=20&pool_timeout=30"
```

### 2. Indexes

The schema includes indexes on:
- Foreign keys (automatic)
- `status` fields
- `createdAt` timestamps
- Unique fields (`email`, `apiKey`)

### 3. Query Optimization

```typescript
// Use include for relations (prevents N+1)
const assets = await db.listAssets({
  userId: user.id,
  // Clips are automatically included
});

// For complex queries, use select
const clips = await prisma.clip.findMany({
  select: {
    id: true,
    score: true,
    asset: {
      select: {
        filename: true,
      },
    },
  },
});
```

### 4. Batch Operations

```typescript
// Create multiple records
await prisma.clip.createMany({
  data: [
    { assetId: id, startTime: 0, endTime: 15 },
    { assetId: id, startTime: 15, endTime: 30 },
  ],
});
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
npx prisma db pull

# Or use psql
psql postgresql://user:pass@host:port/db
```

### Migration Conflicts

```bash
# View migration status
npx prisma migrate status

# Resolve applied migration
npx prisma migrate resolve --applied "migration_name"

# Reset database (WARNING: deletes data)
npm run db:reset
```

### Type Generation

```bash
# Regenerate Prisma Client
npm run db:generate

# Clear cache
rm -rf node_modules/.prisma
npm run db:generate
```

### Performance Issues

```typescript
// Enable query logging
const prisma = new PrismaClient({
  log: ['query', 'info', 'warn', 'error'],
});

// Check slow queries in PostgreSQL
// SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC;
```

## Health Check

```typescript
// Check database health
const isHealthy = await db.healthCheck();

if (!isHealthy) {
  console.error('Database is not healthy');
}
```

## Resources

- [Prisma Documentation](https://www.prisma.io/docs)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Schema Reference](../prisma/schema.prisma)
- [Seed Data](../prisma/seed.ts)
