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

# Default hook templates (fallback when config file is not available)
DEFAULT_HOOK_TEMPLATES = {
    "templates": [
        {
            "id": "hook_numbers",
            "phase": "hook",
            "patterns": [
                "Get {result} in {timeframe}",
                "{number}% improvement in {metric}",
                "Transform in just {number} {unit}"
            ],
            "duration": 3,
            "position": "top_center"
        },
        {
            "id": "hook_question",
            "phase": "hook",
            "patterns": [
                "Struggling with {problem}?",
                "Want to {desire}?",
                "Ready to {transformation}?"
            ],
            "duration": 3,
            "position": "top_center"
        },
        {
            "id": "proof_authority",
            "phase": "proof",
            "patterns": [
                "Certified trainer",
                "{number}+ clients transformed",
                "Science-backed method"
            ],
            "duration": 4,
            "position": "bottom_third"
        },
        {
            "id": "cta_urgency",
            "phase": "cta",
            "patterns": [
                "Start your transformation today",
                "Limited spots available",
                "Book your free consultation"
            ],
            "duration": 3,
            "position": "center"
        }
    ],
    "overlay_styles": {
        "hook": {
            "font_size": 72,
            "font_color": "white",
            "background": "rgba(0,0,0,0.7)",
            "animation": "fade_in"
        },
        "proof": {
            "font_size": 48,
            "font_color": "white",
            "background": "rgba(0,0,0,0.6)",
            "animation": "slide_up"
        },
        "cta": {
            "font_size": 64,
            "font_color": "yellow",
            "background": "rgba(0,0,0,0.8)",
            "animation": "pulse"
        }
    }
}

# Load configuration (with fallback to defaults)
config_path = os.getenv("CONFIG_PATH", "../../shared/config")
try:
    with open(f"{config_path}/hook_templates.json", "r") as f:
        hook_templates = json.load(f)
except (FileNotFoundError, PermissionError, json.JSONDecodeError, OSError):
    hook_templates = DEFAULT_HOOK_TEMPLATES

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
        
        # Enqueue job to Redis
        import redis
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        
        job_payload = {
            "job_id": job_id,
            "request": request.dict(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        redis_client.rpush("render_queue", json.dumps(job_payload))
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Render job queued for worker"
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
        output_dir = os.getenv("OUTPUT_DIR", "/tmp/outputs")
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


@app.post('/generate/batch')
async def generate_batch(request: dict, background_tasks: BackgroundTasks):
    """
    Generate multiple ad variants from a single creative brief
    Returns job IDs for all variants
    """
    try:
        # Import variant generator
        from src.variant_generator import variant_generator
        
        # Extract base creative data
        base_creative = {
            "id": str(uuid.uuid4()),
            "product_name": request.get("product_name"),
            "pain_point": request.get("pain_points", [""])[0] if request.get("pain_points") else "challenges",
            "benefit": request.get("desires", [""])[0] if request.get("desires") else "better results",
            "target_avatar": request.get("target_avatar", "customers"),
            "hook": request.get("hook", "Discover something amazing"),
            "cta": request.get("cta", "Learn More"),
            "cta_type": request.get("cta_type", "learn_more"),
            "avatar_id": request.get("avatar_id"),
            "available_avatars": request.get("available_avatars", []),
            "variant": request.get("variant", "reels"),
            "scenes": request.get("scenes", [])
        }
        
        # Generate variants
        variant_count = request.get("variant_count", 5)
        variants = variant_generator.generate_variants(
            base_creative,
            variant_count=variant_count,
            vary_hooks=request.get("vary_hooks", True),
            vary_ctas=request.get("vary_ctas", True),
            vary_avatars=request.get("vary_avatars", False)
        )
        
        # Queue each variant for rendering
        job_ids = []
        for variant in variants:
            job_id = str(uuid.uuid4())
            job_payload = {
                "job_id": job_id,
                "request": variant,
                "created_at": datetime.utcnow().isoformat()
            }
            
            redis_client.rpush("render_queue", json.dumps(job_payload))
            job_ids.append({
                "job_id": job_id,
                "variant_id": variant["variant_id"],
                "variant_type": variant["variant_type"],
                "hook": variant["hook"]
            })
        
        return {
            "status": "success",
            "message": f"{len(job_ids)} variants queued for rendering",
            "jobs": job_ids,
            "base_id": base_creative["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
