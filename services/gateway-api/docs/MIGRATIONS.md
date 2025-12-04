# Database Migrations Guide

Complete guide for managing database migrations with Prisma.

## Overview

Prisma Migrate is a declarative data modeling and migration system. It uses the Prisma schema as the single source of truth for your database structure.

## Quick Reference

```bash
# Development
npm run db:migrate              # Create and apply migration
npm run db:generate             # Generate Prisma Client
npm run db:seed                 # Run seed script
npm run db:studio               # Open Prisma Studio (GUI)
npm run db:reset                # Reset database (WARNING: deletes data)

# Production
npm run db:migrate:deploy       # Apply pending migrations
```

## Migration Workflow

### Development

1. **Modify Schema**
   ```prisma
   // prisma/schema.prisma
   model User {
     id        String   @id @default(uuid())
     email     String   @unique
     name      String
     createdAt DateTime @default(now())
     // Add new field
     phone     String?
   }
   ```

2. **Create Migration**
   ```bash
   npm run db:migrate
   # You'll be prompted to name the migration
   # Example: add_user_phone_field
   ```

3. **Review Migration**
   Check `prisma/migrations/YYYYMMDDHHMMSS_add_user_phone_field/migration.sql`
   ```sql
   -- AlterTable
   ALTER TABLE "users" ADD COLUMN "phone" TEXT;
   ```

4. **Test Migration**
   The migration is automatically applied to your development database.

### Production

1. **Commit Migrations**
   ```bash
   git add prisma/migrations/
   git commit -m "feat: add user phone field"
   ```

2. **Deploy to Production**
   ```bash
   # On production server
   npm run db:migrate:deploy
   ```

## Common Migration Scenarios

### Adding a Field

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  // Add new optional field
  phone     String?
}
```

```bash
npm run db:migrate
# Migration name: add_user_phone
```

### Making Field Required (with Default)

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  // Make phone required with default
  phone     String   @default("")
}
```

```bash
npm run db:migrate
# Migration name: make_phone_required
```

### Adding an Index

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  phone     String?

  @@index([phone])  // Add index
}
```

```bash
npm run db:migrate
# Migration name: add_phone_index
```

### Adding a New Model

```prisma
model Notification {
  id        String   @id @default(uuid())
  userId    String
  title     String
  message   String
  read      Boolean  @default(false)
  createdAt DateTime @default(now())

  user      User     @relation(fields: [userId], references: [id])

  @@index([userId])
  @@index([read])
}

model User {
  // ... existing fields
  notifications Notification[]
}
```

```bash
npm run db:migrate
# Migration name: add_notifications
```

### Renaming a Field

⚠️ **WARNING**: Prisma will drop and recreate the column, losing data!

```prisma
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  // Renamed from 'name' to 'fullName'
  fullName  String
}
```

**Safe Approach:**
1. Add new field
2. Migrate data
3. Remove old field

```bash
# Step 1: Add new field
# In schema: fullName String?
npm run db:migrate -- --name add_fullname

# Step 2: Copy data (custom SQL)
# See "Custom Migrations" below

# Step 3: Remove old field
# In schema: remove 'name'
npm run db:migrate -- --name remove_name
```

### Changing Field Type

⚠️ **WARNING**: May lose data if types are incompatible!

```prisma
model Asset {
  id        String   @id @default(uuid())
  // Changed from Int to BigInt
  fileSize  BigInt
}
```

Prisma will generate appropriate SQL:
```sql
ALTER TABLE "assets" ALTER COLUMN "fileSize" TYPE BIGINT USING "fileSize"::BIGINT;
```

## Custom Migrations

Sometimes you need to write custom SQL for complex data transformations.

### Creating Empty Migration

```bash
npx prisma migrate dev --create-only
# Name: custom_data_migration
```

### Edit Migration File

```sql
-- prisma/migrations/YYYYMMDDHHMMSS_custom_data_migration/migration.sql

-- Copy data from old to new field
UPDATE users SET "fullName" = name WHERE "fullName" IS NULL;

-- Update calculated field
UPDATE clips SET duration = "endTime" - "startTime";

-- Add custom index
CREATE INDEX CONCURRENTLY idx_clips_score ON clips(score DESC) WHERE score > 0.7;
```

### Apply Migration

```bash
npx prisma migrate dev
```

## Migration States

### Check Migration Status

```bash
npx prisma migrate status
```

Output:
```
Database schema is up to date!

The following migrations have been applied:

migrations/
  └─ 20250601000001_init/
  └─ 20250601000002_add_clips/
  └─ 20250601000003_add_campaigns/
```

### Resolve Failed Migration

If a migration fails partway through:

```bash
# Mark as applied (if you fixed manually)
npx prisma migrate resolve --applied "20250601000001_migration_name"

