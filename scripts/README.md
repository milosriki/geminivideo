# Service Startup Orchestration

€5M Investment-Grade Ad Platform - Service Management System

## Overview

This directory contains scripts for managing the complete lifecycle of all microservices in the platform. The orchestration system handles:

- **Correct startup order** based on dependencies
- **Health checks** between each service
- **Graceful shutdown** in reverse dependency order
- **Development and production** modes
- **Direct process** and **Docker** modes

## Architecture

### Services

1. **Infrastructure** (PostgreSQL, Redis) - Port 5432, 6379
2. **Core Backend**
   - ML Service (Python/FastAPI) - Port 8003
   - Titan Core (Python/FastAPI) - Port 8084
   - Video Agent (Python/FastAPI) - Port 8082
   - Drive Intel (Python/FastAPI) - Port 8081
3. **Publishing Services**
   - Meta Publisher (Node.js/Express) - Port 8083
   - TikTok Ads (Python/FastAPI) - Port 8085
4. **Gateway & Frontend**
   - Gateway API (Node.js/Express) - Port 8080
   - Frontend (Next.js) - Port 3000
5. **Workers**
   - Drive Worker (Python/Celery)
   - Video Worker (Python/Celery)

### Dependencies

```
PostgreSQL & Redis (Infrastructure)
    ↓
ML Service, Titan Core, Video Agent, Drive Intel (Core Backend)
    ↓
Meta Publisher, TikTok Ads (Publishing Services)
    ↓
Gateway API (Unified API Gateway)
    ↓
Frontend (Web UI)
    +
Workers (Background Processing)
```

## Scripts

### start-services.sh

Starts all services in the correct order with health checks.

**Usage:**
```bash
# Development mode with Docker (default)
./scripts/start-services.sh

# Production mode with Docker
./scripts/start-services.sh --prod

# Direct process mode (no Docker for services, databases in Docker)
./scripts/start-services.sh --direct

# Help
./scripts/start-services.sh --help
```

**Features:**
- ✅ Dependency-aware startup order
- ✅ Health checks between each phase
- ✅ Colored output showing status
- ✅ Automatic failure detection
- ✅ Service URLs displayed on success
- ✅ Log locations provided

**Phases:**
1. **Infrastructure** - Start PostgreSQL and Redis
2. **Core Backend** - Start ML Service, Titan Core, Video Agent, Drive Intel
3. **Publishing Services** - Start Meta Publisher, TikTok Ads
4. **Gateway & Workers** - Start Gateway API and background workers
5. **Frontend** - Start web UI
6. **Final Health Check** - Verify all services

### health-check.sh

Checks the health of all services and returns a comprehensive report.

**Usage:**
```bash
# Text output (default)
./scripts/health-check.sh

# JSON output
./scripts/health-check.sh json
```

**Features:**
- ✅ Checks all services systematically
- ✅ Shows response times
- ✅ Returns JSON or text format
- ✅ Exit code 0 if healthy, 1 if unhealthy
- ✅ Color-coded status indicators

**Example Text Output:**
```
════════════════════════════════════════════════════════════
             HEALTH CHECK - All Services
════════════════════════════════════════════════════════════

✓ postgres              http://localhost:5432 - Database ready
✓ redis                 http://localhost:6379 - Redis ready
✓ ml-service            http://localhost:8003/health - OK (25ms)
✓ titan-core            http://localhost:8084/health - OK (18ms)
...
════════════════════════════════════════════════════════════
Overall Status: HEALTHY ✓
════════════════════════════════════════════════════════════
```

**Example JSON Output:**
```json
{
  "timestamp": "2025-12-05T16:00:00Z",
  "services": {
    "postgres": {
      "status": "healthy",
      "port": 5432,
      "endpoint": "",
      "message": "Database ready"
    },
    "ml-service": {
      "status": "healthy",
      "port": 8003,
      "endpoint": "/health",
      "message": "OK",
      "response_time_ms": 25
    }
  },
  "overall_status": "healthy"
}
```

### stop-services.sh

Stops all services gracefully in reverse dependency order.

**Usage:**
```bash
# Graceful shutdown (default)
./scripts/stop-services.sh

# Force stop (immediate)
./scripts/stop-services.sh --force

# Stop direct processes (not Docker)
./scripts/stop-services.sh --direct

# Help
./scripts/stop-services.sh --help
```

**Features:**
- ✅ Reverse dependency order
- ✅ Graceful shutdown with cleanup
- ✅ Force mode for immediate stop
- ✅ Waits for connections to close
- ✅ Status display after shutdown

**Phases:**
1. **Frontend** - Stop web UI
2. **Gateway** - Stop API gateway
3. **Workers** - Stop background workers
4. **Publishing Services** - Stop Meta Publisher, TikTok Ads
5. **Core Backend** - Stop Drive Intel, Video Agent, Titan Core, ML Service
6. **Infrastructure** - Stop Redis and PostgreSQL

## Docker Compose Files

### docker-compose.yml

Base configuration for all services with:
- Service definitions
- Port mappings
- Volume mounts
- Health checks
- Dependency chains
- Restart policies
- Network configuration

**Usage:**
```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d ml-service

# View logs
docker compose logs -f [service-name]

# Stop all services
docker compose down

# Remove volumes
docker compose down -v
```

### docker-compose.prod.yml

Production overrides with:
- Resource limits (CPU, memory)
- Logging configuration
- Restart policies (always)
- Performance optimizations
- Worker replicas
- Production environment variables

