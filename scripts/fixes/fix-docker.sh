#!/bin/bash
# AGENT 90: DOCKER CONFIGURATION FIXES
# Fixes: wget/curl installation, COPY paths, environment variables
# This script is IDEMPOTENT - safe to run multiple times

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "AGENT 90: DOCKER FIXES"
echo "========================================="
echo "Working directory: $PROJECT_ROOT"
echo ""

FIXES_APPLIED=0
FIXES_FAILED=0

# ============================================
# FIX 1-3: Add wget to node:20-alpine Dockerfiles
# ============================================
echo "[FIX 1/8] Adding wget to Node.js Alpine images..."

NODE_DOCKERFILES=(
    "$PROJECT_ROOT/services/gateway-api/Dockerfile"
    "$PROJECT_ROOT/services/meta-publisher/Dockerfile"
    "$PROJECT_ROOT/services/google-ads/Dockerfile"
)

for dockerfile in "${NODE_DOCKERFILES[@]}"; do
    if [ -f "$dockerfile" ]; then
        if ! grep -q "apk add --no-cache wget" "$dockerfile"; then
            # Add wget installation after WORKDIR
            sed -i '/^WORKDIR/a RUN apk add --no-cache wget' "$dockerfile"
            echo "  ✓ Added wget to $(basename $(dirname "$dockerfile"))/Dockerfile"
            ((FIXES_APPLIED++))
        else
            echo "  ⊘ Already has wget: $(basename $(dirname "$dockerfile"))/Dockerfile"
        fi
    else
        echo "  ⊘ Not found: $dockerfile"
    fi
done

# ============================================
# FIX 4-5: Add curl to python:3.11-slim Dockerfiles
# ============================================
echo "[FIX 2/8] Adding curl to Python slim images..."

PYTHON_DOCKERFILES=(
    "$PROJECT_ROOT/services/ml-service/Dockerfile"
    "$PROJECT_ROOT/services/video-agent/Dockerfile"
)

for dockerfile in "${PYTHON_DOCKERFILES[@]}"; do
    if [ -f "$dockerfile" ]; then
        if ! grep -q "curl" "$dockerfile" || ! grep -q "apt-get install" "$dockerfile"; then
            # Find the apt-get install line and add curl to it
            if grep -q "apt-get install -y" "$dockerfile"; then
                sed -i '/apt-get install -y/,/&&/ s/&&/curl \\\n    \&\&/' "$dockerfile"
                echo "  ✓ Added curl to $(basename $(dirname "$dockerfile"))/Dockerfile"
                ((FIXES_APPLIED++))
            else
                # Add new apt-get install if not exists
                sed -i '/^FROM/a RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*' "$dockerfile"
                echo "  ✓ Added curl installation to $(basename $(dirname "$dockerfile"))/Dockerfile"
                ((FIXES_APPLIED++))
            fi
        else
            echo "  ⊘ Already has curl: $(basename $(dirname "$dockerfile"))/Dockerfile"
        fi
    else
        echo "  ⊘ Not found: $dockerfile"
    fi
done

# ============================================
# FIX 6: Fix COPY shared path in Dockerfiles
# ============================================
echo "[FIX 3/8] Fixing shared directory COPY paths..."

if [ -f "$PROJECT_ROOT/services/gateway-api/Dockerfile" ]; then
    if grep -q "^COPY shared /shared" "$PROJECT_ROOT/services/gateway-api/Dockerfile"; then
        sed -i 's|^COPY shared /shared|COPY ../../shared /shared|g' "$PROJECT_ROOT/services/gateway-api/Dockerfile"
        echo "  ✓ Fixed COPY path in gateway-api/Dockerfile"
        ((FIXES_APPLIED++))
    else
        echo "  ⊘ Already fixed or not using shared directory"
    fi
fi

# ============================================
# FIX 7: Fix titan-core WORKDIR before CMD
# ============================================
echo "[FIX 4/8] Fixing titan-core WORKDIR issue..."

if [ -f "$PROJECT_ROOT/services/titan-core/Dockerfile" ]; then
    if grep -q 'CMD.*cd api' "$PROJECT_ROOT/services/titan-core/Dockerfile"; then
        # Replace cd in CMD with proper WORKDIR
        sed -i '/^CMD/i WORKDIR /app/api' "$PROJECT_ROOT/services/titan-core/Dockerfile"
        sed -i 's|CMD \["sh", "-c", "cd api && uvicorn main:app.*\]|CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]|g' "$PROJECT_ROOT/services/titan-core/Dockerfile"
        echo "  ✓ Fixed WORKDIR and CMD in titan-core/Dockerfile"
        ((FIXES_APPLIED++))
    else
        echo "  ⊘ Already fixed or different CMD structure"
    fi
fi

# ============================================
# FIX 8: Update Node version consistency
# ============================================
echo "[FIX 5/8] Updating Node.js version consistency..."

if [ -f "$PROJECT_ROOT/services/tiktok-ads/Dockerfile" ]; then
    if grep -q "FROM node:18-alpine" "$PROJECT_ROOT/services/tiktok-ads/Dockerfile"; then
        sed -i 's/FROM node:18-alpine/FROM node:20-alpine/g' "$PROJECT_ROOT/services/tiktok-ads/Dockerfile"
        echo "  ✓ Updated tiktok-ads to node:20-alpine"
        ((FIXES_APPLIED++))
    else
        echo "  ⊘ Already using node:20-alpine"
    fi
