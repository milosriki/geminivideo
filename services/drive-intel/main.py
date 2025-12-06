"""
Drive Intel Service - Scene Enrichment & Feature Extraction
Handles video ingestion, shot detection, and feature extraction
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
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

# Production safety check - prevent debug mode in production
if app.debug and os.environ.get('ENVIRONMENT') == 'production':
    raise RuntimeError("Debug mode detected in production!")

# Internal API Key Configuration for service-to-service authentication
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "dev-internal-key")
api_key_header = APIKeyHeader(name="X-Internal-API-Key", auto_error=False)

async def verify_internal_api_key(api_key: str = Depends(api_key_header)):
    """Verify internal service-to-service API key"""
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing internal API key")
    if api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid internal API key")
    return api_key

# CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
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
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_internal_api_key)
):
    """
    Ingest videos from Google Drive folder with OAuth 2.0 authentication
    Requires GOOGLE_DRIVE_CREDENTIALS environment variable set to credentials JSON path
    """
    try:
        # Import Google Drive service
        try:
            from services.google_drive_service import GoogleDriveService
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="Google Drive integration not available. Install required packages: "
                       "pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        # Initialize Drive service (will use OAuth token if available)
        try:
            drive_service = GoogleDriveService()
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Google Drive configuration error: {str(e)}. "
                       "Set GOOGLE_DRIVE_CREDENTIALS environment variable."
            )

        # Create temp directory for downloads
        import tempfile
        download_path = tempfile.mkdtemp(prefix='geminivideo_drive_')

        # Ingest videos from folder
        ingested_files = drive_service.ingest_folder(
            folder_id=request.folder_id,
            download_path=download_path,
            max_files=50
        )

        if not ingested_files:
            return {
                "status": "success",
                "folder_id": request.folder_id,
                "videos_ingested": 0,
                "message": "No video files found in folder"
            }

        # Queue each video for analysis
        analysis_jobs = []
        for file_info in ingested_files:
            # Process video through local ingestion pipeline
            if ingest_service:
                asset_id = await ingest_service.ingest_single_video(
                    video_path=file_info['local_path'],
                    filename=file_info['name'],
                    scene_detector=scene_detector,
                    feature_extractor=feature_extractor,
                    search_service=search_service
                )

                analysis_jobs.append({
                    'asset_id': asset_id,
                    'drive_file_id': file_info['file_id'],
                    'name': file_info['name'],
                    'size_mb': file_info['size_bytes'] / 1024 / 1024
                })

        return {
            "status": "success",
            "folder_id": request.folder_id,
            "videos_ingested": len(ingested_files),
            "download_path": download_path,
            "analysis_jobs": analysis_jobs,
            "message": f"Ingested {len(ingested_files)} videos from Google Drive"
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Drive ingestion error: {e}", exc_info=True)
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
