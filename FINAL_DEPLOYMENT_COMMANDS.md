# Final Deployment Commands - Cheat Sheet

**Quick reference for deploying and validating Gemini Video platform**

---

## Pre-Flight Validation (DO THIS FIRST!)

```bash
# Run comprehensive validation (32 checks)
./scripts/pre-flight.sh

# Expected: ✓✓✓ GO FOR LAUNCH ✓✓✓
# Exit code 0 = GO, Exit code 1 = NO-GO
```

---

## Starting Services

### Option 1: Full Stack (Recommended)
```bash
# Start all services with Docker Compose
docker-compose up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Verify all services are healthy
./scripts/test-connections.sh
```

### Option 2: Individual Services
```bash
# Infrastructure only
docker-compose up -d postgres redis

# Core services
docker-compose up -d gateway-api titan-core ml-service

# Additional services
docker-compose up -d video-agent meta-publisher drive-intel

# Frontend
docker-compose up -d frontend
```

---

## Checking Status

### Health Checks
```bash
# All services
curl http://localhost:8080/health
curl http://localhost:8084/health
curl http://localhost:8003/health
curl http://localhost:8082/health
curl http://localhost:8083/health
curl http://localhost:3000

# Or use the test script
./scripts/test-connections.sh
```

### View Logs
```bash
# All services (live)
docker-compose logs -f

# Specific service
docker-compose logs -f gateway-api
docker-compose logs -f titan-core
docker-compose logs -f ml-service

# Last 50 lines
docker-compose logs --tail=50 gateway-api
```

### Container Status
```bash
# List all containers
docker-compose ps

# Check resource usage
docker stats

# Inspect specific container
docker inspect geminivideo-gateway-api
```

---

## Database Operations

### Initialize Database
```bash
# Create schema and load demo data
python scripts/init_db.py --demo

# Create schema only (no demo data)
python scripts/init_db.py
```

### Connect to Database
```bash
# Via Docker
docker-compose exec postgres psql -U geminivideo -d geminivideo

# Or directly (if installed)
psql postgresql://geminivideo:geminivideo@localhost:5432/geminivideo
```

### Common SQL Queries
```sql
-- Check campaign count
SELECT COUNT(*) FROM campaigns;

-- Check video count
SELECT COUNT(*) FROM videos;

-- View recent performance metrics
SELECT * FROM performance_metrics ORDER BY created_at DESC LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('geminivideo'));
```

### Reset Database
```bash
# Stop services and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d postgres
sleep 10

# Re-initialize
python scripts/init_db.py --demo
```

---

## Redis Operations

### Connect to Redis
```bash
# Via Docker
docker-compose exec redis redis-cli

# Or directly (if installed)
redis-cli
```

### Common Redis Commands
```bash
# Ping Redis
redis-cli PING

# Check keys
redis-cli KEYS "*"

# Get cache statistics
redis-cli INFO stats

# Clear all cache
redis-cli FLUSHALL

# Check memory usage
redis-cli INFO memory
```

---

## Running Tests

### Validation Tests
```bash
# Full pre-flight check
./scripts/pre-flight.sh

# Python validation only
python scripts/final-checklist.py

# With JSON output
python scripts/final-checklist.py --json

# Connection tests
./scripts/test-connections.sh
```

### Integration Tests
```bash
# Run integration tests
./scripts/run_integration_tests.sh

# Or with pytest
cd services/gateway-api
pytest tests/integration/

cd services/ml-service
pytest tests/
```

---

## Stopping Services

### Graceful Stop
```bash
# Stop all services (keeps data)
docker-compose stop

# Stop specific service
docker-compose stop gateway-api
```

### Full Shutdown
```bash
# Stop and remove containers (keeps data)
docker-compose down

# Stop, remove containers AND volumes (deletes data)
docker-compose down -v

# Force stop everything
docker-compose kill
```

---

## Restarting Services

### Restart All
```bash
# Restart all services
docker-compose restart

# Or stop and start
docker-compose down
docker-compose up -d
```

### Restart Specific Service
```bash
# Restart one service
docker-compose restart gateway-api

# Rebuild and restart
docker-compose up -d --build gateway-api
```

---

## Development Workflow

### Making Code Changes

#### Backend Service Changes
```bash
# Edit code in services/<service-name>/

# Rebuild and restart
docker-compose up -d --build <service-name>

# Example: Update gateway-api
vim services/gateway-api/main.py
docker-compose up -d --build gateway-api
```

#### Frontend Changes
```bash
# Edit code in frontend/src/

# If using Docker
docker-compose up -d --build frontend

# If running locally
cd frontend
npm run dev
```

---

## Debugging

### Service Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Check if port is in use
lsof -i :<port>

# Kill process using port
kill -9 <PID>

# Remove and rebuild
docker-compose rm -f <service-name>
docker-compose up -d --build <service-name>
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection from host
psql postgresql://geminivideo:geminivideo@localhost:5432/geminivideo

# Check from container
docker-compose exec gateway-api python -c "import psycopg2; conn = psycopg2.connect('postgresql://geminivideo:geminivideo@postgres:5432/geminivideo'); print('Connected!')"
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli PING

# From container
docker-compose exec gateway-api python -c "import redis; r = redis.from_url('redis://redis:6379'); print(r.ping())"
```

### AI API Issues
```bash
# Check API keys are set
cat .env | grep API_KEY

# Test Gemini
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key=$GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'

# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"Hello"}]}'
```

---

## Investor Demo Preparation

### 24 Hours Before
```bash
# 1. Run full validation
./scripts/pre-flight.sh

# 2. Load demo data
python scripts/init_db.py --demo

