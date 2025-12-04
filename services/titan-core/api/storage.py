"""
Video Storage Service
- Upload videos to GCS or local storage
- Generate signed URLs for secure downloads
- Manage video lifecycle (cleanup old files)
"""

import os
import uuid
import logging
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict
from datetime import timedelta, datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
    "video/x-flv",
    "video/3gpp",
}

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".3gp",
}


# Pydantic Models
class VideoInfo(BaseModel):
    """Video information response"""
    video_id: str
    filename: str
    size: int
    storage_path: str
    storage_type: str
    upload_time: str
    url: Optional[str] = None


class SignedUrlResponse(BaseModel):
    """Signed URL response"""
    video_id: str
    url: str
    expires_in: int


class DeleteResponse(BaseModel):
    """Delete response"""
    success: bool
    message: str
    video_id: str


class VideoListResponse(BaseModel):
    """List videos response"""
    videos: List[VideoInfo]
    total: int
    storage_type: str


class VideoStorage:
    """Handle video storage operations with GCS and local fallback"""

    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET", "geminivideo-renders")
        self.local_path = os.getenv("LOCAL_STORAGE_PATH", "/tmp/geminivideo")
        self.use_gcs = os.getenv("USE_GCS", "false").lower() == "true"

        # Initialize GCS if enabled
        if self.use_gcs:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"✅ GCS initialized with bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"⚠️ GCS initialization failed: {e}. Falling back to local storage.")
                self.use_gcs = False

        # Ensure local storage directory exists
        if not self.use_gcs:
            Path(self.local_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Using local storage at: {self.local_path}")

    def _validate_video_file(self, file: UploadFile) -> None:
        """Validate video file type and size"""
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
            )

        # Check content type if provided
        if file.content_type and file.content_type not in ALLOWED_VIDEO_TYPES:
            # Try to guess content type from filename
            guessed_type, _ = mimetypes.guess_type(file.filename)
            if guessed_type not in ALLOWED_VIDEO_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content type: {file.content_type}. Allowed video types only."
                )

    async def upload_video(self, file: UploadFile, folder: str = "uploads") -> VideoInfo:
        """
        Upload video and return storage info

        Args:
            file: Video file to upload
            folder: Folder/prefix for organization

        Returns:
            VideoInfo with storage details
        """
        # Validate file
        self._validate_video_file(file)

        # Generate unique video ID
        video_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        blob_name = f"{folder}/{video_id}{file_ext}"

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )

        try:
            if self.use_gcs:
                # Upload to GCS
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(
                    content,
                    content_type=file.content_type or "video/mp4"
                )
                logger.info(f"✅ Uploaded to GCS: {blob_name} ({file_size} bytes)")
                storage_type = "gcs"
                storage_path = f"gs://{self.bucket_name}/{blob_name}"
            else:
                # Upload to local storage
                local_file_path = Path(self.local_path) / folder / f"{video_id}{file_ext}"
                local_file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(local_file_path, "wb") as f:
                    f.write(content)

                logger.info(f"✅ Uploaded to local: {local_file_path} ({file_size} bytes)")
                storage_type = "local"
                storage_path = str(local_file_path)

            return VideoInfo(
                video_id=video_id,
                filename=file.filename,
                size=file_size,
                storage_path=storage_path,
                storage_type=storage_type,
                upload_time=datetime.utcnow().isoformat()
            )

        except GoogleCloudError as e:
            logger.error(f"❌ GCS upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def upload_rendered(self, local_path: str, job_id: str) -> VideoInfo:
        """
        Upload rendered video from local path to GCS

        Args:
            local_path: Path to the rendered video file
            job_id: Job ID for tracking

        Returns:
            VideoInfo with storage details
        """
        local_file = Path(local_path)

        if not local_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {local_path}"
            )

        file_size = local_file.stat().st_size
        file_ext = local_file.suffix
        blob_name = f"renders/{job_id}{file_ext}"

        try:
            if self.use_gcs:
                # Upload to GCS
                blob = self.bucket.blob(blob_name)

                # Determine content type
                content_type, _ = mimetypes.guess_type(local_path)
                if not content_type or not content_type.startswith("video/"):
                    content_type = "video/mp4"

                blob.upload_from_filename(local_path, content_type=content_type)
                logger.info(f"✅ Uploaded rendered video to GCS: {blob_name} ({file_size} bytes)")
                storage_type = "gcs"
                storage_path = f"gs://{self.bucket_name}/{blob_name}"
            else:
                # Keep in local storage (already there)
                storage_type = "local"
                storage_path = local_path
                logger.info(f"✅ Rendered video in local storage: {local_path}")

            return VideoInfo(
                video_id=job_id,
                filename=local_file.name,
                size=file_size,
                storage_path=storage_path,
                storage_type=storage_type,
                upload_time=datetime.utcnow().isoformat()
            )

        except GoogleCloudError as e:
            logger.error(f"❌ GCS upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def get_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> str:
        """
        Generate signed URL for secure download

        Args:
            blob_name: Name/path of the blob in storage
            expiration_minutes: URL validity period in minutes

        Returns:
            Signed URL string
        """
        if not self.use_gcs:
            # For local storage, return file path (in production, serve via HTTP)
            local_file = Path(self.local_path) / blob_name
            if not local_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Video not found: {blob_name}"
                )
            return f"file://{local_file}"

        try:
            blob = self.bucket.blob(blob_name)

            # Check if blob exists
            if not blob.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Video not found: {blob_name}"
                )

            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )

            logger.info(f"✅ Generated signed URL for: {blob_name} (expires in {expiration_minutes}m)")
            return url

        except GoogleCloudError as e:
            logger.error(f"❌ Failed to generate signed URL: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to generate signed URL: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}"
            )

    async def delete_video(self, blob_name: str) -> bool:
        """
        Delete video from storage

        Args:
            blob_name: Name/path of the blob to delete

        Returns:
            True if deleted successfully
        """
        try:
            if self.use_gcs:
                blob = self.bucket.blob(blob_name)

                if not blob.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Video not found: {blob_name}"
                    )

                blob.delete()
                logger.info(f"✅ Deleted from GCS: {blob_name}")
            else:
                local_file = Path(self.local_path) / blob_name

                if not local_file.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Video not found: {blob_name}"
                    )

                local_file.unlink()
                logger.info(f"✅ Deleted from local: {local_file}")

            return True

        except GoogleCloudError as e:
            logger.error(f"❌ Failed to delete video: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete video: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to delete video: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete video: {str(e)}"
            )

    async def list_videos(self, prefix: str = "", limit: int = 100) -> VideoListResponse:
        """
        List videos in storage

        Args:
            prefix: Filter by prefix/folder
            limit: Maximum number of videos to return

        Returns:
            VideoListResponse with list of videos
        """
        videos = []

        try:
            if self.use_gcs:
                # List blobs from GCS
                blobs = self.bucket.list_blobs(prefix=prefix, max_results=limit)

                for blob in blobs:
                    # Skip directories
                    if blob.name.endswith("/"):
                        continue

                    # Extract video ID from path
                    video_id = Path(blob.name).stem

                    videos.append(VideoInfo(
                        video_id=video_id,
                        filename=Path(blob.name).name,
                        size=blob.size,
                        storage_path=f"gs://{self.bucket_name}/{blob.name}",
                        storage_type="gcs",
                        upload_time=blob.time_created.isoformat() if blob.time_created else ""
                    ))

                logger.info(f"✅ Listed {len(videos)} videos from GCS")
            else:
                # List files from local storage
                search_path = Path(self.local_path)
                if prefix:
                    search_path = search_path / prefix

                if search_path.exists():
                    video_files = []
                    for ext in ALLOWED_VIDEO_EXTENSIONS:
                        video_files.extend(search_path.rglob(f"*{ext}"))

                    # Sort by modification time (newest first) and limit
                    video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    video_files = video_files[:limit]

                    for video_file in video_files:
                        stat = video_file.stat()
                        video_id = video_file.stem

                        videos.append(VideoInfo(
                            video_id=video_id,
                            filename=video_file.name,
                            size=stat.st_size,
                            storage_path=str(video_file),
                            storage_type="local",
                            upload_time=datetime.fromtimestamp(stat.st_mtime).isoformat()
                        ))

                logger.info(f"✅ Listed {len(videos)} videos from local storage")

            return VideoListResponse(
                videos=videos,
                total=len(videos),
                storage_type="gcs" if self.use_gcs else "local"
            )

        except GoogleCloudError as e:
            logger.error(f"❌ Failed to list videos: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list videos: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to list videos: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list videos: {str(e)}"
            )


