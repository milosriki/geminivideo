"""
WebSocket Progress Service - Usage Examples

This file demonstrates how to use the WebSocket progress service
for real-time job updates in your services.
"""

import asyncio
import time
from typing import Dict, Any

from .websocket import ProgressReporter


# ============================================================================
# Example 1: Simple Video Rendering Progress
# ============================================================================

async def example_video_rendering(job_id: str):
    """
    Example: Report progress for a video rendering job
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        # Start rendering
        await reporter.report(
            job_id=job_id,
            stage="rendering",
            progress=0.0,
            message="Starting video render..."
        )

        # Simulate rendering frames
        total_frames = 2000
        for frame in range(0, total_frames, 100):
            # Simulate work
            await asyncio.sleep(0.5)

            # Report progress
            progress = frame / total_frames
            await reporter.report(
                job_id=job_id,
                stage="rendering",
                progress=progress,
                message=f"Rendering frame {frame}/{total_frames}",
                metadata={
                    "current_frame": frame,
                    "total_frames": total_frames,
                    "fps": 30
                }
            )

        # Complete
        await reporter.report_complete(
            job_id=job_id,
            result={
                "video_url": f"https://storage.example.com/videos/{job_id}.mp4",
                "duration": 66.67,
                "frames": total_frames,
                "resolution": "1920x1080"
            },
            message="Video rendering completed successfully"
        )

    except Exception as e:
        await reporter.report_error(job_id, str(e), stage="rendering")
    finally:
        await reporter.close()


# ============================================================================
# Example 2: Multi-Stage AI Processing Pipeline
# ============================================================================

async def example_ai_pipeline(job_id: str, video_path: str):
    """
    Example: Report progress for multi-stage AI processing
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        # Stage 1: Uploading
        await reporter.report(
            job_id=job_id,
            stage="uploading",
            progress=0.0,
            message="Uploading video to processing server..."
        )
        await asyncio.sleep(2)
        await reporter.report(
            job_id=job_id,
            stage="uploading",
            progress=1.0,
            message="Upload complete"
        )

        # Stage 2: AI Analysis
        await reporter.report(
            job_id=job_id,
            stage="analyzing",
            progress=0.0,
            message="Analyzing video content with AI..."
        )
        for i in range(10):
            await asyncio.sleep(1)
            await reporter.report(
                job_id=job_id,
                stage="analyzing",
                progress=(i + 1) / 10,
                message=f"AI analysis {(i+1)*10}% complete"
            )

        # Stage 3: Captioning
        await reporter.report(
            job_id=job_id,
            stage="captioning",
            progress=0.0,
            message="Generating captions..."
        )
        await asyncio.sleep(3)
        await reporter.report(
            job_id=job_id,
            stage="captioning",
            progress=1.0,
            message="Captions generated"
        )

        # Stage 4: Cropping/Formatting
        await reporter.report(
            job_id=job_id,
            stage="cropping",
            progress=0.0,
            message="Cropping and formatting for social media..."
        )
        formats = ["vertical_9:16", "square_1:1", "horizontal_16:9"]
        for idx, fmt in enumerate(formats):
            await asyncio.sleep(2)
            await reporter.report(
                job_id=job_id,
                stage="cropping",
                progress=(idx + 1) / len(formats),
                message=f"Generated {fmt} format",
                metadata={"format": fmt}
            )

        # Complete
        await reporter.report_complete(
            job_id=job_id,
            result={
                "original_video": video_path,
                "ai_score": 0.87,
                "captions": ["Caption 1", "Caption 2", "Caption 3"],
                "formats": {
                    "vertical": f"https://cdn.example.com/{job_id}_9-16.mp4",
                    "square": f"https://cdn.example.com/{job_id}_1-1.mp4",
                    "horizontal": f"https://cdn.example.com/{job_id}_16-9.mp4",
                }
            },
            message="AI processing completed successfully"
        )

    except Exception as e:
        await reporter.report_error(job_id, str(e))
    finally:
        await reporter.close()


# ============================================================================
# Example 3: Batch Processing with Sub-Jobs
# ============================================================================

