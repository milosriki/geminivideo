# Database Quick Start Guide

Get the PostgreSQL database up and running in 5 minutes.

## Prerequisites

- Node.js 20+
- Docker and Docker Compose (optional, for local PostgreSQL)
- PostgreSQL 12+ (if not using Docker)

## 30-Second Setup (Docker)

```bash
# 1. Navigate to gateway-api
cd services/gateway-api

# 2. Start database
docker-compose up -d postgres redis

# 3. Copy environment
cp .env.example .env

# 4. Run setup script
./scripts/setup-db.sh
```

That's it! The database is ready with sample data.

## Test API Keys

Use these for development:

```
Admin:      dev_admin_key_12345
Demo:       dev_demo_key_67890
Enterprise: dev_enterprise_key_abcde
```

## Quick Commands

```bash
# View data in browser
npm run db:studio
# Open http://localhost:5555

# Create migration
npm run db:migrate

# Seed data
npm run db:seed

# Reset database (WARNING: deletes data)
npm run db:reset
```

## Basic Usage

```typescript
import { db } from './services/database';

// Initialize
await db.connect();

// Create user
const user = await db.createUser({
  email: 'user@example.com',
  name: 'John Doe',
});

// Get user by API key
const auth = await db.getUserByApiKey('dev_demo_key_67890');

// Create asset
const asset = await db.createAsset({
  userId: user.id,
  filename: 'video.mp4',
  originalName: 'My Video.mp4',
  mimeType: 'video/mp4',
  fileSize: BigInt(1000000),
  gcsUrl: 'gs://bucket/video.mp4',
  gcsBucket: 'bucket',
  gcsPath: 'videos/video.mp4',
});

// Get top clips
const clips = await db.getTopClips({
  assetId: asset.id,
  limit: 10,
  minScore: 0.7,
});
```

## Environment Variables

Minimal `.env` configuration:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/geminivideo"
NODE_ENV=development
PORT=3000
```

## Troubleshooting

### Database won't connect

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### Migration errors

```bash
# Check status
npx prisma migrate status

# Reset (development only)
npm run db:reset
```

### Type errors

```bash
# Regenerate Prisma Client
npm run db:generate
```

## What's Included

After setup, you'll have:

- ✅ PostgreSQL 16 database
- ✅ Redis cache
- ✅ 8 database models (User, Asset, Clip, Campaign, etc.)
- ✅ Sample data (3 users, 2 videos, 11 clips, 2 campaigns)
- ✅ Connection pooling configured
- ✅ Prisma Studio for data visualization

## Next Steps

1. **Read the docs**: `docs/DATABASE.md` for complete guide
2. **View schema**: `prisma/schema.prisma` for models
3. **Run tests**: `npm test` to verify setup
4. **Explore data**: `npm run db:studio` to browse

## Getting Help

- **Schema Reference**: `prisma/README.md`
- **Full Documentation**: `docs/DATABASE.md`
- **Migration Guide**: `docs/MIGRATIONS.md`
- **Implementation Details**: `DATABASE_IMPLEMENTATION.md`

---

**Ready to build!** The database is now configured and seeded with sample data.
