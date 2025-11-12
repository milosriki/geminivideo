"""
Drive Intel Service - Scene Enrichment & Feature Extraction
Handles video ingestion, shot detection, and feature extraction
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
import yaml
from datetime import datetime

from services.ingestion import IngestService
from services.scene_detector import SceneDetectorService
from services.feature_extractor import FeatureExtractorService
from services.ranking import RankingService
from services.search import SearchService
from models.persistence import PersistenceLayer

app = FastAPI(title="Drive Intel Service", version="1.0.0")

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
try:
    with open(f"{config_path}/scene_ranking.yaml", "r") as f:
        ranking_config = yaml.safe_load(f)
        print(f"✅ Loaded config from {config_path}/scene_ranking.yaml")
except (FileNotFoundError, IOError) as e:
    print(f"⚠️  Config file not found at {config_path}/scene_ranking.yaml, using defaults: {e}")
    ranking_config = {
        "weights": {
            "psychology": 0.3,
            "hook": 0.25,
            "technical": 0.2,
            "demographic": 0.15,
            "novelty": 0.1
        }
    }

# Initialize services with error handling
print("🔧 Initializing services...")
try:
    persistence = PersistenceLayer()
    print("✅ Persistence layer initialized")
except Exception as e:
    print(f"⚠️  Persistence layer failed, using in-memory fallback: {e}")
    persistence = None

try:
    ingest_service = IngestService(persistence) if persistence else None
    print("✅ Ingest service initialized")
except Exception as e:
    print(f"⚠️  Ingest service failed: {e}")
    ingest_service = None

try:
    scene_detector = SceneDetectorService()
    print("✅ Scene detector initialized")
except Exception as e:
    print(f"⚠️  Scene detector failed: {e}")
    scene_detector = None

try:
    feature_extractor = FeatureExtractorService()
    print("✅ Feature extractor initialized")
except Exception as e:
    print(f"⚠️  Feature extractor failed: {e}")
    feature_extractor = None

try:
    ranking_service = RankingService(ranking_config)
    print("✅ Ranking service initialized")
except Exception as e:
    print(f"⚠️  Ranking service failed: {e}")
    ranking_service = None

try:
    search_service = SearchService()
    print("✅ Search service initialized")
except Exception as e:
    print(f"⚠️  Search service failed: {e}")
    search_service = None

print("🚀 Drive Intel service ready!")


# Request/Response Models
class IngestDriveFolderRequest(BaseModel):
    folder_id: str
    credentials: Optional[Dict[str, Any]] = None


class IngestLocalFolderRequest(BaseModel):
    folder_path: str


class SearchClipsRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    filter_asset_id: Optional[str] = None


@app.get("/")
async def root():
    return {"service": "drive-intel", "status": "running", "version": "1.0.0"}


@app.post("/ingest/drive/folder")
async def ingest_drive_folder(
    request: IngestDriveFolderRequest,
    background_tasks: BackgroundTasks
):
    """
    Ingest videos from Google Drive folder
    """
    try:
        # For MVP, this is a stub - full Google Drive integration would require OAuth
        return {
            "status": "stub",
            "message": "Google Drive ingestion not yet implemented",
            "folder_id": request.folder_id,
            "note": "Use /ingest/local/folder for local file ingestion"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/local/folder")
async def ingest_local_folder(
    request: IngestLocalFolderRequest,
    background_tasks: BackgroundTasks
):
    """
    Ingest videos from local folder
    Performs shot detection and feature extraction
    """
    try:
        result = await ingest_service.ingest_folder(
            folder_path=request.folder_path,
            scene_detector=scene_detector,
            feature_extractor=feature_extractor,
            search_service=search_service
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets")
async def list_assets(
    skip: int = 0,
    limit: int = 100
):
    """
    List all ingested assets
    """
    try:
        assets = persistence.list_assets(skip=skip, limit=limit)
        return {
            "assets": [asset.dict() for asset in assets],
            "count": len(assets),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/{asset_id}/clips")
async def get_asset_clips(
    asset_id: str,
    ranked: bool = False,
    top: Optional[int] = None
):
    """
    Get clips for a specific asset
    Optionally ranked and filtered to top N
    """
    try:
        asset = persistence.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        clips = asset.clips
        
        if ranked:
            # Apply ranking
            clips = ranking_service.rank_clips(clips)
            
            # Apply clustering to remove duplicates
            clips = ranking_service.cluster_and_deduplicate(clips)
        
        if top and top > 0:
            clips = clips[:top]
        
        return {
            "asset_id": asset_id,
            "clips": [clip.dict() for clip in clips],
            "count": len(clips),
            "ranked": ranked
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/clips")
async def search_clips(request: SearchClipsRequest):
    """
    Semantic search for clips using text query
    """
    try:
        results = search_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_asset_id=request.filter_asset_id
        )
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "assets_count": len(persistence.assets) if persistence else 0,
        "services": {
            "persistence": persistence is not None,
            "ingest": ingest_service is not None,
            "scene_detector": scene_detector is not None,
            "feature_extractor": feature_extractor is not None,
            "ranking": ranking_service is not None,
            "search": search_service is not None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
