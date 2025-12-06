# Database Setup & Configuration Guide

## Overview

GeminiVideo uses PostgreSQL as its primary database. This guide covers database setup, configuration, and troubleshooting.

## Database URL Configuration

### Format

The `DATABASE_URL` environment variable follows this format:

```
postgresql://[user]:[password]@[host]:[port]/[database]
```

### Examples

#### Local Development

```bash
# PostgreSQL running on localhost
export DATABASE_URL="postgresql://geminivideo:password@localhost:5432/geminivideo"

# With Docker
export DATABASE_URL="postgresql://geminivideo:password@postgres:5432/geminivideo"
```

#### Supabase

```bash
# Supabase connection
export DATABASE_URL="postgresql://postgres:your_password@db.your_project.supabase.co:5432/postgres"

# With connection pooling (recommended)
export DATABASE_URL="postgresql://postgres:your_password@db.your_project.supabase.co:6543/postgres?pgbouncer=true"
```

#### Google Cloud SQL

```bash
# Cloud SQL with public IP
export DATABASE_URL="postgresql://geminivideo:password@35.123.456.789:5432/geminivideo"

# Cloud SQL with Unix socket
export DATABASE_URL="postgresql://geminivideo:password@/cloudsql/project-id:region:instance-name/geminivideo"
```

#### AWS RDS

```bash
export DATABASE_URL="postgresql://geminivideo:password@your-instance.region.rds.amazonaws.com:5432/geminivideo"
```

### Connection Pooling

For production, add connection pooling parameters:

```bash
# With connection limits
DATABASE_URL="postgresql://user:pass@host:5432/db?schema=public&connection_limit=20&pool_timeout=30"

# PgBouncer (Supabase)
DATABASE_URL="postgresql://user:pass@host:6543/db?pgbouncer=true"
```

## Environment Variables

### Option 1: DATABASE_URL (Recommended)

Set a single connection string:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### Option 2: Individual Components

Set individual database parameters:

```bash
export POSTGRES_USER="geminivideo"
export POSTGRES_PASSWORD="your_secure_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="geminivideo"
```

The migration runner will automatically construct the URL from these.

## Quick Setup

### 1. Local PostgreSQL Setup

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql

postgres=# CREATE USER geminivideo WITH PASSWORD 'your_password';
postgres=# CREATE DATABASE geminivideo OWNER geminivideo;
postgres=# GRANT ALL PRIVILEGES ON DATABASE geminivideo TO geminivideo;
postgres=# \q

# Set environment variable
export DATABASE_URL="postgresql://geminivideo:your_password@localhost:5432/geminivideo"
```

### 2. Docker PostgreSQL Setup

```bash
# Start PostgreSQL container
docker run -d \
  --name geminivideo-postgres \
  -e POSTGRES_USER=geminivideo \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=geminivideo \
  -p 5432:5432 \
  postgres:14

# Set environment variable
export DATABASE_URL="postgresql://geminivideo:password@localhost:5432/geminivideo"
```

### 3. Supabase Setup

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Navigate to Settings → Database
3. Copy the connection string
4. Set environment variable:

```bash
export DATABASE_URL="postgresql://postgres:your_password@db.project.supabase.co:5432/postgres"
```

## Running Migrations

### Install Requirements

```bash
# Install Python dependencies
pip install psycopg2-binary

# Or with the project requirements
pip install -r requirements.txt
```

### Run Migrations

```bash
# Check status
python /home/user/geminivideo/database/migrations/run_migrations.py --status

# Dry run (preview)
python /home/user/geminivideo/database/migrations/run_migrations.py --dry-run

# Execute migrations
python /home/user/geminivideo/database/migrations/run_migrations.py
```

### Manual Migration

If you prefer to run migrations manually:

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Run migrations in order
psql $DATABASE_URL -f /home/user/geminivideo/database/migrations/001_creative_assets.sql
psql $DATABASE_URL -f /home/user/geminivideo/database/migrations/002_schema_consolidation.sql
psql $DATABASE_URL -f /home/user/geminivideo/database/migrations/003_performance_indexes.sql
psql $DATABASE_URL -f /home/user/geminivideo/database/migrations/004_schema_validation.sql
```

