# Database Migrations

This directory contains PostgreSQL database migrations for the GeminiVideo platform.

## Migration Files

| Order | File | Description |
|-------|------|-------------|
| 001 | 001_winner_detection_trigger.sql | Winner detection trigger for automatic RAG indexing |
| 002 | 002_batch_jobs_table.sql | Batch jobs queue and execution failures tracking |

## Running Migrations

### Using psql directly:
```bash
psql -U user -d geminivideo -f migrations/001_winner_detection_trigger.sql
psql -U user -d geminivideo -f migrations/002_batch_jobs_table.sql
```

### Using the migration script:
```bash
./scripts/run-migrations.sh
```

## Migration Guidelines

1. **Naming Convention**: `NNN_description.sql` where NNN is a 3-digit sequence number
2. **Idempotent**: Use `IF NOT EXISTS` and `CREATE OR REPLACE` where possible
3. **Rollback**: Include rollback statements in comments when applicable
4. **Testing**: Test migrations on a dev database before production
5. **Permissions**: Always grant appropriate permissions at the end

## Creating New Migrations

1. Create a new file with the next sequence number
2. Add the migration to this README
3. Test the migration locally
4. Commit with message: `[DB] Add migration NNN: description`
