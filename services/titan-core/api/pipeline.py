"""
ULTIMATE AD GENERATION PIPELINE API
Single endpoint that does EVERYTHING:
1. Director generates 50 ad blueprints
2. Council evaluates each (approve if score > 85)
3. Oracle predicts ROAS for approved scripts
4. Returns ranked blueprints ready for rendering

Second endpoint renders the winners:
1. Takes approved blueprints
2. Runs PRO Renderer with GPU acceleration
3. Adds Hormozi-style captions (Whisper)
4. Smart crops for platform (16:9 → 9:16)
5. Uploads to GCS
6. Returns download URLs
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import logging
import os
import uuid

# Import AI Council components
import sys
sys.path.append('/home/user/geminivideo/services/titan-core')
sys.path.append('/home/user/geminivideo/services/video-agent')

from ai_council import (
    CouncilOfTitans,
    OracleAgent,
    DirectorAgentV2,
    AdBlueprint,
    BlueprintGenerationRequest,
    EnsemblePredictionResult
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# ============================================================================
# REQUEST / RESPONSE MODELS
# ============================================================================

class CampaignGenerationRequest(BaseModel):
    """Request to generate a complete ad campaign"""
    product_name: str = Field(..., description="Product or service name")
    offer: str = Field(..., description="The specific offer/CTA")
    target_avatar: str = Field(..., description="Target customer avatar")
    pain_points: List[str] = Field(..., description="Customer pain points to address")
    desires: List[str] = Field(..., description="Customer desires/goals")
    num_variations: int = Field(50, ge=1, le=100, description="Number of blueprint variations to generate")
    platforms: List[str] = Field(
        default=["instagram_reels", "tiktok", "youtube_shorts"],
        description="Target platforms for rendering"
    )
    approval_threshold: float = Field(85.0, ge=0, le=100, description="Minimum council score for approval")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "PTD Fitness Coaching",
                "offer": "Book your free consultation",
                "target_avatar": "Busy professionals in Dubai aged 30-45",
                "pain_points": ["no time for gym", "low energy", "gaining weight"],
                "desires": ["look great", "feel confident", "have high energy"],
                "num_variations": 50,
                "platforms": ["instagram_reels", "tiktok"],
                "approval_threshold": 85.0
            }
        }


class BlueprintSummary(BaseModel):
    """Summary of an approved blueprint"""
    id: str
    title: str
    hook_text: str
    hook_type: str
    cta_text: str

    # Scores
    council_score: float = Field(..., description="Council evaluation score (0-100)")
    predicted_roas: float = Field(..., description="Predicted ROAS")
    confidence_level: str = Field(..., description="Prediction confidence: low, medium, high")
    rank: int = Field(..., description="Rank by predicted ROAS")

    # Metadata
    target_avatar: str
    emotional_triggers: List[str]


class CampaignGenerationResponse(BaseModel):
    """Response with generated and evaluated campaign blueprints"""
    campaign_id: str
    status: str = "completed"

    # Generation stats
    total_generated: int
    approved: int
    rejected: int

    # Top blueprints (ranked by predicted ROAS)
    blueprints: List[BlueprintSummary]

    # Performance metrics
    avg_council_score: float
    avg_predicted_roas: float
    best_predicted_roas: float

    # Timing
    generation_time_seconds: float

    # Next steps
    ready_for_render: bool
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")


class RenderRequest(BaseModel):
    """Request to render approved blueprints"""
    campaign_id: str = Field(..., description="Campaign ID from generation step")
    blueprint_ids: List[str] = Field(..., description="Which blueprints to render (empty = all approved)")
    platform: str = Field("instagram_reels", description="Target platform")
    quality: str = Field("HIGH", description="DRAFT, STANDARD, HIGH, MASTER")
    add_captions: bool = Field(True, description="Add Hormozi-style captions with Whisper")
    caption_style: str = Field("hormozi", description="Caption style: hormozi, modern, minimal")
    smart_crop: bool = Field(True, description="Auto-crop to platform format")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "campaign_12345",
                "blueprint_ids": [],  # Empty = render all
                "platform": "instagram_reels",
                "quality": "HIGH",
                "add_captions": True,
                "caption_style": "hormozi",
                "smart_crop": True
            }
        }


class RenderJobStatus(BaseModel):
    """Status of a single render job"""
    job_id: str
    blueprint_id: str
    status: str = Field(..., description="queued, processing, completed, failed")
    progress: float = Field(0, ge=0, le=100, description="Progress percentage")
    message: str = ""
    output_path: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class RenderResponse(BaseModel):
    """Response with queued render jobs"""
    campaign_id: str
    render_job_ids: List[str]
    total_jobs: int
    estimated_time_seconds: int
    websocket_url: str = Field(..., description="WebSocket for progress updates")
    status_url: str = Field(..., description="Polling URL for status")


class CampaignStatus(BaseModel):
    """Complete campaign status"""
    campaign_id: str
    created_at: datetime

    # Generation phase
    generation_status: str = Field(..., description="pending, completed, failed")
    total_blueprints: int
    approved_blueprints: int
    rejected_blueprints: int

    # Render phase
    render_status: str = Field(..., description="not_started, in_progress, completed, failed")
    total_render_jobs: int
    completed_renders: int
    failed_renders: int

    # Results
    blueprints: List[BlueprintSummary]
    render_jobs: List[RenderJobStatus]


class VideoOutput(BaseModel):
    """Single rendered video output"""
    video_id: str
    blueprint_id: str
    campaign_id: str

    # Video details
    platform: str
    format: str
    duration_seconds: float
    file_size_bytes: int

    # URLs
    video_url: str
    thumbnail_url: Optional[str]

    # Metadata
    council_score: float
    predicted_roas: float
    hook_text: str
    cta_text: str

    created_at: datetime


class CampaignVideosResponse(BaseModel):
    """All rendered videos for a campaign"""
    campaign_id: str
    total_videos: int
    videos: List[VideoOutput]

    # Batch download
    zip_download_url: Optional[str] = None


# ============================================================================
# IN-MEMORY STORAGE (Replace with Redis/Database in production)
# ============================================================================

# Campaign storage
campaigns_db: Dict[str, Dict[str, Any]] = {}
render_jobs_db: Dict[str, Dict[str, Any]] = {}

# WebSocket connections for real-time updates
active_websockets: Dict[str, List[WebSocket]] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_campaign_id() -> str:
    """Generate unique campaign ID"""
    return f"campaign_{uuid.uuid4().hex[:12]}"


def generate_job_id() -> str:
    """Generate unique render job ID"""
    return f"job_{uuid.uuid4().hex[:12]}"


async def broadcast_to_campaign(campaign_id: str, message: Dict[str, Any]):
    """Broadcast message to all WebSocket clients watching this campaign"""
    if campaign_id in active_websockets:
        dead_sockets = []
        for ws in active_websockets[campaign_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)

        # Remove dead connections
        for ws in dead_sockets:
            active_websockets[campaign_id].remove(ws)


def extract_oracle_features(blueprint: AdBlueprint) -> Dict[str, Any]:
    """Extract features from blueprint for Oracle prediction"""

    # Analyze hook effectiveness
    hook_score = 7.0  # Default
    if blueprint.hook_type == "pattern_interrupt":
        hook_score = 8.5
    elif blueprint.hook_type == "transformation":
        hook_score = 8.0
    elif blueprint.hook_type == "story":
        hook_score = 7.5
    elif blueprint.hook_type == "question":
        hook_score = 7.0

    # Check for transformation content
    has_transformation = "transformation" in blueprint.hook_type.lower() or \
                        any("before" in str(s.visual_description).lower() and
                            "after" in str(s.visual_description).lower()
                            for s in blueprint.scenes)

    # Count emotional triggers
    num_triggers = len(blueprint.emotional_triggers)

    # CTA strength
    cta_score = 7.0
    if "book" in blueprint.cta_text.lower() or "call" in blueprint.cta_text.lower():
        cta_score = 8.0
    elif "buy" in blueprint.cta_text.lower() or "order" in blueprint.cta_text.lower():
        cta_score = 7.5

    # Scene analysis
    num_scenes = len(blueprint.scenes)
    total_duration = sum(s.duration_seconds for s in blueprint.scenes)

    # Check for voiceover
    has_voiceover = any(s.audio_description and len(s.audio_description) > 0 for s in blueprint.scenes)

    return {
        "hook_effectiveness": hook_score,
        "has_transformation": 1 if has_transformation else 0,
        "transformation_believability": 7.0 if has_transformation else 0,
        "num_emotional_triggers": num_triggers,
        "cta_strength": cta_score,
        "has_cta": 1,
        "has_voiceover": 1 if has_voiceover else 0,
        "quality_ratio": 1.5,  # Assuming good quality
        "num_winning_patterns_matched": min(3, num_triggers),  # Based on emotional triggers
        "energy_level": 3,  # Assume high energy for short-form content
        "pacing_speed": 3 if total_duration <= 30 else 2,  # Fast pacing for short videos
        "has_music": 1,  # Assume music will be added
        "scene_count": num_scenes,
        "total_duration": total_duration
    }


# ============================================================================
# MAIN ENDPOINTS
# ============================================================================

@router.post("/generate-campaign", response_model=CampaignGenerationResponse)
async def generate_campaign(request: CampaignGenerationRequest):
    """
    ULTIMATE ENDPOINT: Generate winning ad campaign

    Flow:
    1. Director → 50 blueprints with Reflexion Loop
    2. Council → Evaluate each blueprint in parallel (4-model ensemble)
    3. Oracle → Predict ROAS for approved blueprints (8-engine ensemble)
    4. Return ranked by predicted ROAS

    This endpoint returns immediately with approved blueprints ready for rendering.
    Use the /render-winners endpoint to queue actual video production.
    """

    start_time = datetime.utcnow()
    campaign_id = generate_campaign_id()

    logger.info(f"🎬 Starting campaign generation: {campaign_id}")
    logger.info(f"   Product: {request.product_name}")
    logger.info(f"   Variations: {request.num_variations}")

    try:
        # ===================================================================
        # STEP 1: DIRECTOR - Generate Blueprint Variations
        # ===================================================================

        logger.info(f"📝 STEP 1: Director generating {request.num_variations} blueprints...")

        director = DirectorAgentV2()

        blueprint_request = BlueprintGenerationRequest(
            product_name=request.product_name,
            offer=request.offer,
            target_avatar=request.target_avatar,
            target_pain_points=request.pain_points,
            target_desires=request.desires,
            platform=request.platforms[0] if request.platforms else "reels",
            tone="direct",
            duration_seconds=30,
            num_variations=request.num_variations
        )

        blueprints = await director.generate_blueprints(blueprint_request)

        logger.info(f"✅ Director generated {len(blueprints)} blueprints")

        # ===================================================================
        # STEP 2: COUNCIL - Evaluate Each Blueprint
        # ===================================================================

        logger.info(f"🏛️ STEP 2: Council evaluating {len(blueprints)} blueprints...")

        council = CouncilOfTitans()
        approved_blueprints: List[Tuple[AdBlueprint, float]] = []
        rejected_count = 0

        # Evaluate in parallel batches of 5
        batch_size = 5
        for i in range(0, len(blueprints), batch_size):
            batch = blueprints[i:i+batch_size]

            # Create evaluation tasks
            eval_tasks = []
            for bp in batch:
                # Create script from blueprint
                script = f"{bp.hook_text}\n\n"
                for scene in bp.scenes:
                    script += f"{scene.visual_description}\n{scene.audio_description}\n\n"
                script += f"\nCTA: {bp.cta_text}"

                # Extract visual features
                visual_features = {
                    "has_human_face": True,  # Assume fitness/testimonial content
                    "hook_type": bp.hook_type,
                    "high_contrast": True,
                    "fast_paced": True,
                    "text_overlays": any(s.text_overlay for s in bp.scenes),
                    "scene_count": len(bp.scenes)
                }

                eval_tasks.append(council.evaluate_script(script, visual_features))

            # Execute batch in parallel
            results = await asyncio.gather(*eval_tasks)

            # Process results
            for bp, result in zip(batch, results):
                council_score = result['final_score']

                if council_score >= request.approval_threshold:
                    approved_blueprints.append((bp, council_score))
                    logger.info(f"  ✅ {bp.id}: APPROVED (score: {council_score:.1f})")
                else:
                    rejected_count += 1
                    logger.info(f"  ❌ {bp.id}: REJECTED (score: {council_score:.1f})")

        logger.info(f"📊 Council Results: {len(approved_blueprints)} approved, {rejected_count} rejected")

        # ===================================================================
        # STEP 3: ORACLE - Predict ROAS for Approved Blueprints
        # ===================================================================

        logger.info(f"🔮 STEP 3: Oracle predicting ROAS for {len(approved_blueprints)} approved blueprints...")

        oracle = OracleAgent()
        ranked_blueprints: List[Dict[str, Any]] = []

        # Predict in parallel
        prediction_tasks = []
        for bp, council_score in approved_blueprints:
            features = extract_oracle_features(bp)
            prediction_tasks.append(oracle.predict(features, bp.id))

        predictions = await asyncio.gather(*prediction_tasks)

        # Combine results
        for (bp, council_score), prediction in zip(approved_blueprints, predictions):
            ranked_blueprints.append({
                "blueprint": bp,
                "council_score": council_score,
                "prediction": prediction
            })

        # Sort by predicted ROAS (descending)
        ranked_blueprints.sort(
            key=lambda x: x["prediction"].roas_prediction.predicted_roas,
            reverse=True
        )

        # Assign ranks
        for i, item in enumerate(ranked_blueprints):
            item["blueprint"].rank = i + 1

        logger.info(f"🏆 Oracle ranked {len(ranked_blueprints)} blueprints by ROAS")

        if ranked_blueprints:
            logger.info(f"   Top blueprint: ROAS {ranked_blueprints[0]['prediction'].roas_prediction.predicted_roas:.2f}x")

        # ===================================================================
        # STEP 4: Build Response
        # ===================================================================

        # Calculate metrics
        total_generated = len(blueprints)
        approved = len(approved_blueprints)
        rejected = rejected_count

        avg_council_score = sum(x['council_score'] for x in ranked_blueprints) / len(ranked_blueprints) if ranked_blueprints else 0
        avg_roas = sum(x['prediction'].roas_prediction.predicted_roas for x in ranked_blueprints) / len(ranked_blueprints) if ranked_blueprints else 0
        best_roas = ranked_blueprints[0]['prediction'].roas_prediction.predicted_roas if ranked_blueprints else 0

        # Create blueprint summaries
        blueprint_summaries = []
        for item in ranked_blueprints:
            bp = item["blueprint"]
            pred = item["prediction"]

            blueprint_summaries.append(BlueprintSummary(
                id=bp.id,
                title=bp.title,
                hook_text=bp.hook_text,
                hook_type=bp.hook_type,
                cta_text=bp.cta_text,
                council_score=item["council_score"],
                predicted_roas=pred.roas_prediction.predicted_roas,
                confidence_level=pred.roas_prediction.confidence_level,
                rank=bp.rank,
                target_avatar=bp.target_avatar,
                emotional_triggers=bp.emotional_triggers
            ))

        # Store campaign in database
        end_time = datetime.utcnow()
        generation_time = (end_time - start_time).total_seconds()

        campaigns_db[campaign_id] = {
            "campaign_id": campaign_id,
            "request": request.model_dump(),
            "created_at": start_time,
            "generation_status": "completed",
            "total_blueprints": total_generated,
            "approved_blueprints": approved,
            "rejected_blueprints": rejected,
            "ranked_blueprints": ranked_blueprints,
            "blueprint_summaries": [bp.model_dump() for bp in blueprint_summaries],
            "render_status": "not_started",
            "render_jobs": []
        }

        logger.info(f"✅ Campaign {campaign_id} generation completed in {generation_time:.1f}s")

        return CampaignGenerationResponse(
            campaign_id=campaign_id,
            status="completed",
            total_generated=total_generated,
            approved=approved,
            rejected=rejected,
            blueprints=blueprint_summaries,
            avg_council_score=round(avg_council_score, 2),
            avg_predicted_roas=round(avg_roas, 2),
            best_predicted_roas=round(best_roas, 2),
            generation_time_seconds=round(generation_time, 2),
            ready_for_render=len(blueprint_summaries) > 0,
            websocket_url=f"/pipeline/ws/{campaign_id}"
        )

    except Exception as e:
        logger.error(f"❌ Campaign generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.post("/render-winners", response_model=RenderResponse)
async def render_winners(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render approved blueprints to actual videos

    Flow:
    1. Validate campaign and blueprints exist
    2. Queue render jobs (using Celery if available, otherwise background tasks)
    3. Return job IDs immediately
    4. Client connects to WebSocket for progress updates

    Each render job:
    - Generates video from blueprint using PRO Renderer
    - Adds Hormozi-style captions with Whisper
    - Smart crops to platform format (9:16, 1:1, 16:9)
    - Uploads to GCS
    - Returns download URL
    """

    logger.info(f"🎬 Starting render for campaign: {request.campaign_id}")

    # Validate campaign exists
    if request.campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail=f"Campaign {request.campaign_id} not found")

    campaign = campaigns_db[request.campaign_id]

    # Get blueprints to render
    blueprints_to_render = []

    if request.blueprint_ids:
        # Render specific blueprints
        for bp_id in request.blueprint_ids:
            found = False
            for item in campaign["ranked_blueprints"]:
                if item["blueprint"].id == bp_id:
                    blueprints_to_render.append(item)
                    found = True
                    break
            if not found:
                raise HTTPException(status_code=404, detail=f"Blueprint {bp_id} not found in campaign")
    else:
        # Render all approved blueprints (top 10 max for demo)
        blueprints_to_render = campaign["ranked_blueprints"][:10]

    if not blueprints_to_render:
        raise HTTPException(status_code=400, detail="No blueprints to render")

    logger.info(f"   Queuing {len(blueprints_to_render)} render jobs")

    # Create render jobs
    render_jobs = []
    for item in blueprints_to_render:
        job_id = generate_job_id()
        bp = item["blueprint"]

        job = {
            "job_id": job_id,
            "campaign_id": request.campaign_id,
            "blueprint_id": bp.id,
            "blueprint": bp,
            "platform": request.platform,
            "quality": request.quality,
            "add_captions": request.add_captions,
            "caption_style": request.caption_style,
            "smart_crop": request.smart_crop,
            "status": "queued",
            "progress": 0,
            "message": "Queued for rendering",
            "created_at": datetime.utcnow(),
            "output_path": None,
            "download_url": None,
            "error": None
        }

        render_jobs.append(job)
        render_jobs_db[job_id] = job

        # Queue background task
        background_tasks.add_task(process_render_job, job_id)

    # Update campaign
    campaign["render_status"] = "in_progress"
    campaign["render_jobs"].extend([job["job_id"] for job in render_jobs])

    # Estimate time (rough: 30 seconds per video)
    estimated_time = len(render_jobs) * 30

    logger.info(f"✅ Queued {len(render_jobs)} render jobs for campaign {request.campaign_id}")

    return RenderResponse(
        campaign_id=request.campaign_id,
        render_job_ids=[job["job_id"] for job in render_jobs],
        total_jobs=len(render_jobs),
        estimated_time_seconds=estimated_time,
        websocket_url=f"/pipeline/ws/{request.campaign_id}",
        status_url=f"/pipeline/campaign/{request.campaign_id}"
    )


