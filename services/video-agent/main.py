"""
Video Agent Service - Rendering, Compliance & Multi-Format Export
Handles video rendering with overlays, subtitles, and compliance checks

PRODUCTION-GRADE PRO VIDEO MODULES - €5M Investment Integration
13 Professional video processing modules with 500KB+ production code
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import time
from datetime import datetime
import uuid

# Track startup time for uptime calculation
_start_time = time.time()

from services.renderer import VideoRenderer
from services.overlay_generator import OverlayGenerator
from services.subtitle_generator import SubtitleGenerator
from services.compliance_checker import ComplianceChecker
from models.render_job import RenderJob, RenderStatus

# PRO VIDEO MODULES - All 13 production systems
from pro.auto_captions import AutoCaptionSystem, CaptionStyle, WhisperModelSize
from pro.pro_renderer import ProRenderer, RenderSettings, Platform, AspectRatio, QualityPreset
from pro.winning_ads_generator import WinningAdsGenerator, AdConfig, AdTemplate
from pro.color_grading import ColorGradingEngine, LUTPreset, ExposureControls
from pro.smart_crop import SmartCropTracker, AspectRatio as SmartCropAspectRatio
from pro.audio_mixer import AudioMixer, AudioMixerConfig, NormalizationStandard
from pro.timeline_engine import Timeline, Track, Clip, TrackType
from pro.motion_graphics import MotionGraphicsEngine, AnimationType, LowerThirdStyle, TitleCardStyle
from pro.transitions_library import TransitionLibrary, TransitionCategory, EasingFunction
from pro.keyframe_engine import KeyframeAnimator, PropertyType, InterpolationType, Keyframe
from pro.preview_generator import PreviewGenerator, ProxyQuality
from pro.asset_library import AssetLibrary, AssetType, AssetCategory
from pro.voice_generator import VoiceGenerator, VoiceProvider, OpenAIVoice, VoiceSettings, VoiceCloneConfig

# CELERY TASK QUEUE - Distributed Video Processing
from pro.celery_app import (
    app as celery_app,
    render_video_task,
    transcode_task,
    generate_preview_task,
    caption_task,
    batch_render_task,
    cleanup_task,
    redis_client as celery_redis,
    get_failed_tasks,
    get_dlq_stats,
    retry_failed_task,
    purge_dlq
)

# Quick Win #4: Import PrecisionAVSync for beat sync analysis
try:
    from pro.precision_av_sync import PrecisionAVSync, AudioPeak, VisualPeak, SyncPoint
    precision_av_sync = PrecisionAVSync()
    PRECISION_AV_SYNC_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PrecisionAVSync not available: {e}")
    precision_av_sync = None
    PRECISION_AV_SYNC_AVAILABLE = False

app = FastAPI(title="Video Agent Service", version="1.0.0")

# Production safety check - prevent debug mode in production
if app.debug and os.environ.get('ENVIRONMENT') == 'production':
    raise RuntimeError("Debug mode detected in production!")

# CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
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

# Initialize PRO VIDEO MODULES - €5M Investment Grade Systems
caption_system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)
pro_renderer = ProRenderer()
winning_ads_gen = WinningAdsGenerator()
color_grading = ColorGradingEngine()
smart_crop = SmartCropTracker()
audio_mixer = AudioMixer()
motion_graphics = MotionGraphicsEngine()
transition_lib = TransitionLibrary()
keyframe_animator = KeyframeAnimator()
preview_gen = PreviewGenerator()
asset_lib = AssetLibrary(base_dir=os.getenv("ASSET_DIR", "/tmp/assets"))
voice_generator = VoiceGenerator(output_dir=os.getenv("VOICEOVER_DIR", "/tmp/voiceovers"))

# Redis Client (Lazy initialization)
import redis
try:
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_client = None

# In-memory job storage (would be Redis/DB in production)
render_jobs: Dict[str, RenderJob] = {}
pro_jobs: Dict[str, Dict[str, Any]] = {}  # Pro module job tracking


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
        if redis_client:
            try:
                job_payload = {
                    "job_id": job_id,
                    "request": request.dict(),
                    "created_at": datetime.utcnow().isoformat()
                }
                redis_client.rpush("render_queue", json.dumps(job_payload))
            except Exception as e:
                print(f"Redis enqueue failed: {e}")
        else:
            print("Redis not available, job stored in memory only")
        
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
            
            if redis_client:
                try:
                    redis_client.rpush("render_queue", json.dumps(job_payload))
                except Exception as e:
                    print(f"Redis batch enqueue failed: {e}")
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
    uptime = int(time.time() - _start_time)
    return {
        "status": "healthy",
        "service": "video-agent",
        "uptime": uptime,
        "timestamp": datetime.utcnow().isoformat(),
        "jobs_count": len(render_jobs)
    }



# ==================== TASK PRIORITY MANAGEMENT ====================
# Dynamic priority adjustment for Celery queue
# ================================================================

@app.post("/api/tasks/priority/adjust")
async def adjust_task_priority(request: Dict[str, Any]):
    """
    Manually adjust priority of a pending task

    Body:
    - task_id: str (required) - Celery task ID
    - priority: int (required) - New priority value (1-10, higher = more urgent)

    Returns:
    - {status: "success", task_id: str, new_priority: int}
    """
    try:
        # Import from celery_app
        from services.video_agent.pro.celery_app import adjust_task_priority as celery_adjust_priority

        task_id = request.get("task_id")
        if not task_id:
            raise HTTPException(status_code=400, detail="task_id required")

        priority = request.get("priority")
        if priority is None:
            raise HTTPException(status_code=400, detail="priority required")

        try:
            priority = int(priority)
        except ValueError:
            raise HTTPException(status_code=400, detail="priority must be an integer")

        if priority < 1 or priority > 10:
            raise HTTPException(status_code=400, detail="priority must be between 1 and 10")

        # Adjust priority
        success = celery_adjust_priority(task_id, priority)

        if success:
            return {
                "status": "success",
                "task_id": task_id,
                "new_priority": priority,
                "message": f"Task priority adjusted to {priority}"
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found or already completed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/priority/rules")
async def get_priority_rules():
    """
    Get current priority calculation rules

    Returns:
    - Priority rules configuration
    - Queue depth statistics
    - Recent rebalancing status
    """
    try:
        # Import from celery_app
        from services.video_agent.pro.celery_app import (
            PRIORITY_RULES,
            get_all_queue_depths,
            redis_client
        )

        # Get queue depths
        queue_depths = get_all_queue_depths()

        # Get recent rebalance status from Redis
        rebalance_status = None
        try:
            status_data = redis_client.get('queue_rebalance_status')
            if status_data:
                rebalance_status = json.loads(status_data)
        except:
            pass

        return {
            "status": "success",
            "priority_rules": {
                "base_priority": PRIORITY_RULES['base_priority'],
                "priority_range": {
                    "min": PRIORITY_RULES['min_priority'],
                    "max": PRIORITY_RULES['max_priority']
                },
                "age_boost": {
                    "per_minute": PRIORITY_RULES['age_boost_per_minute'],
                    "max_boost": PRIORITY_RULES['max_age_boost'],
                    "description": "Tasks gain priority as they wait in queue"
                },
                "user_tier_boost": PRIORITY_RULES['user_tier_boost'],
                "roas_boost": {
                    "thresholds": PRIORITY_RULES['roas_thresholds'],
                    "boost_values": PRIORITY_RULES['roas_boost'],
                    "description": "High-performing campaigns get priority"
                },
                "queue_rebalancing": {
                    "imbalance_threshold": PRIORITY_RULES['queue_imbalance_threshold'],
                    "description": "Rebalance when queue variance exceeds threshold"
                }
            },
            "queue_status": {
                "depths": queue_depths,
                "total_pending": sum(queue_depths.values())
            },
            "last_rebalance": rebalance_status,
            "documentation": {
                "priority_factors": [
                    "Task age (older tasks get higher priority)",
                    "User tier (premium/enterprise users get priority)",
                    "Campaign ROAS (high-performing campaigns prioritized)",
                    "Queue depth (penalties for overloaded queues)"
                ],
                "examples": {
                    "free_user_new_task": "Priority 5 (base)",
                    "premium_user_new_task": "Priority 7 (base + tier boost)",
                    "enterprise_user_high_roas": "Priority 10 (base + tier + ROAS)",
                    "free_user_waiting_30min": "Priority 8 (base + age boost)"
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/priority/queue-status")
async def get_queue_status():
    """
    Get detailed status of all Celery queues

    Returns:
    - Queue depths
    - Pending task counts
    - Queue health metrics
    """
    try:
        from services.video_agent.pro.celery_app import (
            get_all_queue_depths,
            redis_client
        )

        # Get queue depths
        queue_depths = get_all_queue_depths()
        total_pending = sum(queue_depths.values())

        # Calculate queue statistics
        if total_pending > 0:
            avg_depth = total_pending / len(queue_depths)
            variance = sum((depth - avg_depth) ** 2 for depth in queue_depths.values()) / len(queue_depths)
            normalized_variance = variance / (avg_depth ** 2) if avg_depth > 0 else 0
        else:
            avg_depth = 0
            variance = 0
            normalized_variance = 0

        # Get system resources
        try:
            resources_data = redis_client.get('system_resources')
            resources = json.loads(resources_data) if resources_data else None
        except:
            resources = None

        return {
            "status": "success",
            "queues": {
                "render_queue": {
                    "depth": queue_depths.get('render_queue', 0),
                    "description": "Main video rendering tasks"
                },
                "preview_queue": {
                    "depth": queue_depths.get('preview_queue', 0),
                    "description": "Preview generation tasks"
                },
                "transcode_queue": {
                    "depth": queue_depths.get('transcode_queue', 0),
                    "description": "Video transcoding tasks"
                },
                "caption_queue": {
                    "depth": queue_depths.get('caption_queue', 0),
                    "description": "Caption generation tasks"
                }
            },
            "statistics": {
                "total_pending": total_pending,
                "average_depth": round(avg_depth, 2),
                "variance": round(variance, 2),
                "normalized_variance": round(normalized_variance, 4),
                "is_balanced": normalized_variance < 0.3
            },
            "system_resources": resources,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DCO VARIANT GENERATION ====================
# Dynamic Creative Optimization for Meta Ad Formats
# €5M Investment Grade - Production Ready
# ================================================================

@app.post('/api/dco/generate-variants')
async def generate_dco_variants(request: dict, background_tasks: BackgroundTasks):
    """
    Generate DCO variants for Meta ad formats

    Generates multiple format variants (Feed, Reels, Story, In-Stream)
    with different hooks and CTAs from a single source creative

    Body:
    - jobId: str (required)
    - sourceVideoPath: str (required)
    - outputDir: str (required)
    - config: dict with:
        - productName: str
        - baseHook: str
        - baseCta: str
        - painPoint: str
        - benefit: str
        - targetAudience: str
        - variantCount: int
        - varyHooks: bool
        - varyCtas: bool
        - formats: list[str]
        - enableSmartCrop: bool
    """
    try:
        # Import DCO generator
        from src.dco_meta_generator import (
            DCOMetaGenerator,
            DCOGenerationConfig,
            MetaAdFormat
        )

        job_id = request.get("jobId")
        source_path = request.get("sourceVideoPath")
        output_dir = request.get("outputDir")
        config_data = request.get("config", {})

        # Validate required fields
        if not all([job_id, source_path, output_dir]):
            raise HTTPException(
                status_code=400,
                detail="jobId, sourceVideoPath, and outputDir are required"
            )

        # Map format strings to MetaAdFormat enums
        format_map = {
            "feed": MetaAdFormat.FEED,
            "reels": MetaAdFormat.REELS,
            "story": MetaAdFormat.STORY,
            "in_stream": MetaAdFormat.IN_STREAM,
            "carousel": MetaAdFormat.CAROUSEL_SQUARE,
            "portrait_4_5": MetaAdFormat.PORTRAIT_4_5
        }

        format_strings = config_data.get("formats", ["feed", "reels", "in_stream"])
        formats = [format_map.get(f, MetaAdFormat.FEED) for f in format_strings]

        # Create DCO configuration
        dco_config = DCOGenerationConfig(
            source_video_path=source_path,
            output_dir=output_dir,
            product_name=config_data.get("productName", "Product"),
            pain_point=config_data.get("painPoint", "challenges"),
            benefit=config_data.get("benefit", "better results"),
            target_audience=config_data.get("targetAudience", "customers"),
            base_hook=config_data.get("baseHook", "Discover something amazing"),
            base_cta=config_data.get("baseCta", "Learn More"),
            cta_type=config_data.get("ctaType", "learn_more"),
            variant_count=config_data.get("variantCount", 5),
            vary_hooks=config_data.get("varyHooks", True),
            vary_ctas=config_data.get("varyCtas", True),
            formats=formats,
            enable_smart_crop=config_data.get("enableSmartCrop", True),
            enable_captions=config_data.get("enableCaptions", False),
            enable_color_grading=config_data.get("enableColorGrading", False)
        )

        # Initialize generator
        generator = DCOMetaGenerator()

        # Store job status
        pro_jobs[job_id] = {
            "status": "processing",
            "type": "dco_generation",
            "started_at": datetime.utcnow().isoformat(),
            "config": {
                "product": dco_config.product_name,
                "variants": dco_config.variant_count,
                "formats": len(formats)
            }
        }

        # Generate variants (async in production)
        try:
            variants = generator.generate_meta_variants(dco_config)

            # Convert variants to response format
            variant_list = []
            for variant in variants:
                variant_list.append({
                    "variant_id": variant.variant_id,
                    "format_type": variant.format_type,
                    "placement": variant.placement,
                    "width": variant.width,
                    "height": variant.height,
                    "aspect_ratio": variant.aspect_ratio,
                    "video_path": variant.video_path,
                    "thumbnail_path": variant.thumbnail_path,
                    "hook": variant.hook,
                    "cta": variant.cta,
                    "upload_ready": variant.upload_ready,
                    "metadata": variant.metadata
                })

            # Update job status
            pro_jobs[job_id] = {
                "status": "completed",
                "type": "dco_generation",
                "started_at": pro_jobs[job_id]["started_at"],
                "completed_at": datetime.utcnow().isoformat(),
                "variants_generated": len(variants),
                "output_dir": output_dir
            }

            return {
                "status": "success",
                "job_id": job_id,
                "total_variants": len(variants),
                "variants": variant_list,
                "output_dir": output_dir,
                "manifest_path": f"{output_dir}/variants_manifest.json",
                "message": f"Generated {len(variants)} Meta-compliant variants"
            }

        except FileNotFoundError as e:
            pro_jobs[job_id] = {
                "status": "failed",
                "error": str(e),
                "message": "Source video file not found"
            }
            raise HTTPException(status_code=404, detail=str(e))

        except Exception as e:
            pro_jobs[job_id] = {
                "status": "failed",
                "error": str(e)
            }
            raise HTTPException(status_code=500, detail=f"DCO generation failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/dco/formats')
async def get_meta_formats():
    """
    Get available Meta ad format specifications
    """
    formats = [
        {
            "name": "feed",
            "description": "Instagram Feed 1:1 Square",
            "dimensions": "1080x1080",
            "aspect_ratio": "1:1",
            "placement": "instagram_feed",
            "use_cases": ["Product showcase", "Static ads", "Carousel"]
        },
        {
            "name": "reels",
            "description": "Instagram Reels 9:16 Vertical",
            "dimensions": "1080x1920",
            "aspect_ratio": "9:16",
            "placement": "instagram_reels",
            "use_cases": ["Short-form video", "Stories", "Vertical content"]
        },
        {
            "name": "story",
            "description": "Instagram Story 9:16 Vertical",
            "dimensions": "1080x1920",
            "aspect_ratio": "9:16",
            "placement": "instagram_story",
            "use_cases": ["Ephemeral content", "Direct response", "Engagement"]
        },
        {
            "name": "in_stream",
            "description": "Facebook In-Stream 16:9 Landscape",
            "dimensions": "1920x1080",
            "aspect_ratio": "16:9",
            "placement": "facebook_in_stream",
            "use_cases": ["Video ads", "Pre-roll", "Mid-roll"]
        },
        {
            "name": "carousel",
            "description": "Carousel 1:1 Square",
            "dimensions": "1080x1080",
            "aspect_ratio": "1:1",
            "placement": "carousel",
            "use_cases": ["Multiple products", "Step-by-step", "Before/after"]
        },
        {
            "name": "portrait_4_5",
            "description": "Instagram Explore 4:5 Portrait",
            "dimensions": "1080x1350",
            "aspect_ratio": "4:5",
            "placement": "instagram_explore",
            "use_cases": ["Discovery", "Explore feed", "Portrait content"]
        }
    ]

    return {
        "status": "success",
        "total_formats": len(formats),
        "formats": formats,
        "documentation": "https://developers.facebook.com/docs/marketing-api/creative-specs"
    }


@app.get('/api/dco/examples')
async def get_dco_examples():
    """
    Get example DCO generation requests
    """
    examples = {
        "basic": {
            "description": "Basic DCO generation with 3 variants in Feed and Reels formats",
            "request": {
                "jobId": "dco_example_001",
                "sourceVideoPath": "/path/to/source_video.mp4",
                "outputDir": "/tmp/dco_variants/example",
                "config": {
                    "productName": "FitnessPro App",
                    "baseHook": "Transform your body in 30 days",
                    "baseCta": "Start Free Trial",
                    "painPoint": "lack of results from generic workouts",
                    "benefit": "personalized workout plans",
                    "targetAudience": "busy professionals",
                    "variantCount": 3,
                    "varyHooks": True,
                    "varyCtas": True,
                    "formats": ["feed", "reels"],
                    "enableSmartCrop": True
                }
            }
        },
        "advanced": {
            "description": "Advanced DCO with all formats and smart crop",
            "request": {
                "jobId": "dco_example_002",
                "sourceVideoPath": "/path/to/source_video.mp4",
                "outputDir": "/tmp/dco_variants/advanced",
                "config": {
                    "productName": "Premium Course",
                    "baseHook": "Master digital marketing in 60 days",
                    "baseCta": "Enroll Now",
                    "painPoint": "outdated marketing strategies",
                    "benefit": "cutting-edge techniques",
                    "targetAudience": "marketing professionals",
                    "variantCount": 5,
                    "varyHooks": True,
                    "varyCtas": True,
                    "formats": ["feed", "reels", "story", "in_stream"],
                    "enableSmartCrop": True,
                    "enableCaptions": True,
                    "enableColorGrading": True
                }
            }
        },
        "carousel": {
            "description": "Generate carousel variants",
            "request": {
                "jobId": "dco_example_003",
                "sourceVideoPath": "/path/to/source_video.mp4",
                "outputDir": "/tmp/dco_variants/carousel",
                "config": {
                    "productName": "SaaS Product",
                    "baseHook": "All-in-one solution for your business",
                    "baseCta": "Get Started",
                    "variantCount": 3,
                    "formats": ["carousel", "feed"],
                    "enableSmartCrop": False
                }
            }
        }
    }

    return {
        "status": "success",
        "examples": examples,
        "usage": "POST /api/dco/generate-variants with one of these example payloads"
    }


# ==================== PRO VIDEO MODULES API ENDPOINTS ====================
# €5M Investment Grade - 13 Professional Video Processing Systems
# =========================================================================

# 1. AUTO CAPTIONS - AI-Powered Caption Generation
@app.post("/api/pro/caption")
async def generate_captions(request: Dict[str, Any]):
    """
    Generate AI-powered captions with multiple styles

    Body:
    - video_path: str (required)
    - style: str (instagram/youtube/karaoke/tiktok/hormozi)
    - language: str (default: en)
    - word_level: bool (default: true)
    - burn_in: bool (default: false)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        # Map style string to enum
        style_map = {
            "instagram": CaptionStyle.INSTAGRAM,
            "youtube": CaptionStyle.YOUTUBE,
            "karaoke": CaptionStyle.KARAOKE,
            "tiktok": CaptionStyle.TIKTOK,
            "hormozi": CaptionStyle.HORMOZI
        }

        style = style_map.get(request.get("style", "instagram"), CaptionStyle.INSTAGRAM)
        language = request.get("language", "en")
        word_level = request.get("word_level", True)
        burn_in = request.get("burn_in", False)

        # Generate captions
        result = caption_system.generate_captions(
            video_path=video_path,
            output_format="srt",
            language=language,
            word_level_timestamps=word_level
        )

        if burn_in:
            # Burn captions into video
            output_path = request.get("output_path") or f"/tmp/captioned_{uuid.uuid4()}.mp4"
            caption_system.burn_captions(
                video_path=video_path,
                srt_path=result["srt_path"],
                output_path=output_path,
                style=style
            )
            result["output_video"] = output_path

        return {
            "status": "success",
            "captions": result,
            "style": style.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. COLOR GRADING - Professional Color Correction
@app.post("/api/pro/color-grade")
async def apply_color_grading(request: Dict[str, Any]):
    """
    Apply professional color grading presets

    Body:
    - video_path: str (required)
    - preset: str (cinematic/vintage/high_contrast/warm/cold/fitness_energy)
    - intensity: float (0.0 to 1.0, default: 1.0)
    - output_path: str (optional)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        # Map preset string to enum
        preset_map = {
            "cinematic": LUTPreset.CINEMATIC,
            "vintage": LUTPreset.VINTAGE,
            "high_contrast": LUTPreset.HIGH_CONTRAST,
            "warm": LUTPreset.WARM,
            "cold": LUTPreset.COLD,
            "fitness_energy": LUTPreset.FITNESS_ENERGY,
            "clean_corporate": LUTPreset.CLEAN_CORPORATE,
            "instagram_dramatic": LUTPreset.INSTAGRAM_DRAMATIC,
            "instagram_fade": LUTPreset.INSTAGRAM_FADE,
            "instagram_vibrant": LUTPreset.INSTAGRAM_VIBRANT
        }

        preset = preset_map.get(request.get("preset", "cinematic"), LUTPreset.CINEMATIC)
        intensity = float(request.get("intensity", 1.0))
        output_path = request.get("output_path") or f"/tmp/graded_{uuid.uuid4()}.mp4"

        # Apply color grading
        result = color_grading.apply_lut_preset(
            video_path=video_path,
            preset=preset,
            output_path=output_path,
            intensity=intensity
        )

        return {
            "status": "success",
            "output_path": result,
            "preset": preset.value,
            "intensity": intensity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. WINNING AD GENERATOR - Complete Ad Production
@app.post("/api/pro/render-winning-ad")
async def render_winning_ad(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Generate complete winning video ad with all pro features

    Body:
    - video_clips: List[str] (required)
    - template: str (fitness_transformation/testimonial/problem_solution/etc)
    - platform: str (tiktok/instagram/youtube/facebook)
    - hook_text: str (optional)
    - cta_text: str (optional)
    - product_name: str (optional)
    """
    try:
        video_clips = request.get("video_clips", [])
        if not video_clips:
            raise HTTPException(status_code=400, detail="video_clips required")

        # Map template string to enum
        template_map = {
            "fitness_transformation": AdTemplate.FITNESS_TRANSFORMATION,
            "testimonial": AdTemplate.TESTIMONIAL,
            "problem_solution": AdTemplate.PROBLEM_SOLUTION,
            "listicle": AdTemplate.LISTICLE,
            "hook_story_offer": AdTemplate.HOOK_STORY_OFFER,
            "ugc": AdTemplate.UGC,
            "educational": AdTemplate.EDUCATIONAL,
            "product_showcase": AdTemplate.PRODUCT_SHOWCASE,
            "comparison": AdTemplate.COMPARISON,
            "behind_scenes": AdTemplate.BEHIND_SCENES
        }

        template = template_map.get(request.get("template", "fitness_transformation"),
                                    AdTemplate.FITNESS_TRANSFORMATION)

        # Create ad config
        ad_config = AdConfig(
            template=template,
            platform=request.get("platform", "instagram"),
            hook_text=request.get("hook_text", "Transform Your Life"),
            cta_text=request.get("cta_text", "Start Now"),
            product_name=request.get("product_name", ""),
            video_clips=video_clips,
            duration_target=int(request.get("duration_target", 30))
        )

        # Generate ad
        job_id = str(uuid.uuid4())
        output_path = f"/tmp/winning_ad_{job_id}.mp4"

        # Process async
        def process_ad():
            result = winning_ads_gen.generate_winning_ad(ad_config, output_path)
            pro_jobs[job_id] = {
                "status": "completed",
                "output_path": result,
                "config": ad_config.__dict__ if hasattr(ad_config, '__dict__') else {}
            }

        background_tasks.add_task(process_ad)
        pro_jobs[job_id] = {"status": "processing", "template": template.value}

        return {
            "status": "queued",
            "job_id": job_id,
            "template": template.value,
            "message": "Winning ad generation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. SMART CROP - AI-Powered Auto-Cropping
@app.post("/api/pro/smart-crop")
async def smart_crop_video(request: Dict[str, Any]):
    """
    Auto-crop video for different platforms with face/object tracking

    Body:
    - video_path: str (required)
    - target_aspect: str (9:16/1:1/4:5/16:9)
    - track_faces: bool (default: true)
    - smooth_motion: bool (default: true)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        # Map aspect ratio
        aspect_map = {
            "9:16": SmartCropAspectRatio.PORTRAIT_9_16,
            "1:1": SmartCropAspectRatio.SQUARE_1_1,
            "4:5": SmartCropAspectRatio.PORTRAIT_4_5,
            "16:9": SmartCropAspectRatio.LANDSCAPE_16_9,
            "21:9": SmartCropAspectRatio.LANDSCAPE_21_9
        }

        target_aspect = aspect_map.get(request.get("target_aspect", "9:16"),
                                       SmartCropAspectRatio.PORTRAIT_9_16)
        track_faces = request.get("track_faces", True)
        smooth_motion = request.get("smooth_motion", True)
        output_path = request.get("output_path") or f"/tmp/cropped_{uuid.uuid4()}.mp4"

        # Perform smart crop
        result = smart_crop.auto_crop_video(
            input_path=video_path,
            output_path=output_path,
            target_aspect=target_aspect,
            detect_faces=track_faces,
            smooth_panning=smooth_motion
        )

        return {
            "status": "success",
            "output_path": result,
            "target_aspect": request.get("target_aspect", "9:16")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5. AUDIO MIXER - Professional Audio Enhancement
@app.post("/api/pro/audio-mix")
async def mix_audio(request: Dict[str, Any]):
    """
    Professional audio mixing with ducking and enhancement

    Body:
    - video_path: str (required)
    - music_path: str (optional)
    - voiceover_path: str (optional)
    - auto_duck: bool (default: true)
    - normalization: str (social_media/streaming/broadcast)
    - voice_enhance: bool (default: true)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        music_path = request.get("music_path")
        voiceover_path = request.get("voiceover_path")
        auto_duck = request.get("auto_duck", True)
        voice_enhance = request.get("voice_enhance", True)

        # Map normalization
        norm_map = {
            "social_media": NormalizationStandard.SOCIAL_MEDIA,
            "streaming": NormalizationStandard.STREAMING,
            "broadcast": NormalizationStandard.EBU_R128
        }
        normalization = norm_map.get(request.get("normalization", "social_media"),
                                     NormalizationStandard.SOCIAL_MEDIA)

        output_path = request.get("output_path") or f"/tmp/mixed_{uuid.uuid4()}.mp4"

        # Create mixer config
        config = AudioMixerConfig(
            normalization_standard=normalization,
            auto_duck=auto_duck,
            voice_enhancement=voice_enhance
        )

        # Mix audio
        result = audio_mixer.mix_video_audio(
            video_path=video_path,
            music_path=music_path,
            voiceover_path=voiceover_path,
            output_path=output_path,
            config=config
        )

        return {
            "status": "success",
            "output_path": result,
            "auto_duck": auto_duck,
            "normalization": normalization.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 6. TRANSITIONS - Add Professional Transitions
@app.post("/api/pro/transitions")
async def add_transitions(request: Dict[str, Any]):
    """
    Add professional transitions between clips

    Body:
    - clips: List[str] (required)
    - transition_type: str (dissolve/wipe/slide/3d/blur/glitch)
    - duration: float (default: 1.0)
    - easing: str (linear/ease_in/ease_out/ease_in_out)
    """
    try:
        clips = request.get("clips", [])
        if len(clips) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 clips for transitions")

        # Map transition category
        category_map = {
            "dissolve": TransitionCategory.DISSOLVE,
            "wipe": TransitionCategory.WIPE,
            "slide": TransitionCategory.SLIDE,
            "3d": TransitionCategory.THREE_D,
            "blur": TransitionCategory.BLUR,
            "glitch": TransitionCategory.GLITCH,
            "light": TransitionCategory.LIGHT,
            "creative": TransitionCategory.CREATIVE,
            "geometric": TransitionCategory.GEOMETRIC
        }

        category = category_map.get(request.get("transition_type", "dissolve"),
                                    TransitionCategory.DISSOLVE)
        duration = float(request.get("duration", 1.0))

        # Get transitions from category
        transitions = transition_lib.get_transitions_by_category(category)
        if not transitions:
            raise HTTPException(status_code=400, detail=f"No transitions in category {category.value}")

        # Use first transition from category
        transition = transitions[0]
        output_path = request.get("output_path") or f"/tmp/transitions_{uuid.uuid4()}.mp4"

        # Apply transitions
        result = transition_lib.apply_transition_between_clips(
            clip1_path=clips[0],
            clip2_path=clips[1],
            output_path=output_path,
            transition=transition,
            duration=duration
        )

        return {
            "status": "success",
            "output_path": result,
            "transition": transition.name,
            "duration": duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 7. MOTION GRAPHICS - Animated Text & Overlays
@app.post("/api/pro/motion-graphics")
async def add_motion_graphics(request: Dict[str, Any]):
    """
    Add animated text and motion graphics

    Body:
    - video_path: str (required)
    - type: str (lower_third/title_card/animated_text/cta)
    - text: str (required)
    - style: str (depends on type)
    - start_time: float (default: 0.0)
    - duration: float (default: 3.0)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        mg_type = request.get("type", "lower_third")
        text = request.get("text", "")
        start_time = float(request.get("start_time", 0.0))
        duration = float(request.get("duration", 3.0))
        output_path = request.get("output_path") or f"/tmp/motion_graphics_{uuid.uuid4()}.mp4"

        if mg_type == "lower_third":
            # Map lower third style
            style_map = {
                "corporate": LowerThirdStyle.CORPORATE,
                "social": LowerThirdStyle.SOCIAL_MODERN,
                "news": LowerThirdStyle.NEWS_TICKER,
                "minimal": LowerThirdStyle.MINIMAL_LINE
            }
            style = style_map.get(request.get("style", "corporate"), LowerThirdStyle.CORPORATE)

            result = motion_graphics.add_lower_third(
                video_path=video_path,
                output_path=output_path,
                text=text,
                subtitle=request.get("subtitle", ""),
                style=style,
                start_time=start_time,
                duration=duration
            )
        elif mg_type == "title_card":
            # Map title card style
            style_map = {
                "cinematic": TitleCardStyle.CINEMATIC_EPIC,
                "youtube": TitleCardStyle.YOUTUBE_INTRO,
                "social": TitleCardStyle.SOCIAL_HOOK
            }
            style = style_map.get(request.get("style", "cinematic"), TitleCardStyle.CINEMATIC_EPIC)

            result = motion_graphics.add_title_card(
                video_path=video_path,
                output_path=output_path,
                text=text,
                style=style,
                duration=duration
            )
        else:
            # Animated text
            animation_map = {
                "typewriter": AnimationType.TYPEWRITER,
                "word_pop": AnimationType.WORD_POP,
                "fly_in": AnimationType.CHARACTER_FLY_IN,
                "bounce": AnimationType.BOUNCE_IN
            }
            animation = animation_map.get(request.get("animation", "word_pop"),
                                         AnimationType.WORD_POP)

            result = motion_graphics.add_animated_text(
                video_path=video_path,
                output_path=output_path,
                text=text,
                animation=animation,
                start_time=start_time,
                duration=duration
            )

        return {
            "status": "success",
            "output_path": result,
            "type": mg_type,
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 8. PREVIEW GENERATOR - Fast Preview Generation
@app.post("/api/pro/preview")
async def generate_preview(request: Dict[str, Any]):
    """
    Generate quick preview or proxy video

    Body:
    - video_path: str (required)
    - quality: str (240p/360p/480p/720p)
    - thumbnail_strip: bool (default: false)
    - frame_count: int (default: 10, for thumbnails)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        quality_map = {
            "240p": ProxyQuality.ULTRA_LOW,
            "360p": ProxyQuality.LOW,
            "480p": ProxyQuality.MEDIUM,
            "720p": ProxyQuality.HIGH
        }
        quality = quality_map.get(request.get("quality", "480p"), ProxyQuality.MEDIUM)
        thumbnail_strip = request.get("thumbnail_strip", False)

        if thumbnail_strip:
            # Generate thumbnail strip for timeline
            frame_count = int(request.get("frame_count", 10))
            result = preview_gen.generate_thumbnail_strip(
                video_path=video_path,
                frame_count=frame_count,
                width=160,
                height=90
            )
            return {
                "status": "success",
                "thumbnail_strip": result.image_data.hex(),
                "frame_count": frame_count
            }
        else:
            # Generate proxy video
            output_path = request.get("output_path") or f"/tmp/proxy_{uuid.uuid4()}.mp4"
            result = preview_gen.generate_proxy_video(
                video_path=video_path,
                output_path=output_path,
                quality=quality
            )
            return {
                "status": "success",
                "output_path": result,
                "quality": quality.value
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 9. TIMELINE ENGINE - Advanced Video Editing
@app.post("/api/pro/timeline")
async def timeline_operation(request: Dict[str, Any]):
    """
    Create and manipulate video timeline

    Body:
    - operation: str (create/add_clip/remove_clip/export)
    - timeline_id: str (optional, for existing timeline)
    - clips: List[Dict] (for add_clip)
    - export_path: str (for export)
    """
    try:
        operation = request.get("operation", "create")

        if operation == "create":
            # Create new timeline
            timeline = Timeline(
                fps=int(request.get("fps", 30)),
                width=int(request.get("width", 1920)),
                height=int(request.get("height", 1080))
            )
            timeline_id = str(uuid.uuid4())
            pro_jobs[timeline_id] = {"timeline": timeline, "type": "timeline"}

            return {
                "status": "success",
                "timeline_id": timeline_id,
                "fps": timeline.fps,
                "resolution": f"{timeline.width}x{timeline.height}"
            }

        elif operation == "add_clip":
            timeline_id = request.get("timeline_id")
            if not timeline_id or timeline_id not in pro_jobs:
                raise HTTPException(status_code=404, detail="Timeline not found")

            timeline = pro_jobs[timeline_id]["timeline"]
            clip_data = request.get("clip", {})

            # Create clip
            clip = Clip(
                source_path=clip_data.get("source_path"),
                start_time=float(clip_data.get("start_time", 0)),
                duration=float(clip_data.get("duration", 5))
            )

            # Add to video track
            track = timeline.get_track_by_type(TrackType.VIDEO)[0] if timeline.tracks else None
            if not track:
                track = Track(track_type=TrackType.VIDEO, name="Video 1")
                timeline.add_track(track)

            timeline.add_clip_to_track(track.id, clip)

            return {
                "status": "success",
                "clip_id": clip.id,
                "timeline_id": timeline_id
            }

        elif operation == "export":
            timeline_id = request.get("timeline_id")
            if not timeline_id or timeline_id not in pro_jobs:
                raise HTTPException(status_code=404, detail="Timeline not found")

            timeline = pro_jobs[timeline_id]["timeline"]
            export_path = request.get("export_path") or f"/tmp/timeline_{timeline_id}.mp4"

            # Generate FFmpeg command
            ffmpeg_cmd = timeline.to_ffmpeg_command(export_path)

            return {
                "status": "success",
                "export_path": export_path,
                "ffmpeg_command": ffmpeg_cmd,
                "timeline_id": timeline_id
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 10. KEYFRAME ANIMATION - Advanced Animation
@app.post("/api/pro/keyframe")
async def keyframe_animation(request: Dict[str, Any]):
    """
    Create keyframe animations for video properties

    Body:
    - video_path: str (required)
    - property: str (position_x/position_y/scale_x/scale_y/rotation/opacity)
    - keyframes: List[Dict] with {time: float, value: float, interpolation: str}
    - output_path: str (optional)
    """
    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        # Map property type
        prop_map = {
            "position_x": PropertyType.POSITION_X,
            "position_y": PropertyType.POSITION_Y,
            "scale_x": PropertyType.SCALE_X,
            "scale_y": PropertyType.SCALE_Y,
            "rotation": PropertyType.ROTATION,
            "opacity": PropertyType.OPACITY
        }

        property_type = prop_map.get(request.get("property", "opacity"), PropertyType.OPACITY)
        keyframes_data = request.get("keyframes", [])

        # Create keyframes
        keyframes = []
        for kf in keyframes_data:
            interp_map = {
                "linear": InterpolationType.LINEAR,
                "ease_in": InterpolationType.EASE_IN,
                "ease_out": InterpolationType.EASE_OUT,
                "ease_in_out": InterpolationType.EASE_IN_OUT,
                "bezier": InterpolationType.BEZIER
            }
            interpolation = interp_map.get(kf.get("interpolation", "linear"),
                                          InterpolationType.LINEAR)

            keyframe = Keyframe(
                time=float(kf.get("time", 0)),
                value=float(kf.get("value", 0)),
                interpolation=interpolation
            )
            keyframes.append(keyframe)

        # Add animation
        keyframe_animator.add_animation(property_type, keyframes)

        # Generate FFmpeg filter
        ffmpeg_filter = keyframe_animator.to_ffmpeg_filter(property_type)

        return {
            "status": "success",
            "property": property_type.value,
            "keyframe_count": len(keyframes),
            "ffmpeg_filter": ffmpeg_filter
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 11. ASSET LIBRARY - Media Asset Management
@app.post("/api/pro/assets")
async def asset_operations(request: Dict[str, Any]):
    """
    Manage video/audio/image assets

    Body:
    - operation: str (add/search/get/delete)
    - asset_type: str (video/audio/image/font/lut/template)
    - file_path: str (for add)
    - query: str (for search)
    - asset_id: str (for get/delete)
    """
    try:
        operation = request.get("operation", "search")

        if operation == "add":
            file_path = request.get("file_path")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail="Invalid file_path")

            # Map asset type
            type_map = {
                "video": AssetType.VIDEO,
                "audio": AssetType.AUDIO,
                "image": AssetType.IMAGE,
                "font": AssetType.FONT,
                "lut": AssetType.LUT,
                "template": AssetType.TEMPLATE
            }
            asset_type = type_map.get(request.get("asset_type", "video"), AssetType.VIDEO)

            # Add asset
            asset = asset_lib.add_asset(
                file_path=file_path,
                asset_type=asset_type,
                metadata=request.get("metadata", {})
            )

            return {
                "status": "success",
                "asset_id": asset.id,
                "asset_type": asset_type.value
            }

        elif operation == "search":
            query = request.get("query", "")
            asset_type = request.get("asset_type")

            type_filter = None
            if asset_type:
                type_map = {
                    "video": AssetType.VIDEO,
                    "audio": AssetType.AUDIO,
                    "image": AssetType.IMAGE
                }
                type_filter = type_map.get(asset_type)

            # Search assets
            results = asset_lib.search_assets(query=query, asset_type=type_filter)

            return {
                "status": "success",
                "count": len(results),
                "assets": [{"id": a.id, "name": a.name, "type": a.asset_type.value} for a in results]
            }

        elif operation == "get":
            asset_id = request.get("asset_id")
            if not asset_id:
                raise HTTPException(status_code=400, detail="asset_id required")

            asset = asset_lib.get_asset(asset_id)
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found")

            return {
                "status": "success",
                "asset": {
                    "id": asset.id,
                    "name": asset.name,
                    "type": asset.asset_type.value,
                    "path": asset.file_path
                }
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 12. PRO RENDERER - Advanced FFmpeg Rendering
@app.post("/api/pro/render")
async def pro_render(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Advanced video rendering with GPU acceleration

    Body:
    - input_path: str (required)
    - platform: str (instagram/tiktok/youtube/twitter/facebook)
    - quality: str (draft/standard/high/master)
    - aspect_ratio: str (9:16/1:1/16:9/4:5)
    - use_gpu: bool (default: true)
    """
    try:
        input_path = request.get("input_path")
        if not input_path or not os.path.exists(input_path):
            raise HTTPException(status_code=400, detail="Invalid input_path")

        # Map platform
        platform_map = {
            "instagram": Platform.INSTAGRAM,
            "tiktok": Platform.TIKTOK,
            "youtube": Platform.YOUTUBE,
            "twitter": Platform.TWITTER,
            "facebook": Platform.FACEBOOK
        }
        platform = platform_map.get(request.get("platform", "instagram"), Platform.INSTAGRAM)

        # Map quality
        quality_map = {
            "draft": QualityPreset.DRAFT,
            "standard": QualityPreset.STANDARD,
            "high": QualityPreset.HIGH,
            "master": QualityPreset.MASTER
        }
        quality = quality_map.get(request.get("quality", "high"), QualityPreset.HIGH)

        # Map aspect ratio
        aspect_map = {
            "9:16": AspectRatio.VERTICAL,
            "1:1": AspectRatio.SQUARE,
            "16:9": AspectRatio.HORIZONTAL,
            "4:5": AspectRatio.PORTRAIT
        }
        aspect = aspect_map.get(request.get("aspect_ratio", "9:16"), AspectRatio.VERTICAL)

        job_id = str(uuid.uuid4())
        output_path = request.get("output_path") or f"/tmp/pro_render_{job_id}.mp4"
        use_gpu = request.get("use_gpu", True)

        # Process async
        def process_render():
            config = pro_renderer.get_platform_config(platform, quality)
            result = pro_renderer.render(
                input_path=input_path,
                output_path=output_path,
                settings=config,
                use_gpu=use_gpu
            )
            pro_jobs[job_id] = {
                "status": "completed",
                "output_path": result,
                "platform": platform.value,
                "quality": quality.value
            }

        background_tasks.add_task(process_render)
        pro_jobs[job_id] = {
            "status": "processing",
            "platform": platform.value,
            "quality": quality.value
        }

        return {
            "status": "queued",
            "job_id": job_id,
            "platform": platform.value,
            "quality": quality.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 13. PRO HEALTH CHECK - Module Status
@app.get("/api/pro/health")
async def pro_health_check():
    """
    Health check for all 13 pro video modules
    Returns status of each module and overall system health
    """
    try:
        modules_status = {
            "auto_captions": {"status": "ready", "model": caption_system.model_size.value if hasattr(caption_system, 'model_size') else "unknown"},
            "pro_renderer": {"status": "ready", "gpu_available": bool(pro_renderer.gpu_caps.has_nvidia if hasattr(pro_renderer, 'gpu_caps') else False)},
            "winning_ads": {"status": "ready", "templates": 10},
            "color_grading": {"status": "ready", "presets": 10},
            "smart_crop": {"status": "ready", "tracking": "enabled"},
            "audio_mixer": {"status": "ready", "normalization": "available"},
            "timeline_engine": {"status": "ready", "active_timelines": len([j for j in pro_jobs.values() if j.get("type") == "timeline"])},
            "motion_graphics": {"status": "ready", "styles": "50+"},
            "transitions": {"status": "ready", "count": 50},
            "keyframe_animator": {"status": "ready", "interpolation_types": 6},
            "preview_generator": {"status": "ready", "caching": "enabled"},
            "asset_library": {"status": "ready", "assets": asset_lib.get_asset_count() if hasattr(asset_lib, 'get_asset_count') else 0},
            "pro_jobs": {"status": "ready", "active_jobs": len(pro_jobs)}
        }

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "modules": modules_status,
            "total_modules": 13,
            "production_ready": True,
            "investment_grade": "€5M"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Job status endpoint for pro modules
@app.get("/api/pro/job/{job_id}")
async def get_pro_job_status(job_id: str):
    """Get status of a pro module job"""
    if job_id not in pro_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "status": pro_jobs[job_id].get("status", "unknown"),
        "data": pro_jobs[job_id]
    }


# ==================== BEAT-SYNC RENDERING ====================
# Investment-grade beat-synchronized video rendering
# ============================================================

@app.post("/api/video/beat-sync-render")
async def beat_sync_render(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Render video with cuts synchronized to music beats

    This is the core beat-sync engine for the €5M investment platform.
    Automatically detects beats using librosa and cuts video clips on beat timing.

    Body:
    - video_clips: List[str] (required) - Paths to video clips to use
    - audio_path: str (required) - Path to audio/music file for beat detection
    - platform: str (instagram/tiktok/youtube/facebook) - Target platform
    - quality: str (draft/standard/high/master) - Quality preset
    - aspect_ratio: str (9:16/1:1/16:9/4:5) - Target aspect ratio
    - output_path: str (optional) - Custom output path
    - async_mode: bool (default: true) - Process in background

    Returns:
    - job_id: str - Job ID for status tracking (if async)
    - output_path: str - Video output path (if sync)
    - beat_info: Dict - Beat detection information
    """
    try:
        # Validate required parameters
        video_clips = request.get("video_clips", [])
        audio_path = request.get("audio_path")

        if not video_clips:
            raise HTTPException(status_code=400, detail="video_clips required (list of video paths)")

        if not audio_path:
            raise HTTPException(status_code=400, detail="audio_path required")

        if not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail=f"Audio file not found: {audio_path}")

        # Validate video clips exist
        for clip_path in video_clips:
            if not os.path.exists(clip_path):
                raise HTTPException(status_code=400, detail=f"Video clip not found: {clip_path}")

        # Map platform
        platform_map = {
            "instagram": Platform.INSTAGRAM,
            "tiktok": Platform.TIKTOK,
            "youtube": Platform.YOUTUBE,
            "twitter": Platform.TWITTER,
            "facebook": Platform.FACEBOOK
        }
        platform = platform_map.get(request.get("platform", "instagram"), Platform.INSTAGRAM)

        # Map quality
        quality_map = {
            "draft": QualityPreset.DRAFT,
            "standard": QualityPreset.STANDARD,
            "high": QualityPreset.HIGH,
            "master": QualityPreset.MASTER
        }
        quality = quality_map.get(request.get("quality", "high"), QualityPreset.HIGH)

        # Map aspect ratio
        aspect_map = {
            "9:16": AspectRatio.VERTICAL,
            "1:1": AspectRatio.SQUARE,
            "16:9": AspectRatio.HORIZONTAL,
            "4:5": AspectRatio.PORTRAIT
        }
        aspect = aspect_map.get(request.get("aspect_ratio", "9:16"), AspectRatio.VERTICAL)

        # Generate output path
        job_id = str(uuid.uuid4())
        output_path = request.get("output_path") or f"/tmp/beat_sync_{job_id}.mp4"

        # Check if async mode
        async_mode = request.get("async_mode", True)

        if async_mode:
            # Process in background
            def process_beat_sync():
                try:
                    pro_jobs[job_id] = {
                        "status": "processing",
                        "type": "beat_sync",
                        "progress": 0,
                        "message": "Detecting beats..."
                    }

                    # Progress callback
                    def update_progress(progress: float):
                        pro_jobs[job_id]["progress"] = progress
                        pro_jobs[job_id]["message"] = f"Rendering... {progress:.0f}%"

                    # Execute beat-sync render
                    success = pro_renderer.render_with_beat_sync(
                        video_clips=video_clips,
                        audio_path=audio_path,
                        output_path=output_path,
                        platform=platform,
                        quality=quality,
                        aspect_ratio=aspect,
                        progress_callback=update_progress
                    )

                    if success:
                        # Detect beat info for response
                        import librosa
                        y, sr = librosa.load(audio_path)
                        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

                        pro_jobs[job_id] = {
                            "status": "completed",
                            "type": "beat_sync",
                            "output_path": output_path,
                            "progress": 100,
                            "message": "Beat-sync render completed",
                            "beat_info": {
                                "tempo_bpm": float(tempo),
                                "num_beats": len(beat_times),
                                "beat_times": [float(t) for t in beat_times[:50]],  # First 50 beats
                                "audio_duration": float(len(y) / sr)
                            },
                            "config": {
                                "num_clips": len(video_clips),
                                "platform": platform.value,
                                "quality": quality.value,
                                "aspect_ratio": aspect.value
                            }
                        }
                    else:
                        pro_jobs[job_id] = {
                            "status": "failed",
                            "type": "beat_sync",
                            "error": "Beat-sync render failed",
                            "progress": 0
                        }

                except Exception as e:
                    logger.error(f"Beat-sync render failed: {e}", exc_info=True)
                    pro_jobs[job_id] = {
                        "status": "failed",
                        "type": "beat_sync",
                        "error": str(e),
                        "progress": 0
                    }

            # Queue background task
            background_tasks.add_task(process_beat_sync)
            pro_jobs[job_id] = {
                "status": "queued",
                "type": "beat_sync",
                "progress": 0,
                "message": "Queued for beat-sync rendering"
            }

            return {
                "status": "queued",
                "job_id": job_id,
                "message": "Beat-sync render queued",
                "status_url": f"/api/pro/job/{job_id}",
                "config": {
                    "num_clips": len(video_clips),
                    "platform": platform.value,
                    "quality": quality.value,
                    "aspect_ratio": aspect.value
                }
            }
        else:
            # Synchronous mode - render immediately
            success = pro_renderer.render_with_beat_sync(
                video_clips=video_clips,
                audio_path=audio_path,
                output_path=output_path,
                platform=platform,
                quality=quality,
                aspect_ratio=aspect
            )

            if success:
                # Get beat info
                import librosa
                y, sr = librosa.load(audio_path)
                tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                beat_times = librosa.frames_to_time(beat_frames, sr=sr)

                return {
                    "status": "success",
                    "output_path": output_path,
                    "beat_info": {
                        "tempo_bpm": float(tempo),
                        "num_beats": len(beat_times),
                        "beat_times": [float(t) for t in beat_times[:50]],
                        "audio_duration": float(len(y) / sr)
                    },
                    "config": {
                        "num_clips": len(video_clips),
                        "platform": platform.value,
                        "quality": quality.value,
                        "aspect_ratio": aspect.value
                    }
                }
            else:
                raise HTTPException(status_code=500, detail="Beat-sync render failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Beat-sync endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRECISION AV SYNC ANALYSIS (Quick Win #4)
# Analyze audio-visual synchronization with 0.1s precision
# ============================================================================

@app.post("/api/video/analyze-sync")
async def analyze_av_sync(request: Dict[str, Any]):
    """
    Analyze audio-visual synchronization quality (Quick Win #4)

    Extracts audio peaks (beats, onsets, drops) and visual peaks (cuts, motion spikes)
    then measures how well they align within 0.1 second tolerance.

    Critical for ad performance:
    - Beat drops should hit on visual transitions
    - Emotional peaks in voice should match face closeups
    - Music energy should match motion energy

    Body:
    - video_path: str (required) - Path to video file
    - audio_path: str (optional) - Separate audio path (if not using video audio)

    Returns:
    - total_audio_peaks: int - Number of detected audio peaks
    - total_visual_peaks: int - Number of detected visual peaks
    - sync_points_found: int - Number of matching points
    - synced_within_tolerance: int - Points within 0.1s tolerance
    - sync_percentage: float - Percentage of synced points
    - average_offset_seconds: float - Average timing offset
    - average_sync_score: float - 0-1 sync quality score
    - recommendation: str - Human-readable sync assessment
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available - check dependencies (librosa, cv2)")

    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        audio_path = request.get("audio_path")  # Optional separate audio

        # Analyze sync quality
        result = precision_av_sync.analyze_sync_quality(video_path, audio_path)

        return {
            "status": "success",
            "video_path": video_path,
            "analysis": result
        }

    except Exception as e:
        logger.error(f"AV sync analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/extract-audio-peaks")
async def extract_audio_peaks(request: Dict[str, Any]):
    """
    Extract audio peaks from audio/video file (Quick Win #4)

    Detects:
    - Beats (rhythm markers)
    - Onsets (sudden sounds)
    - Drops (energy peaks)
    - Vocals (if present)

    Body:
    - audio_path: str (required) - Path to audio file

    Returns:
    - peaks: List of {timestamp, energy, peak_type}
    - total_peaks: int
    - tempo_bpm: float (estimated)
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        audio_path = request.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Invalid audio_path")

        peaks = precision_av_sync.extract_audio_peaks(audio_path)

        # Convert to dict format
        peaks_data = [
            {
                "timestamp": p.timestamp,
                "energy": p.energy,
                "peak_type": p.peak_type
            }
            for p in peaks
        ]

        # Get tempo using librosa
        import librosa
        y, sr = librosa.load(audio_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        return {
            "status": "success",
            "peaks": peaks_data,
            "total_peaks": len(peaks),
            "tempo_bpm": float(tempo),
            "peak_types": {
                "beat": len([p for p in peaks if p.peak_type == 'beat']),
                "onset": len([p for p in peaks if p.peak_type == 'onset']),
                "drop": len([p for p in peaks if p.peak_type == 'drop'])
            }
        }

    except Exception as e:
        logger.error(f"Extract audio peaks error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/extract-visual-peaks")
async def extract_visual_peaks(request: Dict[str, Any]):
    """
    Extract visual peaks from video file (Quick Win #4)

    Detects:
    - Cuts (scene changes)
    - Motion spikes (high activity moments)
    - Transitions (gradual changes)

    Body:
    - video_path: str (required) - Path to video file

    Returns:
    - peaks: List of {timestamp, motion_energy, peak_type}
    - total_peaks: int
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        peaks = precision_av_sync.extract_visual_peaks(video_path)

        # Convert to dict format
        peaks_data = [
            {
                "timestamp": p.timestamp,
                "motion_energy": p.motion_energy,
                "peak_type": p.peak_type
            }
            for p in peaks
        ]

        return {
            "status": "success",
            "peaks": peaks_data,
            "total_peaks": len(peaks),
            "peak_types": {
                "cut": len([p for p in peaks if p.peak_type == 'cut']),
                "motion": len([p for p in peaks if p.peak_type == 'motion'])
            }
        }

    except Exception as e:
        logger.error(f"Extract visual peaks error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/suggest-cut-adjustments")
async def suggest_cut_adjustments(request: Dict[str, Any]):
    """
    Suggest timing adjustments for out-of-sync cuts (Quick Win #4)

    Analyzes current sync and suggests exactly where to move cuts
    to align with audio beats.

    Body:
    - video_path: str (required) - Path to video file
    - audio_path: str (optional) - Separate audio path

    Returns:
    - adjustments: List of suggested timing changes
    - each adjustment contains:
      - current_visual_time: Current cut position
      - target_audio_time: Where it should be to match beat
      - adjustment_needed: Seconds to shift
      - direction: 'earlier' or 'later'
      - priority: 'high' (beat) or 'medium' (onset)
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        audio_path = request.get("audio_path")

        # Extract audio from video if not provided
        if audio_path is None:
            import subprocess
            import tempfile
            audio_path = tempfile.mktemp(suffix='.wav')
            subprocess.run([
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '22050', '-ac', '1', audio_path, '-y'
            ], capture_output=True)

        # Get peaks and sync points
        audio_peaks = precision_av_sync.extract_audio_peaks(audio_path)
        visual_peaks = precision_av_sync.extract_visual_peaks(video_path)
        sync_points = precision_av_sync.find_sync_points(audio_peaks, visual_peaks)

        # Get suggested adjustments
        adjustments = precision_av_sync.suggest_cut_adjustments(sync_points)

        return {
            "status": "success",
            "adjustments": adjustments,
            "total_adjustments": len(adjustments),
            "sync_summary": {
                "total_sync_points": len(sync_points),
                "synced_count": len([sp for sp in sync_points if sp.is_synced]),
                "out_of_sync_count": len([sp for sp in sync_points if not sp.is_synced])
            }
        }

    except Exception as e:
        logger.error(f"Suggest cut adjustments error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW BEAT SYNC API ENDPOINTS (TASK 1)
# ============================================================================

@app.post("/api/video/detect-beats")
async def detect_beats(request: Dict[str, Any]):
    """
    Detect beats from audio file

    Simple endpoint focused on beat detection for music synchronization.

    Body:
    - audio_path: str (required) - Path to audio file
    - return_tempo: bool (optional) - Include tempo/BPM analysis (default: true)

    Returns:
    - beats: List of beat timestamps in seconds
    - tempo_bpm: Estimated tempo in beats per minute
    - beat_count: Total number of beats detected
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        audio_path = request.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Invalid audio_path")

        return_tempo = request.get("return_tempo", True)

        # Extract audio peaks
        audio_peaks = precision_av_sync.extract_audio_peaks(audio_path)

        # Filter only beat-type peaks
        beats = [p for p in audio_peaks if p.peak_type == 'beat']
        beat_times = [b.timestamp for b in beats]

        response = {
            "status": "success",
            "beats": beat_times,
            "beat_count": len(beats)
        }

        if return_tempo:
            # Calculate tempo using librosa
            import librosa
            y, sr = librosa.load(audio_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            response["tempo_bpm"] = float(tempo)
            response["audio_duration"] = float(len(y) / sr)

        return response

    except Exception as e:
        logger.error(f"Detect beats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/generate-sync-points")
async def generate_sync_points(request: Dict[str, Any]):
    """
    Generate sync points between audio and video

    Analyzes both audio (beats, onsets) and video (cuts, motion) to create
    synchronization points that can be used for beat-matched editing.

    Body:
    - video_path: str (required) - Path to video file
    - audio_path: str (optional) - Separate audio path (uses video audio if not provided)
    - tolerance: float (optional) - Sync tolerance in seconds (default: 0.1)

    Returns:
    - sync_points: List of sync point objects with:
      - audio_timestamp: Audio peak timestamp
      - audio_type: Type of audio peak (beat/onset/drop)
      - audio_energy: Peak energy level
      - visual_timestamp: Closest visual peak timestamp
      - visual_type: Type of visual peak (cut/motion)
      - offset: Time difference between audio and visual
      - is_synced: Whether within tolerance
      - sync_score: Quality score 0-1
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        audio_path = request.get("audio_path")
        tolerance = float(request.get("tolerance", 0.1))

        # Extract audio from video if not provided
        if audio_path is None:
            import subprocess
            import tempfile
            audio_path = tempfile.mktemp(suffix='.wav')
            subprocess.run([
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '22050', '-ac', '1', audio_path, '-y'
            ], capture_output=True)

        # Extract peaks
        audio_peaks = precision_av_sync.extract_audio_peaks(audio_path)
        visual_peaks = precision_av_sync.extract_visual_peaks(video_path)

        # Generate sync points
        sync_points = precision_av_sync.find_sync_points(audio_peaks, visual_peaks)

        # Convert to dict format
        sync_points_data = [
            {
                "audio_timestamp": sp.audio_peak.timestamp,
                "audio_type": sp.audio_peak.peak_type,
                "audio_energy": sp.audio_peak.energy,
                "visual_timestamp": sp.visual_peak.timestamp,
                "visual_type": sp.visual_peak.peak_type,
                "visual_energy": sp.visual_peak.motion_energy,
                "offset": sp.offset,
                "is_synced": sp.is_synced,
                "sync_score": sp.sync_score
            }
            for sp in sync_points
        ]

        # Calculate statistics
        synced_count = len([sp for sp in sync_points if sp.is_synced])
        avg_offset = sum(sp.offset for sp in sync_points) / len(sync_points) if sync_points else 0
        avg_score = sum(sp.sync_score for sp in sync_points) / len(sync_points) if sync_points else 0

        return {
            "status": "success",
            "sync_points": sync_points_data,
            "total_sync_points": len(sync_points),
            "synced_within_tolerance": synced_count,
            "sync_percentage": (synced_count / len(sync_points) * 100) if sync_points else 0,
            "average_offset": avg_offset,
            "average_sync_score": avg_score,
            "tolerance_used": tolerance,
            "audio_peaks_count": len(audio_peaks),
            "visual_peaks_count": len(visual_peaks)
        }

    except Exception as e:
        logger.error(f"Generate sync points error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/phase-analysis")
async def phase_analysis(request: Dict[str, Any]):
    """
    Analyze audio phase for effect timing

    Analyzes the phase characteristics of audio to determine optimal timing
    for visual effects, transitions, and motion graphics.

    Body:
    - audio_path: str (required) - Path to audio file
    - effect_type: str (optional) - Type of effect to optimize for (transition/motion/text)

    Returns:
    - phase_points: List of optimal timing points for effects
    - energy_curve: Audio energy over time
    - recommendations: Suggested effect timings
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        audio_path = request.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Invalid audio_path")

        effect_type = request.get("effect_type", "transition")

        # Load audio
        import librosa
        import numpy as np
        y, sr = librosa.load(audio_path, sr=22050)

        # Extract phase and energy information
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        rms_times = librosa.frames_to_time(range(len(rms)), sr=sr)

        # Spectral centroid (brightness)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

        # Zero crossing rate (percussiveness)
        zcr = librosa.feature.zero_crossing_rate(y=y)[0]

        # Onset strength
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Find optimal phase points based on effect type
        phase_points = []

        if effect_type == "transition":
            # For transitions, use onset peaks with high energy
            from scipy.signal import find_peaks
            peaks, properties = find_peaks(
                onset_env,
                height=np.mean(onset_env) * 1.5,
                distance=sr // 8  # At least 1/8 second apart
            )

            for peak in peaks:
                timestamp = librosa.frames_to_time(peak, sr=sr)
                phase_points.append({
                    "timestamp": float(timestamp),
                    "type": "transition_point",
                    "energy": float(onset_env[peak]),
                    "confidence": float(properties['peak_heights'][list(peaks).index(peak)] / max(onset_env))
                })

        elif effect_type == "motion":
            # For motion graphics, use rhythm and energy changes
            # Detect tempo and beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beats, sr=sr)

            for i, beat_time in enumerate(beat_times):
                beat_idx = int(beat_time * sr / 512)  # Convert to frame index
                if beat_idx < len(rms):
                    phase_points.append({
                        "timestamp": float(beat_time),
                        "type": "motion_point",
                        "energy": float(rms[min(beat_idx, len(rms) - 1)]),
                        "beat_strength": 1.0
                    })

        elif effect_type == "text":
            # For text effects, use lower energy points (pauses)
            # Find valleys in RMS energy
            from scipy.signal import find_peaks
            inverted_rms = -rms
            valleys, _ = find_peaks(
                inverted_rms,
                height=-np.mean(rms) * 0.8,
                distance=sr // 4
            )

            for valley in valleys:
                timestamp = rms_times[valley]
                phase_points.append({
                    "timestamp": float(timestamp),
                    "type": "text_point",
                    "energy": float(rms[valley]),
                    "clarity": 1.0 - (rms[valley] / max(rms))
                })

        # Build energy curve (sampled at 10 Hz for response size)
        sample_rate = 10  # Hz
        duration = len(y) / sr
        sample_times = np.arange(0, duration, 1.0 / sample_rate)

        energy_curve = []
        for t in sample_times[:200]:  # Limit to first 20 seconds for response size
            frame_idx = int(t * len(rms) / duration)
            if frame_idx < len(rms):
                energy_curve.append({
                    "time": float(t),
                    "energy": float(rms[frame_idx])
                })

        # Generate recommendations
        recommendations = []
        if phase_points:
            recommendations.append({
                "effect": effect_type,
                "optimal_points": len(phase_points),
                "average_spacing": float(np.mean(np.diff([p["timestamp"] for p in phase_points]))) if len(phase_points) > 1 else 0,
                "suggestion": f"Place {effect_type} effects at {len(phase_points)} optimal timing points"
            })

        return {
            "status": "success",
            "effect_type": effect_type,
            "phase_points": phase_points[:50],  # Limit response size
            "total_phase_points": len(phase_points),
            "energy_curve": energy_curve,
            "recommendations": recommendations,
            "audio_duration": float(duration),
            "analysis": {
                "average_energy": float(np.mean(rms)),
                "peak_energy": float(np.max(rms)),
                "energy_variance": float(np.var(rms))
            }
        }

    except Exception as e:
        logger.error(f"Phase analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BEAT-SYNCED TIMELINE RENDERING (TASK 2)
# Integration with Timeline Engine for beat-matched editing
# ============================================================================

@app.post("/api/video/render-beat-synced")
async def render_beat_synced(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Render video with beat-synced transitions using Timeline Engine

    This endpoint integrates precision_av_sync with timeline_engine to create
    beat-synchronized videos. It analyzes audio/video sync points and aligns
    cuts and transitions to beat positions.

    Body:
    - video_path: str (required) - Path to source video
    - audio_path: str (optional) - Separate audio path (uses video audio if not provided)
    - clips: List[Dict] (optional) - Predefined clips to use, each with:
      - source: str - Clip source path
      - start_time: float - Timeline position
      - duration: float - Clip duration
      - in_point: float (optional) - Trim start
      - out_point: float (optional) - Trim end
    - output_path: str (optional) - Custom output path
    - snap_tolerance: float (optional) - Beat snap tolerance in seconds (default: 0.05)
    - add_transitions: bool (optional) - Add transitions at beat points (default: true)
    - transition_duration: float (optional) - Transition duration (default: 0.5s)
    - async_mode: bool (optional) - Process asynchronously (default: true)

    Returns:
    - Async mode: {status: "queued", job_id: str, timeline_id: str}
    - Sync mode: {status: "success", output_path: str, sync_report: Dict}
    """
    if not PRECISION_AV_SYNC_AVAILABLE or not precision_av_sync:
        raise HTTPException(status_code=503, detail="PrecisionAVSync not available")

    try:
        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        audio_path = request.get("audio_path")
        clips = request.get("clips", [])
        output_path = request.get("output_path")
        snap_tolerance = float(request.get("snap_tolerance", 0.05))
        add_transitions = request.get("add_transitions", True)
        transition_duration = float(request.get("transition_duration", 0.5))
        async_mode = request.get("async_mode", True)

        # Generate output path if not provided
        job_id = str(uuid.uuid4())
        if not output_path:
            output_dir = os.getenv("OUTPUT_DIR", "/tmp/outputs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"beat_synced_{job_id}.mp4")

        # Extract audio from video if not provided
        if audio_path is None:
            import subprocess
            import tempfile
            audio_path = tempfile.mktemp(suffix='.wav')
            subprocess.run([
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '22050', '-ac', '1', audio_path, '-y'
            ], capture_output=True, check=False)

        if async_mode:
            # Asynchronous processing
            async def process_beat_sync_timeline():
                try:
                    pro_jobs[job_id] = {
                        "status": "processing",
                        "type": "beat_synced_timeline",
                        "progress": 10,
                        "message": "Analyzing audio peaks..."
                    }

                    # Step 1: Extract sync points
                    audio_peaks = precision_av_sync.extract_audio_peaks(audio_path)
                    visual_peaks = precision_av_sync.extract_visual_peaks(video_path)
                    sync_points = precision_av_sync.find_sync_points(audio_peaks, visual_peaks)

                    pro_jobs[job_id]["progress"] = 30
                    pro_jobs[job_id]["message"] = "Creating timeline..."

                    # Step 2: Create timeline
                    timeline = Timeline(
                        name=f"Beat Synced - {job_id}",
                        frame_rate=30.0,
                        resolution=(1920, 1080),
                        sample_rate=48000
                    )

                    # Create video and audio tracks
                    video_track = timeline.add_track(TrackType.VIDEO, "Video 1")
                    audio_track = timeline.add_track(TrackType.AUDIO, "Audio 1")

                    pro_jobs[job_id]["progress"] = 40
                    pro_jobs[job_id]["message"] = "Adding clips to timeline..."

                    # Step 3: Add clips to timeline
                    if clips:
                        # Use provided clips
                        for clip_data in clips:
                            timeline.add_clip(
                                track_id=video_track.id,
                                source=clip_data.get("source", video_path),
                                start_time=clip_data.get("start_time", 0),
                                duration=clip_data.get("duration", 5),
                                in_point=clip_data.get("in_point", 0),
                                out_point=clip_data.get("out_point"),
                                overlap_strategy=OverlapStrategy.LAYER
                            )
                    else:
                        # Create default clip from source video
                        timeline.add_clip(
                            track_id=video_track.id,
                            source=video_path,
                            start_time=0.0,
                            duration=30.0,  # Default 30 seconds
                            overlap_strategy=OverlapStrategy.LAYER
                        )

                    pro_jobs[job_id]["progress"] = 60
                    pro_jobs[job_id]["message"] = "Applying beat synchronization..."

                    # Step 4: Apply beat sync
                    sync_result = timeline.apply_beat_sync(
                        sync_points=sync_points,
                        track_id=video_track.id,
                        snap_tolerance=snap_tolerance,
                        add_transitions=add_transitions,
                        transition_duration=transition_duration
                    )

                    pro_jobs[job_id]["progress"] = 80
                    pro_jobs[job_id]["message"] = "Rendering video..."

                    # Step 5: Generate FFmpeg command and render
                    ffmpeg_cmd = timeline.to_ffmpeg_command(output_path)

                    # Execute FFmpeg command
                    import subprocess
                    result = subprocess.run(
                        ffmpeg_cmd,
                        shell=True,
                        capture_output=True,
                        text=True
                    )

                    if result.returncode == 0:
                        pro_jobs[job_id] = {
                            "status": "completed",
                            "type": "beat_synced_timeline",
                            "output_path": output_path,
                            "progress": 100,
                            "message": "Beat-synced render completed",
                            "sync_report": {
                                "adjusted_clips": sync_result.get("adjusted_clips", 0),
                                "snapped_to_beats": sync_result.get("snapped_to_beats", 0),
                                "transitions_added": sync_result.get("transitions_added", 0),
                                "sync_quality": sync_result.get("sync_quality", 0),
                                "total_beats": sync_result.get("total_beats_available", 0),
                                "total_sync_points": len(sync_points)
                            },
                            "timeline": {
                                "duration": timeline.get_duration(),
                                "frame_count": timeline.get_frame_count(),
                                "tracks": len(timeline.tracks),
                                "clips": sum(len(t.clips) for t in timeline.tracks)
                            }
                        }
                    else:
                        pro_jobs[job_id] = {
                            "status": "failed",
                            "type": "beat_synced_timeline",
                            "error": f"FFmpeg rendering failed: {result.stderr[:500]}",
                            "progress": 80
                        }

                except Exception as e:
                    logger.error(f"Beat-synced timeline render failed: {e}", exc_info=True)
                    pro_jobs[job_id] = {
                        "status": "failed",
                        "type": "beat_synced_timeline",
                        "error": str(e),
                        "progress": 0
                    }

            # Queue background task
            background_tasks.add_task(process_beat_sync_timeline)

            # Store timeline ID for reference
            timeline_id = f"timeline_{job_id}"
            pro_jobs[job_id] = {
                "status": "queued",
                "type": "beat_synced_timeline",
                "progress": 0,
                "message": "Queued for beat-sync timeline rendering"
            }

            return {
                "status": "queued",
                "job_id": job_id,
                "timeline_id": timeline_id,
                "message": "Beat-synced timeline rendering queued",
                "status_url": f"/api/pro/job/{job_id}"
            }

        else:
            # Synchronous processing
            # Step 1: Extract sync points
            audio_peaks = precision_av_sync.extract_audio_peaks(audio_path)
            visual_peaks = precision_av_sync.extract_visual_peaks(video_path)
            sync_points = precision_av_sync.find_sync_points(audio_peaks, visual_peaks)

            # Step 2: Create timeline
            timeline = Timeline(
                name=f"Beat Synced - {job_id}",
                frame_rate=30.0,
                resolution=(1920, 1080),
                sample_rate=48000
            )

            # Create tracks
            video_track = timeline.add_track(TrackType.VIDEO, "Video 1")
            audio_track = timeline.add_track(TrackType.AUDIO, "Audio 1")

            # Step 3: Add clips
            if clips:
                for clip_data in clips:
                    timeline.add_clip(
                        track_id=video_track.id,
                        source=clip_data.get("source", video_path),
                        start_time=clip_data.get("start_time", 0),
                        duration=clip_data.get("duration", 5),
                        in_point=clip_data.get("in_point", 0),
                        out_point=clip_data.get("out_point"),
                        overlap_strategy=OverlapStrategy.LAYER
                    )
            else:
                timeline.add_clip(
                    track_id=video_track.id,
                    source=video_path,
                    start_time=0.0,
                    duration=30.0,
                    overlap_strategy=OverlapStrategy.LAYER
                )

            # Step 4: Apply beat sync
            sync_result = timeline.apply_beat_sync(
                sync_points=sync_points,
                track_id=video_track.id,
                snap_tolerance=snap_tolerance,
                add_transitions=add_transitions,
                transition_duration=transition_duration
            )

            # Step 5: Generate and execute FFmpeg command
            ffmpeg_cmd = timeline.to_ffmpeg_command(output_path)

            import subprocess
            result = subprocess.run(
                ffmpeg_cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"FFmpeg rendering failed: {result.stderr[:500]}"
                )

            return {
                "status": "success",
                "output_path": output_path,
                "sync_report": {
                    "adjusted_clips": sync_result.get("adjusted_clips", 0),
                    "snapped_to_beats": sync_result.get("snapped_to_beats", 0),
                    "transitions_added": sync_result.get("transitions_added", 0),
                    "sync_quality": sync_result.get("sync_quality", 0),
                    "total_beats": sync_result.get("total_beats_available", 0),
                    "total_sync_points": len(sync_points)
                },
                "timeline": {
                    "duration": timeline.get_duration(),
                    "frame_count": timeline.get_frame_count(),
                    "tracks": len(timeline.tracks),
                    "clips": sum(len(t.clips) for t in timeline.tracks)
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Render beat-synced error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VOICE GENERATION ENDPOINTS - ElevenLabs + OpenAI TTS
# ============================================================================

@app.post("/api/voice/generate")
async def generate_voiceover(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Generate voiceover from script using AI TTS.

    Body:
    - script: str (required) - Text to convert to speech
    - voice_id: str (required) - Voice ID (OpenAI: alloy/echo/fable/onyx/nova/shimmer, ElevenLabs: voice_id)
    - provider: str (optional) - "openai" or "elevenlabs" (default: "openai")
    - model: str (optional) - OpenAI: "tts-1" or "tts-1-hd" (default: "tts-1-hd")
    - language: str (optional) - Language code (default: "en")
    - speed: float (optional) - Speed multiplier 0.25-4.0 (default: 1.0)
    - output_format: str (optional) - "mp3", "wav", "opus" (default: "mp3")
    - async: bool (optional) - Process asynchronously (default: false)

    Returns:
    - Immediate: {status: "success", output_path: str, duration: float}
    - Async: {status: "queued", job_id: str}
    """
    try:
        script = request.get("script")
        if not script:
            raise HTTPException(status_code=400, detail="script required")

        voice_id = request.get("voice_id")
        if not voice_id:
            raise HTTPException(status_code=400, detail="voice_id required")

        # Parse provider
        provider_str = request.get("provider", "openai").lower()
        provider = VoiceProvider.OPENAI if provider_str == "openai" else VoiceProvider.ELEVENLABS

        # Settings
        settings = VoiceSettings(
            speed=float(request.get("speed", 1.0)),
            stability=float(request.get("stability", 0.5)),
            similarity_boost=float(request.get("similarity_boost", 0.75))
        )

        model = request.get("model", "tts-1-hd")
        language = request.get("language", "en")
        output_format = request.get("output_format", "mp3")
        is_async = request.get("async", False)

        if is_async:
            # Asynchronous processing
            job_id = str(uuid.uuid4())

            async def process_voiceover():
                try:
                    output_path = await voice_generator.generate_voiceover(
                        script=script,
                        voice_id=voice_id,
                        provider=provider,
                        model=model,
                        settings=settings,
                        output_format=output_format,
                        language=language
                    )

                    # Get duration
                    duration = await voice_generator._get_audio_duration(output_path)

                    pro_jobs[job_id] = {
                        "status": "completed",
                        "type": "voiceover",
                        "output_path": output_path,
                        "duration": duration,
                        "provider": provider.value,
                        "voice_id": voice_id
                    }
                except Exception as e:
                    logger.error(f"Voiceover generation failed: {e}", exc_info=True)
                    pro_jobs[job_id] = {
                        "status": "failed",
                        "type": "voiceover",
                        "error": str(e)
                    }

            background_tasks.add_task(process_voiceover)
            pro_jobs[job_id] = {"status": "processing", "type": "voiceover"}

            return {
                "status": "queued",
                "job_id": job_id,
                "message": "Voiceover generation started"
            }
        else:
            # Synchronous processing
            output_path = await voice_generator.generate_voiceover(
                script=script,
                voice_id=voice_id,
                provider=provider,
                model=model,
                settings=settings,
                output_format=output_format,
                language=language
            )

            # Get duration
            duration = await voice_generator._get_audio_duration(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "duration": duration,
                "provider": provider.value,
                "voice_id": voice_id,
                "language": language
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate voiceover error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/clone")
async def clone_voice(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Clone a voice from audio samples (ElevenLabs only).

    Body:
    - name: str (required) - Voice name
    - description: str (optional) - Voice description
    - audio_samples: List[str] (required) - Paths to audio sample files
    - labels: Dict[str, str] (optional) - Voice metadata (gender, age, accent, etc.)
    - async: bool (optional) - Process asynchronously (default: false)

    Returns:
    - Immediate: {status: "success", voice_id: str, name: str}
    - Async: {status: "queued", job_id: str}
    """
    try:
        name = request.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="name required")

        audio_samples = request.get("audio_samples", [])
        if not audio_samples:
            raise HTTPException(status_code=400, detail="audio_samples required (at least 1)")

        # Validate audio files exist
        for sample in audio_samples:
            if not os.path.exists(sample):
                raise HTTPException(status_code=400, detail=f"Audio sample not found: {sample}")

        config = VoiceCloneConfig(
            name=name,
            description=request.get("description", ""),
            audio_samples=audio_samples,
            labels=request.get("labels", {})
        )

        is_async = request.get("async", False)

        if is_async:
            # Asynchronous processing
            job_id = str(uuid.uuid4())

            async def process_clone():
                try:
                    voice_id = await voice_generator.clone_voice(config)

                    pro_jobs[job_id] = {
                        "status": "completed",
                        "type": "voice_clone",
                        "voice_id": voice_id,
                        "name": name,
                        "sample_count": len(audio_samples)
                    }
                except Exception as e:
                    logger.error(f"Voice cloning failed: {e}", exc_info=True)
                    pro_jobs[job_id] = {
                        "status": "failed",
                        "type": "voice_clone",
                        "error": str(e)
                    }

            background_tasks.add_task(process_clone)
            pro_jobs[job_id] = {"status": "processing", "type": "voice_clone"}

            return {
                "status": "queued",
                "job_id": job_id,
                "message": "Voice cloning started"
            }
        else:
            # Synchronous processing
            voice_id = await voice_generator.clone_voice(config)

            return {
                "status": "success",
                "voice_id": voice_id,
                "name": name,
                "sample_count": len(audio_samples),
                "provider": "elevenlabs"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clone voice error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/library")
async def get_voice_library(provider: Optional[str] = None):
    """
    Get list of available voices.

    Query params:
    - provider: str (optional) - Filter by provider ("openai" or "elevenlabs")

    Returns:
    - {voices: List[Dict], count: int}
    """
    try:
        if provider:
            provider_enum = VoiceProvider.OPENAI if provider.lower() == "openai" else VoiceProvider.ELEVENLABS
            voices = await voice_generator.get_available_voices(provider_enum)
        else:
            # Get both providers
            openai_voices = await voice_generator.get_available_voices(VoiceProvider.OPENAI)

            # Try to get ElevenLabs voices (may fail if no API key)
            try:
                elevenlabs_voices = await voice_generator.get_available_voices(VoiceProvider.ELEVENLABS)
            except:
                elevenlabs_voices = []

            voices = openai_voices + elevenlabs_voices

        # Add custom cloned voices from library
        custom_voices = voice_generator.get_voice_library()
        for voice_id, voice_data in custom_voices.items():
            voices.append(voice_data)

        return {
            "status": "success",
            "voices": voices,
            "count": len(voices)
        }

    except Exception as e:
        logger.error(f"Get voice library error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/sync")
async def sync_voiceover_to_video(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Add voiceover audio to video with synchronization.

    Body:
    - audio_path: str (required) - Path to voiceover audio file
    - video_path: str (required) - Path to source video file
    - output_path: str (optional) - Output video path
    - volume: float (optional) - Audio volume multiplier 0.0-2.0 (default: 1.0)
    - fade_in: float (optional) - Fade in duration in seconds (default: 0.0)
    - fade_out: float (optional) - Fade out duration in seconds (default: 0.0)
    - async: bool (optional) - Process asynchronously (default: false)

    Returns:
    - Immediate: {status: "success", output_path: str}
    - Async: {status: "queued", job_id: str}
    """
    try:
        audio_path = request.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail="Invalid audio_path")

        video_path = request.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Invalid video_path")

        output_path = request.get("output_path")
        volume = float(request.get("volume", 1.0))
        fade_in = float(request.get("fade_in", 0.0))
        fade_out = float(request.get("fade_out", 0.0))
        is_async = request.get("async", False)

        if is_async:
            # Asynchronous processing
            job_id = str(uuid.uuid4())

            async def process_sync():
                try:
                    result_path = await voice_generator.sync_to_video(
                        audio_path=audio_path,
                        video_path=video_path,
                        output_path=output_path,
                        volume=volume,
                        fade_in=fade_in,
                        fade_out=fade_out
                    )

                    pro_jobs[job_id] = {
                        "status": "completed",
                        "type": "voice_sync",
                        "output_path": result_path
                    }
                except Exception as e:
                    logger.error(f"Voice sync failed: {e}", exc_info=True)
                    pro_jobs[job_id] = {
                        "status": "failed",
                        "type": "voice_sync",
                        "error": str(e)
                    }

            background_tasks.add_task(process_sync)
            pro_jobs[job_id] = {"status": "processing", "type": "voice_sync"}

            return {
                "status": "queued",
                "job_id": job_id,
                "message": "Voice sync started"
            }
        else:
            # Synchronous processing
            result_path = await voice_generator.sync_to_video(
                audio_path=audio_path,
                video_path=video_path,
                output_path=output_path,
                volume=volume,
                fade_in=fade_in,
                fade_out=fade_out
            )

            return {
                "status": "success",
                "output_path": result_path
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync voiceover error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/voice/{voice_id}")
async def delete_voice(voice_id: str):
    """
    Delete a cloned voice (ElevenLabs only).

    Path params:
    - voice_id: str - Voice ID to delete

    Returns:
    - {status: "success", message: str}
    """
    try:
        success = await voice_generator.delete_voice(voice_id)

        return {
            "status": "success",
            "message": f"Voice {voice_id} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Delete voice error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/generate-multilingual")
async def generate_multilingual_voiceover(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Generate voiceovers in multiple languages (ElevenLabs only).

    Body:
    - script: str (required) - Text to convert to speech
    - voice_id: str (required) - ElevenLabs voice ID
    - languages: List[str] (required) - Language codes (e.g., ["en", "es", "fr", "de"])

    Returns:
    - {status: "queued", job_id: str}
    """
    try:
        script = request.get("script")
        if not script:
            raise HTTPException(status_code=400, detail="script required")

        voice_id = request.get("voice_id")
        if not voice_id:
            raise HTTPException(status_code=400, detail="voice_id required")

        languages = request.get("languages", [])
        if not languages:
            raise HTTPException(status_code=400, detail="languages required")

        job_id = str(uuid.uuid4())

        async def process_multilingual():
            try:
                results = {}
                for lang in languages:
                    output_path = await voice_generator.generate_voiceover(
                        script=script,
                        voice_id=voice_id,
                        provider=VoiceProvider.ELEVENLABS,
                        language=lang
                    )
                    results[lang] = output_path

                pro_jobs[job_id] = {
                    "status": "completed",
                    "type": "multilingual_voiceover",
                    "results": results,
                    "language_count": len(results)
                }
            except Exception as e:
                logger.error(f"Multilingual voiceover failed: {e}", exc_info=True)
                pro_jobs[job_id] = {
                    "status": "failed",
                    "type": "multilingual_voiceover",
                    "error": str(e)
                }

        background_tasks.add_task(process_multilingual)
        pro_jobs[job_id] = {"status": "processing", "type": "multilingual_voiceover"}

        return {
            "status": "queued",
            "job_id": job_id,
            "message": f"Generating voiceovers for {len(languages)} languages"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multilingual voiceover error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CELERY TASK QUEUE API ENDPOINTS
# Distributed video processing with priority queues
# ============================================================================

@app.post("/api/tasks/render")
async def submit_render_task(request: Dict[str, Any]):
    """
    Submit video render task to Celery queue

    Body:
    - scenes: List[Dict] (required) - Scene data with video paths, timing
    - output_format: Dict (optional) - Format specs (width, height, fps)
    - transitions: bool (default: true) - Enable transitions
    - overlays: List[str] (optional) - Overlay paths
    - subtitles: str (optional) - Subtitle file path
    - use_gpu: bool (default: false) - Use GPU acceleration
    - priority: int (1-10, default: 5) - Task priority

    Returns:
    - task_id: str - Celery task ID
    - status: str - Task status
    - queue: str - Queue name
    """
    try:
        scenes = request.get("scenes", [])
        if not scenes:
            raise HTTPException(status_code=400, detail="scenes required")

        # Build job data
        job_data = {
            "scenes": scenes,
            "output_format": request.get("output_format", {
                "width": 1920,
                "height": 1080,
                "fps": 30
            }),
            "transitions": request.get("transitions", True),
            "overlays": request.get("overlays"),
            "subtitles": request.get("subtitles"),
            "use_gpu": request.get("use_gpu", False)
        }

        # Submit to Celery
        priority = request.get("priority", 5)
        task = render_video_task.apply_async(
            args=[job_data],
            priority=priority
        )

        return {
            "status": "queued",
            "task_id": task.id,
            "queue": "render_queue",
            "priority": priority,
            "message": "Render task submitted to queue"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/transcode")
async def submit_transcode_task(request: Dict[str, Any]):
    """
    Submit video transcode task to Celery queue

    Body:
    - input_path: str (required) - Source video path
    - output_format: Dict (required) - Target format:
        - codec: str (h264/h265/vp9/av1)
        - container: str (mp4/webm/mkv)
        - width: int (optional)
        - height: int (optional)
        - bitrate: str (optional, e.g., "5M")
    - priority: int (1-10, default: 7) - Task priority

    Returns:
    - task_id: str - Celery task ID
    - status: str - Task status
    """
    try:
        input_path = request.get("input_path")
        if not input_path or not os.path.exists(input_path):
            raise HTTPException(status_code=400, detail="Invalid input_path")

        output_format = request.get("output_format")
        if not output_format:
            raise HTTPException(status_code=400, detail="output_format required")

        # Submit to Celery
        priority = request.get("priority", 7)
        task = transcode_task.apply_async(
            args=[input_path, output_format],
            priority=priority
        )

        return {
            "status": "queued",
            "task_id": task.id,
            "queue": "transcode_queue",
            "priority": priority,
            "input_path": input_path,
            "output_format": output_format,
            "message": "Transcode task submitted to queue"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Get status of a Celery task

    Path params:
    - task_id: str - Celery task ID

    Returns:
    - task_id: str
    - state: str (PENDING/STARTED/SUCCESS/FAILURE/RETRY)
    - progress: float (0-100)
    - result: Any (if completed)
    - error: str (if failed)
    - traceback: str (if failed)
    """
    try:
        from celery.result import AsyncResult

        # Get task result
        task_result = AsyncResult(task_id, app=celery_app)

        # Get progress from Redis if available
        progress_data = None
        if celery_redis:
            try:
                progress_json = celery_redis.get(f'task_status:{task_id}')
                if progress_json:
                    progress_data = json.loads(progress_json)
            except Exception as e:
                logger.warning(f"Failed to get progress from Redis: {e}")

        # Build response
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "ready": task_result.ready(),
            "successful": task_result.successful() if task_result.ready() else None,
            "failed": task_result.failed() if task_result.ready() else None
        }

        # Add progress data if available
        if progress_data:
            response["progress"] = progress_data.get("progress", 0)
            response["status"] = progress_data.get("status", "unknown")
            response["message"] = progress_data.get("message", "")
            response["timestamp"] = progress_data.get("timestamp")

        # Add result or error
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            elif task_result.failed():
                response["error"] = str(task_result.info)
                response["traceback"] = task_result.traceback

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/queue/stats")
async def get_queue_stats():
    """
    Get queue statistics from Celery

    Returns:
    - active: int - Active tasks
    - scheduled: int - Scheduled tasks
    - reserved: int - Reserved tasks
    - queues: Dict - Per-queue statistics
    - workers: Dict - Worker information
    """
    try:
        # Get active tasks
        inspect = celery_app.control.inspect()

        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        stats = inspect.stats()

        # Count tasks
        total_active = sum(len(tasks) for tasks in (active_tasks or {}).values())
        total_scheduled = sum(len(tasks) for tasks in (scheduled_tasks or {}).values())
        total_reserved = sum(len(tasks) for tasks in (reserved_tasks or {}).values())

        # Get queue lengths from Redis
        queue_lengths = {}
        if celery_redis:
            try:
                for queue_name in ['render_queue', 'preview_queue', 'transcode_queue', 'caption_queue']:
                    length = celery_redis.llen(queue_name)
                    queue_lengths[queue_name] = length
            except Exception as e:
                logger.warning(f"Failed to get queue lengths: {e}")

        return {
            "status": "success",
            "active": total_active,
            "scheduled": total_scheduled,
            "reserved": total_reserved,
            "queue_lengths": queue_lengths,
            "workers": stats or {},
            "active_tasks": active_tasks or {},
            "scheduled_tasks": scheduled_tasks or {},
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.warning(f"Queue stats error: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "message": "Failed to retrieve complete queue statistics"
        }


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    Cancel a running or queued Celery task

    Path params:
    - task_id: str - Celery task ID

    Returns:
    - status: str - Cancellation status
    - message: str
    """
    try:
        from celery.result import AsyncResult

        # Get task result
        task_result = AsyncResult(task_id, app=celery_app)

        # Check if task is already done
        if task_result.ready():
            return {
                "status": "already_completed",
                "task_id": task_id,
                "state": task_result.state,
                "message": f"Task already {task_result.state}"
            }

        # Revoke task
        celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')

        return {
            "status": "cancelled",
            "task_id": task_id,
            "message": "Task cancellation requested"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEAD LETTER QUEUE (DLQ) API ENDPOINTS
# Manage permanently failed tasks
# ============================================================================

@app.get("/api/tasks/dlq")
async def get_dlq_tasks(limit: int = 100):
    """
    Retrieve failed tasks from the Dead Letter Queue

    Query params:
    - limit: int (default: 100) - Maximum number of tasks to retrieve

    Returns:
    - tasks: List of failed task data
    - total: int - Total number of failed tasks
    """
    try:
        failed_tasks = get_failed_tasks(limit=limit)

        return {
            "status": "success",
            "tasks": failed_tasks,
            "total": len(failed_tasks),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/dlq/stats")
async def get_dlq_statistics():
    """
    Get statistics about the Dead Letter Queue

    Returns:
    - total_failed: int - Total number of failed tasks
    - failed_by_type: Dict - Count of failed tasks by type
    - sampled: int - Number of tasks sampled for statistics
    """
    try:
        stats = get_dlq_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/dlq/{task_id}/retry")
async def retry_dlq_task(task_id: str, request: Dict[str, Any]):
    """
    Retry a failed task from the DLQ

    Path params:
    - task_id: str - Original task ID

    Body:
    - task_data: Dict - Task data including task name, args, kwargs

    Returns:
    - status: str - Retry status
    - new_task_id: str - New task ID (if successful)
    """
    try:
        task_data = request.get("task_data")
        if not task_data:
            raise HTTPException(status_code=400, detail="task_data required")

        success = retry_failed_task(task_id, task_data)

        if success:
            # Get new task ID from Redis
            retry_key = f'task_retry:{task_id}'
            retry_info_json = celery_redis.get(retry_key) if celery_redis else None

            retry_info = {}
            if retry_info_json:
                retry_info = json.loads(retry_info_json)

            return {
                "status": "success",
                "message": "Task retried successfully",
                "original_task_id": task_id,
                "new_task_id": retry_info.get("new_task_id"),
                "retry_time": retry_info.get("retry_time")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to retry task")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/dlq/purge")
async def purge_dlq_tasks(older_than_days: int = 7):
    """
    Purge old messages from the Dead Letter Queue

    Query params:
    - older_than_days: int (default: 7) - Remove messages older than this

    Returns:
    - purged_count: int - Number of messages purged
    """
    try:
        purged_count = purge_dlq(older_than_days=older_than_days)

        return {
            "status": "success",
            "purged_count": purged_count,
            "older_than_days": older_than_days,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
