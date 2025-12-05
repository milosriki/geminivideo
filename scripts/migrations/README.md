# GeminiVideo Database Migrations

€5M Investment-Grade Migration System

## Overview

This directory contains all database migrations for the GeminiVideo platform. The migrations are designed to be:
- **Idempotent**: Safe to run multiple times
- **Ordered**: Run in numerical sequence
- **Comprehensive**: Cover all aspects of the platform
- **Production-ready**: Supports PostgreSQL 14 and 16

## Migration Files

### 001_initial_schema.sql
Core platform tables for campaigns, videos, ads, and performance tracking.

**Tables created:**
- `users` - Platform users with Meta integration
- `campaigns` - Ad campaigns with budgets and performance
- `blueprints` - AI-generated video scripts
- `videos` - Generated video assets
- `ads` - Ad creatives with approval workflow
- `clips` - Video segments with analysis
- `emotions` - Emotional analysis data
- `performance_metrics` - Daily performance tracking
- `daily_analytics` - Aggregated analytics
- `jobs` - Background job queue
- `render_jobs` - Video rendering queue
- `audit_logs` - System audit trail

### 002_add_predictions.sql
ML prediction tracking for model validation and accuracy monitoring.

**Tables created:**
- `predictions` - Predicted vs actual performance tracking

**Views created:**
- `prediction_accuracy_summary` - Overall model accuracy
- `prediction_accuracy_by_platform` - Platform-specific accuracy
- `prediction_accuracy_by_hook` - Hook type performance
- `prediction_outliers` - Predictions with large errors

**Functions:**
- `calculate_prediction_score()` - Calculate overall accuracy (0-100)

### 003_add_pgvector.sql
Vector embeddings for semantic similarity search.

**Extensions:**
- `vector` - pgvector extension for vector operations

**Tables created:**
- `video_embeddings` - Video content embeddings (3072 dims)
- `script_embeddings` - Script content embeddings
- `ad_creative_embeddings` - Ad creative embeddings with performance
- `winning_ad_patterns` - Learned patterns from high performers

**Functions:**
- `find_similar_videos()` - Find similar videos by embedding
- `find_similar_scripts()` - Find similar scripts
- `find_matching_patterns()` - Find matching winning patterns

### 004_add_semantic_cache.sql
Semantic caching system for 80%+ cache hit rate.

**Tables created:**
- `semantic_cache_entries` - Cache with embedding-based matching

**Views created:**
- `semantic_cache_stats` - Performance statistics by query type
- `semantic_cache_popular` - Top 100 most accessed entries

**Functions:**
- `find_semantic_cache()` - Find semantically similar cache entries
- `increment_cache_access()` - Update access counts
- `cleanup_expired_cache()` - Remove expired entries

### 005_add_creative_dna.sql
Creative DNA extraction for pattern recognition.

**Tables created:**
- `creative_formulas` - Winning formulas per account
- `creative_dna_extractions` - Individual DNA extraction records
- `dna_applications` - DNA application tracking

**Views created:**
- `top_performing_dna` - Top 100 DNA extractions
- `formula_effectiveness` - Formula performance metrics
- `dna_pattern_frequency` - Pattern frequency analysis

**Functions:**
- `get_account_formula()` - Get formula for account
- `count_winning_creatives()` - Count winners above threshold

### 006_add_cross_learning.sql
Cross-account learning for platform-wide intelligence.

**Tables created:**
- `cross_account_patterns` - Platform-wide winning patterns
- `pattern_contributions` - Account contributions to patterns
- `pattern_applications` - Pattern application results
- `industry_benchmarks` - Industry performance data

**Views created:**
- `top_cross_patterns` - Top 50 validated patterns
- `pattern_effectiveness_by_industry` - Industry breakdown
- `pattern_success_metrics` - Application success rates

**Functions:**
- `get_patterns_for_industry()` - Get patterns for industry
- `calculate_pattern_roi()` - Calculate pattern ROI

### 007_add_compound_learning.sql
Compound learning system for continuous improvement.

**Tables created:**
- `learning_cycles` - Track distinct learning cycles
- `learning_metrics` - Detailed metric tracking
- `feedback_loops` - Automated improvement loops
- `feedback_events` - Loop activation logs
- `compound_learnings` - Learnings that compound over time
- `improvement_trajectory` - Performance trend tracking

**Views created:**
- `learning_cycle_performance` - Cycle performance summary
- `compound_learning_effectiveness` - Learning effectiveness
- `feedback_loop_effectiveness` - Loop performance metrics
- `improvement_trends` - Aggregated trends

**Functions:**
- `calculate_compound_rate()` - Calculate CAGR for learning
- `get_active_feedback_loops()` - Get active loops

### 008_add_indexes.sql
Performance indexes for production-grade query optimization.

**Indexes created:**
- 50+ composite and partial indexes
- Vector similarity indexes (IVFFlat)
- JSONB GIN indexes for pattern matching
- Time-series indexes for analytics
- Covering indexes for common queries

**Views created:**
- `index_usage_stats` - Monitor index usage
- `unused_indexes` - Identify unused indexes

## Running Migrations

### Prerequisites

```bash
# Install psycopg2
pip install psycopg2-binary

# Set database URL (or individual components)
export DATABASE_URL="postgresql://user:password@host:5432/database"

# OR set individual components
export POSTGRES_USER="geminivideo"
export POSTGRES_PASSWORD="your_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="geminivideo"
```