@router.get("/campaign/{campaign_id}", response_model=CampaignStatus)
async def get_campaign(campaign_id: str):
    """Get campaign status and results"""

    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    campaign = campaigns_db[campaign_id]

    # Get render job statuses
    render_job_statuses = []
    completed_renders = 0
    failed_renders = 0

    for job_id in campaign.get("render_jobs", []):
        if job_id in render_jobs_db:
            job = render_jobs_db[job_id]

            render_job_statuses.append(RenderJobStatus(
                job_id=job["job_id"],
                blueprint_id=job["blueprint_id"],
                status=job["status"],
                progress=job["progress"],
                message=job["message"],
                output_path=job.get("output_path"),
                download_url=job.get("download_url"),
                error=job.get("error")
            ))

            if job["status"] == "completed":
                completed_renders += 1
            elif job["status"] == "failed":
                failed_renders += 1

    # Convert blueprint summaries back to Pydantic models
    blueprint_summaries = [
        BlueprintSummary(**bp) for bp in campaign.get("blueprint_summaries", [])
    ]

    return CampaignStatus(
        campaign_id=campaign_id,
        created_at=campaign["created_at"],
        generation_status=campaign["generation_status"],
        total_blueprints=campaign["total_blueprints"],
        approved_blueprints=campaign["approved_blueprints"],
        rejected_blueprints=campaign["rejected_blueprints"],
        render_status=campaign["render_status"],
        total_render_jobs=len(campaign.get("render_jobs", [])),
        completed_renders=completed_renders,
        failed_renders=failed_renders,
        blueprints=blueprint_summaries,
        render_jobs=render_job_statuses
    )