async def example_batch_processing(batch_id: str, video_ids: list):
    """
    Example: Report progress for batch processing multiple videos
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        total_videos = len(video_ids)

        for idx, video_id in enumerate(video_ids):
            # Report overall batch progress
            overall_progress = idx / total_videos
            await reporter.report(
                job_id=batch_id,
                stage="processing",
                progress=overall_progress,
                message=f"Processing video {idx + 1}/{total_videos}",
                metadata={
                    "current_video": video_id,
                    "completed": idx,
                    "total": total_videos
                }
            )

            # Simulate processing this video
            await asyncio.sleep(2)

        # Complete batch
        await reporter.report_complete(
            job_id=batch_id,
            result={
                "total_processed": total_videos,
                "successful": total_videos,
                "failed": 0,
                "videos": [
                    {"id": vid, "status": "completed"}
                    for vid in video_ids
                ]
            },
            message=f"Batch processing completed: {total_videos} videos processed"
        )

    except Exception as e:
        await reporter.report_error(batch_id, str(e), stage="processing")
    finally:
        await reporter.close()


# ============================================================================
# Example 4: Error Handling
# ============================================================================

async def example_with_error_handling(job_id: str):
    """
    Example: Proper error handling and reporting
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        await reporter.report(
            job_id=job_id,
            stage="processing",
            progress=0.0,
            message="Starting job..."
        )

        # Simulate some work
        await asyncio.sleep(1)
        await reporter.report(
            job_id=job_id,
            stage="processing",
            progress=0.3,
            message="Processing..."
        )

        # Simulate an error
        raise ValueError("Something went wrong during processing")

    except ValueError as e:
        # Report specific error
        await reporter.report_error(
            job_id=job_id,
            error=str(e),
            stage="processing"
        )
    except Exception as e:
        # Report unexpected error
        await reporter.report_error(
            job_id=job_id,
            error=f"Unexpected error: {str(e)}",
            stage="error"
        )
    finally:
        await reporter.close()


# ============================================================================
# Example 5: Check Job Status
# ============================================================================

async def example_check_status(job_id: str):
    """
    Example: Check the current status of a job
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        status = await reporter.get_status(job_id)

        if status:
            print(f"Job {job_id} Status:")
            print(f"  Status: {status.get('status')}")
            print(f"  Stage: {status.get('stage')}")
            print(f"  Progress: {status.get('progress', 0) * 100:.1f}%")
            print(f"  Message: {status.get('message')}")

            if status.get('error'):
                print(f"  Error: {status.get('error')}")

            if status.get('result'):
                print(f"  Result: {status.get('result')}")
        else:
            print(f"No status found for job {job_id}")

    finally:
        await reporter.close()


# ============================================================================
# Example 6: Integration with FastAPI Endpoint
# ============================================================================

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()


class JobRequest(BaseModel):
    video_url: str
    format: str = "mp4"


@router.post("/jobs/render")
async def create_render_job(request: JobRequest, background_tasks: BackgroundTasks):
    """
    Create a new render job and return job_id
    Client can connect to ws://server/ws/jobs/{job_id} for progress
    """
    import uuid

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Start job in background
    background_tasks.add_task(
        example_video_rendering,
        job_id=job_id
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "websocket_url": f"/ws/jobs/{job_id}",
        "message": "Job queued. Connect to websocket for real-time updates."
    }


@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Get current job status (alternative to WebSocket for polling)
    """
    reporter = ProgressReporter()
    await reporter.initialize()

    try:
        status = await reporter.get_status(job_id)
        if status:
            return status
        else:
            return {
                "error": "Job not found",
                "job_id": job_id
            }
    finally:
        await reporter.close()


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    import sys

    async def main():
        print("WebSocket Progress Service Examples")
        print("=" * 50)

        # Example 1: Simple rendering
        print("\n1. Simple Video Rendering:")
        await example_video_rendering("job_001")

        # Example 2: Multi-stage pipeline
        print("\n2. Multi-Stage AI Pipeline:")
        await example_ai_pipeline("job_002", "/videos/input.mp4")

        # Example 3: Batch processing
        print("\n3. Batch Processing:")
        await example_batch_processing("batch_001", ["video1", "video2", "video3"])

        # Example 4: Error handling
        print("\n4. Error Handling:")
        await example_with_error_handling("job_003")

        # Example 5: Check status
        print("\n5. Check Job Status:")
        await example_check_status("job_001")

    # Run examples
    asyncio.run(main())
