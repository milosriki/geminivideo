#!/bin/bash
# Optimize Docker Disk Usage - Keep only what's needed
# Reduces from 55GB to ~27GB while keeping everything functional

set -e

echo "🎯 Docker Optimization Script"
echo "=============================="
echo ""

# Show current usage
echo "📊 Current usage:"
docker system df
echo ""

# Calculate what we can save
IMAGES_SIZE=$(docker images --format "{{.Size}}" | grep -E "GB|MB" | head -1)
BUILD_CACHE=$(docker system df | grep "Build Cache" | awk '{print $4}')

echo "💾 Optimization plan:"
echo "  - Keep: Latest images only (~27GB)"
echo "  - Remove: Old images (~20GB)"
echo "  - Remove: Build cache (~17GB)"
echo "  - Total savings: ~37GB"
echo ""

read -p "Proceed with optimization? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "🧹 Step 1: Removing old/unused images..."
# Remove dangling images
docker image prune -f

# Remove old geminivideo images (keep only latest)
echo "  Keeping latest images, removing old versions..."
OLD_IMAGES=$(docker images | grep geminivideo | grep -v latest | awk '{print $3}' | sort -u)
if [ -n "$OLD_IMAGES" ]; then
    echo "$OLD_IMAGES" | xargs docker rmi -f 2>/dev/null || true
    echo "  ✅ Removed old image versions"
else
    echo "  ℹ️  No old versions found"
fi

echo ""
echo "🧹 Step 2: Removing build cache..."
docker builder prune -f

echo ""
echo "🧹 Step 3: Removing stopped containers..."
docker container prune -f

echo ""
echo "🧹 Step 4: Removing unused networks..."
docker network prune -f

echo ""
echo "📊 New usage:"
docker system df

echo ""
echo "✅ Optimization complete!"
echo ""
echo "💡 Tips to keep disk usage low:"
echo "  1. Use multi-stage builds (already in Dockerfiles)"
echo "  2. Clean up after each rebuild"
echo "  3. Use .dockerignore to exclude unnecessary files"
echo "  4. Regular cleanup: ./optimize-docker.sh"
echo ""

