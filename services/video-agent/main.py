from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
import time
import os
import subprocess
import json

app = FastAPI(title="Video Agent API")

# In-memory job store
jobs: Dict[str, dict] = {}

class StoryboardClip(BaseModel):
    clipId: str
    duration: float
    transition: Optional[str] = None
    effects: Optional[List[str]] = None

class RemixRequest(BaseModel):
    storyboard: List[StoryboardClip]
    assetMap: Dict[str, str]
    outputFormat: Optional[str] = "mp4"
    overlays: Optional[Dict[str, str]] = None

class RenderJob(BaseModel):
    jobId: str
    status: str
    progress: float
    outputUrl: Optional[str] = None
    error: Optional[str] = None
    createdAt: str
    completedAt: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "video-agent"}

@app.post("/render/remix")
async def create_remix(request: RemixRequest):
    """Create a new video remix job"""
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "jobId": job_id,
        "status": "pending",
        "progress": 0.0,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "request": request.dict()
    }
    
    # Start async processing (in production, use background tasks or queue)
    # For now, we'll simulate processing
    try:
        output_path = render_storyboard_video(job_id, request)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100.0
        jobs[job_id]["outputUrl"] = f"/outputs/{job_id}.mp4"
        jobs[job_id]["completedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    
    return {
        "jobId": job_id,
        "status": jobs[job_id]["status"]
    }

@app.get("/render/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get render job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return RenderJob(**job)

def render_storyboard_video(job_id: str, request: RemixRequest) -> str:
    """
    Render video from storyboard using FFmpeg
    TODO: Implement actual video concatenation and effects
    """
    output_dir = "/app/outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{job_id}.mp4")
    
    # Update job status
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["progress"] = 10.0
    
    # TODO: Actual FFmpeg pipeline
    # For now, create a simple placeholder video or use first asset
    # In production: concat clips, apply transitions, add overlays
    
    # Check if we have assets to work with
    if not request.assetMap:
        # Create a dummy video file for testing
        create_dummy_video(output_path)
    else:
        # TODO: Implement actual video processing
        # 1. Extract clips from assets based on storyboard
        # 2. Apply transitions
        # 3. Add overlays (CTA, logo)
        # 4. Concatenate into final video
        
        # For now, just copy first asset if available
        first_asset = list(request.assetMap.values())[0] if request.assetMap else None
        if first_asset and os.path.exists(first_asset):
            # Simple copy for now
            subprocess.run(["cp", first_asset, output_path], check=True)
        else:
            create_dummy_video(output_path)
    
    # Add overlays if requested
    if request.overlays and request.overlays.get("cta"):
        apply_cta_overlay(output_path, request.overlays["cta"])
    
    jobs[job_id]["progress"] = 90.0
    
    return output_path

def create_dummy_video(output_path: str):
    """Create a simple test video using FFmpeg"""
    # Create a 10-second test pattern video
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=10:size=1080x1920:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
        "-pix_fmt", "yuv420p", "-y", output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    except Exception as e:
        print(f"FFmpeg error creating dummy video: {e}")
        # Fallback: create an empty file
        with open(output_path, 'w') as f:
            f.write("placeholder video")

def apply_cta_overlay(video_path: str, cta_text: str):
    """
    Apply CTA text overlay to last 3 seconds of video
    TODO: Implement actual FFmpeg text overlay
    """
    # Placeholder for CTA overlay logic
    # In production: use FFmpeg drawtext filter
    pass

def check_compliance(video_path: str, platform: str = "meta_feed") -> dict:
    """
    Check video compliance using ffprobe
    TODO: Implement full compliance checking against platform specs
    """
    try:
        # Get video metadata using ffprobe
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        metadata = json.loads(result.stdout)
        
        # Extract video properties
        video_stream = next((s for s in metadata.get("streams", []) if s["codec_type"] == "video"), None)
        
        if not video_stream:
            return {"compliant": False, "reason": "No video stream found"}
        
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(metadata.get("format", {}).get("duration", 0))
        file_size_mb = int(metadata.get("format", {}).get("size", 0)) / (1024 * 1024)
        
        # Calculate aspect ratio
        aspect_ratio = f"{width}:{height}"
        
        # TODO: Check against platform_specs from weights.yaml
        # For now, basic checks
        compliance = {
            "compliant": True,
            "resolution": f"{width}x{height}",
            "aspectRatio": aspect_ratio,
            "duration": duration,
            "fileSizeMB": file_size_mb,
            "issues": []
        }
        
        # Basic validation
        if width < 1080 or height < 1080:
            compliance["issues"].append("Resolution below minimum")
        if duration < 3:
            compliance["issues"].append("Duration too short")
        if duration > 90:
            compliance["issues"].append("Duration too long")
        
        compliance["compliant"] = len(compliance["issues"]) == 0
        
        return compliance
    except Exception as e:
        return {"compliant": False, "error": str(e)}

@app.get("/compliance/check")
async def check_video_compliance(video_url: str, platform: str = "meta_feed"):
    """Check video compliance for platform"""
    # TODO: Download video from URL if needed
    # For now, assume local path
    compliance = check_compliance(video_url, platform)
    return compliance
