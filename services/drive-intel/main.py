"""
Drive Intel Service - FastAPI application for video ingestion, scene detection, and ranking.
"""
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
from contextlib import asynccontextmanager

from services.ingestion import IngestionService
from services.scene_detector import SceneDetectorService
from services.feature_extractor import FeatureExtractorService
from services.ranking import RankingService
from services.search import SearchService
from services.storage import StorageService

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
    logger.info("Initializing Drive Intel services...")
    
    # Initialize services
    services["storage"] = StorageService()
    services["ingestion"] = IngestionService(services["storage"])
    services["scene_detector"] = SceneDetectorService()
    services["feature_extractor"] = FeatureExtractorService()
    services["ranking"] = RankingService()
    services["search"] = SearchService()
    
    logger.info("Services initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    services.clear()

app = FastAPI(
    title="Drive Intel Service",
    description="Video ingestion, scene detection, and intelligent ranking",
    version="1.0.0",
    lifespan=lifespan
)

# Request/Response models
class IngestDriveFolderRequest(BaseModel):
    folderId: Optional[str] = Field(None, description="Google Drive folder ID")
    maxFiles: Optional[int] = Field(None, description="Maximum number of files to ingest")

class IngestLocalFolderRequest(BaseModel):
    folderPath: str = Field(..., description="Local folder path")
    maxFiles: Optional[int] = Field(None, description="Maximum number of files to process")

class SearchClipsRequest(BaseModel):
    q: str = Field(..., description="Search query")
    topK: int = Field(10, description="Number of results to return")

class Asset(BaseModel):
    id: str
    name: str
    path: str
    driveFileId: Optional[str] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class Clip(BaseModel):
    id: str
    videoId: str
    start: float
    end: float
    duration: float
    objects: List[str] = []
    ocr_tokens: List[str] = []
    motion_score: float = 0.0
    transcript_excerpt: Optional[str] = None
    embeddingVectorId: Optional[str] = None
    rankScore: float = 0.0
    clusterId: Optional[str] = None

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "drive-intel"}

# Ingestion endpoints
@app.post("/ingest/drive/folder")
async def ingest_drive_folder(request: IngestDriveFolderRequest):
    """Ingest videos from Google Drive folder."""
    try:
        ingestion_service: IngestionService = services["ingestion"]
        result = await ingestion_service.ingest_from_drive(
            folder_id=request.folderId,
            max_files=request.maxFiles
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Drive ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/local/folder")
async def ingest_local_folder(request: IngestLocalFolderRequest):
    """Ingest videos from local folder."""
    try:
        ingestion_service: IngestionService = services["ingestion"]
        result = await ingestion_service.ingest_from_local(
            folder_path=request.folderPath,
            max_files=request.maxFiles
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Local ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Asset endpoints
@app.get("/assets")
async def get_assets() -> List[Asset]:
    """Get all ingested assets."""
    try:
        storage: StorageService = services["storage"]
        assets = storage.get_all_assets()
        return [Asset(**asset) for asset in assets]
    except Exception as e:
        logger.error(f"Failed to get assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assets/{asset_id}/clips")
async def get_asset_clips(
    asset_id: str,
    ranked: bool = Query(False, description="Return ranked clips"),
    top: Optional[int] = Query(None, description="Return top N clips")
) -> List[Clip]:
    """Get clips for an asset."""
    try:
        storage: StorageService = services["storage"]
        
        # Get the asset
        asset = storage.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Get or generate clips
        clips = storage.get_clips(asset_id)
        if not clips:
            # Detect scenes if not already done
            scene_detector: SceneDetectorService = services["scene_detector"]
            feature_extractor: FeatureExtractorService = services["feature_extractor"]
            ranking_service: RankingService = services["ranking"]
            
            # Detect scenes
            scenes = await scene_detector.detect_scenes(asset["path"])
            
            # Extract features for each scene
            enriched_clips = []
            for scene in scenes:
                features = await feature_extractor.extract_features(
                    asset["path"],
                    scene["start"],
                    scene["end"]
                )
                clip = {
                    "id": f"{asset_id}_clip_{len(enriched_clips)}",
                    "videoId": asset_id,
                    **scene,
                    **features
                }
                enriched_clips.append(clip)
            
            # Rank clips
            ranked_clips = ranking_service.rank_clips(enriched_clips)
            
            # Store clips
            storage.store_clips(asset_id, ranked_clips)
            clips = ranked_clips
        
        # Filter and sort
        if ranked:
            clips = sorted(clips, key=lambda c: c.get("rankScore", 0), reverse=True)
        
        if top:
            clips = clips[:top]
        
        return [Clip(**clip) for clip in clips]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get clips: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoint
@app.post("/search/clips")
async def search_clips(request: SearchClipsRequest) -> List[Clip]:
    """Search clips using semantic search."""
    try:
        search_service: SearchService = services["search"]
        results = await search_service.search(request.q, request.topK)
        return [Clip(**clip) for clip in results]
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Config endpoint
@app.get("/config/ranking")
async def get_ranking_config():
    """Get ranking configuration."""
    try:
        ranking_service: RankingService = services["ranking"]
        return ranking_service.get_config()
    except Exception as e:
        logger.error(f"Failed to get config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
