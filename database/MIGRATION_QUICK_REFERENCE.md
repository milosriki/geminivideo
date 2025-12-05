# Database Migration Quick Reference

## TL;DR - Get Started in 30 Seconds

```bash
# 1. Set database URL
export DATABASE_URL="postgresql://user:password@host:5432/database"

# 2. Run migrations
python /home/user/geminivideo/database/migrations/run_migrations.py

# Done! ✅
```

## Common Commands

### Check Migration Status

```bash
python database/migrations/run_migrations.py --status
```

### Preview Changes (Dry Run)

```bash
python database/migrations/run_migrations.py --dry-run
```

### Run All Pending Migrations

```bash
python database/migrations/run_migrations.py
```

### Manual Migration

```bash
psql $DATABASE_URL -f database/migrations/001_creative_assets.sql
```

## Environment Variables

### Quick Setup

```bash
# Copy and modify
cp .env.example .env

# Add to .env file:
DATABASE_URL=postgresql://geminivideo:password@localhost:5432/geminivideo
```

### Verify Configuration

```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

## Migration Files

Located in `/home/user/geminivideo/database/migrations/`:

1. **001_creative_assets.sql** - Creative assets table for uploads
2. **002_schema_consolidation.sql** - Fix schema conflicts
3. **003_performance_indexes.sql** - Add performance indexes
4. **004_schema_validation.sql** - Validate and fix schema

## Database URL Formats

### Local PostgreSQL
```
postgresql://geminivideo:password@localhost:5432/geminivideo
```

### Docker
```
postgresql://geminivideo:password@postgres:5432/geminivideo
```

### Supabase
```
postgresql://postgres:password@db.project.supabase.co:5432/postgres
```

### Cloud SQL
```
postgresql://user:pass@/cloudsql/project:region:instance/db
```

## Troubleshooting

### Connection Failed?

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check if port is open
netstat -tlnp | grep 5432

# Test connection
psql -h localhost -U geminivideo -d geminivideo
```

### Migration Failed?

```bash
# Check logs
tail -f /var/log/postgresql/postgresql-14-main.log

# View schema validation
psql $DATABASE_URL -c "SELECT * FROM schema_validation_report;"

# Check schema health
psql $DATABASE_URL -c "SELECT * FROM schema_health_report;"
```

### Permission Denied?

```bash
sudo -u postgres psql
postgres=# GRANT ALL ON SCHEMA public TO geminivideo;
postgres=# GRANT ALL ON ALL TABLES IN SCHEMA public TO geminivideo;
```

## Quick Checks

### List Tables

```bash
psql $DATABASE_URL -c "\dt"
```

### Count Records

```bash
psql $DATABASE_URL -c "
SELECT
    'campaigns' as table, COUNT(*) as count FROM campaigns
UNION ALL
SELECT 'videos', COUNT(*) FROM videos
UNION ALL
SELECT 'blueprints', COUNT(*) FROM blueprints;
"
```

### Check Indexes

```bash
psql $DATABASE_URL -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"
```

## Backup & Restore

### Quick Backup

```bash
pg_dump $DATABASE_URL > backup.sql
```

### Quick Restore

```bash
psql $DATABASE_URL < backup.sql
```

## Production Deployment

### Before Deployment

```bash
# 1. Backup database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Test migrations (dry run)
python database/migrations/run_migrations.py --dry-run

# 3. Check status
python database/migrations/run_migrations.py --status
```

### Deploy

```bash
# Run migrations
python database/migrations/run_migrations.py
```

### After Deployment

```bash
# Verify schema health
psql $DATABASE_URL -c "SELECT * FROM schema_health_report;"

# Check for issues
psql $DATABASE_URL -c "SELECT * FROM schema_validation_report;"
```

## Schema Information

### Required Tables

✅ Users
✅ Campaigns
✅ Blueprints
✅ Videos
✅ Ads
✅ Clips
✅ Emotions
✅ Performance Metrics
✅ Daily Analytics
✅ Jobs
✅ Render Jobs
✅ Predictions
✅ AB Tests
✅ Creative Assets

### Key Relationships

```
Users
  └─> Campaigns
       ├─> Blueprints
       │    └─> Render Jobs
       ├─> Videos
       │    ├─> Clips
       │    │    └─> Emotions
       │    └─> Performance Metrics
       └─> Ads
```

## Helper Commands

### Generate Secure Password

```bash
openssl rand -base64 32
```

### Create Database

```bash
sudo -u postgres createdb geminivideo -O geminivideo
```

### Drop and Recreate (⚠️ DANGER)

```bash
# ONLY IN DEVELOPMENT!
sudo -u postgres dropdb geminivideo
sudo -u postgres createdb geminivideo -O geminivideo
```

### Reset Migration Tracking

```bash
psql $DATABASE_URL -c "DROP TABLE IF EXISTS schema_migrations;"
```

## Performance

### Enable Query Logging

```sql
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

### View Slow Queries

```sql
SELECT * FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;
```

### Check Table Sizes

```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;
```

## Need Help?

1. ✅ Check `DATABASE_SETUP_GUIDE.md` for detailed instructions
2. ✅ Run schema validation: `SELECT * FROM schema_validation_report;`
3. ✅ Check PostgreSQL logs
4. ✅ Verify environment variables are set correctly
