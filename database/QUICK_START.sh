#!/bin/bash
# =============================================================================
# Database Quick Start Script
# =============================================================================

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           GeminiVideo Database Quick Start                       ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is not set"
    echo ""
    echo "Please set DATABASE_URL. Examples:"
    echo ""
    echo "Local PostgreSQL:"
    echo "  export DATABASE_URL='postgresql://geminivideo:password@localhost:5432/geminivideo'"
    echo ""
    echo "Supabase:"
    echo "  export DATABASE_URL='postgresql://postgres:password@db.project.supabase.co:5432/postgres'"
    echo ""
    echo "See .env.database.example for more options"
    exit 1
fi

echo "✓ DATABASE_URL is set"
echo ""

# Test connection
echo "Testing database connection..."
if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✓ Connection successful"
else
    echo "❌ Connection failed"
    echo ""
    echo "Check your DATABASE_URL and ensure PostgreSQL is running"
    exit 1
fi

echo ""
echo "Running migrations..."
python /home/user/geminivideo/database/migrations/run_migrations.py

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                     Setup Complete!                               ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Verify schema: psql \$DATABASE_URL -c 'SELECT * FROM schema_health_report;'"
echo "  2. Check for issues: psql \$DATABASE_URL -c 'SELECT * FROM schema_validation_report;'"
echo "  3. List tables: psql \$DATABASE_URL -c '\\dt'"
echo ""