### Run All Migrations

```bash
# Run all pending migrations
python scripts/migrate.py

# Dry run (see what would be executed)
python scripts/migrate.py --dry-run

# Check migration status
python scripts/migrate.py --status
```

### Migration Output

The migration runner provides clear progress feedback:
```
======================================================================
                    DATABASE MIGRATION RUNNER
======================================================================

ℹ Project root: /home/user/geminivideo
ℹ Migrations directory: /home/user/geminivideo/scripts/migrations
✓ Found 8 migration files
ℹ Connecting to database...
✓ Database connection established
✓ Migration tracking table ready
ℹ Already applied: 0 migrations
⚠ Pending migrations: 8

======================================================================
                       EXECUTING MIGRATIONS
======================================================================

Migration: 001_initial_schema
  File: 001_initial_schema.sql
✓ Completed in 234ms

...

======================================================================
                       MIGRATION SUMMARY
======================================================================
Total migrations: 8
✓ Successful: 8
```

## Seeding Demo Data

```bash
# Seed full demo dataset
python scripts/seed-demo.py

# Seed minimal dataset (faster)
python scripts/seed-demo.py --minimal

# Clear existing data first
python scripts/seed-demo.py --clear
```

## Database Health Check

```bash
# Run full health check
python scripts/db-health.py

# Quick check (connectivity + tables)
python scripts/db-health.py --quick

# Detailed report with statistics
python scripts/db-health.py --detailed

# Output as JSON
python scripts/db-health.py --json
```

### Health Check Output

```
======================================================================
                      DATABASE HEALTH CHECK
======================================================================

1. Database Connectivity
✓ Connected to database
ℹ   Version: PostgreSQL 14.x

2. pgvector Extension
✓ pgvector extension installed (version 0.5.0)

3. Required Tables
✓ All 34 required tables exist

4. Migration Status
✓ Applied 8 migrations successfully
ℹ   Last migration: 2024-12-05 15:30:45

5. Table Row Counts
✓   users: 3 rows
✓   campaigns: 6 rows
✓   videos: 12 rows
✓   ads: 24 rows
✓   predictions: 24 rows
✓   video_embeddings: 0 rows (empty)
✓   semantic_cache_entries: 0 rows (empty)

6. Data Integrity
✓   Campaigns Have Users
✓   Videos Have Campaigns
✓   Predictions Have Actuals

======================================================================
                      HEALTH CHECK SUMMARY
======================================================================

✓ Database is healthy and operational

Status: HEALTHY
Timestamp: 2024-12-05T15:45:23
```

## Production Deployment

### Step 1: Backup Database

```bash
# Create backup before migrations
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Run Health Check

```bash
# Verify database is healthy
python scripts/db-health.py --quick
```

### Step 3: Run Migrations (Dry Run)

```bash
# See what will be executed
python scripts/migrate.py --dry-run
```

### Step 4: Run Migrations

```bash
# Execute migrations
python scripts/migrate.py
```

### Step 5: Verify

```bash
# Run health check again
python scripts/db-health.py --detailed
```

## Troubleshooting

### pgvector Not Found

If you see "pgvector extension not installed":

**PostgreSQL 14:**
```bash
# Install from source
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**PostgreSQL 16:**
```bash
# Usually available via package manager
sudo apt install postgresql-16-pgvector  # Debian/Ubuntu
```

### Connection Failed

Check your database URL and credentials:
```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

### Migration Failed

Migrations run in transactions. If one fails:
1. Check the error message
2. Fix the issue (e.g., missing extension)
3. Run migrations again - they're idempotent

### Rollback

Currently, manual rollback is required:
```bash
# Restore from backup
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

## Architecture

```
scripts/
├── migrate.py              # Migration runner
├── seed-demo.py           # Demo data seeder
├── db-health.py           # Health checker
└── migrations/
    ├── 001_initial_schema.sql
    ├── 002_add_predictions.sql
    ├── 003_add_pgvector.sql
    ├── 004_add_semantic_cache.sql
    ├── 005_add_creative_dna.sql
    ├── 006_add_cross_learning.sql
    ├── 007_add_compound_learning.sql
    └── 008_add_indexes.sql
```

## Database ERD Summary

```
Users
  ↓
Campaigns ─→ Daily Analytics
  ↓
Blueprints ─→ Script Embeddings
  ↓
Videos ─→ Video Embeddings ─→ Winning Patterns
  ↓              ↓
Clips ─→ Emotions
  ↓
Ads ─→ Ad Embeddings ─→ Creative DNA
  ↓
Predictions ─→ Performance Metrics
  ↓
Cross-Account Patterns ─→ Industry Benchmarks
  ↓
Learning Cycles ─→ Compound Learnings
  ↓
Improvement Trajectory
```

## Support

For issues or questions:
1. Check `db-health.py --detailed` output
2. Review migration logs
3. Check database logs
4. Verify pgvector installation

## Version History

- **v1.0.0** (2024-12-05): Initial release
  - 8 comprehensive migrations
  - 34 tables, 15+ views, 20+ functions
  - Full vector similarity support
  - Semantic caching system
  - Creative DNA extraction
  - Cross-account learning
  - Compound learning system
  - Production-grade indexes

## License

Internal - GeminiVideo Platform
