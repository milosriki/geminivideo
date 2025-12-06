"""
AdIntel OS - REST API
Complete API for ad intelligence platform (replaces Foreplay API)

Features:
- Discovery API (search winning ads)
- Spyder API (brand tracking)
- Enrichment API (AI analysis)
- Credits system
- Rate limiting
"""

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import hashlib
import logging
import os

# Local imports
from .search_engine import AdSearchEngine, SearchConfig, AdDocument, SearchResponse
from .ad_enrichment import AdEnrichmentPipeline, EnrichedAd
from .ad_library_scraper import MetaAdLibraryScraper, BrandTracker, WinnerDetector, to_foreplay_format

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AdIntel OS API",
    description="AI-powered ad intelligence platform - Your own Foreplay alternative",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# =============================================================================
# Models
# =============================================================================

class Platform(str, Enum):
    META = "meta"
    TIKTOK = "tiktok"
    GOOGLE = "google"
    ALL = "all"


class AdFormat(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    ALL = "all"


class SortOption(str, Enum):
    RUNNING_DAYS_DESC = "running_duration_days:desc"
    RUNNING_DAYS_ASC = "running_duration_days:asc"
    WINNER_SCORE_DESC = "winner_score:desc"
    CREATED_AT_DESC = "created_at:desc"
    RELEVANCE = "_text_match:desc"


# Request/Response Models
class SearchRequest(BaseModel):
    query: str = "*"
    platform: Optional[Platform] = None
    format: Optional[AdFormat] = None
    industry: Optional[str] = None
    emotion: Optional[str] = None
    hook_type: Optional[str] = None
    min_running_days: int = 0
    winners_only: bool = False
    brand_name: Optional[str] = None
    sort_by: SortOption = SortOption.RUNNING_DAYS_DESC
    page: int = 1
    per_page: int = 20


class AdResponse(BaseModel):
    ad_id: str
    brand_name: str
    platform: str
    format: str
    headline: Optional[str] = None
    body_text: Optional[str] = None
    transcription: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    industry: Optional[str] = None
    primary_emotion: Optional[str] = None
    emotional_drivers: List[str] = []
    hook_type: Optional[str] = None
    hook_text: Optional[str] = None
    winning_patterns: List[str] = []
    running_duration_days: int
    is_winner: bool
    winner_score: Optional[int] = None
    first_seen: datetime
    last_seen: datetime


class SearchResponseModel(BaseModel):
    hits: List[AdResponse]
    total: int
    page: int
    per_page: int
    facets: Dict[str, List[Dict[str, Any]]] = {}
    credits_used: int = 1
    remaining_credits: int


class BrandTrackRequest(BaseModel):
    brand_name: str
    domain: Optional[str] = None
    platforms: List[Platform] = [Platform.META]
    check_interval_hours: int = 24


class BrandTrackResponse(BaseModel):
    brand_id: str
    brand_name: str
    status: str
    ad_count: int = 0
    winner_count: int = 0
    last_checked: Optional[datetime] = None
    next_check: Optional[datetime] = None


class EnrichmentRequest(BaseModel):
    ad_id: str
    video_url: Optional[str] = None
    force_refresh: bool = False


class EnrichmentResponse(BaseModel):
    ad_id: str
    transcription: Optional[str] = None
    hook_analysis: Optional[Dict[str, Any]] = None
    emotional_drivers: List[str] = []
    visual_analysis: Optional[Dict[str, Any]] = None
    winning_patterns: List[str] = []
    winner_score: int
    credits_used: int = 5


class CreditBalance(BaseModel):
    total_credits: int
    used_credits: int
    remaining_credits: int
    reset_date: datetime
    plan: str


class ApiKeyInfo(BaseModel):
    key_id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    credits_used: int = 0


# =============================================================================
# Credit System
# =============================================================================

class CreditManager:
    """Manages API credits for users"""

    # Credit costs per operation
    COSTS = {
        "search": 1,
        "search_export": 5,
        "enrich": 5,
        "enrich_batch": 3,  # per ad when batching
        "brand_track": 10,  # per brand per day
        "download_video": 2,
        "similar_search": 2,
    }

    def __init__(self):
        self._balances: Dict[str, Dict] = {}  # In-memory for now, use Redis in prod

    async def check_credits(self, api_key: str, operation: str, count: int = 1) -> bool:
        """Check if user has enough credits"""
        balance = await self.get_balance(api_key)
        cost = self.COSTS.get(operation, 1) * count
        return balance["remaining_credits"] >= cost

    async def use_credits(self, api_key: str, operation: str, count: int = 1) -> int:
        """Deduct credits and return amount used"""
        cost = self.COSTS.get(operation, 1) * count
        if api_key not in self._balances:
            self._balances[api_key] = self._default_balance()

        self._balances[api_key]["used_credits"] += cost
        return cost

    async def get_balance(self, api_key: str) -> Dict:
        """Get credit balance for API key"""
        if api_key not in self._balances:
            self._balances[api_key] = self._default_balance()
        return self._balances[api_key]

    def _default_balance(self) -> Dict:
        return {
            "total_credits": 10000,
            "used_credits": 0,
            "remaining_credits": 10000,
            "reset_date": datetime.now() + timedelta(days=30),
            "plan": "starter",
        }


credit_manager = CreditManager()


# =============================================================================
# Dependencies
# =============================================================================

async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate API key and return it"""
    api_key = credentials.credentials

    # In production, validate against database
    # For demo/dev, accept "demo-key" or any key >= 5 chars
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # Allow demo key for development
    if api_key in ("demo-key", "test-key", "dev-key"):
        return api_key

    # Require minimum length for real keys
    if len(api_key) < 5:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


# Global search engine instance (initialized on startup)
_search_engine: Optional[AdSearchEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize search engine on startup"""
    global _search_engine
    config = SearchConfig.from_env()
    _search_engine = AdSearchEngine(config)
    try:
        await _search_engine.initialize()
        logger.info("Search engine initialized")
    except Exception as e:
        logger.warning(f"Search engine init failed (may not be running): {e}")


async def get_search_engine() -> AdSearchEngine:
    """Get search engine instance"""
    if _search_engine is None:
        config = SearchConfig.from_env()
        engine = AdSearchEngine(config)
        return engine
    return _search_engine


async def get_enrichment_pipeline() -> AdEnrichmentPipeline:
    """Get enrichment pipeline instance"""
    pipeline = AdEnrichmentPipeline()
    return pipeline


# =============================================================================
# Discovery API - Search Ads
# =============================================================================

@app.post("/api/v1/discovery/search", response_model=SearchResponseModel)
async def search_ads(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """
    Search the ad library with filters

    Credits: 1 per search
    """
    # Check credits
    if not await credit_manager.check_credits(api_key, "search"):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Build filters
    filters = {}
    if request.platform and request.platform != Platform.ALL:
        filters["platform"] = request.platform.value
    if request.format and request.format != AdFormat.ALL:
        filters["format"] = request.format.value
    if request.industry:
        filters["industry"] = request.industry
    if request.emotion:
        filters["primary_emotion"] = request.emotion
    if request.hook_type:
        filters["hook_type"] = request.hook_type
    if request.min_running_days > 0:
        filters["running_duration_days"] = f">={request.min_running_days}"
    if request.winners_only:
        filters["is_winner"] = True
    if request.brand_name:
        filters["brand_name"] = request.brand_name

    # Execute search
    result = await engine.search(
        query=request.query,
        filters=filters,
        sort_by=request.sort_by.value,
        page=request.page,
        per_page=request.per_page,
    )

    # Use credits
    credits_used = await credit_manager.use_credits(api_key, "search")
    balance = await credit_manager.get_balance(api_key)

    # Convert to response
    hits = [
        AdResponse(
            ad_id=h.document.ad_id,
            brand_name=h.document.brand_name,
            platform=h.document.platform,
            format=h.document.format,
            headline=h.document.headline,
            transcription=h.document.transcription,
            thumbnail_url=h.document.thumbnail_url,
            video_url=h.document.video_url,
            industry=h.document.industry,
            primary_emotion=h.document.primary_emotion,
            hook_type=h.document.hook_type,
            running_duration_days=h.document.running_duration_days,
            is_winner=h.document.is_winner,
            winner_score=h.document.winner_score,
            first_seen=datetime.fromtimestamp(h.document.first_seen),
            last_seen=datetime.fromtimestamp(h.document.last_seen),
        )
        for h in result.hits
    ]

    return SearchResponseModel(
        hits=hits,
        total=result.found,
        page=result.page,
        per_page=result.per_page,
        facets={k: [{"value": f.value, "count": f.count} for f in v] for k, v in result.facets.items()},
        credits_used=credits_used,
        remaining_credits=balance["remaining_credits"],
    )


@app.get("/api/v1/discovery/winners")
async def get_winners(
    industry: Optional[str] = None,
    platform: Optional[Platform] = None,
    min_days: int = 30,
    page: int = 1,
    per_page: int = 20,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """
    Get winning ads (running 30+ days)

    Credits: 1 per search
    """
    if not await credit_manager.check_credits(api_key, "search"):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    result = await engine.search_winners(
        industry=industry,
        platform=platform.value if platform else None,
        min_days=min_days,
        page=page,
        per_page=per_page,
    )

    await credit_manager.use_credits(api_key, "search")
    balance = await credit_manager.get_balance(api_key)

    return {
        "winners": [
            {
                "ad_id": h.document.ad_id,
                "brand_name": h.document.brand_name,
                "running_days": h.document.running_duration_days,
                "winner_score": h.document.winner_score,
                "thumbnail_url": h.document.thumbnail_url,
            }
            for h in result.hits
        ],
        "total": result.found,
        "remaining_credits": balance["remaining_credits"],
    }


@app.get("/api/v1/discovery/similar/{ad_id}")
async def find_similar(
    ad_id: str,
    limit: int = 10,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """
    Find ads similar to a given ad

    Credits: 2 per search
    """
    if not await credit_manager.check_credits(api_key, "similar_search"):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    result = await engine.search_similar(ad_id, limit)

    await credit_manager.use_credits(api_key, "similar_search")
    balance = await credit_manager.get_balance(api_key)

    return {
        "similar_ads": [
            {
                "ad_id": h.document.ad_id,
                "brand_name": h.document.brand_name,
                "similarity_score": h.score,
            }
            for h in result.hits
        ],
        "remaining_credits": balance["remaining_credits"],
    }


@app.get("/api/v1/discovery/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = 10,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """
    Get autocomplete suggestions

    Credits: 0 (free)
    """
    suggestions = await engine.get_suggestions(q, limit)
    return {"suggestions": suggestions}


# =============================================================================
# Spyder API - Brand Tracking
# =============================================================================

# In-memory store for demo (use Redis/DB in production)
tracked_brands: Dict[str, Dict] = {}


@app.post("/api/v1/spyder/track", response_model=BrandTrackResponse)
async def track_brand(
    request: BrandTrackRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """
    Start tracking a brand's ads

    Credits: 10 per brand per day
    """
    if not await credit_manager.check_credits(api_key, "brand_track"):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    brand_id = hashlib.md5(request.brand_name.lower().encode()).hexdigest()[:12]

    # Check if already tracking
    if brand_id in tracked_brands:
        return BrandTrackResponse(
            brand_id=brand_id,
            brand_name=request.brand_name,
            status="already_tracking",
            ad_count=tracked_brands[brand_id].get("ad_count", 0),
            winner_count=tracked_brands[brand_id].get("winner_count", 0),
            last_checked=tracked_brands[brand_id].get("last_checked"),
            next_check=tracked_brands[brand_id].get("next_check"),
        )

    # Start tracking
    tracked_brands[brand_id] = {
        "brand_name": request.brand_name,
        "domain": request.domain,
        "platforms": [p.value for p in request.platforms],
        "interval_hours": request.check_interval_hours,
        "ad_count": 0,
        "winner_count": 0,
        "last_checked": None,
        "next_check": datetime.now(),
        "status": "pending",
    }

    # Queue background scrape
    background_tasks.add_task(scrape_brand_ads, brand_id, request.brand_name)

    await credit_manager.use_credits(api_key, "brand_track")

    return BrandTrackResponse(
        brand_id=brand_id,
        brand_name=request.brand_name,
        status="tracking_started",
        next_check=datetime.now(),
    )


@app.get("/api/v1/spyder/brands")
async def list_tracked_brands(
    api_key: str = Depends(get_api_key),
):
    """List all tracked brands"""
    return {
        "brands": [
            BrandTrackResponse(
                brand_id=bid,
                brand_name=data["brand_name"],
                status=data["status"],
                ad_count=data["ad_count"],
                winner_count=data["winner_count"],
                last_checked=data["last_checked"],
                next_check=data["next_check"],
            )
            for bid, data in tracked_brands.items()
        ]
    }


@app.get("/api/v1/spyder/brand/{brand_id}/ads")
async def get_brand_ads(
    brand_id: str,
    page: int = 1,
    per_page: int = 20,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get all ads from a tracked brand"""
    if brand_id not in tracked_brands:
        raise HTTPException(status_code=404, detail="Brand not tracked")

    brand_name = tracked_brands[brand_id]["brand_name"]
    result = await engine.search(
        query="*",
        filters={"brand_name": brand_name},
        sort_by="running_duration_days:desc",
        page=page,
        per_page=per_page,
    )

    return {
        "brand_name": brand_name,
        "ads": [
            {
                "ad_id": h.document.ad_id,
                "headline": h.document.headline,
                "running_days": h.document.running_duration_days,
                "is_winner": h.document.is_winner,
            }
            for h in result.hits
        ],
        "total": result.found,
    }


@app.delete("/api/v1/spyder/brand/{brand_id}")
async def untrack_brand(
    brand_id: str,
    api_key: str = Depends(get_api_key),
):
    """Stop tracking a brand"""
    if brand_id in tracked_brands:
        del tracked_brands[brand_id]
        return {"status": "untracked"}
    raise HTTPException(status_code=404, detail="Brand not found")


async def scrape_brand_ads(brand_id: str, brand_name: str):
    """Background task to scrape brand ads"""
    try:
        # Use our scraper
        scraper = MetaAdLibraryScraper()
        ads = await scraper.scrape_brand_page(brand_name, max_ads=50)

        if brand_id in tracked_brands:
            tracked_brands[brand_id]["ad_count"] = len(ads)
            tracked_brands[brand_id]["winner_count"] = sum(1 for a in ads if a.running_duration_days >= 30)
            tracked_brands[brand_id]["last_checked"] = datetime.now()
            tracked_brands[brand_id]["next_check"] = datetime.now() + timedelta(
                hours=tracked_brands[brand_id]["interval_hours"]
            )
            tracked_brands[brand_id]["status"] = "active"

        # Index ads
        engine = AdSearchEngine(SearchConfig.from_env())
        for ad in ads:
            doc = AdDocument.from_enriched_ad(to_foreplay_format(ad))
            await engine.index_ad(doc)

        logger.info(f"Scraped {len(ads)} ads for brand {brand_name}")

    except Exception as e:
        logger.error(f"Failed to scrape brand {brand_name}: {e}")
        if brand_id in tracked_brands:
            tracked_brands[brand_id]["status"] = f"error: {str(e)}"


# =============================================================================
# Enrichment API - AI Analysis
# =============================================================================

@app.post("/api/v1/enrich", response_model=EnrichmentResponse)
async def enrich_ad(
    request: EnrichmentRequest,
    api_key: str = Depends(get_api_key),
    pipeline: AdEnrichmentPipeline = Depends(get_enrichment_pipeline),
):
    """
    Enrich an ad with AI analysis

    Credits: 5 per ad
    """
    if not await credit_manager.check_credits(api_key, "enrich"):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    try:
        # Run enrichment
        enriched = await pipeline.enrich(
            ad_id=request.ad_id,
            video_url=request.video_url,
        )

        await credit_manager.use_credits(api_key, "enrich")

        return EnrichmentResponse(
            ad_id=request.ad_id,
            transcription=enriched.transcription.full_text if enriched.transcription else None,
            hook_analysis=enriched.hook_analysis.to_dict() if enriched.hook_analysis else None,
            emotional_drivers=enriched.emotional_drivers,
            visual_analysis=enriched.visual_analysis.to_dict() if enriched.visual_analysis else None,
            winning_patterns=enriched.winning_patterns,
            winner_score=enriched.winner_score,
            credits_used=5,
        )

    except Exception as e:
        logger.error(f"Enrichment failed for {request.ad_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/enrich/batch")
async def enrich_batch(
    ad_ids: List[str],
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
):
    """
    Queue batch enrichment

    Credits: 3 per ad (bulk discount)
    """
    total_cost = len(ad_ids) * 3
    if not await credit_manager.check_credits(api_key, "enrich_batch", count=len(ad_ids)):
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Queue for background processing
    job_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]

    background_tasks.add_task(process_batch_enrichment, job_id, ad_ids)

    await credit_manager.use_credits(api_key, "enrich_batch", count=len(ad_ids))

    return {
        "job_id": job_id,
        "ad_count": len(ad_ids),
        "status": "queued",
        "credits_used": total_cost,
    }


async def process_batch_enrichment(job_id: str, ad_ids: List[str]):
    """Background batch enrichment"""
    pipeline = AdEnrichmentPipeline()
    for ad_id in ad_ids:
        try:
            await pipeline.enrich(ad_id=ad_id)
        except Exception as e:
            logger.error(f"Batch enrich failed for {ad_id}: {e}")


# =============================================================================
# Analytics API
# =============================================================================

@app.get("/api/v1/analytics/trends")
async def get_trends(
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get industry-wide trends from winning ads"""
    trends = await engine.get_industry_trends()
    return trends


@app.get("/api/v1/analytics/brand/{brand_name}")
async def get_brand_analytics(
    brand_name: str,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get analytics for a specific brand"""
    analytics = await engine.get_brand_analytics(brand_name)
    if not analytics:
        raise HTTPException(status_code=404, detail="Brand not found")
    return analytics


@app.get("/api/v1/analytics/emotions")
async def get_emotion_breakdown(
    industry: Optional[str] = None,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get emotional driver breakdown"""
    filters = {"is_winner": True}
    if industry:
        filters["industry"] = industry

    result = await engine.search(
        query="*",
        filters=filters,
        facet_by=["primary_emotion", "emotional_drivers"],
        per_page=0,
    )

    return {
        "primary_emotions": result.facets.get("primary_emotion", []),
        "emotional_drivers": result.facets.get("emotional_drivers", []),
    }


@app.get("/api/v1/analytics/hooks")
async def get_hook_patterns(
    industry: Optional[str] = None,
    api_key: str = Depends(get_api_key),
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get winning hook patterns"""
    filters = {"is_winner": True}
    if industry:
        filters["industry"] = industry

    result = await engine.search(
        query="*",
        filters=filters,
        facet_by=["hook_type", "winning_patterns"],
        per_page=0,
    )

    return {
        "hook_types": result.facets.get("hook_type", []),
        "winning_patterns": result.facets.get("winning_patterns", []),
    }


# =============================================================================
# Account API
# =============================================================================

@app.get("/api/v1/account/credits", response_model=CreditBalance)
async def get_credits(
    api_key: str = Depends(get_api_key),
):
    """Get current credit balance"""
    balance = await credit_manager.get_balance(api_key)
    return CreditBalance(
        total_credits=balance["total_credits"],
        used_credits=balance["used_credits"],
        remaining_credits=balance["remaining_credits"] - balance["used_credits"],
        reset_date=balance["reset_date"],
        plan=balance["plan"],
    )


@app.get("/api/v1/account/usage")
async def get_usage(
    api_key: str = Depends(get_api_key),
):
    """Get usage breakdown"""
    # In production, track by operation type
    return {
        "period_start": datetime.now() - timedelta(days=30),
        "period_end": datetime.now(),
        "operations": {
            "searches": 0,
            "enrichments": 0,
            "brand_tracks": 0,
            "similar_searches": 0,
        },
    }


# =============================================================================
# System
# =============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/stats")
async def get_stats(
    engine: AdSearchEngine = Depends(get_search_engine),
):
    """Get system statistics"""
    stats = await engine.get_stats()
    return {
        "total_ads_indexed": stats.get("total_ads", 0),
        "tracked_brands": len(tracked_brands),
        "active_scrapers": 1,
    }


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "adintel_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