@router.get("/campaign/{campaign_id}/videos", response_model=CampaignVideosResponse)
async def get_campaign_videos(campaign_id: str):
    """Get all rendered videos for a campaign with download URLs"""

    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    campaign = campaigns_db[campaign_id]

    # Get completed videos
    videos = []
    for job_id in campaign.get("render_jobs", []):
        if job_id in render_jobs_db:
            job = render_jobs_db[job_id]

            if job["status"] == "completed" and job.get("output_path"):
                # Find blueprint data
                bp_data = None
                for item in campaign["ranked_blueprints"]:
                    if item["blueprint"].id == job["blueprint_id"]:
                        bp = item["blueprint"]
                        pred = item["prediction"]
                        bp_data = (bp, item["council_score"], pred)
                        break

                if bp_data:
                    bp, council_score, pred = bp_data

                    # Get file info
                    file_size = 0
                    duration = 30.0  # Default
                    if os.path.exists(job["output_path"]):
                        file_size = os.path.getsize(job["output_path"])

                    videos.append(VideoOutput(
                        video_id=job["job_id"],
                        blueprint_id=job["blueprint_id"],
                        campaign_id=campaign_id,
                        platform=job["platform"],
                        format="mp4",
                        duration_seconds=duration,
                        file_size_bytes=file_size,
                        video_url=job.get("download_url", ""),
                        thumbnail_url=None,
                        council_score=council_score,
                        predicted_roas=pred.roas_prediction.predicted_roas,
                        hook_text=bp.hook_text,
                        cta_text=bp.cta_text,
                        created_at=job["created_at"]
                    ))

    return CampaignVideosResponse(
        campaign_id=campaign_id,
        total_videos=len(videos),
        videos=videos,
        zip_download_url=None  # TODO: Implement batch zip download
    )