# Mark as rolled back (to retry)
npx prisma migrate resolve --rolled-back "20250601000001_migration_name"
```

## Best Practices

### 1. Always Review Generated SQL

```bash
# Create migration without applying
npx prisma migrate dev --create-only

# Review the SQL
cat prisma/migrations/YYYYMMDDHHMMSS_*/migration.sql

# Apply if looks good
npx prisma migrate dev
```

### 2. Test on Staging First

```bash
# On staging
npm run db:migrate:deploy

# Verify everything works
npm test

# Then deploy to production
```

### 3. Backup Before Major Migrations

```bash
# Backup database
pg_dump -U postgres geminivideo > backup_$(date +%Y%m%d).sql

# Run migration
npm run db:migrate:deploy

# If issues, restore
# psql -U postgres geminivideo < backup_20250601.sql
```

### 4. Use Descriptive Names

```bash
# ✅ Good
add_user_phone_field
create_notifications_table
add_clip_scoring_indexes

# ❌ Bad
migration_1
update
fix
```

### 5. Keep Migrations Small

Each migration should do one thing:
- ✅ Add one model
- ✅ Add one field
- ✅ Add indexes for one table
- ❌ Multiple unrelated changes

### 6. Never Edit Applied Migrations

Once a migration is applied:
- Don't edit it
- Create a new migration to make changes
- Editing causes database drift

## Zero-Downtime Migrations

For production systems that can't afford downtime:

### Adding a Required Field

**Step 1**: Add as optional
```prisma
model User {
  newField String?
}
```

**Step 2**: Deploy and populate
```bash
npm run db:migrate:deploy
# Run script to populate newField
```

**Step 3**: Make required
```prisma
model User {
  newField String @default("value")
}
```

### Removing a Field

**Step 1**: Stop using field in code
```typescript
// Remove all references to oldField
```

**Step 2**: Deploy code changes

**Step 3**: Remove from schema
```prisma
model User {
  // oldField removed
}
```

### Renaming a Field

**Step 1**: Add new field
```prisma
model User {
  oldField String
  newField String?
}
```

**Step 2**: Dual writes
```typescript
// Write to both fields
await prisma.user.update({
  data: {
    oldField: value,
    newField: value,
  },
});
```

**Step 3**: Backfill data
```sql
UPDATE users SET "newField" = "oldField" WHERE "newField" IS NULL;
```

**Step 4**: Switch reads to new field
```typescript
// Read from newField
```

**Step 5**: Remove old field
```prisma
model User {
  newField String
}
```

## Rollback Strategies

Prisma Migrate doesn't have built-in rollback. Strategies:

### 1. Database Backup
```bash
# Before migration
pg_dump geminivideo > backup.sql

# If issues
psql geminivideo < backup.sql
```

### 2. Manual Rollback Migration
```bash
# Create rollback migration
npx prisma migrate dev --create-only
# Name: rollback_feature_x

# Write reverse SQL
# migration.sql:
ALTER TABLE users DROP COLUMN phone;
```

### 3. Git-Based Rollback
```bash
# Revert schema changes
git revert <commit>

# Create new migration
npm run db:migrate
```

## Troubleshooting

### Migration Fails Midway

```bash
# Check status
npx prisma migrate status

# Review migration.sql
cat prisma/migrations/failed_migration/migration.sql

# Fix database manually if needed
psql geminivideo

# Mark as resolved
npx prisma migrate resolve --applied "migration_name"
```

### Schema Drift

```bash
# Database doesn't match schema
npx prisma db pull  # Pull database schema
npx prisma migrate dev  # Create migration to match
```

### Reset Development Database

```bash
# WARNING: Deletes all data!
npm run db:reset

# This will:
# 1. Drop database
# 2. Create database
# 3. Apply all migrations
# 4. Run seed script
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Database Migrations

on:
  push:
    branches: [main]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run migrations
        run: npm run db:migrate:deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      - name: Generate Prisma Client
        run: npm run db:generate
```

## Advanced Topics

### Shadow Database

Prisma uses a shadow database for development. Configure in schema:

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  shadowDatabaseUrl = env("SHADOW_DATABASE_URL")
}
```

### Prisma Migrate in Docker

```dockerfile
# Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
COPY prisma ./prisma/

RUN npm ci
RUN npm run db:generate

COPY . .

# Run migrations on container start
CMD ["sh", "-c", "npm run db:migrate:deploy && npm start"]
```

## Resources

- [Prisma Migrate Documentation](https://www.prisma.io/docs/concepts/components/prisma-migrate)
- [Migration Troubleshooting](https://www.prisma.io/docs/guides/migrate/troubleshooting)
- [Production Migrations](https://www.prisma.io/docs/guides/migrate/production-troubleshooting)