**Usage:**
```bash
# Start in production mode
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop production services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# View production logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

**Resource Allocation:**
- **Total CPUs:** ~20 cores (limits)
- **Total Memory:** ~40GB (limits)
- **Recommended Hardware:** 32 cores, 64GB RAM, 500GB SSD

## Health Endpoints

All services implement a `/health` endpoint that returns:

```json
{
  "status": "healthy",
  "service": "service-name",
  "uptime": 3600
}
```

### Service Health Endpoints

| Service | Endpoint | Port |
|---------|----------|------|
| PostgreSQL | `pg_isready` | 5432 |
| Redis | `redis-cli ping` | 6379 |
| ML Service | `/health` | 8003 |
| Titan Core | `/health` | 8084 |
| Video Agent | `/health` | 8082 |
| Drive Intel | `/health` | 8081 |
| Meta Publisher | `/health` | 8083 |
| TikTok Ads | `/health` | 8085 |
| Gateway API | `/health` | 8080 |
| Frontend | `/` | 3000 |

## Monitoring

### Real-time Logs

**Docker mode:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ml-service

# Last 100 lines
docker compose logs -f --tail=100 gateway-api
```

**Direct mode:**
```bash
# View logs
tail -f logs/ml-service.log

# View all logs
tail -f logs/*.log
```

### Resource Usage

```bash
# Docker stats
docker stats

# Specific container
docker stats geminivideo-ml-service

# Container processes
docker compose top
```

### Health Monitoring

```bash
# Continuous health checks (every 30 seconds)
watch -n 30 ./scripts/health-check.sh

# JSON monitoring
watch -n 30 './scripts/health-check.sh json | jq .'
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   docker compose logs [service-name]
   ```

2. Check dependencies:
   ```bash
   docker compose ps
   ```

3. Restart specific service:
   ```bash
   docker compose restart [service-name]
   ```

### Health Check Fails

1. Verify service is running:
   ```bash
   docker compose ps
   ```

2. Test endpoint manually:
   ```bash
   curl http://localhost:8003/health
   ```

3. Check service logs for errors:
   ```bash
   docker compose logs [service-name]
   ```

### Port Conflicts

1. Check what's using the port:
   ```bash
   lsof -i :8080
   ```

2. Change port in docker-compose.yml or stop conflicting service

### Out of Resources

1. Check Docker resources:
   ```bash
   docker system df
   ```

2. Clean up unused resources:
   ```bash
   docker system prune -a
   ```

3. Adjust resource limits in `docker-compose.prod.yml`

## Production Deployment

### Initial Setup

1. **Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env with production credentials
   ```

2. **Build Images:**
   ```bash
   docker compose build
   ```

3. **Start Services:**
   ```bash
   ./scripts/start-services.sh --prod
   ```

### Daily Operations

**Start:**
```bash
./scripts/start-services.sh --prod
```

**Health Check:**
```bash
./scripts/health-check.sh
```

**Stop:**
```bash
./scripts/stop-services.sh
```

**Logs:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Backup & Recovery

**Database Backup:**
```bash
docker compose exec postgres pg_dump -U geminivideo geminivideo > backup.sql
```

**Database Restore:**
```bash
cat backup.sql | docker compose exec -T postgres psql -U geminivideo geminivideo
```

**Redis Backup:**
```bash
docker compose exec redis redis-cli SAVE
```

### Scaling Workers

```bash
# Scale video workers to 5 instances
docker compose up -d --scale video-worker=5

# Scale drive workers to 3 instances
docker compose up -d --scale drive-worker=3
```

## Development Workflow

### Local Development

1. **Start infrastructure only:**
   ```bash
   docker compose up -d postgres redis
   ```

2. **Start services directly:**
   ```bash
   ./scripts/start-services.sh --direct
   ```

3. **Develop with hot reload:**
   - Python services: auto-reload enabled
   - Node.js services: `npm run dev`
   - Frontend: Vite hot module replacement

4. **Stop when done:**
   ```bash
   ./scripts/stop-services.sh --direct
   ```

### Testing Changes

1. **Build and test:**
   ```bash
   docker compose build [service-name]
   docker compose up -d [service-name]
   ```

2. **Check health:**
   ```bash
   ./scripts/health-check.sh
   ```

3. **View logs:**
   ```bash
   docker compose logs -f [service-name]
   ```

## Service URLs

After successful startup, access services at:

- **Frontend:** http://localhost:3000
- **Gateway API:** http://localhost:8080
- **Drive Intel:** http://localhost:8081
- **Video Agent:** http://localhost:8082
- **Meta Publisher:** http://localhost:8083
- **Titan Core:** http://localhost:8084
- **TikTok Ads:** http://localhost:8085
- **ML Service:** http://localhost:8003
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## API Documentation

- **Gateway API:** http://localhost:8080/docs
- **ML Service:** http://localhost:8003/docs
- **Video Agent:** http://localhost:8082/docs
- **Titan Core:** http://localhost:8084/docs

## Support

For issues or questions:
1. Check logs: `docker compose logs [service-name]`
2. Run health check: `./scripts/health-check.sh`
3. Review this documentation
4. Check service-specific README files

## Investment-Grade Features

✅ **Dependency Management** - Correct startup order
✅ **Health Monitoring** - Comprehensive health checks
✅ **Graceful Degradation** - Handles partial failures
✅ **Resource Management** - Production resource limits
✅ **Logging** - Structured logging with rotation
✅ **Monitoring** - Real-time status tracking
✅ **Scalability** - Worker scaling support
✅ **Security** - Production security settings
✅ **Backup** - Database backup procedures
✅ **Recovery** - Disaster recovery procedures

---

**€5M Investment-Grade Platform** - Production-Ready Service Orchestration
