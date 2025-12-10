#!/bin/bash
# Rebuild All Docker Images with Latest Code
# This rebuilds all services with the latest changes

set -e

echo "🔨 Rebuilding All Docker Images"
echo "=============================="
echo ""
echo "This will rebuild all services with latest code..."
echo "This may take 10-15 minutes depending on your system."
echo ""

# Stop running containers
echo "🛑 Stopping running containers..."
docker-compose down 2>/dev/null || true

# Remove old images (optional - uncomment if you want to free space)
# echo "🗑️  Removing old images..."
# docker-compose down --rmi all 2>/dev/null || true

# Rebuild all services
echo ""
echo "🔨 Building all services (parallel build)..."
docker-compose build --no-cache --parallel

echo ""
echo "✅ All images rebuilt successfully!"
echo ""
echo "📋 Rebuilt services:"
docker-compose config --services | grep -v "postgres\|redis\|supabase" | while read service; do
    echo "   ✅ $service"
done

echo ""
echo "🚀 To start all services:"
echo "   docker-compose up -d"
echo ""