## Verification

### Check Connection

```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"

# List tables
psql $DATABASE_URL -c "\dt"

# Check schema health
psql $DATABASE_URL -c "SELECT * FROM schema_health_report;"
```

### Verify Tables

```bash
# Count tables
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

# List all tables
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
```

### Check Data Integrity

```bash
# Run validation report
psql $DATABASE_URL -c "SELECT * FROM schema_validation_report;"
```

## Common Issues & Solutions

### Issue: Connection Refused

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify host and port in DATABASE_URL
3. Check firewall rules
4. For Docker: ensure container is running

### Issue: Authentication Failed

**Symptoms:**
```
psycopg2.OperationalError: FATAL: password authentication failed
```

**Solutions:**
1. Verify username and password in DATABASE_URL
2. Check pg_hba.conf for authentication method
3. Reset password if needed:
   ```bash
   sudo -u postgres psql
   postgres=# ALTER USER geminivideo PASSWORD 'new_password';
   ```

### Issue: Database Does Not Exist

**Symptoms:**
```
psycopg2.OperationalError: FATAL: database "geminivideo" does not exist
```

**Solutions:**
1. Create the database:
   ```bash
   sudo -u postgres createdb geminivideo -O geminivideo
   ```
2. Or via psql:
   ```sql
   CREATE DATABASE geminivideo OWNER geminivideo;
   ```

### Issue: Permission Denied

**Symptoms:**
```
psycopg2.errors.InsufficientPrivilege: permission denied for schema public
```

**Solutions:**
```bash
sudo -u postgres psql geminivideo
geminivideo=# GRANT ALL ON SCHEMA public TO geminivideo;
geminivideo=# GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO geminivideo;
```

### Issue: Too Many Connections

**Symptoms:**
```
psycopg2.OperationalError: FATAL: sorry, too many clients already
```

**Solutions:**
1. Use connection pooling in DATABASE_URL
2. Increase max_connections in postgresql.conf
3. Use PgBouncer for connection pooling

## Production Checklist

- [ ] Use strong passwords (at least 32 characters)
- [ ] Enable SSL connections
- [ ] Set up connection pooling
- [ ] Configure backup strategy
- [ ] Enable query logging for debugging
- [ ] Set appropriate connection limits
- [ ] Use read replicas for analytics queries
- [ ] Monitor database performance
- [ ] Set up alerts for connection issues
- [ ] Document disaster recovery procedures

## Security Best Practices

### 1. Strong Passwords

```bash
# Generate secure password
openssl rand -base64 32
```

### 2. SSL Connections

```bash
# Force SSL in DATABASE_URL
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require"
```

### 3. Restrict Network Access

```bash
# Edit pg_hba.conf to restrict access
# Allow only specific IPs
host    geminivideo    geminivideo    10.0.0.0/8    md5
```

### 4. Rotate Credentials Regularly

Update passwords every 90 days and use different passwords for each environment.

## Backup & Restore

### Backup

```bash
# Full database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema only
pg_dump --schema-only $DATABASE_URL > schema_backup.sql

# Data only
pg_dump --data-only $DATABASE_URL > data_backup.sql
```

### Restore

```bash
# Restore from backup
psql $DATABASE_URL < backup_20241205_120000.sql

# Restore from compressed backup
gunzip -c backup_20241205_120000.sql.gz | psql $DATABASE_URL
```

## Performance Tuning

### Recommended postgresql.conf Settings

```ini
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# Connections
max_connections = 100
superuser_reserved_connections = 3

# Query Performance
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_connections = on
log_disconnections = on
```

## Monitoring

### Query Performance

```sql
-- Slow queries
SELECT * FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Support

For database-related issues:

1. Check this guide first
2. Review migration logs
3. Run schema validation: `SELECT * FROM schema_validation_report;`
4. Check database logs
5. Consult PostgreSQL documentation

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Supabase Database Guide](https://supabase.com/docs/guides/database)
- [Google Cloud SQL](https://cloud.google.com/sql/docs)
- [AWS RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
