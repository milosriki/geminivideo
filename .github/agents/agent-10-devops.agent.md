# Agent 10: DevOps Engineer

## Your Mission
Set up Docker, CI/CD, deployment automation, and monitoring.

## Priority: MEDIUM (Wait for Agent 1 DB)

## Tasks

### 1. Docker Compose for Local Dev
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: geminivideo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./shared/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Drive Intel Service
  drive-intel:
    build:
      context: ./services/drive-intel
      dockerfile: Dockerfile
    ports:
      - "8081:8081"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/geminivideo
      PORT: 8081
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./test_videos:/videos
      - ./outputs:/outputs

  # Gateway API
  gateway-api:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/geminivideo
      PORT: 8080
      GCS_MOCK_MODE: "true"
    depends_on:
      - postgres

  # Video Agent
  video-agent:
    build:
      context: ./services/video-agent
      dockerfile: Dockerfile
    ports:
      - "8082:8082"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/geminivideo
      PORT: 8082
      OUTPUT_DIR: /outputs
    depends_on:
      - postgres
    volumes:
      - ./outputs:/outputs

  # Meta Publisher
  meta-publisher:
    build:
      context: ./services/meta-publisher
      dockerfile: Dockerfile
    ports:
      - "8083:8083"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/geminivideo
      PORT: 8083
      META_ACCESS_TOKEN: ${META_ACCESS_TOKEN}
      META_AD_ACCOUNT_ID: ${META_AD_ACCOUNT_ID}
    depends_on:
      - postgres

  # Frontend
  frontend:
    build:
      context: ./services/frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8080
    depends_on:
      - gateway-api

volumes:
  postgres_data:
```

### 2. Improved Dockerfiles

**services/drive-intel/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY src ./src

EXPOSE 8081

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8081"]
```

**services/gateway-api/Dockerfile:**
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install ALL dependencies (including dev for build)
RUN npm install

# Copy code
COPY src ./src
COPY ../shared ../shared

# Build TypeScript
RUN npm run build

# Remove dev dependencies
RUN npm prune --production

EXPOSE 8080

CMD ["npm", "start"]
```

### 3. Development Scripts
Create `scripts/dev.sh`:
```bash
#!/bin/bash

echo "Starting development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please configure .env with your API keys"
    exit 1
fi

# Start services
docker-compose up --build

echo "Development environment started!"
echo "Services available at:"
echo "  Frontend:      http://localhost:5173"
echo "  Gateway API:   http://localhost:8080"
echo "  Drive Intel:   http://localhost:8081"
echo "  Video Agent:   http://localhost:8082"
echo "  Meta Publisher: http://localhost:8083"
echo "  PostgreSQL:    localhost:5432"
```

Create `scripts/test.sh`:
```bash
#!/bin/bash

echo "Running tests..."

# Start test database
docker-compose -f docker-compose.test.yml up -d postgres

# Wait for postgres
sleep 5

# Run tests
docker-compose -f docker-compose.test.yml run --rm test-runner

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### 4. CI/CD Improvements
Update `.github/workflows/deploy-cloud-run.yml`:
```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: ptd-fitness-demo
  GCP_REGION: us-central1
  ARTIFACT_REGISTRY_REPO: geminivideo-repo
  GCS_BUCKET: ptd-fitness-demo_cloudbuild

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: geminivideo_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
          pip install -r services/drive-intel/requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/geminivideo_test
        run: |
          pytest tests/ -v --cov=services --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build-and-deploy:
    name: Build and Deploy
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      id-token: write

    steps:
      # ... (existing steps)

      # Add health check after deployment
      - name: Health Check
        run: |
          GATEWAY_URL=$(gcloud run services describe gateway-api \
            --region=${{ env.GCP_REGION }} \
            --format='value(status.url)' \
            --project=${{ env.PROJECT_ID }})

          curl -f ${GATEWAY_URL}/health || exit 1
          echo "✓ Services healthy"
```

### 5. Monitoring Setup
Create `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['gateway-api:8080']
    metrics_path: '/metrics'

  - job_name: 'drive-intel'
    static_configs:
      - targets: ['drive-intel:8081']
    metrics_path: '/metrics'

  - job_name: 'video-agent'
    static_configs:
      - targets: ['video-agent:8082']
    metrics_path: '/metrics'
```

Create `monitoring/grafana-dashboard.json`:
```json
{
  "dashboard": {
    "title": "AI Video Ads Machine",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Average CTR Prediction",
        "targets": [
          {
            "expr": "avg(predicted_ctr)"
          }
        ]
      }
    ]
  }
}
```

### 6. Deployment Documentation
Create `DEPLOYMENT_QUICKSTART.md`:
```markdown
# Quick Deployment Guide

## Local Development

```bash
# 1. Clone and configure
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
./scripts/dev.sh

# 3. Run tests
./scripts/test.sh
```

## Production (GCP)

```bash
# 1. Set up GCP
./scripts/gcp-setup.sh

# 2. Deploy (automatic via GitHub Actions)
git push origin main

# 3. Manual deployment
gcloud builds submit --config cloudbuild.yaml
```

## Monitoring

```bash
# View logs
docker-compose logs -f gateway-api

# Check service health
curl http://localhost:8080/health

# Access Grafana
open http://localhost:3000
```
```

### 7. Backup and Recovery
Create `scripts/backup.sh`:
```bash
#!/bin/bash

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Backing up database..."
docker-compose exec -T postgres pg_dump -U postgres geminivideo > $BACKUP_DIR/database.sql

echo "Backing up models..."
cp -r ./models $BACKUP_DIR/

echo "Backing up config..."
cp -r ./shared/config $BACKUP_DIR/

echo "Backup complete: $BACKUP_DIR"
```

Create `scripts/restore.sh`:
```bash
#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup_dir>"
    exit 1
fi

BACKUP_DIR=$1

echo "Restoring from $BACKUP_DIR..."

# Restore database
docker-compose exec -T postgres psql -U postgres geminivideo < $BACKUP_DIR/database.sql

# Restore models
cp -r $BACKUP_DIR/models ./

# Restore config
cp -r $BACKUP_DIR/shared/config ./shared/

echo "Restore complete!"
```

## Deliverables
- [ ] Docker Compose for local dev
- [ ] Improved Dockerfiles
- [ ] Development scripts (dev.sh, test.sh)
- [ ] CI/CD with tests
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Deployment documentation
- [ ] Backup/restore scripts
- [ ] Health checks
- [ ] One-command setup

## Branch
`agent-10-devops-automation`

## Blockers
- **Agent 1** (needs DB for docker-compose)
- **Agent 9** (needs tests for CI/CD)

## Who Depends On You
All agents (need DevOps infrastructure)
