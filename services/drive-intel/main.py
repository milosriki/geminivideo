from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import subprocess
import uuid

app = FastAPI(title="Drive Intel API")

# In-memory asset store
assets_db: dict = {}
clips_db: dict = {}

class Asset(BaseModel):
    id: str
    filename: str
    duration: float
    resolution: str
    aspectRatio: str
    fileSize: int
    path: str
    thumbnail: Optional[str] = None
    tags: List[str] = []

class Clip(BaseModel):
    id: str
    assetId: str
    startTime: float
    endTime: float
    duration: float
    tags: List[str] = []
    sceneType: Optional[str] = None
    objects: Optional[List[str]] = None
    transcript: Optional[str] = None

class IngestRequest(BaseModel):
    source: str = "local"
    folderId: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "drive-intel"}

@app.post("/ingest/scan")
async def ingest_scan(request: IngestRequest):
    """Scan and ingest videos from local folder or Google Drive"""
    if request.source == "local":
        # Scan local data/input directory
        input_dir = "/app/data/input"
        ingested_assets = scan_local_folder(input_dir)
        
        return {
            "assets": ingested_assets,
            "message": f"Scanned {len(ingested_assets)} assets from local folder"
        }
    elif request.source == "drive":
        # TODO: Implement Google Drive integration
        return {
            "assets": [],
            "message": "Google Drive integration not yet implemented"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid source")

@app.get("/assets")
async def get_assets():
    """Get all ingested assets"""
    return list(assets_db.values())

@app.get("/assets/{asset_id}/clips")
async def get_asset_clips(asset_id: str):
    """Get clips for a specific asset"""
    if asset_id not in assets_db:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Return clips for this asset
    asset_clips = [clip for clip in clips_db.values() if clip["assetId"] == asset_id]
    return asset_clips

def scan_local_folder(folder_path: str) -> List[dict]:
    """
    Scan local folder for video files and create asset entries
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return []
    
    ingested = []
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Check if it's a video file
        if not os.path.isfile(file_path):
            continue
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in video_extensions:
            continue
        
        # Get video metadata
        try:
            metadata = get_video_metadata(file_path)
            
            asset_id = str(uuid.uuid4())
            asset = {
                "id": asset_id,
                "filename": filename,
                "duration": metadata["duration"],
                "resolution": metadata["resolution"],
                "aspectRatio": metadata["aspectRatio"],
                "fileSize": metadata["fileSize"],
                "path": file_path,
                "thumbnail": None,  # TODO: Generate thumbnail
                "tags": []  # TODO: Add intelligent tagging
            }
            
            assets_db[asset_id] = asset
            ingested.append(asset)
            
            # Create a basic single clip for the entire video
            # TODO: Implement scene detection for multiple clips
            create_basic_clip(asset_id, metadata["duration"])
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    return ingested

def get_video_metadata(video_path: str) -> dict:
    """Extract video metadata using ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        metadata = json.loads(result.stdout)
        
        # Extract video stream info
        video_stream = next((s for s in metadata.get("streams", []) if s["codec_type"] == "video"), None)
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(metadata.get("format", {}).get("duration", 0))
        file_size = int(metadata.get("format", {}).get("size", 0))
        
        # Calculate aspect ratio
        from math import gcd
        ratio_gcd = gcd(width, height)
        aspect_w = width // ratio_gcd
        aspect_h = height // ratio_gcd
        aspect_ratio = f"{aspect_w}:{aspect_h}"
        
        return {
            "duration": duration,
            "resolution": f"{width}x{height}",
            "aspectRatio": aspect_ratio,
            "fileSize": file_size,
            "width": width,
            "height": height
        }
    except Exception as e:
        print(f"Error getting metadata: {e}")
        # Return defaults
        return {
            "duration": 10.0,
            "resolution": "1920x1080",
            "aspectRatio": "16:9",
            "fileSize": 0,
            "width": 1920,
            "height": 1080
        }

def create_basic_clip(asset_id: str, duration: float):
    """
    Create a basic clip covering the entire video
    TODO: Implement scene detection to create multiple clips
    TODO: Add OCR for text detection
    TODO: Add object detection
    """
    clip_id = str(uuid.uuid4())
    clip = {
        "id": clip_id,
        "assetId": asset_id,
        "startTime": 0.0,
        "endTime": duration,
        "duration": duration,
        "tags": [],  # TODO: Add intelligent tagging
        "sceneType": None,  # TODO: Scene classification
        "objects": [],  # TODO: Object detection with YOLO
        "transcript": None  # TODO: Speech-to-text transcription
    }
    
    clips_db[clip_id] = clip
    return clip

# TODO: Future endpoints for intelligence features
# - POST /assets/{id}/analyze - Trigger deep analysis (scenes, OCR, objects)
# - GET /assets/{id}/scenes - Get detected scenes
# - GET /assets/{id}/transcript - Get full transcript
# - GET /assets/{id}/objects - Get detected objects with timestamps