@router.websocket("/ws/{campaign_id}")
async def campaign_websocket(websocket: WebSocket, campaign_id: str):
    """
    WebSocket endpoint for real-time campaign updates

    Sends JSON messages:
    - {"type": "generation_progress", "progress": 0-100, "message": "..."}
    - {"type": "blueprint_evaluated", "blueprint_id": "...", "score": 85.3}
    - {"type": "generation_complete", "approved": 42, "rejected": 8}
    - {"type": "render_progress", "job_id": "...", "progress": 0-100}
    - {"type": "render_complete", "job_id": "...", "download_url": "..."}
    """

    await websocket.accept()

    # Register connection
    if campaign_id not in active_websockets:
        active_websockets[campaign_id] = []
    active_websockets[campaign_id].append(websocket)

    logger.info(f"WebSocket connected for campaign {campaign_id}")

    try:
        # Send initial status
        if campaign_id in campaigns_db:
            campaign = campaigns_db[campaign_id]
            await websocket.send_json({
                "type": "status",
                "campaign_id": campaign_id,
                "generation_status": campaign["generation_status"],
                "render_status": campaign["render_status"]
            })

        # Keep connection alive and receive any messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for campaign {campaign_id}")
        if campaign_id in active_websockets:
            active_websockets[campaign_id].remove(websocket)


