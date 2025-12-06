# Database Migrations

This directory contains all database migrations for the GeminiVideo platform.

## Structure

- `001_*.sql` - Initial schema migrations
- `002_*.sql` - Feature additions
- `003_*.sql` - Indexes and performance
- `004_*.sql` - Schema fixes and refinements

## Running Migrations

### Using the Migration Runner

```bash
# Run all pending migrations
python /home/user/geminivideo/database/migrations/run_migrations.py

# Check migration status
python /home/user/geminivideo/database/migrations/run_migrations.py --status

# Dry run (preview what would execute)
python /home/user/geminivideo/database/migrations/run_migrations.py --dry-run
```

### Manual Execution

```bash
# Set database URL
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Run a specific migration
psql $DATABASE_URL -f 001_creative_assets.sql
```

## Database URL Format

The DATABASE_URL should follow this format:

```
postgresql://username:password@host:port/database_name
```

### Examples:

**Local PostgreSQL:**
```
postgresql://geminivideo:password@localhost:5432/geminivideo
```

**Supabase:**
```
postgresql://postgres:password@db.project.supabase.co:5432/postgres
```

**Cloud SQL:**
```
postgresql://geminivideo:password@/cloudsql/project:region:instance/geminivideo
```

## Migration Order

1. `001_creative_assets.sql` - Creative assets table for uploads
2. `002_schema_consolidation.sql` - Consolidate and fix schema conflicts
3. `003_performance_indexes.sql` - Add performance indexes
4. `004_prediction_enhancements.sql` - Enhanced prediction logging

## Idempotency

All migrations use `IF NOT EXISTS` and `IF EXISTS` clauses to ensure they can be run multiple times safely.

## Production Deployment

1. **Backup database:**
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

2. **Test in staging:**
   ```bash
   DATABASE_URL=$STAGING_URL python run_migrations.py --dry-run
   ```

3. **Run migrations:**
   ```bash
   python run_migrations.py
   ```

4. **Verify:**
   ```bash
   python run_migrations.py --status
   ```
