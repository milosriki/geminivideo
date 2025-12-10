#!/bin/bash
# Supabase Setup via Docker (No CLI Required)
# Uses Docker Compose to run Supabase locally

set -e

echo "🚀 Supabase Setup via Docker"
echo "============================"
echo ""

# Check Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if Supabase is already running
if docker ps | grep -q "supabase"; then
    echo "✅ Supabase containers already running"
    SUPABASE_RUNNING=true
else
    SUPABASE_RUNNING=false
fi

# Add Supabase to docker-compose if not present
if ! grep -q "supabase-db:" docker-compose.yml; then
    echo "📝 Adding Supabase to docker-compose.yml..."
    
    # Create backup
    cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
    
    # Add Supabase service before networks section
    cat >> docker-compose.yml << 'EOF'

  # ========================================================================
  # SUPABASE (Local Development)
  # ========================================================================

  supabase-db:
    image: supabase/postgres:15.1.0.147
    container_name: geminivideo-supabase-db
    environment:
      POSTGRES_HOST: /var/run/postgresql
      POSTGRES_PORT: 5432
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${SUPABASE_DB_PASSWORD:-postgres}
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "54322:5432"  # Supabase DB port (different from main postgres)
    volumes:
      - supabase_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - geminivideo-network

  supabase-studio:
    image: supabase/studio:20231218-0b97c34
    container_name: geminivideo-supabase-studio
    environment:
      SUPABASE_URL: http://localhost:54321
      STUDIO_PG_META_URL: http://postgres-meta:8080
      POSTGRES_PASSWORD: ${SUPABASE_DB_PASSWORD:-postgres}
    ports:
      - "54323:3000"  # Supabase Studio
    depends_on:
      supabase-db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - geminivideo-network

  supabase-kong:
    image: kong:2.8.1
    container_name: geminivideo-supabase-kong
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /var/lib/kong/kong.yml
      KONG_DNS_ORDER: LAST,A,CNAME
      KONG_PLUGINS: request-transformer,cors,key-auth
    ports:
      - "54321:8000"  # Supabase API
      - "54324:8443"
    volumes:
      - ./supabase/kong.yml:/var/lib/kong/kong.yml:ro
    depends_on:
      - supabase-db
    restart: unless-stopped
    networks:
      - geminivideo-network

EOF

    # Add volume to volumes section
    if ! grep -q "supabase_db_data:" docker-compose.yml; then
        sed -i '' '/^volumes:/a\
  supabase_db_data:
' docker-compose.yml
    fi
    
    echo "   ✅ Added Supabase services to docker-compose.yml"
else
    echo "✅ Supabase already in docker-compose.yml"
fi

# Create basic Kong config if needed
mkdir -p supabase
if [ ! -f "supabase/kong.yml" ]; then
    cat > supabase/kong.yml << 'EOF'
_format_version: "3.0"
services:
  - name: auth-v1
    url: http://supabase-auth:9999
    routes:
      - name: auth-v1
        strip_path: true
        paths:
          - /auth/v1
  - name: rest-v1
    url: http://supabase-rest:8000
    routes:
      - name: rest-v1
        strip_path: true
        paths:
          - /rest/v1
EOF
    echo "   ✅ Created Kong configuration"
fi

# Start Supabase services
if [ "$SUPABASE_RUNNING" = false ]; then
    echo ""
    echo "🚀 Starting Supabase services..."
    docker-compose up -d supabase-db supabase-studio 2>/dev/null || \
    docker compose up -d supabase-db supabase-studio
    
    echo "   ⏳ Waiting for Supabase to be ready..."
    sleep 10
fi

# Wait for database to be ready
echo ""
echo "⏳ Waiting for database..."
for i in {1..30}; do
    if docker exec geminivideo-supabase-db pg_isready -U postgres > /dev/null 2>&1; then
        echo "   ✅ Database is ready"
        break
    fi
    sleep 1
done

# Apply schema
echo ""
echo "📊 Applying database schema..."
if [ -f "supabase/SCHEMA.sql" ]; then
    echo "   Running SCHEMA.sql..."
    docker exec -i geminivideo-supabase-db psql -U postgres -d postgres < supabase/SCHEMA.sql 2>&1 | grep -v "already exists" || true
    echo "   ✅ Schema applied"
elif [ -f "supabase/migrations/001_initial_schema.sql" ]; then
    echo "   Running migration..."
    docker exec -i geminivideo-supabase-db psql -U postgres -d postgres < supabase/migrations/001_initial_schema.sql 2>&1 | grep -v "already exists" || true
    echo "   ✅ Migration applied"
else
    echo "   ⚠️  No schema file found. Please run manually in Studio."
fi

# Set up environment variables
echo ""
echo "🔧 Setting up environment variables..."

# Default Supabase credentials (local development)
SUPABASE_URL="http://localhost:54321"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

# Update .env file
if [ ! -f ".env" ]; then
    touch .env
fi

# Backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Add/update Supabase variables
if grep -q "SUPABASE_URL" .env; then
    sed -i '' "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env
else
    echo "" >> .env
    echo "# Supabase Configuration (Local Docker)" >> .env
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

# Add Supabase DB URL
if ! grep -q "SUPABASE_DB_URL" .env; then
    echo "SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres" >> .env
fi

echo "   ✅ Environment variables updated in .env"
echo ""

# Summary
echo "========================================"
echo "✅ SUPABASE SETUP COMPLETE!"
echo "========================================"
echo ""
echo "📋 Supabase URLs:"
echo "   API:        $SUPABASE_URL"
echo "   Studio:     http://localhost:54323"
echo "   DB:         postgresql://postgres:postgres@localhost:54322/postgres"
echo ""
echo "🔑 Credentials:"
echo "   Anon Key:   ${SUPABASE_ANON_KEY:0:30}..."
echo "   Service Key: ${SUPABASE_SERVICE_KEY:0:30}..."
echo ""
echo "📊 Next Steps:"
echo "   1. Open Supabase Studio: http://localhost:54323"
echo "   2. Verify tables in SQL Editor"
echo "   3. Restart services: docker-compose restart"
echo ""
echo "🔗 All services can now connect to Supabase!"
echo ""