fi

# ============================================
# FIX 9: Add missing environment variables to .env.example
# ============================================
echo "[FIX 6/8] Adding missing environment variables to .env.example..."

ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

if [ -f "$ENV_EXAMPLE" ]; then
    # Add Firebase config
    if ! grep -q "FIREBASE_SERVICE_ACCOUNT_PATH" "$ENV_EXAMPLE"; then
        cat >> "$ENV_EXAMPLE" << 'EOF'

# Firebase Authentication (ADDED BY AGENT 90)
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
EOF
        echo "  ✓ Added Firebase environment variables"
        ((FIXES_APPLIED++))
    fi

    # Add WebSocket URL
    if ! grep -q "VITE_WS_URL" "$ENV_EXAMPLE"; then
        cat >> "$ENV_EXAMPLE" << 'EOF'

# WebSocket Configuration (ADDED BY AGENT 90)
VITE_WS_URL=ws://localhost:8080
# Production: VITE_WS_URL=wss://api.your-domain.com
EOF
        echo "  ✓ Added WebSocket environment variables"
        ((FIXES_APPLIED++))
    fi

    # Add Meta Pixel ID
    if ! grep -q "VITE_META_PIXEL_ID" "$ENV_EXAMPLE"; then
        cat >> "$ENV_EXAMPLE" << 'EOF'

# Meta Pixel Tracking (ADDED BY AGENT 90)
VITE_META_PIXEL_ID=1234567890123456
EOF
        echo "  ✓ Added Meta Pixel environment variable"
        ((FIXES_APPLIED++))
    fi

    # Add GCS Bucket
    if ! grep -q "GCS_BUCKET" "$ENV_EXAMPLE"; then
        cat >> "$ENV_EXAMPLE" << 'EOF'

# Google Cloud Storage (ADDED BY AGENT 90)
GCS_BUCKET=your-gcs-bucket-name
GCP_PROJECT_ID=your-gcp-project-id
PROJECT_ID=your-gcp-project-id
EOF
        echo "  ✓ Added GCS environment variables"
        ((FIXES_APPLIED++))
    fi

    # Add ENVIRONMENT variable
    if ! grep -q "^ENVIRONMENT=" "$ENV_EXAMPLE"; then
        cat >> "$ENV_EXAMPLE" << 'EOF'

# Runtime Environment (ADDED BY AGENT 90)
ENVIRONMENT=development
# Production: ENVIRONMENT=production
EOF
        echo "  ✓ Added ENVIRONMENT variable"
        ((FIXES_APPLIED++))
    fi
else
    echo "  ⊘ .env.example not found"
fi

# ============================================
# FIX 10: Add DATABASE_URL to docker-compose.yml
# ============================================
echo "[FIX 7/8] Adding DATABASE_URL to gateway-api in docker-compose..."

DOCKER_COMPOSE="$PROJECT_ROOT/docker-compose.yml"

if [ -f "$DOCKER_COMPOSE" ]; then
    if ! grep -A 20 "gateway-api:" "$DOCKER_COMPOSE" | grep -q "DATABASE_URL"; then
        # This requires manual editing due to YAML structure
        echo "  ⚠ WARNING: Manually add DATABASE_URL to gateway-api service:"
        echo "    environment:"
        echo "      DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo"
        ((FIXES_FAILED++))
    else
        echo "  ⊘ Already has DATABASE_URL"
    fi
else
    echo "  ⊘ docker-compose.yml not found"
fi

# ============================================
# FIX 11: Fix prisma copy order in gateway-api Dockerfile
# ============================================
echo "[FIX 8/8] Verifying prisma folder copy order..."

if [ -f "$PROJECT_ROOT/services/gateway-api/Dockerfile" ]; then
    # Check if prisma is copied before npm install
    PRISMA_LINE=$(grep -n "COPY prisma" "$PROJECT_ROOT/services/gateway-api/Dockerfile" | cut -d: -f1)
    NPM_LINE=$(grep -n "RUN npm install" "$PROJECT_ROOT/services/gateway-api/Dockerfile" | cut -d: -f1)

    if [ -n "$PRISMA_LINE" ] && [ -n "$NPM_LINE" ]; then
        if [ $PRISMA_LINE -lt $NPM_LINE ]; then
            echo "  ✓ Prisma folder copied before npm install (correct order)"
        else
            echo "  ⚠ WARNING: Prisma folder copied AFTER npm install - may cause build issues"
            ((FIXES_FAILED++))
        fi
    else
        echo "  ⊘ Could not verify copy order"
    fi
else
    echo "  ⊘ File not found"
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo "========================================="
echo "DOCKER FIXES SUMMARY"
echo "========================================="
echo "Fixes applied: $FIXES_APPLIED"
echo "Fixes requiring manual attention: $FIXES_FAILED"
echo ""

if [ $FIXES_APPLIED -gt 0 ]; then
    echo "✓ Docker configuration fixes have been applied!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Rebuild all Docker images: docker-compose build --no-cache"
    echo "2. Test container health: docker-compose up -d && docker-compose ps"
    echo "3. Check health status: docker inspect <container_id> --format='{{.State.Health.Status}}'"
    echo "4. Run: ./scripts/fixes/verify-fixes.sh"
fi

exit 0
