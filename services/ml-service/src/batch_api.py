"""
Batch API Endpoints - REST API for batch processing

AGENT 42: 10x LEVERAGE - Batch API

FastAPI endpoints for batch processing operations:
- Queue jobs
- Submit batches
- Check status
- Retrieve results
- Get metrics
- Dashboard data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

try:
    from src.batch_processor import (
        BatchProcessor,
        BatchJobType,
        BatchProvider,
        BatchStatus
    )
    from src.batch_scheduler import BatchScheduler
    from src.batch_monitoring import BatchMonitor
    BATCH_MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Batch modules not available: {e}")
    BATCH_MODULES_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class BatchProcessor:
        pass
    class BatchJobType:
        pass
    class BatchProvider:
        pass
    class BatchStatus:
        pass
    class BatchScheduler:
        pass
    class BatchMonitor:
        pass

logger = logging.getLogger(__name__)

# Initialize components
batch_processor = BatchProcessor()
batch_scheduler = BatchScheduler(batch_processor=batch_processor)
batch_monitor = BatchMonitor(batch_processor=batch_processor)

# Create router
router = APIRouter(prefix="/batch", tags=["batch"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueueJobRequest(BaseModel):
    """Request to queue a job."""
    job_type: str = Field(..., description="Type of batch job")
    provider: str = Field(..., description="API provider (openai, anthropic, gemini)")
    data: Dict[str, Any] = Field(..., description="Job data")
    priority: int = Field(5, description="Job priority (1-10, higher = more urgent)")


class QueueJobResponse(BaseModel):
    """Response after queuing a job."""
    job_id: str
    status: str = "queued"
    message: str


class ProcessBatchRequest(BaseModel):
    """Request to process a batch."""
    job_type: str = Field(..., description="Type of jobs to process")
    provider: str = Field(..., description="API provider")
    max_jobs: int = Field(1000, description="Maximum jobs per batch")


class ProcessBatchResponse(BaseModel):
    """Response after processing batch."""
    batch_id: Optional[str]
    status: str
    job_count: Optional[int] = None
    message: str


class BatchStatusResponse(BaseModel):
    """Batch status response."""
    batch_id: str
    provider: str
    job_type: str
    status: str
    job_count: int
    cost_savings: float
    created_at: Optional[float]
    submitted_at: Optional[float]
    completed_at: Optional[float]
    provider_status: Optional[Dict[str, Any]]


# ============================================================================
# JOB QUEUING ENDPOINTS
# ============================================================================

@router.post("/queue", response_model=QueueJobResponse)
async def queue_job(request: QueueJobRequest):
    """
    Queue a job for batch processing.

    This adds a job to the queue without processing it immediately.
    Jobs will be processed during the next batch window (2 AM by default).

    **Benefits:**
    - 50% cost reduction
    - No impact on user experience
    - Automatic retry on failure

    **Example:**
    ```python
    {
        "job_type": "creative_scoring",
        "provider": "openai",
        "data": {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Score this creative..."}
            ]
        },
        "priority": 5
    }
    ```
    """
    try:
        # Validate enum values
        job_type = BatchJobType(request.job_type)
        provider = BatchProvider(request.provider)

        # Queue job
        job_id = await batch_processor.queue_job(
            job_type=job_type,
            provider=provider,
            data=request.data,
            priority=request.priority
        )

        return QueueJobResponse(
            job_id=job_id,
            status="queued",
            message=f"Job queued successfully for batch processing"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid job type or provider: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to queue job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/bulk")
async def queue_jobs_bulk(jobs: List[QueueJobRequest]):
    """
    Queue multiple jobs at once.

    This is useful for:
    - Bulk imports
    - Historical data reprocessing
    - Large-scale operations
    """
    try:
        job_data = [
            {
                "job_type": job.job_type,
                "provider": job.provider,
                "data": job.data,
                "priority": job.priority
            }
            for job in jobs
        ]

        job_ids = await batch_processor.queue_jobs_bulk(job_data)

        successful = len([jid for jid in job_ids if jid])
        failed = len(job_ids) - successful

        return {
            "total": len(jobs),
            "successful": successful,
            "failed": failed,
            "job_ids": job_ids
        }

    except Exception as e:
        logger.error(f"Failed to queue bulk jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status")
async def get_queue_status():
    """
    Get current queue status.

    Returns the number of jobs waiting to be processed.
    """
    try:
        total = batch_processor.get_queued_job_count()

        breakdown = {}
        for job_type in BatchJobType:
            for provider in BatchProvider:
                count = batch_processor.get_queued_job_count(job_type, provider)
                if count > 0:
                    key = f"{job_type.value}_{provider.value}"
                    breakdown[key] = count

        return {
            "total_queued": total,
            "breakdown": breakdown
        }

    except Exception as e:
        logger.error(f"Failed to get queue status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH PROCESSING ENDPOINTS
# ============================================================================

@router.post("/process", response_model=ProcessBatchResponse)
async def process_batch(request: ProcessBatchRequest):
    """
    Manually trigger batch processing.

    This submits queued jobs to the batch API immediately,
    instead of waiting for the scheduled time (2 AM).

    **Use cases:**
    - Testing
    - Emergency processing
    - On-demand batch runs
    """
    try:
        job_type = BatchJobType(request.job_type)
        provider = BatchProvider(request.provider)

        batch_id = await batch_processor.process_batch(
            job_type=job_type,
            provider=provider,
            max_jobs=request.max_jobs
        )

        if batch_id:
            # Get job count
            batch_info = await batch_processor.check_batch_status(batch_id)

            return ProcessBatchResponse(
                batch_id=batch_id,
                status="submitted",
                job_count=batch_info.get("job_count"),
                message=f"Batch submitted successfully"
            )
        else:
            return ProcessBatchResponse(
                batch_id=None,
                status="no_jobs",
                message="No jobs to process"
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid job type or provider: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/all")
async def process_all_batches(background_tasks: BackgroundTasks):
    """
    Process all queued batches.

    This triggers immediate processing of all pending jobs
    across all job types and providers.
    """
    try:
        # Run in background
        background_tasks.add_task(batch_scheduler.run_now)

        return {
            "status": "started",
            "message": "Batch processing started in background"
        }

    except Exception as e:
        logger.error(f"Failed to process all batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATUS & RESULTS ENDPOINTS
# ============================================================================

@router.get("/status/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Check the status of a batch.

    Returns detailed information about batch progress,
    including provider status and completion estimates.
    """
    try:
        status = await batch_processor.check_batch_status(batch_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return BatchStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{batch_id}")
async def get_batch_results(batch_id: str):
    """
    Retrieve results from a completed batch.

    Returns the processed results for all jobs in the batch.
    """
    try:
        results = await batch_processor.retrieve_batch_results(batch_id)

        if not results:
            raise HTTPException(
                status_code=404,
                detail="Batch not found or not yet completed"
            )

        return {
            "batch_id": batch_id,
            "result_count": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_batches():
    """
    Get list of active (in-progress) batches.

    Returns all batches that are currently being processed.
    """
    try:
        active_batches = batch_processor.get_active_batches()

        return {
            "count": len(active_batches),
            "batches": active_batches
        }

    except Exception as e:
        logger.error(f"Failed to get active batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS & MONITORING ENDPOINTS
# ============================================================================

@router.get("/metrics")
async def get_metrics(category: Optional[str] = None):
    """
    Get batch processing metrics.

    Returns comprehensive metrics including:
    - Jobs processed
    - Batches submitted/completed
    - Cost savings
    - Success rates
    """
    try:
        metrics = batch_processor.get_metrics(category=category)
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard():
    """
    Get comprehensive dashboard data.

    Returns all data needed for batch processing dashboard:
    - Overview statistics
    - Active batches
    - Queue breakdown
    - Cost savings
    - Recent activity
    - Performance trends
    """
    try:
        dashboard_data = batch_monitor.get_dashboard_data()
        return dashboard_data

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/savings")
async def get_cost_savings():
    """
    Get cost savings report.

    Returns detailed cost savings analysis:
    - Total savings
    - Savings by job type
    - Savings by provider
    - Comparison with realtime costs
    """
    try:
        from dataclasses import asdict
        report = batch_monitor.get_cost_savings_report()
        return asdict(report)

    except Exception as e:
        logger.error(f"Failed to get cost savings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_report(days: int = 30, format: str = "json"):
    """
    Generate comprehensive batch processing report.

    Args:
        days: Number of days to include in report
        format: Output format (json or markdown)
    """
    try:
        report = batch_monitor.generate_report(period_days=days, format=format)

        if format == "markdown":
            return {"content": report, "format": "markdown"}
        else:
            import json
            return json.loads(report)

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts():
    """
    Get current alerts and warnings.

    Returns alerts for:
    - High failure rates
    - Stale batches
    - Large queue buildup
    - Cost savings milestones
    """
    try:
        alerts = batch_monitor.check_alerts()
        return {
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SCHEDULER CONTROL ENDPOINTS
# ============================================================================

@router.post("/scheduler/start")
async def start_scheduler(background_tasks: BackgroundTasks):
    """
    Start the batch scheduler.

    This starts automatic batch processing at scheduled times (2 AM).
    """
    try:
        # Start scheduler in background
        background_tasks.add_task(batch_scheduler.start)

        return {
            "status": "started",
            "message": "Batch scheduler started",
            "schedule_time": str(batch_scheduler.schedule_time)
        }

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the batch scheduler."""
    try:
        batch_scheduler.stop()

        return {
            "status": "stopped",
            "message": "Batch scheduler stopped"
        }

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the health status of the batch processing system.
    """
    try:
        # Check Redis connection
        redis_connected = False
        try:
            batch_processor.redis.ping()
            redis_connected = True
        except:
            pass

        # Get system status
        queue_size = batch_processor.get_queued_job_count()
        active_batches = len(batch_processor.get_active_batches())

        return {
            "status": "healthy" if redis_connected else "degraded",
            "redis_connected": redis_connected,
            "queue_size": queue_size,
            "active_batches": active_batches,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

@router.post("/integrate/creative-scoring")
async def queue_creative_scoring(
    creative_id: str,
    script: str,
    niche: str = "fitness",
    priority: int = 5
):
    """
    Helper endpoint to queue creative scoring jobs.

    This is a convenience wrapper for the most common use case.
    """
    try:
        job_id = await batch_processor.queue_job(
            job_type=BatchJobType.CREATIVE_SCORING,
            provider=BatchProvider.OPENAI,
            data={
                "creative_id": creative_id,
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are evaluating ad creatives for {niche}."
                    },
                    {
                        "role": "user",
                        "content": f"Score this creative:\n\n{script}"
                    }
                ],
                "temperature": 0.3
            },
            priority=priority
        )

        return {
            "job_id": job_id,
            "creative_id": creative_id,
            "status": "queued",
            "message": "Creative scoring queued for batch processing"
        }

    except Exception as e:
        logger.error(f"Failed to queue creative scoring: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrate/embeddings")
async def queue_embeddings(
    texts: List[str],
    priority: int = 5
):
    """
    Helper endpoint to queue embedding generation jobs.

    This batches embedding generation for cost optimization.
    """
    try:
        job_ids = []

        for text in texts:
            job_id = await batch_processor.queue_job(
                job_type=BatchJobType.EMBEDDING_GENERATION,
                provider=BatchProvider.OPENAI,
                data={
                    "model": "text-embedding-3-large",
                    "input": text
                },
                priority=priority
            )
            job_ids.append(job_id)

        return {
            "job_ids": job_ids,
            "count": len(job_ids),
            "status": "queued",
            "message": f"{len(job_ids)} embedding jobs queued for batch processing"
        }

    except Exception as e:
        logger.error(f"Failed to queue embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime
