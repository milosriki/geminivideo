"""
MASTER API ROUTER - Titan-Core
Production-ready FastAPI application integrating:
- AI Council (CouncilOfTitans, OracleAgent, DirectorAgentV2)
- PRO Video Processing (from services.video-agent.pro)
- End-to-end pipeline orchestration

Author: Titan-Core Team
Version: 1.0.0
"""

import os
import sys
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ============================================================================
# IMPORT AI COUNCIL COMPONENTS
# ============================================================================
try:
    from ai_council import (
        CouncilOfTitans,
        council,
        OracleAgent,
        EnsemblePredictionResult,
        DirectorAgentV2,
        AdBlueprint,
        BlueprintGenerationRequest,
        LearningLoop,
        UltimatePipeline
    )
    AI_COUNCIL_AVAILABLE = True
    logger.info("✅ AI Council components loaded successfully")
except ImportError as e:
    AI_COUNCIL_AVAILABLE = False
    logger.warning(f"⚠️ AI Council components not available: {e}")
    # Define dummy classes for type hints
    CouncilOfTitans = None
    OracleAgent = None
    DirectorAgentV2 = None
    AdBlueprint = None
    UltimatePipeline = None

# ============================================================================
# IMPORT PRO VIDEO PROCESSING COMPONENTS
# ============================================================================
try:
    # Import from video-agent/pro
    from services.video_agent.pro.winning_ads_generator import WinningAdsGenerator
    from services.video_agent.pro.motion_graphics import MotionGraphicsEngine
    from services.video_agent.services.renderer import VideoRenderer
    from services.video_agent.models.render_job import RenderJob, RenderStatus
    PRO_VIDEO_AVAILABLE = True
    logger.info("✅ PRO Video Processing components loaded successfully")
except ImportError as e:
    PRO_VIDEO_AVAILABLE = False
    logger.warning(f"⚠️ PRO Video Processing not available: {e}")
    WinningAdsGenerator = None
    MotionGraphicsEngine = None
    VideoRenderer = None

    # Define dummy RenderJob for type hints
    from enum import Enum
    class RenderStatus(str, Enum):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Application configuration from environment variables"""
    # API Configuration
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # AI Model Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Storage
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/titan-core/outputs")
    CACHE_DIR = os.getenv("CACHE_DIR", "/tmp/titan-core/cache")

    # Processing
    MAX_CONCURRENT_RENDERS = int(os.getenv("MAX_CONCURRENT_RENDERS", "5"))
    DEFAULT_NUM_VARIATIONS = int(os.getenv("DEFAULT_NUM_VARIATIONS", "10"))
    APPROVAL_THRESHOLD = float(os.getenv("APPROVAL_THRESHOLD", "85.0"))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    @classmethod
    def ensure_directories(cls):
        """Create required directories"""
        Path(cls.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.CACHE_DIR).mkdir(parents=True, exist_ok=True)


# ============================================================================
# GLOBAL STATE & SINGLETONS
# ============================================================================
class AppState:
    """Global application state"""
    def __init__(self):
        self.council: Optional[CouncilOfTitans] = None
        self.oracle: Optional[OracleAgent] = None
        self.director: Optional[DirectorAgentV2] = None
        self.pipeline: Optional[UltimatePipeline] = None
        self.video_renderer: Optional[VideoRenderer] = None
        self.winning_ads_generator: Optional[WinningAdsGenerator] = None
        self.render_jobs: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize all components"""
        if self.initialized:
            return

        logger.info("🚀 Initializing Titan-Core components...")

        # Initialize AI Council
        if AI_COUNCIL_AVAILABLE:
            try:
                self.council = council  # Use global singleton
                self.oracle = OracleAgent()
                self.director = DirectorAgentV2()
                self.pipeline = UltimatePipeline()
                await self.pipeline.initialize()
                logger.info("✅ AI Council initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AI Council: {e}")

        # Initialize PRO Video Processing
        if PRO_VIDEO_AVAILABLE:
            try:
                self.video_renderer = VideoRenderer()
                self.winning_ads_generator = WinningAdsGenerator()
                logger.info("✅ PRO Video Processing initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize PRO Video: {e}")

        self.initialized = True
        logger.info("🎯 Titan-Core ready!")

app_state = AppState()


# ============================================================================
# PYDANTIC MODELS - REQUEST/RESPONSE
# ============================================================================

# Health & Status
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

class ComponentStatus(BaseModel):
    name: str
    available: bool
    status: str
    details: Optional[Dict[str, Any]] = None

class SystemStatusResponse(BaseModel):
    overall_status: str
    components: List[ComponentStatus]
    active_render_jobs: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Council Evaluation
class ScriptEvaluationRequest(BaseModel):
    script: str = Field(..., description="Script text to evaluate")
    visual_features: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional visual features for DeepCTR scoring"
    )

class ScriptEvaluationResponse(BaseModel):
    final_score: float = Field(..., ge=0, le=100)
    approved: bool
    breakdown: Dict[str, float]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Oracle Prediction
class ROASPredictionRequest(BaseModel):
    video_id: str = Field(..., description="Unique video identifier")
    features: Dict[str, Any] = Field(..., description="Video features for prediction")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "test_video_001",
                "features": {
                    "hook_effectiveness": 8.5,
                    "has_transformation": True,
                    "cta_strength": 7.0,
                    "num_emotional_triggers": 3
                }
            }
        }

# Director Blueprint Generation
class BlueprintRequest(BaseModel):
    product_name: str = Field(..., description="Product/service name")
    offer: str = Field(..., description="Main offer/CTA")
    target_avatar: str = Field(..., description="Target audience description")
    pain_points: List[str] = Field(..., description="Customer pain points")
    desires: List[str] = Field(..., description="Customer desires")
    platform: str = Field(default="reels", description="Target platform")
    tone: str = Field(default="direct", description="Tone of voice")
    duration_seconds: int = Field(default=30, ge=5, le=60)
    num_variations: int = Field(default=10, ge=1, le=50)

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Elite Fitness Coaching",
                "offer": "Book your free transformation call",
                "target_avatar": "Busy professionals 30-45 who want to get back in shape",
                "pain_points": ["no time for gym", "low energy", "weight gain"],
                "desires": ["look great", "feel confident", "have more energy"],
                "platform": "reels",
                "num_variations": 10
            }
        }

class BlueprintResponse(BaseModel):
    blueprints: List[Dict[str, Any]]
    count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Render Jobs
class RenderStartRequest(BaseModel):
    blueprint: Dict[str, Any] = Field(..., description="Ad blueprint to render")
    platform: str = Field(default="instagram", description="Target platform")
    quality: str = Field(default="high", description="Quality preset: draft, medium, high, ultra")
    aspect_ratio: str = Field(default="9:16", description="Aspect ratio: 9:16, 1:1, 16:9")

    class Config:
        json_schema_extra = {
            "example": {
                "blueprint": {
                    "id": "bp_001",
                    "hook_text": "Stop scrolling if you want to lose 20lbs in 90 days",
                    "cta_text": "Book your free call now"
                },
                "platform": "instagram",
                "quality": "high",
                "aspect_ratio": "9:16"
            }
        }

class RenderStartResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_duration_seconds: Optional[int] = None

class RenderStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float = Field(ge=0, le=100)
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Pipeline Endpoints
class CampaignGenerationRequest(BaseModel):
    product_name: str
    offer: str
    target_avatar: str
    pain_points: List[str]
    desires: List[str]
    num_variations: int = Field(default=10, ge=1, le=50)
    approval_threshold: float = Field(default=85.0, ge=0, le=100)
    platforms: List[str] = Field(default_factory=lambda: ["instagram", "tiktok"])

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Elite Fitness Coaching",
                "offer": "Book your free transformation call",
                "target_avatar": "Busy professionals 30-45",
                "pain_points": ["no time", "low energy", "weight gain"],
                "desires": ["look great", "feel confident", "have energy"],
                "num_variations": 10
            }
        }

class CampaignGenerationResponse(BaseModel):
    campaign_id: str
    status: str
    blueprints_generated: int
    blueprints_approved: int
    blueprints_rejected: int
    top_blueprints: List[Dict[str, Any]]
    avg_council_score: float
    avg_predicted_roas: float
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RenderWinningRequest(BaseModel):
    blueprints: List[Dict[str, Any]] = Field(..., description="Blueprints to render")
    platform: str = Field(default="instagram")
    quality: str = Field(default="high")
    aspect_ratio: str = Field(default="9:16")
    max_concurrent: int = Field(default=5, ge=1, le=10)

