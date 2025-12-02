#!/bin/bash

###############################################################################
# Database Setup Script
# Sets up PostgreSQL database with Prisma for development
###############################################################################

set -e

echo "🚀 Setting up Gateway API Database..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please update DATABASE_URL in .env with your PostgreSQL credentials${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Check if PostgreSQL is running (for local development)
echo "🔍 Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:pass@host:port/db
    DB_HOST=$(echo $DATABASE_URL | sed -E 's/postgresql:\/\/[^@]+@([^:]+).*/\1/')

    if [ "$DB_HOST" = "localhost" ] || [ "$DB_HOST" = "127.0.0.1" ]; then
        echo "📦 Local PostgreSQL detected"

        # Check if PostgreSQL is running
        if pg_isready -h $DB_HOST &> /dev/null; then
            echo -e "${GREEN}✅ PostgreSQL is running${NC}"
        else
            echo -e "${YELLOW}⚠️  PostgreSQL is not running${NC}"
            echo "   You can start it with Docker:"
            echo "   docker-compose up -d postgres"
            exit 1
        fi
    else
        echo "☁️  Remote PostgreSQL detected at $DB_HOST"
    fi
else
    echo "⏭️  Skipping PostgreSQL check (psql not installed)"
fi

echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Generate Prisma Client
echo "🔧 Generating Prisma Client..."
npm run db:generate
echo -e "${GREEN}✅ Prisma Client generated${NC}"
echo ""

# Run migrations
echo "🗃️  Running database migrations..."
read -p "Do you want to apply migrations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run db:migrate
    echo -e "${GREEN}✅ Migrations applied${NC}"
else
    echo -e "${YELLOW}⏭️  Skipped migrations${NC}"
fi
echo ""

# Seed database
echo "🌱 Seeding database..."
read -p "Do you want to seed the database with sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm run db:seed
    echo -e "${GREEN}✅ Database seeded${NC}"
    echo ""
    echo "🔑 Test API Keys:"
    echo "   Admin:      dev_admin_key_12345"
    echo "   Demo:       dev_demo_key_67890"
    echo "   Enterprise: dev_enterprise_key_abcde"
else
    echo -e "${YELLOW}⏭️  Skipped seeding${NC}"
fi

echo ""
echo -e "${GREEN}✨ Database setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Run 'npm run dev' to start the API"
echo "3. Run 'npm run db:studio' to open Prisma Studio"
echo ""
