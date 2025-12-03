# Troubleshooting Guide

**Gemini Video Platform - Troubleshooting & Support**
Version: 1.0.0
Last Updated: 2025-12-02

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Service-Specific Issues](#service-specific-issues)
3. [Debug Logging](#debug-logging)
4. [Health Checks](#health-checks)
5. [Performance Issues](#performance-issues)
6. [Support Contacts](#support-contacts)

---

## Common Issues

### Issue: Services Won't Start

**Symptoms:**
- Docker containers exit immediately
- "Error: Cannot connect to database"
- Services in crash loop

**Solutions:**

1. **Check environment variables:**
```bash
# Verify .env.production exists
ls -la .env.production

# Check for syntax errors
cat .env.production | grep "="

# Common issue: Missing quotes around values with special chars
# Wrong: PASSWORD=abc$123
# Right: PASSWORD="abc$123"
```

2. **Verify database is running:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U geminivideo -c "SELECT 1"

# Expected: Returns "1"
```

3. **Check Docker resources:**
```bash
# View Docker stats
docker stats

# Ensure enough memory allocated (8GB minimum)
# Docker Desktop > Settings > Resources > Memory
```

4. **View service logs:**
```bash
# Gateway API logs
docker-compose logs gateway-api

# Look for specific error:
# "ECONNREFUSED" -> Database not ready
# "ENOTFOUND" -> DNS/network issue
# "MODULE_NOT_FOUND" -> Dependency issue
```

**Fix:**
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Rebuild if needed
docker-compose up -d --build
```

---

### Issue: 500 Internal Server Error

**Symptoms:**
- API returns 500 status
- "Internal Server Error" in browser
- Empty response body

**Solutions:**

1. **Check logs for stack trace:**
```bash
# Gateway API logs
docker-compose logs gateway-api | grep ERROR

# Common errors:
# - "Cannot read property of undefined" -> Null pointer
# - "ECONNREFUSED" -> Downstream service down
# - "Timeout" -> Service not responding
```

2. **Verify all services are healthy:**
```bash
# Check health of all services
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8082/health

# Expected: {"status":"healthy"}
```

3. **Test database connection:**
```bash
docker-compose exec postgres psql -U geminivideo -d geminivideo -c "\dt"

# Should list all tables
# If empty: Run migrations
```

4. **Check for missing API keys:**
```bash
# Verify in .env.production
grep "GEMINI_API_KEY" .env.production
grep "META_ACCESS_TOKEN" .env.production

# Ensure values are set (not empty)
```

---

### Issue: Video Analysis Stuck

**Symptoms:**
- Analysis status: "processing" for >10 minutes
- No progress updates
- Queue never empties

**Solutions:**

1. **Check worker status:**
```bash
# View drive-worker logs
docker-compose logs drive-worker

# Look for:
# - "Processing asset_id: ..." -> Worker is working
# - "Error:" -> Worker crashed
# - Nothing -> Worker not running
```

2. **Check Redis queue:**
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check queue depth
> LLEN analysis_jobs

# View queued jobs
> LRANGE analysis_jobs 0 -1

# Clear stuck jobs (⚠️ use with caution)
> DEL analysis_jobs
```

3. **Restart workers:**
```bash
# Restart drive worker
docker-compose restart drive-worker

# Restart video worker
docker-compose restart video-worker

# Check logs
docker-compose logs -f drive-worker
```

4. **Check for resource exhaustion:**
```bash
# View resource usage
docker stats drive-intel drive-worker

# If CPU at 100% or memory at limit:
# - Increase resources in docker-compose.yml
# - Reduce concurrent jobs
```

---

### Issue: Unable to Upload Videos

**Symptoms:**
- Upload fails with "413 Payload Too Large"
- Upload stalls at 0%
- "Network error" during upload

**Solutions:**

1. **Check file size:**
```bash
# Max file size: 500 MB
ls -lh /path/to/video.mp4

# If larger than 500 MB:
# - Compress video
# - Split into chunks
# - Contact support for enterprise plan
```

2. **Check Nginx/reverse proxy limits:**
```bash
# In nginx.conf or docker-compose.yml
client_max_body_size 500M;

# Restart after change
docker-compose restart frontend
```

3. **Test with curl:**
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/videos/test.mp4",
    "filename": "test.mp4"
  }'

# Should return: {"asset_id": "...", "status": "queued"}
```

4. **Check network timeout:**
```bash
# Increase timeout in gateway-api/src/index.ts
server.timeout = 600000; // 10 minutes
```

---

### Issue: High Memory Usage

**Symptoms:**
- Container OOMKilled (Out of Memory)
- System becomes slow
- "Cannot allocate memory" errors

**Solutions:**

1. **Identify memory hog:**
```bash
# View memory usage by container
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# Common culprits:
# - ml-service (ML models loaded)
# - drive-intel (video processing)
# - video-agent (FFmpeg rendering)
```

2. **Increase container limits:**
```yaml
# In docker-compose.production.yml
ml-service:
  deploy:
    resources:
      limits:
        memory: 16G  # Increase from 8G
```

3. **Optimize ML model loading:**
```python
# In ml-service, lazy load models
def load_model():
    if not hasattr(load_model, 'model'):
        load_model.model = joblib.load('model.pkl')
    return load_model.model
```

4. **Enable memory limits in Docker:**
```bash
# Docker Desktop > Settings > Resources
# Memory: Set to 12 GB (if available)
# Swap: Set to 2 GB
```

---

### Issue: Redis Connection Failed

**Symptoms:**
- "ECONNREFUSED 127.0.0.1:6379"
- "Redis connection lost"
- Rate limiting not working

**Solutions:**

1. **Check Redis status:**
```bash
# Is Redis running?
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Expected: PONG
```

2. **Verify Redis URL:**
```bash
# In .env.production
REDIS_URL=redis://redis:6379

# Note: Use service name "redis", not "localhost"
```

3. **Check Redis logs:**
```bash
docker-compose logs redis

# Look for:
# - "Ready to accept connections" -> Good
# - "Out of memory" -> Increase memory limit
# - "Max number of clients reached" -> Increase max clients
```

4. **Restart Redis:**
```bash
docker-compose restart redis

# If data corruption suspected:
docker-compose down
docker volume rm geminivideo_redis_data
docker-compose up -d
```

---

### Issue: Meta API Errors

**Symptoms:**
- "Invalid OAuth 2.0 Access Token"
- "Application does not have permission"
- Campaign creation fails

**Solutions:**

1. **Verify access token:**
```bash
# Test token with curl
curl -G \
  -d "access_token=YOUR_TOKEN" \
  https://graph.facebook.com/v19.0/me

# Should return user info
# If error: Token expired or invalid
```

2. **Check token permissions:**
```bash
curl -G \
  -d "access_token=YOUR_TOKEN" \
  -d "fields=permissions" \
  https://graph.facebook.com/v19.0/me/permissions

# Required: ads_management, ads_read, business_management
```

3. **Regenerate long-lived token:**
```bash
# Exchange short-lived for long-lived token
curl -G \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "fb_exchange_token=SHORT_LIVED_TOKEN" \
  https://graph.facebook.com/v19.0/oauth/access_token

# Update META_ACCESS_TOKEN in .env.production
```

4. **Verify Ad Account ID:**
```bash
# List your ad accounts
curl -G \
  -d "access_token=YOUR_TOKEN" \
  https://graph.facebook.com/v19.0/me/adaccounts

# Use format: act_1234567890
```

---

## Service-Specific Issues

### Gateway API

**Issue: CORS errors**

```
Access to fetch at 'http://localhost:8080/api/assets' from origin
'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
```typescript
// In gateway-api/src/index.ts
const corsConfig = {
  origin: [
    'http://localhost:3000',
    'http://localhost:5173',  // Vite dev server
    'https://your-production-domain.com'
  ],
  credentials: true
};

app.use(cors(corsConfig));
```

---

### Drive Intel

**Issue: YOLOv8 model not found**

```
FileNotFoundError: [Errno 2] No such file or directory: 'yolov8n.pt'
```

**Solution:**
```bash
# Download model manually
cd services/drive-intel
mkdir -p models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt

# Or in Python:
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Auto-downloads
```

---

### Video Agent

**Issue: FFmpeg not found**

```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solution:**
```bash
# Install FFmpeg in container
# In services/video-agent/Dockerfile
RUN apt-get update && apt-get install -y ffmpeg

# Verify installation
docker-compose exec video-agent ffmpeg -version
```

---

### ML Service

**Issue: Model prediction errors**

```
ValueError: X has 75 features, but XGBoostRegressor is expecting 80 features
```

**Solution:**
```python
# Feature mismatch - retrain model or fix feature extraction
# Check feature count
print(f"Features extracted: {len(features)}")
print(f"Features expected: {model.n_features_in_}")

# Ensure feature extraction matches training
# Common issue: Missing features or wrong order
```

---

## Debug Logging

### Enable Debug Mode

**Gateway API (Node.js):**
```bash
# In .env.production
DEBUG=express:*,app:*
LOG_LEVEL=debug

# Or at runtime
docker-compose exec gateway-api sh -c "export DEBUG=* && npm run dev"
```

**Python Services:**
```bash
# In .env.production
LOG_LEVEL=DEBUG
PYTHONPATH=/app

# View detailed logs
docker-compose logs -f drive-intel | grep DEBUG
```

### Log Levels

- **ERROR:** Critical issues only
- **WARN:** Warnings and errors
- **INFO:** Normal operation (default)
- **DEBUG:** Detailed debugging info
- **TRACE:** Everything (very verbose)

### Structured Logging

All logs are JSON formatted:

```json
{
  "timestamp": "2025-12-02T10:30:00.123Z",
  "level": "ERROR",
  "service": "gateway-api",
  "message": "Database connection failed",
  "error": {
    "code": "ECONNREFUSED",
    "errno": -111,
    "syscall": "connect"
  },
  "context": {
    "request_id": "req_abc123",
    "user_id": "user_xyz"
  }
}
```

### Export Logs

```bash
# Export logs to file
docker-compose logs --since 24h > debug_logs.txt

# Export specific service
docker-compose logs gateway-api --since 1h > gateway_debug.txt

# Upload to support
# Include: service name, timestamp, error message
```

---

## Health Checks

### Manual Health Checks

```bash
# Gateway API
curl http://localhost:8080/health
# Expected: {"status":"healthy","timestamp":"...","services":{...}}

# Drive Intel
curl http://localhost:8081/health
# Expected: {"status":"healthy"}

# Video Agent
curl http://localhost:8082/health

# ML Service
curl http://localhost:8003/health

# Meta Publisher
curl http://localhost:8083/health

# Titan Core
curl http://localhost:8084/health
```

### Database Health

```bash
# PostgreSQL
docker-compose exec postgres pg_isready -U geminivideo
# Expected: accepting connections

# Check connections
docker-compose exec postgres psql -U geminivideo -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose exec postgres psql -U geminivideo -c "SELECT pg_size_pretty(pg_database_size('geminivideo'));"
```

### Redis Health

```bash
# Ping
docker-compose exec redis redis-cli ping
# Expected: PONG

# Get info
docker-compose exec redis redis-cli INFO

# Check memory usage
docker-compose exec redis redis-cli INFO memory | grep used_memory_human

# Check connected clients
docker-compose exec redis redis-cli CLIENT LIST
```

---

## Performance Issues

### Issue: Slow API Responses

**Diagnosis:**
```bash
# Test response time
time curl http://localhost:8080/api/assets

# Enable query logging in PostgreSQL
docker-compose exec postgres psql -U geminivideo -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"

# Restart PostgreSQL
docker-compose restart postgres

# Check slow queries
docker-compose logs postgres | grep "duration:"
```

**Solutions:**
1. Add database indexes
2. Enable Redis caching
3. Optimize N+1 queries
4. Increase connection pool size

---

### Issue: High CPU Usage

**Diagnosis:**
```bash
# View CPU usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}"

# Profile Python service
docker-compose exec drive-intel py-spy top --pid 1
```

**Solutions:**
1. Optimize hot code paths
2. Add caching for expensive operations
3. Increase number of instances (horizontal scaling)
4. Use background workers for heavy tasks

---

### Issue: Slow Video Processing

**Diagnosis:**
```bash
# Check FFmpeg performance
docker-compose exec video-agent ffmpeg -i input.mp4 -f null - -benchmark

# Check disk I/O
docker stats --no-stream --format "table {{.Container}}\t{{.BlockIO}}"
```

**Solutions:**
1. Enable hardware acceleration (GPU)
2. Reduce video quality settings
3. Use faster FFmpeg presets
4. Process videos in parallel

---

## Support Contacts

### Community Support

**GitHub Issues:**
- URL: https://github.com/milosriki/geminivideo/issues
- For: Bug reports, feature requests
- Response time: 24-48 hours

**Discussion Forum:**
- URL: https://community.geminivideo.com
- For: General questions, best practices
- Response time: Community-driven

**Stack Overflow:**
- Tag: `geminivideo`
- For: Technical questions
- Response time: Community-driven

### Professional Support

**Email Support:**
- Free tier: support@geminivideo.com (48-72h response)
- Pro tier: priority@geminivideo.com (8-24h response)
- Enterprise: dedicated account manager (4h response)

**Live Chat:**
- Pro/Enterprise only
- Available: Mon-Fri 9am-5pm PST
- Access: In-app chat widget

**Phone Support:**
- Enterprise only
- Schedule via support portal
- 24/7 emergency hotline for critical issues

### Emergency Contact

**Critical Production Issues:**
- Email: oncall@geminivideo.com
- Include: Service, error message, impact, urgency
- Response: Within 1 hour (Enterprise), 4 hours (Pro)

### Submit Debug Report

When contacting support, include:

1. **Environment info:**
```bash
docker --version
docker-compose --version
uname -a
```

2. **Service logs:**
```bash
docker-compose logs --tail=100 > debug_logs.txt
```

3. **Configuration (without secrets):**
```bash
cat .env.production | grep -v "PASSWORD\|SECRET\|KEY\|TOKEN"
```

4. **Error message:**
```
Copy exact error from logs
Include stack trace if available
```

5. **Steps to reproduce:**
```
1. Do X
2. Then Y
3. Observe error Z
```

---

## Useful Commands

### View All Logs
```bash
docker-compose logs -f
```

### Restart All Services
```bash
docker-compose restart
```

### Rebuild Single Service
```bash
docker-compose up -d --build gateway-api
```

### Clean Everything (⚠️ Destroys Data)
```bash
docker-compose down -v
docker system prune -a
```

### Database Backup
```bash
docker-compose exec postgres pg_dump -U geminivideo geminivideo > backup.sql
```

### Database Restore
```bash
cat backup.sql | docker-compose exec -T postgres psql -U geminivideo geminivideo
```

### Check Disk Usage
```bash
docker system df
```

### View Container Processes
```bash
docker-compose top
```

---

## FAQ

**Q: Why is my video analysis taking so long?**
A: Video analysis time depends on duration and quality. Typical: 2-5 minutes. Check worker logs for progress.

**Q: Can I run this on Windows?**
A: Yes, using Docker Desktop. Ensure WSL 2 backend is enabled for best performance.

**Q: How do I update to the latest version?**
A: Pull latest code, rebuild images: `git pull && docker-compose up -d --build`

**Q: Where are my videos stored?**
A: In GCS bucket (production) or Docker volume (local): `geminivideo_drive_intel_data`

**Q: How do I reset the database?**
A: `docker-compose down -v && docker-compose up -d` (⚠️ destroys all data)

**Q: Can I use a different database?**
A: PostgreSQL is required. MySQL/SQLite not supported due to JSONB and vector features.

**Q: How do I increase upload size limit?**
A: Edit `MAX_VIDEO_SIZE_MB` in `.env.production` and nginx `client_max_body_size`

**Q: Is GPU required?**
A: No, but recommended for faster ML inference. System works fine on CPU.

---

*Last Updated: 2025-12-02*
*Version: 1.0.0*

**Need more help? Contact support@geminivideo.com**