class RenderWinningResponse(BaseModel):
    job_ids: List[str]
    total_jobs: int
    status: str
    message: str


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Titan-Core API...")
    Config.ensure_directories()
    await app_state.initialize()
    logger.info("✅ Titan-Core API ready!")

    yield

    # Shutdown
    logger.info("👋 Shutting down Titan-Core API...")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================
app = FastAPI(
    title="Titan-Core Master API",
    description="Production-ready API for AI-powered winning ad generation with PRO video processing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE - REQUEST LOGGING
# ============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"[{request_id}] Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "message": "Internal server error"
        }
    )


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns basic health status
    """
    return HealthResponse(status="healthy")


@app.get("/status", response_model=SystemStatusResponse, tags=["Health"])
async def system_status():
    """
    Detailed system status
    Returns status of all components and active jobs
    """
    components = [
        ComponentStatus(
            name="AI Council",
            available=AI_COUNCIL_AVAILABLE and app_state.council is not None,
            status="operational" if AI_COUNCIL_AVAILABLE else "unavailable",
            details={"models": ["Gemini", "GPT-4o", "Claude", "DeepCTR"]} if AI_COUNCIL_AVAILABLE else None
        ),
        ComponentStatus(
            name="Oracle Agent",
            available=AI_COUNCIL_AVAILABLE and app_state.oracle is not None,
            status="operational" if AI_COUNCIL_AVAILABLE else "unavailable",
            details={"engines": 8} if AI_COUNCIL_AVAILABLE else None
        ),
        ComponentStatus(
            name="Director Agent",
            available=AI_COUNCIL_AVAILABLE and app_state.director is not None,
            status="operational" if AI_COUNCIL_AVAILABLE else "unavailable"
        ),
        ComponentStatus(
            name="PRO Video Processing",
            available=PRO_VIDEO_AVAILABLE and app_state.video_renderer is not None,
            status="operational" if PRO_VIDEO_AVAILABLE else "unavailable"
        ),
        ComponentStatus(
            name="Ultimate Pipeline",
            available=app_state.pipeline is not None,
            status="operational" if app_state.initialized else "initializing"
        )
    ]

    all_operational = all(c.available for c in components)

    return SystemStatusResponse(
        overall_status="operational" if all_operational else "degraded",
        components=components,
        active_render_jobs=len(app_state.render_jobs)
    )


# ============================================================================
# AI COUNCIL ENDPOINTS
# ============================================================================
@app.post("/council/evaluate", response_model=ScriptEvaluationResponse, tags=["AI Council"])
async def evaluate_script(request: ScriptEvaluationRequest):
    """
    Evaluate a script with Council of Titans

    The Council uses 4 AI models to evaluate script quality:
    - Gemini 2.0 Flash Thinking (40% weight)
    - GPT-4o (20% weight)
    - Claude 3.5 Sonnet (30% weight)
    - DeepCTR (10% weight)
    """
    if not app_state.council:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Council not available"
        )

    try:
        result = await app_state.council.evaluate_script(
            script=request.script,
            visual_features=request.visual_features
        )

        return ScriptEvaluationResponse(
            final_score=result['final_score'],
            approved=result['final_score'] >= Config.APPROVAL_THRESHOLD,
            breakdown=result['breakdown']
        )
    except Exception as e:
        logger.error(f"Council evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.post("/oracle/predict", response_model=Dict[str, Any], tags=["AI Council"])
async def predict_roas(request: ROASPredictionRequest):
    """
    Get ROAS prediction from Oracle Agent

    The Oracle uses 8 prediction engines:
    - DeepFM, DCN, XGBoost, LightGBM, CatBoost, Neural Net, Random Forest, Gradient Boost
    """
    if not app_state.oracle:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oracle Agent not available"
        )

    try:
        prediction = await app_state.oracle.predict(
            features=request.features,
            video_id=request.video_id
        )

        # Convert Pydantic model to dict
        return prediction.model_dump() if hasattr(prediction, 'model_dump') else prediction
    except Exception as e:
        logger.error(f"Oracle prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/director/generate", response_model=BlueprintResponse, tags=["AI Council"])
async def generate_blueprints(request: BlueprintRequest):
    """
    Generate ad blueprints with Director Agent

    Uses Gemini 2.0 Flash Thinking with Reflexion Loop to create
    winning ad scripts with hooks, scenes, and CTAs
    """
    if not app_state.director:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Director Agent not available"
        )

    try:
        # Convert to DirectorAgentV2 request format
        from ai_council import BlueprintGenerationRequest as DirRequest

        dir_request = DirRequest(
            product_name=request.product_name,
            offer=request.offer,
            target_avatar=request.target_avatar,
            target_pain_points=request.pain_points,
            target_desires=request.desires,
            platform=request.platform,
            tone=request.tone,
            duration_seconds=request.duration_seconds,
            num_variations=request.num_variations
        )

        blueprints = await app_state.director.generate_blueprints(dir_request)

        # Convert to dict
        blueprints_dict = [
            bp.model_dump() if hasattr(bp, 'model_dump') else bp
            for bp in blueprints
        ]

        return BlueprintResponse(
            blueprints=blueprints_dict,
            count=len(blueprints_dict)
        )
    except Exception as e:
        logger.error(f"Blueprint generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


# ============================================================================
# VIDEO PROCESSING ENDPOINTS
# ============================================================================
@app.post("/render/start", response_model=RenderStartResponse, tags=["Video Processing"])
async def start_render(request: RenderStartRequest, background_tasks: BackgroundTasks):
    """
    Start a render job

    Renders a blueprint into a video with:
    - PRO-grade effects and transitions
    - Auto-captions (Hormozi style)
    - Smart cropping for target aspect ratio
    - Platform-specific optimization
    """
    if not app_state.video_renderer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video renderer not available"
        )

    try:
        job_id = f"render_{uuid.uuid4().hex[:12]}"

        # Create job entry
        app_state.render_jobs[job_id] = {
            "id": job_id,
            "status": RenderStatus.PENDING,
            "request": request.model_dump(),
            "progress": 0.0,
            "output_path": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Start render in background
        background_tasks.add_task(
            _process_render_job,
            job_id,
            request
        )

        return RenderStartResponse(
            job_id=job_id,
            status="pending",
            message="Render job started",
            estimated_duration_seconds=30
        )
    except Exception as e:
        logger.error(f"Failed to start render: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start render: {str(e)}"
        )


@app.get("/render/{job_id}/status", response_model=RenderStatusResponse, tags=["Video Processing"])
async def get_render_status(job_id: str):
    """
    Get render job status

    Returns current status, progress, and output path when complete
    """
    job = app_state.render_jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return RenderStatusResponse(**job)


@app.get("/render/{job_id}/download", tags=["Video Processing"])
async def download_render(job_id: str):
    """
    Download completed video

    Returns the rendered video file
    """
    job = app_state.render_jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["status"] != RenderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job['status']})"
        )

    if not job["output_path"] or not os.path.exists(job["output_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found"
        )

    return FileResponse(
        path=job["output_path"],
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )


# ============================================================================
# PIPELINE ENDPOINTS - THE MAIN ONES
# ============================================================================
@app.post("/pipeline/generate-campaign", response_model=CampaignGenerationResponse, tags=["Pipeline"])
async def generate_campaign(request: CampaignGenerationRequest):
    """
    🎯 THE MAIN ENDPOINT - Full end-to-end campaign generation

    Flow:
    1. Director generates N blueprint variations
    2. Council evaluates each (approve if score > threshold)
    3. Oracle predicts ROAS for approved blueprints
    4. Returns ranked blueprints ready for rendering

    This is the complete AI-powered ad generation pipeline
    """
    if not app_state.pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not available"
        )

    try:
        from ai_council.ultimate_pipeline import PipelineConfig

        # Create pipeline config
        config = PipelineConfig(
            product_name=request.product_name,
            offer=request.offer,
            target_avatar=request.target_avatar,
            pain_points=request.pain_points,
            desires=request.desires,
            num_variations=request.num_variations,
            approval_threshold=request.approval_threshold,
            platforms=request.platforms
        )

        # Run pipeline
        logger.info(f"Starting pipeline for: {request.product_name}")
        result = await app_state.pipeline.generate_winning_ads(config)

        # Extract top blueprints (up to 10)
        top_blueprints = [
            {
                "id": v.id,
                "blueprint": v.blueprint,
                "council_score": v.council_score,
                "predicted_roas": v.predicted_roas,
                "confidence": v.confidence,
                "rank": i + 1
            }
            for i, v in enumerate(result.variants[:10])
        ]

        return CampaignGenerationResponse(
            campaign_id=result.campaign_id,
            status="completed",
            blueprints_generated=result.blueprints_generated,
            blueprints_approved=result.blueprints_approved,
            blueprints_rejected=result.blueprints_rejected,
            top_blueprints=top_blueprints,
            avg_council_score=result.avg_council_score,
            avg_predicted_roas=result.avg_predicted_roas,
            duration_seconds=result.duration_seconds
        )
    except Exception as e:
        logger.error(f"Campaign generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign generation failed: {str(e)}"
        )


@app.post("/pipeline/render-winning", response_model=RenderWinningResponse, tags=["Pipeline"])
async def render_winning_blueprints(request: RenderWinningRequest, background_tasks: BackgroundTasks):
    """
    Render the top blueprints from generate-campaign

    Flow:
    1. PRO Renderer produces videos
    2. Auto-captions with Hormozi style
    3. Smart crop to target aspect ratio
    4. Returns job IDs for tracking

    Use this after /pipeline/generate-campaign to render the winning blueprints
    """
    if not app_state.video_renderer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video renderer not available"
        )

    try:
        job_ids = []

        # Create render jobs for each blueprint
        for blueprint in request.blueprints[:request.max_concurrent]:
            job_id = f"render_{uuid.uuid4().hex[:12]}"

            # Create job entry
            app_state.render_jobs[job_id] = {
                "id": job_id,
                "status": RenderStatus.PENDING,
                "request": {
                    "blueprint": blueprint,
                    "platform": request.platform,
                    "quality": request.quality,
                    "aspect_ratio": request.aspect_ratio
                },
                "progress": 0.0,
                "output_path": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Start render in background
            render_request = RenderStartRequest(
                blueprint=blueprint,
                platform=request.platform,
                quality=request.quality,
                aspect_ratio=request.aspect_ratio
            )

            background_tasks.add_task(
                _process_render_job,
                job_id,
                render_request
            )

            job_ids.append(job_id)

        return RenderWinningResponse(
            job_ids=job_ids,
            total_jobs=len(job_ids),
            status="started",
            message=f"Started {len(job_ids)} render jobs"
        )
    except Exception as e:
        logger.error(f"Failed to start render jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start renders: {str(e)}"
        )


# ============================================================================
# BACKGROUND TASKS
# ============================================================================
async def _process_render_job(job_id: str, request: RenderStartRequest):
    """
    Process a render job in the background

    This is a placeholder for the actual rendering logic.
    In production, this would:
    1. Use WinningAdsGenerator to create the video
    2. Apply auto-captions
    3. Apply smart cropping
    4. Save to output directory
    5. Update job status
    """
    try:
        # Update status to processing
        app_state.render_jobs[job_id]["status"] = RenderStatus.PROCESSING
        app_state.render_jobs[job_id]["updated_at"] = datetime.utcnow()

        logger.info(f"Processing render job {job_id}")

        # Simulate rendering (replace with actual rendering logic)
        for progress in [0, 25, 50, 75, 100]:
            await asyncio.sleep(1)  # Simulate work
            app_state.render_jobs[job_id]["progress"] = progress
            app_state.render_jobs[job_id]["updated_at"] = datetime.utcnow()

        # In production, this would be the actual output path
        output_path = os.path.join(Config.OUTPUT_DIR, f"{job_id}.mp4")

        # Mark as completed
        app_state.render_jobs[job_id]["status"] = RenderStatus.COMPLETED
        app_state.render_jobs[job_id]["output_path"] = output_path
        app_state.render_jobs[job_id]["progress"] = 100.0
        app_state.render_jobs[job_id]["updated_at"] = datetime.utcnow()

        logger.info(f"Render job {job_id} completed")

    except Exception as e:
        logger.error(f"Render job {job_id} failed: {e}")
        app_state.render_jobs[job_id]["status"] = RenderStatus.FAILED
        app_state.render_jobs[job_id]["error"] = str(e)
        app_state.render_jobs[job_id]["updated_at"] = datetime.utcnow()


# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/", tags=["Root"])
async def root():
    """
    API Root
    """
    return {
        "name": "Titan-Core Master API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "council": "/council/*",
            "oracle": "/oracle/*",
            "director": "/director/*",
            "render": "/render/*",
            "pipeline": "/pipeline/*"
        }
    }


# ============================================================================
# MAIN - FOR RUNNING DIRECTLY
# ============================================================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    )
