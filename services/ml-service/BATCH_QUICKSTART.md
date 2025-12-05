# Batch API Processing - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /home/user/geminivideo/services/ml-service
pip install -r requirements_batch.txt
```

### Step 2: Configure Environment

```bash
# Add to .env
export REDIS_URL="redis://localhost:6379"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

### Step 3: Start Redis (if not running)

```bash
docker-compose up -d redis
```

### Step 4: Start Batch Scheduler

```bash
# Run in background
python src/batch_scheduler.py &

# Or for testing, run immediately
python src/batch_scheduler.py --run-now
```

### Step 5: Queue Your First Job

```python
import asyncio
from src.batch_processor import BatchProcessor, BatchJobType, BatchProvider

async def first_batch():
    batch = BatchProcessor()

    job_id = await batch.queue_job(
        job_type=BatchJobType.CREATIVE_SCORING,
        provider=BatchProvider.OPENAI,
        data={
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Score this creative..."}
            ]
        }
    )

    print(f"✅ Job queued: {job_id}")
    print("Results will be available in ~24 hours")

asyncio.run(first_batch())
```

### Step 6: Monitor Progress

```bash
# View dashboard
curl http://localhost:8003/batch/dashboard | jq

# Check metrics
curl http://localhost:8003/batch/metrics | jq

# View cost savings
curl http://localhost:8003/batch/savings | jq
```

## 📊 Expected Results

After 24 hours:
- ✅ Batch processed
- 💰 50% cost savings
- 📈 Metrics tracked
- 🎯 Zero impact on users

## 🎯 Real-World Example

**Scenario**: Score 1,000 creatives

**Real-time (Before):**
```python
# Cost: $10
# Time: ~30 minutes
for creative in creatives:
    score = await council.evaluate_script(creative)
```

**Batch (After):**
```python
# Cost: $5 (50% savings!)
# Time: 24 hours (overnight)
for creative in creatives:
    await batch.queue_job(
        job_type=BatchJobType.CREATIVE_SCORING,
        provider=BatchProvider.OPENAI,
        data={"creative": creative}
    )
```

## ⚡ Pro Tips

1. **Schedule for 2 AM** - Processes during off-peak hours
2. **Use priorities** - Critical jobs process first
3. **Monitor alerts** - Get notified of issues
4. **Track savings** - See your ROI in real-time

## 🆘 Troubleshooting

### Jobs not processing?
```bash
# Check scheduler status
curl http://localhost:8003/batch/health

# Check queue
curl http://localhost:8003/batch/queue/status
```

### Results taking too long?
- Batch APIs have 24-hour turnaround
- For urgent needs, use real-time API
- Check provider status page

## 📚 Next Steps

1. Read full documentation: `AGENT42_BATCH_API_PROCESSING.md`
2. Review integration examples: `batch_integration_example.py`
3. Explore API endpoints: `src/batch_api.py`
4. Monitor your savings! 💰

## 🎉 Success!

You're now saving 50% on batch-able API operations!

Track your savings at: http://localhost:8003/batch/dashboard
