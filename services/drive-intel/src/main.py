from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import uuid

app = FastAPI(title="Drive Intel Service", version="1.0.0")

# In-memory storage for development (replace with database in production)
assets_db: Dict[str, Any] = {}
clips_db: Dict[str, List[Any]] = {}


class IngestRequest(BaseModel):
    path: str
    recursive: bool = True
    filters: Optional[Dict[str, Any]] = None


class Asset(BaseModel):
    asset_id: str
    path: str
    filename: str
    size_bytes: int
    duration_seconds: float
    resolution: str
    format: str
    ingested_at: str
    status: str


class Clip(BaseModel):
    clip_id: str
    asset_id: str
    start_time: float
    end_time: float
    duration: float
    scene_score: float
    features: Dict[str, Any]
    thumbnail_url: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "drive-intel",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/ingest/local/folder")
async def ingest_local_folder(request: IngestRequest):
    """
    Ingest video files from local folder
    - Scans directory for video files
    - Extracts metadata
    - Triggers scene detection and feature extraction
    """
    try:
        # Simulate ingestion process
        asset_id = str(uuid.uuid4())
        
        # Mock asset data
        # TODO: [CRITICAL] Replace with real Google Drive / GCS file listing
        # Needs integration with services/google_drive_service.py
        asset = {
            "asset_id": asset_id,
            "path": request.path,
            "filename": request.path.split("/")[-1] or "video.mp4",
            "size_bytes": 10485760,  # 10MB placeholder
            "duration_seconds": 30.0,
            "resolution": "1920x1080",
            "format": "mp4",
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        assets_db[asset_id] = asset
        
        # Trigger background processing
        asyncio.create_task(process_asset(asset_id))
        
        return {
            "asset_id": asset_id,
            "status": "processing",
            "message": f"Ingestion started for {request.path}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/ingest/drive/folder")
async def ingest_drive_folder(request: IngestRequest):
    """
    Ingest video files from Google Drive folder
    - Authenticates with Google Drive API
    - Downloads or streams videos
    - Triggers processing pipeline
    """
    try:
        from src.drive_client import drive_client
        
        # List videos from Drive (real)
        # If request.path is a folder ID, use it, else list root
        folder_id = request.path if "drive.google.com" not in request.path else None
        videos = drive_client.list_videos(folder_id=folder_id)
        
        ingested_ids = []
        for video in videos:
            asset_id = video['asset_id']
            assets_db[asset_id] = video
            assets_db[asset_id]['status'] = 'processing'
            
            # Trigger background processing
            asyncio.create_task(process_asset(asset_id))
            ingested_ids.append(asset_id)
        
        return {
            "status": "processing",
            "message": f"Started ingestion for {len(videos)} videos from Drive",
            "asset_ids": ingested_ids
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive ingestion failed: {str(e)}")


@app.get("/assets")
async def list_assets(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List all ingested assets
    """
    assets = list(assets_db.values())
    
    if status:
        assets = [a for a in assets if a.get("status") == status]
    
    return {
        "assets": assets[:limit],
        "count": len(assets),
        "total": len(assets_db)
    }


@app.get("/assets/{asset_id}/clips")
async def get_asset_clips(
    asset_id: str,
    ranked: bool = Query(False, description="Return ranked clips"),
    top: int = Query(10, ge=1, le=50, description="Number of top clips to return")
):
    """
    Get clips for an asset
    - Returns detected scenes/clips
    - Can return ranked by composite score
    - Supports pagination via 'top' parameter
    """
    if asset_id not in assets_db:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    clips = clips_db.get(asset_id, [])
    
    if ranked:
        # Sort by scene_score descending
        clips = sorted(clips, key=lambda x: x.get("scene_score", 0), reverse=True)
    
    clips = clips[:top]
    
    return {
        "asset_id": asset_id,
        "clips": clips,
        "count": len(clips),
        "ranked": ranked
    }


async def process_asset(asset_id: str):
    """
    Background processing task for asset
    - Scene detection (PySceneDetect placeholder)
    - Feature extraction (motion, YOLO, OCR, embeddings)
    - FAISS indexing
    """
    await asyncio.sleep(2)  # Simulate processing time
    
    # Update asset status
    if asset_id in assets_db:
        assets_db[asset_id]["status"] = "completed"
    
    # Real Scene Detection
    try:
        from src.drive_client import drive_client
        from src.scene_detector import scene_detector
        import tempfile
        import os
        
        asset = assets_db.get(asset_id)
        if not asset:
            return

        # Download file to temp for processing
        # In production, we might stream or use a shared volume
        with tempfile.NamedTemporaryFile(suffix=f".{asset['format']}", delete=False) as tmp_file:
            temp_path = tmp_file.name
            
        # Download if it's a Drive file
        if asset.get('source') == 'google_drive':
            success = drive_client.download_file(asset_id, temp_path)
            if not success:
                logger.error(f"Failed to download asset {asset_id}")
                return
        else:
            # Local file simulation (or copy if path exists)
            pass 

        # Detect Scenes (Real)
        detected_scenes = scene_detector.detect_scenes(temp_path)
        
        # --- FEATURE EXTRACTION (THE EYES) ---
        from src.feature_extractor import get_feature_extractor
        extractor = get_feature_extractor()
        
        final_clips = []
        for scene in detected_scenes:
            scene['asset_id'] = asset_id
            scene['thumbnail_url'] = f"/thumbnails/{asset_id}_{scene['clip_id']}.jpg"
            
            # 1. Detect Objects (YOLO)
            # Sample middle of the scene
            mid_point = (scene['start_time'] + scene['end_time']) / 2
            objects = extractor.detect_objects_at_timestamp(temp_path, mid_point)
            
            # 2. Generate Embeddings (SentenceTransformer)
            # Create a rich description for embedding
            description = f"Scene with {', '.join(objects)}." if objects else "Scene with unknown content."
            embedding = extractor.generate_embedding(description)
            
            # Update features
            if 'features' not in scene:
                scene['features'] = {}
            
            scene['features']['objects_detected'] = objects
            scene['features']['embedding'] = embedding
            scene['features']['description'] = description
            
            final_clips.append(scene)
            
        clips_db[asset_id] = final_clips
        assets_db[asset_id]["status"] = "completed"
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    except Exception as e:
        logger.error(f"Processing failed for {asset_id}: {e}")
        assets_db[asset_id]["status"] = "failed"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
