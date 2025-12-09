#!/bin/bash
# Run all database migrations in order

set -e

DB_URL="${DATABASE_URL:-postgres://user:pass@localhost:5432/geminivideo}"

echo "Running database migrations..."

for migration in migrations/*.sql; do
  echo "Running $migration..."
  psql "$DB_URL" -f "$migration"
  echo "Completed $migration"
done

echo "All migrations completed successfully!"