# Initialize storage service
storage_service = VideoStorage()

# Create FastAPI router
router = APIRouter(prefix="/storage", tags=["storage"])


@router.post("/upload", response_model=VideoInfo)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload"),
    folder: str = Query("uploads", description="Folder to store the video")
):
    """
    Upload a video file

    - **file**: Video file (mp4, mov, avi, etc.)
    - **folder**: Optional folder/prefix for organization

    Returns video information including storage path and video_id
    """
    logger.info(f"📤 Uploading video: {file.filename} to folder: {folder}")
    return await storage_service.upload_video(file, folder)


@router.get("/{video_id}/url", response_model=SignedUrlResponse)
async def get_video_url(
    video_id: str,
    folder: str = Query("uploads", description="Folder where video is stored"),
    expiration: int = Query(60, description="URL expiration time in minutes", ge=1, le=1440)
):
    """
    Get signed download URL for a video

    - **video_id**: UUID of the video
    - **folder**: Folder where the video is stored
    - **expiration**: URL validity period (1-1440 minutes)

    Returns a signed URL for secure video download
    """
    logger.info(f"🔗 Generating signed URL for: {video_id}")

    # Find the blob by searching for video_id in the folder
    # This assumes video_id is the filename without extension
    # We need to find the actual file with extension

    try:
        if storage_service.use_gcs:
            # List blobs with prefix
            blobs = list(storage_service.bucket.list_blobs(prefix=f"{folder}/{video_id}"))
            if not blobs:
                raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")
            blob_name = blobs[0].name
        else:
            # Search local storage
            search_path = Path(storage_service.local_path) / folder
            video_files = []
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                matches = list(search_path.glob(f"{video_id}{ext}"))
                if matches:
                    video_files.extend(matches)

            if not video_files:
                raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

            blob_name = str(video_files[0].relative_to(storage_service.local_path))

        url = storage_service.get_signed_url(blob_name, expiration)

        return SignedUrlResponse(
            video_id=video_id,
            url=url,
            expires_in=expiration
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get video URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_id}", response_model=DeleteResponse)
async def delete_video(
    video_id: str,
    folder: str = Query("uploads", description="Folder where video is stored")
):
    """
    Delete a video from storage

    - **video_id**: UUID of the video
    - **folder**: Folder where the video is stored

    Returns success status
    """
    logger.info(f"🗑️ Deleting video: {video_id}")

    try:
        if storage_service.use_gcs:
            # Find the blob
            blobs = list(storage_service.bucket.list_blobs(prefix=f"{folder}/{video_id}"))
            if not blobs:
                raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")
            blob_name = blobs[0].name
        else:
            # Search local storage
            search_path = Path(storage_service.local_path) / folder
            video_files = []
            for ext in ALLOWED_VIDEO_EXTENSIONS:
                matches = list(search_path.glob(f"{video_id}{ext}"))
                if matches:
                    video_files.extend(matches)

            if not video_files:
                raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

            blob_name = str(video_files[0].relative_to(storage_service.local_path))

        success = await storage_service.delete_video(blob_name)

        return DeleteResponse(
            success=success,
            message=f"Video {video_id} deleted successfully",
            video_id=video_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=VideoListResponse)
async def list_videos(
    prefix: str = Query("", description="Filter by folder/prefix"),
    limit: int = Query(100, description="Maximum number of videos to return", ge=1, le=1000)
):
    """
    List all videos in storage

    - **prefix**: Optional filter by folder/prefix
    - **limit**: Maximum number of videos to return (1-1000)

    Returns list of videos with metadata
    """
    logger.info(f"📋 Listing videos with prefix: {prefix or '(all)'}")
    return await storage_service.list_videos(prefix, limit)


@router.get("/health")
async def storage_health():
    """Check storage service health"""
    return {
        "status": "healthy",
        "storage_type": "gcs" if storage_service.use_gcs else "local",
        "bucket": storage_service.bucket_name if storage_service.use_gcs else None,
        "local_path": storage_service.local_path if not storage_service.use_gcs else None
    }
