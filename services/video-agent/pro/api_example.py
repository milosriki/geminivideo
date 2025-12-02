"""
FastAPI Integration Example for Celery Task Queue

This example shows how to integrate the Celery task queue with FastAPI
for asynchronous video processing with real-time progress updates.

Usage:
    uvicorn services.video-agent.pro.api_example:app --host 0.0.0.0 --port 8000

Endpoints:
    POST   /api/render          - Submit render job
    POST   /api/preview         - Generate preview frames
    POST   /api/transcode       - Transcode video
    POST   /api/caption         - Generate captions
    POST   /api/batch-render    - Batch render multiple videos
    GET    /api/task/{task_id}  - Get task status
    GET    /api/tasks           - List all tasks
    GET    /api/workers         - Get worker status
    GET    /api/resources       - Get system resources
    DELETE /api/task/{task_id}  - Cancel/revoke task
    WS     /ws/progress/{task_id} - WebSocket for real-time progress
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from celery.result import AsyncResult

from services.video_agent.pro.celery_app import (
    app as celery_app,
    render_video_task,
    generate_preview_task,
    transcode_task,
    caption_task,
    batch_render_task,
    cleanup_task,
    monitor_resources_task,
    get_system_resources,
    REDIS_URL
)

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Video Processing API",
    description="Distributed video processing with Celery task queue",
    version="1.0.0"
)

# Redis client for progress tracking
redis_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    global redis_client
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SceneData(BaseModel):
    """Scene data for video rendering"""
    video_path: str = Field(..., description="Path to video file")
    start_time: Optional[float] = Field(None, description="Start time in seconds")
    end_time: Optional[float] = Field(None, description="End time in seconds")


class OutputFormat(BaseModel):
    """Output format specification"""
    width: int = Field(1920, description="Video width")
    height: int = Field(1080, description="Video height")
    fps: int = Field(30, description="Frames per second")


class RenderRequest(BaseModel):
    """Render job request"""
    scenes: List[SceneData] = Field(..., description="List of scenes to render")
    output_format: OutputFormat = Field(default_factory=OutputFormat)
    transitions: bool = Field(True, description="Enable transitions between scenes")
    use_gpu: bool = Field(False, description="Use GPU acceleration if available")
    subtitles: Optional[str] = Field(None, description="Path to subtitle file (SRT)")
    priority: int = Field(5, ge=0, le=10, description="Task priority (0-10)")


class PreviewRequest(BaseModel):
    """Preview generation request"""
    video_path: str = Field(..., description="Path to video file")
    num_frames: int = Field(10, ge=1, le=100, description="Number of preview frames")


class TranscodeRequest(BaseModel):
    """Video transcode request"""
    input_path: str = Field(..., description="Input video path")
    codec: str = Field("h264", description="Video codec (h264, h265, vp9, av1)")
    container: str = Field("mp4", description="Container format (mp4, webm, mkv)")
    width: Optional[int] = Field(None, description="Target width")
    height: Optional[int] = Field(None, description="Target height")
    bitrate: Optional[str] = Field(None, description="Target bitrate (e.g., '5M')")


class CaptionRequest(BaseModel):
    """Caption generation request"""
    video_path: str = Field(..., description="Path to video file")
    model: str = Field("base", description="Whisper model (tiny, base, small, medium, large)")


class BatchRenderRequest(BaseModel):
    """Batch render request"""
    jobs: List[RenderRequest] = Field(..., description="List of render jobs")


class TaskResponse(BaseModel):
    """Task submission response"""
    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    submitted_at: str = Field(..., description="Submission timestamp")


class TaskStatus(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Video Processing API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "render": "/api/render",
            "preview": "/api/preview",
            "transcode": "/api/transcode",
            "caption": "/api/caption",
            "batch": "/api/batch-render",
            "task_status": "/api/task/{task_id}",
            "workers": "/api/workers",
            "resources": "/api/resources"
        }
    }


@app.post("/api/render", response_model=TaskResponse)
async def submit_render_job(request: RenderRequest):
    """
    Submit a video render job to the queue

    Returns task_id for tracking progress
    """
    try:
        # Prepare job data
        job_data = {
            'scenes': [scene.dict() for scene in request.scenes],
            'output_format': request.output_format.dict(),
            'transitions': request.transitions,
            'use_gpu': request.use_gpu,
            'subtitles': request.subtitles
        }

        # Submit task
        result = render_video_task.apply_async(
            args=[job_data],
            priority=request.priority
        )

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message='Render job submitted successfully',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.post("/api/preview", response_model=TaskResponse)
async def submit_preview_job(request: PreviewRequest):
    """Generate preview frames from video"""
    try:
        result = generate_preview_task.apply_async(
            args=[request.video_path],
            kwargs={'num_frames': request.num_frames}
        )

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message='Preview generation job submitted',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.post("/api/transcode", response_model=TaskResponse)
async def submit_transcode_job(request: TranscodeRequest):
    """Transcode video to different format"""
    try:
        output_format = {
            'codec': request.codec,
            'container': request.container,
            'width': request.width,
            'height': request.height,
            'bitrate': request.bitrate
        }

        result = transcode_task.apply_async(
            args=[request.input_path, output_format]
        )

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message='Transcode job submitted',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.post("/api/caption", response_model=TaskResponse)
async def submit_caption_job(request: CaptionRequest):
    """Generate captions using Whisper"""
    try:
        result = caption_task.apply_async(
            args=[request.video_path],
            kwargs={'model': request.model}
        )

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message='Caption generation job submitted',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@app.post("/api/batch-render", response_model=TaskResponse)
async def submit_batch_render(request: BatchRenderRequest):
    """Submit multiple render jobs for batch processing"""
    try:
        job_list = []
        for job in request.jobs:
            job_data = {
                'scenes': [scene.dict() for scene in job.scenes],
                'output_format': job.output_format.dict(),
                'transitions': job.transitions,
                'use_gpu': job.use_gpu,
                'subtitles': job.subtitles
            }
            job_list.append(job_data)

        result = batch_render_task.apply_async(args=[job_list])

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message=f'Batch render submitted with {len(job_list)} jobs',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit batch: {str(e)}")


@app.get("/api/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get status of a specific task

    Returns current progress, status, and result if completed
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)

        # Get progress from Redis
        progress_data = await redis_client.get(f'task_status:{task_id}')

        if progress_data:
            progress_info = json.loads(progress_data)
            progress = progress_info.get('progress', 0)
            message = progress_info.get('message', '')
        else:
            progress = 0
            message = 'No progress data available'

        # Determine status
        if task_result.ready():
            if task_result.successful():
                status = 'completed'
                result = task_result.result
                error = None
            else:
                status = 'failed'
                result = None
                error = str(task_result.info)
        else:
            status = task_result.state.lower()
            result = None
            error = None

        return TaskStatus(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            result=result,
            error=error,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@app.get("/api/tasks")
async def list_tasks():
    """List all active and recent tasks"""
    try:
        inspect = celery_app.control.inspect()

        # Get active tasks
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        all_tasks = []

        # Process active tasks
        for worker, tasks in active.items():
            for task in tasks:
                all_tasks.append({
                    'task_id': task['id'],
                    'name': task['name'].split('.')[-1],
                    'status': 'active',
                    'worker': worker,
                    'args': task.get('args', []),
                })

        # Process scheduled tasks
        for worker, tasks in scheduled.items():
            for task in tasks:
                all_tasks.append({
                    'task_id': task['request']['id'],
                    'name': task['request']['name'].split('.')[-1],
                    'status': 'scheduled',
                    'worker': worker,
                })

        return {
            'count': len(all_tasks),
            'tasks': all_tasks,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@app.delete("/api/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel/revoke a task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)

        return {
            'task_id': task_id,
            'status': 'revoked',
            'message': 'Task cancellation requested',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@app.get("/api/workers")
async def get_workers():
    """Get status of all workers"""
    try:
        inspect = celery_app.control.inspect()

        stats = inspect.stats() or {}
        active = inspect.active() or {}
        registered = inspect.registered() or {}

        workers = []

        for worker_name in stats.keys():
            worker_stats = stats.get(worker_name, {})
            worker_active = active.get(worker_name, [])
            worker_tasks = registered.get(worker_name, [])

            workers.append({
                'name': worker_name,
                'status': 'online',
                'active_tasks': len(worker_active),
                'registered_tasks': len([t for t in worker_tasks if 'celery_app' in t]),
                'pool': worker_stats.get('pool', {}),
                'total_tasks': worker_stats.get('total', {})
            })

        return {
            'count': len(workers),
            'workers': workers,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")


@app.get("/api/resources")
async def get_resources():
    """Get current system resource usage"""
    try:
        resources = get_system_resources()
        return resources

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resources: {str(e)}")


@app.post("/api/cleanup")
async def trigger_cleanup(max_age_days: int = 7, max_size_gb: int = 50):
    """Manually trigger cleanup task"""
    try:
        result = cleanup_task.apply_async(
            kwargs={'max_age_days': max_age_days, 'max_size_gb': max_size_gb}
        )

        return TaskResponse(
            task_id=result.id,
            status='pending',
            message='Cleanup task submitted',
            submitted_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


# ============================================================================
# WEBSOCKET FOR REAL-TIME PROGRESS
# ============================================================================

@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time progress updates

    Connect to this endpoint to receive live progress updates for a task
    """
    await websocket.accept()

    try:
        # Subscribe to Redis pub/sub for this task
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f'task_progress:{task_id}')

        # Send initial connection message
        await websocket.send_json({
            'type': 'connected',
            'task_id': task_id,
            'message': 'Connected to progress stream'
        })

        # Listen for progress updates
        while True:
            # Check for messages with timeout
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=1.0
                )

                if message and message['type'] == 'message':
                    progress_data = json.loads(message['data'])
                    await websocket.send_json(progress_data)

                    # Close connection if task completed or failed
                    if progress_data['status'] in ['completed', 'failed']:
                        break

            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({
                    'type': 'ping',
                    'timestamp': datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            'type': 'error',
            'message': str(e)
        })
    finally:
        await pubsub.unsubscribe(f'task_progress:{task_id}')
        await pubsub.close()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        await redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    # Check workers
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        worker_count = len(stats) if stats else 0
        worker_status = "healthy" if worker_count > 0 else "no_workers"
    except:
        worker_count = 0
        worker_status = "unhealthy"

    overall_status = "healthy" if redis_status == "healthy" and worker_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "redis": redis_status,
        "workers": {
            "status": worker_status,
            "count": worker_count
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    Starting Video Processing API...

    API Documentation: http://localhost:8000/docs
    Health Check: http://localhost:8000/health

    Make sure to start:
    1. Redis: redis-server
    2. Celery Worker: celery -A services.video-agent.pro.celery_app worker --loglevel=info
    3. Celery Beat: celery -A services.video-agent.pro.celery_app beat --loglevel=info
    """)

    uvicorn.run(app, host="0.0.0.0", port=8000)
