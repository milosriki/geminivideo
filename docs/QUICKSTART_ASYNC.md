# Quick Start Guide: Async Queues & Story Arcs

## 🚀 Quick Start

### 1. Start Services
```bash
docker-compose up
```

Wait for all services to be healthy (~2-3 minutes).

### 2. Upload & Queue Analysis
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/data/inputs/workout.mp4",
    "filename": "workout.mp4",
    "size_bytes": 10485760,
    "duration_seconds": 45
  }'
```

Response (instant):
```json
{
  "asset_id": "abc123-...",
  "status": "QUEUED",
  "message": "Analysis job queued successfully"
}
```

### 3. Check Status
```bash
# Replace abc123 with your asset_id
curl http://localhost:8080/api/assets/abc123
```

Look for `"status": "READY"` (takes 1-3 minutes depending on video length).

### 4. Create Transformation Ad
```bash
curl -X POST http://localhost:8080/api/render/story_arc \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "abc123-...",
    "arc_name": "fitness_transformation"
  }'
```

Response:
```json
{
  "job_id": "render-xyz789",
  "status": "QUEUED",
  "selected_clips": ["clip1", "clip2", "clip3"],
  "message": "Render job queued successfully"
}
```

## 🎨 Frontend Usage

### Using the UI

1. **Upload Video**
   - Go to: http://localhost:80
   - Navigate to "Assets & Ingest" tab
   - Enter video path
   - Click "Ingest from Local Folder"
   - Get instant response with asset ID

2. **Create Story Arc Ad**
   - Navigate to "Render Job" tab
   - Scroll to "Create Story Arc Ad" section
   - Enter your asset ID
   - Select template:
     - **Fitness Transformation (30s)**: Full transformation story
     - **Motivation Arc (20s)**: Energy and motivation
     - **Quick Win (15s)**: Fast high-energy
   - Click "🎥 Render Transformation Ad"
   - Note the job ID

3. **Check Render Status**
   - In same "Render Job" tab
   - Enter job ID
   - Click "Check Status"
   - See progress and output path

## 📋 Story Arc Templates

### fitness_transformation (30s)
Perfect for: Before/after transformation ads

**Emotional Journey:**
1. **Struggle** (5s) - sad/frustrated clips
2. **Training** (10s) - neutral workout clips
3. **Success** (10s) - happy achievement clips
4. **CTA** (5s) - happy call-to-action

### motivation_arc (20s)
Perfect for: Inspirational content

**Emotional Journey:**
1. **Baseline** (5s) - neutral starting point
2. **Energy** (15s) - happy high-energy clips

### quick_win (15s)
Perfect for: Social media shorts

**Emotional Journey:**
1. **Results** (15s) - all happy success clips

## 🔍 Monitoring

### Check Worker Logs
```bash
# Analysis worker
docker-compose logs -f drive-worker

# Render worker
docker-compose logs -f video-worker
```

### Check Queue Status
```bash
docker exec -it geminivideo-redis redis-cli

# In Redis CLI:
> LLEN analysis_queue
> LLEN render_queue
> LRANGE analysis_queue 0 -1
```

### Check Database
```bash
docker exec -it geminivideo-postgres psql -U geminivideo

# In PostgreSQL:
\c geminivideo
SELECT asset_id, filename, status FROM assets;
SELECT clip_id, emotion FROM emotions LIMIT 10;
```

## 🐛 Troubleshooting

### "Asset status is still QUEUED"
- Worker might be processing another job
- Check worker logs: `docker-compose logs drive-worker`
- Wait a few more seconds

### "No clips found for story arc"
- Asset might not have emotion data
- Check: `SELECT * FROM emotions WHERE asset_id = 'your-id';`
- Make sure Google Cloud credentials are set

### "Worker not processing jobs"
- Check Redis connection: `docker-compose logs redis`
- Check worker is running: `docker-compose ps`
- Restart workers: `docker-compose restart drive-worker video-worker`

### "Emotion detection not working"
- Set Google Cloud credentials:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
  docker-compose restart drive-worker
  ```
- Or worker will continue without emotion data (fallback to highest CTR scores)

## 🎯 Example Workflow

### Complete End-to-End Example

```bash
# 1. Start everything
docker-compose up -d

# 2. Upload video
ASSET_ID=$(curl -s -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"path":"/data/inputs/workout.mp4","filename":"workout.mp4"}' \
  | jq -r '.asset_id')

echo "Asset ID: $ASSET_ID"

# 3. Wait for analysis (check every 5 seconds)
while true; do
  STATUS=$(curl -s "http://localhost:8080/api/assets?asset_id=$ASSET_ID" \
    | jq -r '.assets[0].status')
  echo "Status: $STATUS"
  [ "$STATUS" = "READY" ] && break
  sleep 5
done

# 4. Create transformation ad
JOB_ID=$(curl -s -X POST http://localhost:8080/api/render/story_arc \
  -H "Content-Type: application/json" \
  -d "{\"asset_id\":\"$ASSET_ID\",\"arc_name\":\"fitness_transformation\"}" \
  | jq -r '.job_id')

echo "Render Job ID: $JOB_ID"

# 5. Check render status
curl "http://localhost:8080/api/render/status/$JOB_ID"
```

## 📊 Performance Tips

### Scale Workers for Faster Processing
```bash
# Run 3 analysis workers and 2 render workers
docker-compose up --scale drive-worker=3 --scale video-worker=2
```

### Optimize Video Processing
- Use smaller videos for testing (under 1 minute)
- H.264 codec processes fastest
- 1080p recommended (4K takes longer)

### Monitor Resource Usage
```bash
docker stats geminivideo-drive-worker geminivideo-video-worker
```

## 🔧 Configuration

### Modify Story Arcs
Edit `shared/config/story_arcs.json` to add your own templates:

```json
{
  "my_custom_arc": {
    "name": "My Custom Arc",
    "description": "Your description",
    "target_industry": "fitness",
    "duration_seconds": 20,
    "steps": [
      {
        "order": 1,
        "emotion": "happy",
        "duration": 20,
        "description": "All happy clips"
      }
    ]
  }
}
```

Restart gateway-api to load changes:
```bash
docker-compose restart gateway-api
```

### Change Scene Detection Threshold
Edit `services/drive-intel/services/scene_detector.py`:

```python
# Lower = more scenes detected
self.threshold = 20.0  # Default is 27.0
```

## 📚 Learn More

- Full documentation: `docs/ASYNC_QUEUES_AND_STORY_ARCS.md`
- API reference: `services/gateway-api/README.md`
- Database schema: `shared/db.py`
- Worker implementation: `services/drive-intel/worker.py`

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs [service-name]`
2. Verify services are healthy: `docker-compose ps`
3. Check queue status in Redis
4. Verify database connections
5. Review comprehensive docs

## ✅ Success Checklist

- [ ] Services started successfully
- [ ] Video uploaded and queued
- [ ] Asset status changed to READY
- [ ] Story arc render job created
- [ ] Output video generated
- [ ] Frontend displays results

## 🎉 You're Ready!

You now have:
- ⚡ Instant API responses
- 🎭 Automatic emotion detection
- 🎬 Story-driven ad generation
- 📈 Scalable background processing

Happy creating! 🚀
