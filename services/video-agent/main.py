"""
Video Agent Service - Rendering, Compliance & Multi-Format Export
Handles video rendering with overlays, subtitles, and compliance checks
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime
import uuid

from services.renderer import VideoRenderer
from services.overlay_generator import OverlayGenerator
from services.subtitle_generator import SubtitleGenerator
from services.compliance_checker import ComplianceChecker
from models.render_job import RenderJob, RenderStatus

app = FastAPI(title="Video Agent Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config_path = os.getenv("CONFIG_PATH", "../../shared/config")
with open(f"{config_path}/hook_templates.json", "r") as f:
    hook_templates = json.load(f)

# Initialize services
renderer = VideoRenderer()
overlay_generator = OverlayGenerator(hook_templates)
subtitle_generator = SubtitleGenerator()
compliance_checker = ComplianceChecker()

# In-memory job storage (would be Redis/DB in production)
render_jobs: Dict[str, RenderJob] = {}


# Request/Response Models
class SceneInput(BaseModel):
    """Input scene for remix"""
    clip_id: str
    asset_id: str
    start_time: float
    end_time: float
    video_path: str


class RemixRequest(BaseModel):
    """Request to render a remixed video"""
    scenes: List[SceneInput]
    variant: str = Field(default="reels", pattern="^(reels|feed|stories)$")
    template_id: Optional[str] = None
    driver_signals: Dict[str, Any] = Field(default_factory=dict)
    enable_transitions: bool = True
    enable_subtitles: bool = True
    enable_overlays: bool = True


@app.get("/")
async def root():
    return {"service": "video-agent", "status": "running", "version": "1.0.0"}


@app.post("/render/remix")
async def render_remix(
    request: RemixRequest,
    background_tasks: BackgroundTasks
):
    """
    Render a remixed video with overlays, subtitles, and transitions
    Returns job ID for async processing
    """
    try:
        # Create render job
        job_id = str(uuid.uuid4())
        job = RenderJob(
            id=job_id,
            status=RenderStatus.PENDING,
            request=request.dict()
        )
        render_jobs[job_id] = job
        
        # Start rendering in background
        background_tasks.add_task(
            _process_render_job,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Render job queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/render/status/{job_id}")
async def get_render_status(job_id: str):
    """
    Get status of a render job
    """
    if job_id not in render_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = render_jobs[job_id]
    return job.dict()


async def _process_render_job(job_id: str, request: RemixRequest):
    """
    Process a render job (runs in background)
    """
    job = render_jobs[job_id]
    
    try:
        job.status = RenderStatus.PROCESSING
        job.updated_at = datetime.utcnow()
        
        # Determine output format based on variant
        formats = {
            "reels": {"width": 1080, "height": 1920, "aspect": "9:16"},
            "feed": {"width": 1080, "height": 1080, "aspect": "1:1"},
            "stories": {"width": 1080, "height": 1920, "aspect": "9:16"}
        }
        
        output_format = formats.get(request.variant, formats["reels"])
        
        # Output directory
        output_dir = os.getenv("OUTPUT_DIR", "../../data/outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(
            output_dir,
            f"remix_{job_id}_{request.variant}.mp4"
        )
        
        # Step 1: Concatenate scenes
        job.progress = 0.2
        concatenated_path = await renderer.concatenate_scenes(
            scenes=request.scenes,
            enable_transitions=request.enable_transitions
        )
        
        # Step 2: Generate overlays if enabled
        overlay_path = None
        if request.enable_overlays:
            job.progress = 0.4
            overlay_path = overlay_generator.generate_overlays(
                scenes=request.scenes,
                driver_signals=request.driver_signals,
                template_id=request.template_id,
                duration=sum(s.end_time - s.start_time for s in request.scenes)
            )
        
        # Step 3: Generate subtitles if enabled
        subtitle_path = None
        if request.enable_subtitles:
            job.progress = 0.6
            subtitle_path = subtitle_generator.generate_subtitles(
                scenes=request.scenes,
                driver_signals=request.driver_signals
            )
        
        # Step 4: Final composition
        job.progress = 0.8
        await renderer.compose_final_video(
            input_path=concatenated_path,
            output_path=output_path,
            output_format=output_format,
            overlay_path=overlay_path,
            subtitle_path=subtitle_path
        )
        
        # Step 5: Compliance checks
        job.progress = 0.9
        compliance_result = compliance_checker.check_compliance(
            video_path=output_path,
            variant=request.variant,
            subtitle_path=subtitle_path
        )
        
        # Update job with results
        job.status = RenderStatus.COMPLETED
        job.progress = 1.0
        job.output_path = output_path
        job.compliance = compliance_result
        job.updated_at = datetime.utcnow()
        
    except Exception as e:
        job.status = RenderStatus.FAILED
        job.error = str(e)
        job.updated_at = datetime.utcnow()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "jobs_count": len(render_jobs)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
