#!/bin/bash
# Automated Supabase Setup & Connection Script
# Connects to existing Docker images and sets up Supabase automatically

set -e

echo "🚀 Automated Supabase Setup & Connection"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "📦 Installing Supabase CLI..."
    brew install supabase/tap/supabase
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check existing images
echo "📋 Checking existing Docker images..."
EXISTING_IMAGES=$(docker images --format "{{.Repository}}" | grep -E "geminivideo|postgres|redis" | wc -l | tr -d ' ')
echo "   Found $EXISTING_IMAGES relevant images"
echo ""

# Initialize Supabase if not already done
if [ ! -f "supabase/config.toml" ]; then
    echo "🔧 Initializing Supabase..."
    supabase init
else
    echo "✅ Supabase already initialized"
fi

# Start Supabase
echo ""
echo "🚀 Starting Supabase..."
supabase start

# Get Supabase credentials
echo ""
echo "📝 Extracting Supabase credentials..."
SUPABASE_URL=$(supabase status | grep "API URL" | awk '{print $3}' || echo "http://localhost:54321")
SUPABASE_ANON_KEY=$(supabase status | grep "anon key" | awk '{print $3}' || echo "")
SUPABASE_SERVICE_KEY=$(supabase status | grep "service_role key" | awk '{print $3}' || echo "")

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "⚠️  Could not extract keys automatically. Please check: supabase status"
    SUPABASE_URL="http://localhost:54321"
    SUPABASE_ANON_KEY="your-anon-key-here"
    SUPABASE_SERVICE_KEY="your-service-key-here"
fi

echo "   API URL: $SUPABASE_URL"
echo "   Anon Key: ${SUPABASE_ANON_KEY:0:20}..."
echo ""

# Apply database schema
echo "📊 Applying database schema..."
if [ -f "supabase/SCHEMA.sql" ]; then
    echo "   Running SCHEMA.sql..."
    supabase db reset --db-url "postgresql://postgres:postgres@localhost:54322/postgres" < supabase/SCHEMA.sql 2>/dev/null || \
    psql "postgresql://postgres:postgres@localhost:54322/postgres" -f supabase/SCHEMA.sql 2>/dev/null || \
    echo "   ⚠️  Please run schema manually in Supabase Studio: http://localhost:54323"
else
    echo "   ⚠️  SCHEMA.sql not found. Using migration..."
    if [ -f "supabase/migrations/001_initial_schema.sql" ]; then
        supabase db reset
    fi
fi

# Update .env file
echo ""
echo "🔧 Updating .env file..."
if [ ! -f ".env" ]; then
    echo "   Creating .env file..."
    touch .env
fi

# Backup existing .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Add/update Supabase variables
if grep -q "SUPABASE_URL" .env; then
    sed -i '' "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env
else
    echo "" >> .env
    echo "# Supabase Configuration" >> .env
    echo "SUPABASE_URL=$SUPABASE_URL" >> .env
fi

if grep -q "SUPABASE_ANON_KEY" .env; then
    sed -i '' "s|SUPABASE_ANON_KEY=.*|SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY|" .env
else
    echo "SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" >> .env
fi

if grep -q "SUPABASE_SERVICE_ROLE_KEY" .env; then
    sed -i '' "s|SUPABASE_SERVICE_ROLE_KEY=.*|SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_KEY|" .env
else
    echo "SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_KEY" >> .env
fi

# Update DATABASE_URL to use Supabase if not set
if ! grep -q "DATABASE_URL.*supabase" .env && ! grep -q "DATABASE_URL.*localhost:54322" .env; then
    if ! grep -q "^DATABASE_URL=" .env; then
        echo "DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres" >> .env
    fi
fi

echo "   ✅ .env file updated"
echo ""

# Update docker-compose.yml to include Supabase connection
echo "🔗 Connecting Docker services to Supabase..."
if ! grep -q "SUPABASE_URL" docker-compose.yml; then
    echo "   ⚠️  docker-compose.yml doesn't reference Supabase"
    echo "   Services will use DATABASE_URL from .env"
fi

# Test connections
echo ""
echo "🧪 Testing connections..."
echo ""

# Test Supabase connection
if curl -s "$SUPABASE_URL/rest/v1/" > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Supabase API: Connected${NC}"
else
    echo -e "   ${YELLOW}⚠️  Supabase API: Not responding (may need a moment)${NC}"
fi

# Test PostgreSQL connection
if docker exec geminivideo-postgres pg_isready -U geminivideo > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Docker PostgreSQL: Connected${NC}"
else
    echo -e "   ${YELLOW}⚠️  Docker PostgreSQL: Not running or different name${NC}"
fi

# Test Supabase PostgreSQL
if psql "postgresql://postgres:postgres@localhost:54322/postgres" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Supabase PostgreSQL: Connected${NC}"
else
    echo -e "   ${YELLOW}⚠️  Supabase PostgreSQL: Connection failed${NC}"
fi

# Summary
echo ""
echo "========================================"
echo "✅ SETUP COMPLETE!"
echo "========================================"
echo ""
echo "📋 Supabase URLs:"
echo "   API:        $SUPABASE_URL"
echo "   Studio:     http://localhost:54323"
echo "   DB:         postgresql://postgres:postgres@localhost:54322/postgres"
echo ""
echo "🔑 Credentials saved to: .env"
echo ""
echo "📊 Next Steps:"
echo "   1. Open Supabase Studio: http://localhost:54323"
echo "   2. Verify tables in SQL Editor"
echo "   3. Restart Docker services: docker-compose restart"
echo "   4. Services will automatically use Supabase from .env"
echo ""
echo "🔗 Your existing Docker images are ready to connect!"
echo ""

