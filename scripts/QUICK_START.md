# Quick Start Guide - Database Migration System

## Prerequisites

### 1. Install Python Dependencies

```bash
# Install psycopg2 for PostgreSQL connectivity
pip install psycopg2-binary

# Or if you prefer the full version:
pip install psycopg2
```

### 2. Set Database Connection

**Option A: Use DATABASE_URL**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/geminivideo"
```

**Option B: Use Individual Components**
```bash
export POSTGRES_USER="geminivideo"
export POSTGRES_PASSWORD="your_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="geminivideo"
```

### 3. Verify Database Connection

```bash
# Test with psql
psql $DATABASE_URL -c "SELECT version();"

# Or use our health checker (after installing psycopg2)
python scripts/db-health.py --quick
```

---

## Running Migrations

### Step 1: Check Current Status

```bash
python scripts/migrate.py --status
```

This shows:
- Which migrations have been applied
- Which migrations are pending
- When the last migration ran

### Step 2: Dry Run (Recommended First)

```bash
python scripts/migrate.py --dry-run
```

This shows:
- What would be executed
- File sizes
- Checksums
- No actual changes made

### Step 3: Run Migrations

```bash
python scripts/migrate.py
```

This will:
- Apply all pending migrations in order
- Track each migration in `_migrations` table
- Run each migration in its own transaction
- Roll back automatically on error
- Show clear progress with colored output

**Expected Output:**
```
======================================================================
                    DATABASE MIGRATION RUNNER
======================================================================

ℹ Found 8 migration files
✓ Database connection established
✓ Migration tracking table ready
⚠ Pending migrations: 8

======================================================================
                       EXECUTING MIGRATIONS
======================================================================

Migration: 001_initial_schema
✓ Completed in 234ms

Migration: 002_add_predictions
✓ Completed in 156ms

...

======================================================================
                       MIGRATION SUMMARY
======================================================================
✓ Successful: 8
```

---

## Verify Health

```bash
python scripts/db-health.py --detailed
```

This checks:
- ✓ Database connectivity
- ✓ pgvector extension
- ✓ All 34 required tables
- ✓ Migration status
- ✓ Row counts
- ✓ Data integrity
- ✓ Database size
- ✓ Index usage
- ✓ Performance metrics

---

## Seed Demo Data (Optional)

### Full Dataset (Recommended for Demos)

```bash
python scripts/seed-demo.py
```

Creates:
- 3 demo users
- 6 campaigns with realistic metrics
- 24+ ads with predictions
- 14 days of performance data per ad
- Creative DNA patterns
- Cross-account learning patterns
- 30 days of daily analytics

**Time:** ~10-30 seconds

### Minimal Dataset (Faster)

```bash
python scripts/seed-demo.py --minimal
```

Creates a smaller dataset for quick testing.

**Time:** ~5-10 seconds

### Clear and Reseed

```bash
python scripts/seed-demo.py --clear
```

Clears all existing demo data before seeding.

---

## Common Commands

### Check Migration Status
```bash
python scripts/migrate.py --status
```

### Preview Changes
```bash
python scripts/migrate.py --dry-run
```

### Run Migrations
```bash
python scripts/migrate.py
```

### Quick Health Check
```bash
python scripts/db-health.py --quick
```

### Detailed Health Report
```bash
python scripts/db-health.py --detailed
```

### Health Check as JSON (for automation)
```bash
python scripts/db-health.py --json
```

### Seed Demo Data
```bash
python scripts/seed-demo.py
```

### Seed Minimal Data
```bash
python scripts/seed-demo.py --minimal
```

---

## Troubleshooting

### "No module named 'psycopg2'"

Install the package:
```bash
pip install psycopg2-binary
```

### "Failed to connect to database"

1. Check your DATABASE_URL:
```bash
echo $DATABASE_URL
```

2. Test connection manually:
```bash
psql $DATABASE_URL -c "SELECT 1;"
```

3. Verify credentials and host are correct

### "pgvector extension not installed"

**For PostgreSQL 14:**
```bash
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**For PostgreSQL 16:**
```bash
# Usually available via package manager
sudo apt install postgresql-16-pgvector  # Debian/Ubuntu
brew install pgvector                     # macOS
```

