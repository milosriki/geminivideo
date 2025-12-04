# Database Schema & Migrations

This directory contains the Prisma schema, migrations, and seed data for the Gateway API.

## Quick Start

### 1. Setup Database

```bash
# Copy environment file
cp .env.example .env

# Update DATABASE_URL in .env with your PostgreSQL connection string
# Example: postgresql://postgres:password@localhost:5432/geminivideo
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Run Migrations

```bash
# Generate Prisma Client
npm run db:generate

# Create and apply migrations
npm run db:migrate

# Or for production deployment
npm run db:migrate:deploy
```

### 4. Seed Database (Optional)

```bash
# Populate with sample data
npm run db:seed
```

## Database Schema

### Core Models

#### User
- Manages user accounts and authentication
- Roles: USER, ADMIN, ENTERPRISE
- Includes API key management

#### Asset
- Video files uploaded by users
- Stored in Google Cloud Storage
- Tracks processing status and metadata

#### Clip
- Extracted segments from assets
- AI-analyzed features and scoring
- Ranked by quality/engagement

#### Campaign
- Ad campaigns on Meta/Google
- Budget and performance tracking
- Integration with external platforms

#### Experiment
- A/B testing framework
- Variant comparison
- Statistical confidence tracking

#### Prediction
- ML model predictions for clips
- Predicted vs actual metrics
- Model versioning

#### Conversion
- Conversion tracking from ads
- Multi-source attribution
- Revenue tracking

#### KnowledgeDocument
- RAG knowledge base
- Vector embeddings for search
- Versioned documents

## Available Commands

### Development

```bash
# Generate Prisma Client
npm run db:generate

# Create new migration
npm run db:migrate

# Apply migrations (development)
npm run db:migrate

# Open Prisma Studio (database GUI)
npm run db:studio

# Seed database with sample data
npm run db:seed

# Reset database (WARNING: deletes all data)
npm run db:reset
```

### Production

```bash
# Apply migrations without prompts
npm run db:migrate:deploy
```

## Connection Pooling

The DATABASE_URL supports connection pooling via query parameters:

```
DATABASE_URL="postgresql://user:pass@host:port/db?connection_limit=10&pool_timeout=20&connect_timeout=10"
```

### Recommended Pool Sizes

- **Development**: 5-10 connections
- **Production (small)**: 10-20 connections
- **Production (large)**: 20-50 connections

## Migrations

### Creating a New Migration

1. Modify `schema.prisma`
2. Run `npm run db:migrate`
3. Name the migration descriptively
4. Review the generated SQL in `prisma/migrations/`

### Migration Best Practices

- Always review generated SQL before deploying
- Test migrations on staging first
- Use transactions for complex migrations
- Keep migrations small and focused
- Never edit existing migrations

## Indexes

The schema includes optimized indexes for:

- Foreign key relationships
- Frequently queried fields (status, createdAt, etc.)
- Unique constraints (email, apiKey, gcsUrl, etc.)

## Data Types

### Decimals
Used for currency and precise calculations:
- Campaign budgets
- Conversion values
- Avoids floating-point precision issues

### BigInt
Used for large counters:
- File sizes
- Impression counts
- Click counts

### JSON
Used for flexible metadata:
- User settings
- Experiment variants
- Feature vectors

### Arrays
Used for lists:
- Float[] for embeddings
- String[] for tags

## Security

### Soft Deletes
Most models support soft deletes via `deletedAt`:
- Users
- Assets
- Clips
- Campaigns
- KnowledgeDocuments

### Cascade Deletes
Configured relationships:
- User → Assets → Clips
- Campaign → Experiments
- Asset → Clips → Predictions

## Backup & Recovery

### Backup

```bash
# PostgreSQL backup
pg_dump -U postgres geminivideo > backup.sql

# Or use Prisma migrations
npm run db:migrate -- --create-only
```

### Restore

```bash
# PostgreSQL restore
psql -U postgres geminivideo < backup.sql

# Or apply migrations
npm run db:migrate:deploy
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql postgresql://user:pass@host:port/db

# Check Prisma connection
npx prisma db pull
```

### Migration Conflicts

```bash
# Reset migrations (WARNING: deletes data)
npm run db:reset

# Or resolve manually
npx prisma migrate resolve --applied "migration_name"
```

### Type Generation Issues

```bash
# Regenerate Prisma Client
npm run db:generate

# Or force regenerate
rm -rf node_modules/.prisma
npm run db:generate
```

## Performance Optimization

### Query Optimization

1. Use `select` to fetch only needed fields
2. Use `include` carefully to avoid N+1 queries
3. Implement cursor-based pagination for large datasets
4. Use database indexes effectively

### Connection Pooling

Configure pool size based on:
- Concurrent users
- Request patterns
- Database capacity

### Monitoring

Monitor these metrics:
- Query execution time
- Connection pool usage
- Slow query logs
- Index usage

## Resources

- [Prisma Documentation](https://www.prisma.io/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Best Practices](https://www.prisma.io/docs/guides/performance-and-optimization)
