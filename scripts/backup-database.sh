#!/bin/bash

# Database Backup Script
# Creates a backup of your Supabase database

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "📦 Database Backup Script"
echo "========================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get connection string from env or prompt
DB_URL="${SUPABASE_DB_URL}"

if [ -z "$DB_URL" ]; then
    echo -e "${YELLOW}⚠️  SUPABASE_DB_URL not set in environment${NC}"
    echo ""
    echo "Please provide database connection string:"
    read -p "DB URL: " DB_URL
    
    if [ -z "$DB_URL" ]; then
        echo -e "${RED}❌ Database URL required${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Database URL found${NC}"
echo ""

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}❌ pg_dump not found${NC}"
    echo ""
    echo "Install PostgreSQL client:"
    echo "  macOS: brew install postgresql"
    echo "  Linux: sudo apt-get install postgresql-client"
    exit 1
fi

echo "📦 Creating backup..."
echo "   File: $BACKUP_FILE"
echo ""

# Create backup
if pg_dump "$DB_URL" --file="$BACKUP_FILE" --verbose 2>&1 | grep -v "pg_dump: warning"; then
    echo ""
    echo -e "${GREEN}✅ Backup created successfully${NC}"
else
    echo ""
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "📊 Size: $FILE_SIZE"
echo ""

# Compress backup
echo "🗜️  Compressing backup..."
gzip "$BACKUP_FILE"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)

echo -e "${GREEN}✅ Compressed: $COMPRESSED_FILE${NC}"
echo "📊 Compressed size: $COMPRESSED_SIZE"
echo ""

# Keep only last 10 backups
echo "🧹 Cleaning old backups (keeping last 10)..."
cd "$BACKUP_DIR"
BACKUP_COUNT=$(ls -1 backup_*.sql.gz 2>/dev/null | wc -l | tr -d ' ')

if [ "$BACKUP_COUNT" -gt 10 ]; then
    ls -t backup_*.sql.gz | tail -n +11 | xargs rm -f
    echo -e "${GREEN}✅ Removed old backups${NC}"
else
    echo "ℹ️  No old backups to remove (have $BACKUP_COUNT backups)"
fi

echo ""
echo -e "${GREEN}✅ Backup complete!${NC}"
echo ""
echo "📁 Backup location: $COMPRESSED_FILE"
echo ""
echo "💡 To restore:"
echo "   gunzip < $COMPRESSED_FILE | psql \"\$SUPABASE_DB_URL\""