Then enable in your database:
```sql
CREATE EXTENSION vector;
```

### Migration Failed

1. Check the error message
2. Fix the underlying issue
3. Run migrations again (they're idempotent)

For severe issues, restore from backup:
```bash
psql $DATABASE_URL < backup_file.sql
```

---

## Production Deployment

### 1. Backup First

```bash
# Create timestamped backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Run Pre-Deployment Checks

```bash
# Verify current state
python scripts/db-health.py --detailed

# Preview changes
python scripts/migrate.py --dry-run
```

### 3. Apply Migrations

```bash
# Run migrations
python scripts/migrate.py
```

### 4. Verify Post-Deployment

```bash
# Run health check
python scripts/db-health.py --detailed

# Check specific tables
psql $DATABASE_URL -c "SELECT COUNT(*) FROM campaigns;"
```

### 5. Monitor

```bash
# Check index usage
psql $DATABASE_URL -c "SELECT * FROM index_usage_stats LIMIT 10;"

# Check for unused indexes
psql $DATABASE_URL -c "SELECT * FROM unused_indexes;"
```

---

## File Structure

```
scripts/
├── migrate.py              # Master migration runner
├── seed-demo.py           # Demo data seeder
├── db-health.py           # Health checker
├── QUICK_START.md         # This file
└── migrations/
    ├── README.md          # Detailed migration documentation
    ├── 001_initial_schema.sql
    ├── 002_add_predictions.sql
    ├── 003_add_pgvector.sql
    ├── 004_add_semantic_cache.sql
    ├── 005_add_creative_dna.sql
    ├── 006_add_cross_learning.sql
    ├── 007_add_compound_learning.sql
    └── 008_add_indexes.sql
```

---

## What Gets Created

### Tables (34 total)
- **Core:** users, campaigns, blueprints, videos, ads, clips, emotions
- **Metrics:** performance_metrics, daily_analytics, predictions
- **Jobs:** jobs, render_jobs, audit_logs
- **Embeddings:** video_embeddings, script_embeddings, ad_creative_embeddings, winning_ad_patterns
- **Cache:** semantic_cache_entries
- **DNA:** creative_formulas, creative_dna_extractions, dna_applications
- **Cross-Learning:** cross_account_patterns, pattern_contributions, pattern_applications, industry_benchmarks
- **Compound Learning:** learning_cycles, learning_metrics, feedback_loops, feedback_events, compound_learnings, improvement_trajectory

### Views (15+)
- Prediction accuracy views
- Semantic cache stats
- DNA effectiveness views
- Cross-pattern views
- Learning cycle views
- Index usage views

### Functions (20+)
- Prediction scoring
- Vector similarity search
- Cache operations
- DNA analysis
- Pattern matching
- Learning calculations

### Indexes (100+)
- B-tree indexes for lookups
- Composite indexes for queries
- Partial indexes for filters
- Vector indexes (IVFFlat)
- JSONB GIN indexes
- Time-series indexes

---

## Next Steps

1. ✅ Install psycopg2: `pip install psycopg2-binary`
2. ✅ Set DATABASE_URL environment variable
3. ✅ Run migrations: `python scripts/migrate.py`
4. ✅ Verify health: `python scripts/db-health.py --detailed`
5. ✅ Seed demo data: `python scripts/seed-demo.py` (optional)
6. ✅ Start building features on top of this foundation!

---

## Support

- 📖 Full documentation: `scripts/migrations/README.md`
- 📊 Delivery summary: `AGENT_52_DELIVERY_SUMMARY.md`
- 🔍 Health checks: `python scripts/db-health.py --detailed`
- 📋 Migration status: `python scripts/migrate.py --status`

---

**Ready to go! 🚀**
