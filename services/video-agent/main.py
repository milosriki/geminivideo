"""
Video Agent Service - FastAPI application for video rendering and remixing.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
import uuid
from contextlib import asynccontextmanager
from enum import Enum

from services.job_manager import JobManager
from services.renderer import RendererService
from services.overlay import OverlayGenerator
from services.subtitle import SubtitlePipeline
from services.compliance import ComplianceChecker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global service instances
services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    logger.info("Initializing Video Agent services...")
    
    # Initialize services
    services["job_manager"] = JobManager()
    services["renderer"] = RendererService()
    services["overlay"] = OverlayGenerator()
    services["subtitle"] = SubtitlePipeline()
    services["compliance"] = ComplianceChecker()
    
    logger.info("Services initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    await services["job_manager"].shutdown()
    services.clear()

app = FastAPI(
    title="Video Agent Service",
    description="Video rendering, remixing, and compliance checking",
    version="1.0.0",
    lifespan=lifespan
)

# Enums
class VariantType(str, Enum):
    REELS = "reels"
    FEED = "feed"
    STORIES = "stories"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Request/Response models
class RemixRequest(BaseModel):
    clips: List[Dict[str, Any]] = Field(..., description="List of clips to remix")
    variant: VariantType = Field(VariantType.REELS, description="Output variant type")
    enableSubtitles: bool = Field(True, description="Enable subtitle generation")
    enableOverlays: bool = Field(True, description="Enable overlay generation")
    useTransitions: bool = Field(False, description="Use transitions between clips")
    normalize Audio: bool = Field(True, description="Apply loudness normalization")

class JobResponse(BaseModel):
    jobId: str
    status: JobStatus
    progress: float = 0.0
    outputUrl: Optional[str] = None
    compliance: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "video-agent"}

# Rendering endpoints
@app.post("/render/remix", response_model=JobResponse)
async def create_remix_job(request: RemixRequest):
    """Create a video remix job."""
    try:
        job_manager: JobManager = services["job_manager"]
        
        # Create job
        job_id = str(uuid.uuid4())
        job = {
            "jobId": job_id,
            "status": JobStatus.PENDING,
            "progress": 0.0,
            "request": request.dict()
        }
        
        # Start async processing
        await job_manager.create_job(job_id, job)
        await job_manager.process_job(job_id, services)
        
        return JobResponse(
            jobId=job_id,
            status=JobStatus.PENDING,
            progress=0.0
        )
    except Exception as e:
        logger.error(f"Failed to create remix job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/render/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Get the status of a rendering job."""
    try:
        job_manager: JobManager = services["job_manager"]
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/render/jobs")
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of jobs to return")
) -> List[JobResponse]:
    """List all rendering jobs."""
    try:
        job_manager: JobManager = services["job_manager"]
        jobs = job_manager.list_jobs(status=status, limit=limit)
        return [JobResponse(**job) for job in jobs]
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Compliance endpoint
@app.post("/compliance/check")
async def check_compliance(videoPath: str):
    """Check compliance for a video file."""
    try:
        compliance_checker: ComplianceChecker = services["compliance"]
        result = await compliance_checker.check(videoPath)
        return result
    except Exception as e:
        logger.error(f"Compliance check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