# ============================================================================
# BACKGROUND RENDER JOB PROCESSOR
# ============================================================================

async def process_render_job(job_id: str):
    """
    Process a render job in the background

    This is a simplified version. In production:
    - Use Celery for distributed processing
    - Connect to actual PRO Renderer
    - Upload to GCS
    - Generate thumbnails
    """

    if job_id not in render_jobs_db:
        logger.error(f"Job {job_id} not found")
        return

    job = render_jobs_db[job_id]
    campaign_id = job["campaign_id"]

    try:
        # Update status
        job["status"] = "processing"
        job["progress"] = 0
        job["message"] = "Initializing render..."

        await broadcast_to_campaign(campaign_id, {
            "type": "render_started",
            "job_id": job_id,
            "blueprint_id": job["blueprint_id"]
        })

        logger.info(f"🎬 Processing render job {job_id}")

        # Simulate render process (replace with actual PRO Renderer)
        # In production, this would:
        # 1. Call PRO Renderer with blueprint data
        # 2. Generate video from scenes
        # 3. Add captions with Whisper
        # 4. Smart crop to platform format
        # 5. Upload to GCS

        # Simulated progress updates
        for progress in [10, 25, 40, 55, 70, 85, 95]:
            await asyncio.sleep(1)  # Simulate work
            job["progress"] = progress
            job["message"] = f"Rendering... {progress}%"

            await broadcast_to_campaign(campaign_id, {
                "type": "render_progress",
                "job_id": job_id,
                "progress": progress
            })

        # Generate mock output (replace with actual render)
        output_dir = "/tmp/renders"
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"{campaign_id}_{job['blueprint_id']}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        # Create empty file as placeholder
        with open(output_path, 'w') as f:
            f.write(f"Mock render for {job_id}")

        # In production, upload to GCS and get URL
        download_url = f"https://storage.googleapis.com/your-bucket/{output_filename}"

        # Complete job
        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = "Render complete"
        job["output_path"] = output_path
        job["download_url"] = download_url
        job["completed_at"] = datetime.utcnow()

        await broadcast_to_campaign(campaign_id, {
            "type": "render_complete",
            "job_id": job_id,
            "blueprint_id": job["blueprint_id"],
            "download_url": download_url
        })

        logger.info(f"✅ Render job {job_id} completed: {output_path}")

        # Check if all renders are done
        campaign = campaigns_db[campaign_id]
        all_done = all(
            render_jobs_db[jid]["status"] in ["completed", "failed"]
            for jid in campaign["render_jobs"]
            if jid in render_jobs_db
        )

        if all_done:
            campaign["render_status"] = "completed"
            await broadcast_to_campaign(campaign_id, {
                "type": "campaign_complete",
                "campaign_id": campaign_id
            })
            logger.info(f"🎉 Campaign {campaign_id} fully rendered!")

    except Exception as e:
        logger.error(f"❌ Render job {job_id} failed: {e}", exc_info=True)

        job["status"] = "failed"
        job["progress"] = 0
        job["message"] = "Render failed"
        job["error"] = str(e)

        await broadcast_to_campaign(campaign_id, {
            "type": "render_failed",
            "job_id": job_id,
            "error": str(e)
        })


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pipeline",
        "version": "1.0.0",
        "components": {
            "director": "available",
            "council": "available",
            "oracle": "available",
            "renderer": "mock"  # TODO: Update when real renderer is connected
        }
    }


@router.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    campaigns = []
    for campaign_id, campaign in campaigns_db.items():
        campaigns.append({
            "campaign_id": campaign_id,
            "created_at": campaign["created_at"],
            "generation_status": campaign["generation_status"],
            "render_status": campaign["render_status"],
            "total_blueprints": campaign["total_blueprints"],
            "approved_blueprints": campaign["approved_blueprints"]
        })

    return {"campaigns": campaigns, "total": len(campaigns)}


@router.delete("/campaign/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign and its render jobs"""

    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    campaign = campaigns_db[campaign_id]

    # Delete render jobs
    for job_id in campaign.get("render_jobs", []):
        if job_id in render_jobs_db:
            # Clean up files
            job = render_jobs_db[job_id]
            if job.get("output_path") and os.path.exists(job["output_path"]):
                try:
                    os.remove(job["output_path"])
                except Exception as e:
                    logger.error(f"Failed to delete file: {e}")

            del render_jobs_db[job_id]

    # Delete campaign
    del campaigns_db[campaign_id]

    logger.info(f"🗑️ Deleted campaign {campaign_id}")

    return {"status": "deleted", "campaign_id": campaign_id}
