#!/bin/bash
# Docker Cleanup Script - Safe cleanup of old/unused Docker data
# Keeps current images, removes old unused ones

set -e

echo "🧹 Docker Cleanup Script"
echo "======================="
echo ""

# Show current usage
echo "📊 Current Docker disk usage:"
docker system df
echo ""

# Ask what to clean
echo "What would you like to clean?"
echo ""
echo "1. Remove unused images (dangling/untagged) - SAFE"
echo "2. Remove old geminivideo images (keep latest) - SAFE"
echo "3. Remove stopped containers - SAFE"
echo "4. Remove unused volumes - CAREFUL (may remove data)"
echo "5. Full cleanup (all unused) - SAFE"
echo "6. Remove old builds (build cache) - SAFE"
echo ""

read -p "Enter choice (1-6) or 'all' for everything safe: " choice

case $choice in
  1)
    echo "🧹 Removing dangling/untagged images..."
    docker image prune -f
    ;;
  2)
    echo "🧹 Removing old geminivideo images (keeping latest)..."
    # Keep latest, remove others
    docker images | grep geminivideo | grep -v latest | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
    echo "✅ Kept latest images, removed old ones"
    ;;
  3)
    echo "🧹 Removing stopped containers..."
    docker container prune -f
    ;;
  4)
    echo "⚠️  Removing unused volumes (this may remove data)..."
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      docker volume prune -f
    else
      echo "Skipped"
    fi
    ;;
  5)
    echo "🧹 Full cleanup (all unused resources)..."
    docker system prune -f
    ;;
  6)
    echo "🧹 Removing build cache..."
    docker builder prune -f
    ;;
  all)
    echo "🧹 Full safe cleanup..."
    echo "  - Removing dangling images..."
    docker image prune -f
    echo "  - Removing old geminivideo images (keeping latest)..."
    docker images | grep geminivideo | grep -v latest | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
    echo "  - Removing stopped containers..."
    docker container prune -f
    echo "  - Removing build cache..."
    docker builder prune -f
    echo ""
    echo "✅ Cleanup complete!"
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "📊 New Docker disk usage:"
docker system df

echo ""
echo "✅ Cleanup complete!"