# 3. Restart all services (fresh state)
docker-compose down
docker-compose up -d
sleep 30

# 4. Run validation again
./scripts/pre-flight.sh

# 5. Test manually
open http://localhost:3000
```

### 1 Hour Before
```bash
# 1. Restart services
docker-compose restart

# 2. Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# 3. Run validation
./scripts/pre-flight.sh

# 4. Check all URLs
curl -I http://localhost:3000
curl -I http://localhost:8080/health
```

### 5 Minutes Before
```bash
# Final check
./scripts/pre-flight.sh

# Open frontend
open http://localhost:3000

# Have backup ready
cat INVESTOR_DEMO.md
```

---

## Emergency Recovery

### If Demo Crashes
```bash
# Quick restart (30 seconds)
docker-compose restart
sleep 30
./scripts/pre-flight.sh

# Full reset (2 minutes)
docker-compose down
docker-compose up -d
sleep 30
python scripts/init_db.py --demo
./scripts/pre-flight.sh
```

### If Database Corrupted
```bash
# Nuclear option: complete reset
docker-compose down -v
docker-compose up -d postgres
sleep 10
python scripts/init_db.py --demo
docker-compose up -d
sleep 30
./scripts/pre-flight.sh
```

---

## Useful URLs

### Services
- Frontend: http://localhost:3000
- Gateway API: http://localhost:8080
- Titan Core: http://localhost:8084
- ML Service: http://localhost:8003
- Video Agent: http://localhost:8082
- Meta Publisher: http://localhost:8083
- Drive Intel: http://localhost:8081
- TikTok Ads: http://localhost:8085

### API Docs
- Gateway API Docs: http://localhost:8080/docs
- Gateway API ReDoc: http://localhost:8080/redoc

### Health Endpoints
- Gateway: http://localhost:8080/health
- Titan Core: http://localhost:8084/health
- ML Service: http://localhost:8003/health

---

## Environment Variables

### View Current Config
```bash
# Show all env vars
cat .env

# Check specific vars
echo $GEMINI_API_KEY
echo $DATABASE_URL
echo $REDIS_URL
```

### Update Config
```bash
# Edit .env file
nano .env

# Or copy from example
cp .env.example .env
nano .env

# Restart services to pick up changes
docker-compose restart
```

---

## Monitoring

### Resource Usage
```bash
# CPU and memory usage
docker stats

# Disk usage
docker system df

# Network usage
docker network ls
docker network inspect geminivideo_default
```

### Performance
```bash
# Check response times
time curl http://localhost:8080/health
time curl http://localhost:8003/health

# Load testing (if hey is installed)
hey -n 100 -c 10 http://localhost:8080/health
```

---

## Production Deployment

### GCP Cloud Run
```bash
# Deploy all services
./scripts/deploy-production.sh

# Or individual service
gcloud run deploy gateway-api \
  --source=./services/gateway-api \
  --region=us-central1
```

### Docker Production
```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# With environment
NODE_ENV=production docker-compose -f docker-compose.production.yml up -d
```

---

## Backup and Restore

### Backup Database
```bash
# Export database
docker-compose exec -T postgres pg_dump -U geminivideo geminivideo > backup-$(date +%Y%m%d).sql

# Compress backup
gzip backup-$(date +%Y%m%d).sql
```

### Restore Database
```bash
# Import backup
docker-compose exec -T postgres psql -U geminivideo geminivideo < backup-20251205.sql

# Or from compressed
gunzip -c backup-20251205.sql.gz | docker-compose exec -T postgres psql -U geminivideo geminivideo
```

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | `lsof -i :8080` then `kill -9 <PID>` |
| Service won't start | `docker-compose logs <service>` |
| Database connection failed | `docker-compose restart postgres` |
| Redis connection failed | `docker-compose restart redis` |
| Out of memory | `docker system prune -a` |
| Slow performance | `docker stats` to check resources |
| Can't connect to frontend | Check firewall, try http://127.0.0.1:3000 |
| AI API rate limited | Use lower tier or enable mock mode |

---

## Documentation

### Read Docs
```bash
# Main deployment guide
cat DEPLOYMENT.md

# Investor demo guide
cat INVESTOR_DEMO.md

# Agent 60 summary
cat AGENT_60_FINAL_DEPLOYMENT_SUMMARY.md

# Quick start validation
cat QUICK_START_FINAL_VALIDATION.md
```

### Find Files
```bash
# Find all Python files
find . -name "*.py" -type f

# Find all config files
find . -name "*.yml" -o -name "*.yaml"

# Find all docs
find . -name "*.md"
```

---

## One-Line Wonders

```bash
# Start everything and validate
docker-compose up -d && sleep 30 && ./scripts/pre-flight.sh

# Restart and test
docker-compose restart && sleep 10 && ./scripts/test-connections.sh

# View all logs (last 50 lines)
docker-compose logs --tail=50

# Check if all ports are open
for port in 5432 6379 3000 8080 8081 8082 8003 8083 8084 8085; do nc -zv localhost $port; done

# Quick health check
for url in http://localhost:{8080,8084,8003,8082,8083}/health; do echo "Checking $url..."; curl -s $url | jq -r '.status // "ERROR"'; done

# Clear everything and start fresh
docker-compose down -v && docker-compose up -d && sleep 30 && python scripts/init_db.py --demo && ./scripts/pre-flight.sh
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success / GO |
| 1 | Failure / NO-GO |
| 130 | Interrupted (Ctrl+C) |
| 2 | Fatal error |

---

**Keep this file handy during demo day! 🚀**

---

*Cheat Sheet created by Agent 60: Final Deployment Checklist*
*Last Updated: December 5, 2025*
