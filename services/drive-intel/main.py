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
with open(f"{config_path}/scene_ranking.yaml", "r") as f:
    ranking_config = yaml.safe_load(f)

# Initialize services
persistence = PersistenceLayer()
ingest_service = IngestService(persistence)
scene_detector = SceneDetectorService()
feature_extractor = FeatureExtractorService()
ranking_service = RankingService(ranking_config)
search_service = SearchService()


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
        "assets_count": len(persistence.assets)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
