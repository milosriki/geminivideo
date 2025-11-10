"""
Ingestion service for downloading and caching videos.
"""
import os
import logging
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class IngestionService:
    """Service for ingesting videos from various sources."""
    
    def __init__(self, storage_service):
        self.storage = storage_service
        self.cache_dir = Path(os.getenv("CACHE_DIR", "/app/data/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Google Drive settings
        self.use_google_drive = os.getenv("USE_GOOGLE_DRIVE", "false").lower() == "true"
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.drive_folder_id = os.getenv("DRIVE_FOLDER_ID")
        self.max_drive_videos = int(os.getenv("MAX_DRIVE_VIDEOS", "500"))
        
        self.drive_service = None
        if self.use_google_drive:
            self._init_drive_service()
        
        logger.info(f"Ingestion service initialized (Google Drive: {self.use_google_drive})")
    
    def _init_drive_service(self):
        """Initialize Google Drive service."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            if not self.credentials_path or not os.path.exists(self.credentials_path):
                logger.warning("Google Drive credentials not found, Drive ingestion disabled")
                self.use_google_drive = False
                return
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.use_google_drive = False
    
    async def ingest_from_drive(
        self,
        folder_id: Optional[str] = None,
        max_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """Ingest videos from Google Drive."""
        if not self.use_google_drive or not self.drive_service:
            raise ValueError("Google Drive ingestion is not enabled")
        
        folder_id = folder_id or self.drive_folder_id
        max_files = max_files or self.max_drive_videos
        
        if not folder_id:
            raise ValueError("No folder ID provided")
        
        logger.info(f"Ingesting from Drive folder: {folder_id} (max: {max_files})")
        
        try:
            # Query for video files in the folder
            query = f"'{folder_id}' in parents and (mimeType contains 'video/')"
            results = self.drive_service.files().list(
                q=query,
                pageSize=max_files,
                fields="files(id, name, size, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} video files in Drive folder")
            
            ingested = []
            for file_info in files:
                try:
                    asset = await self._download_and_cache_drive_file(file_info)
                    self.storage.store_asset(asset)
                    ingested.append(asset)
                except Exception as e:
                    logger.error(f"Failed to ingest {file_info['name']}: {e}")
                    continue
            
            return {
                "total_found": len(files),
                "ingested": len(ingested),
                "assets": [a["id"] for a in ingested]
            }
        except Exception as e:
            logger.error(f"Drive ingestion failed: {e}", exc_info=True)
            raise
    
    async def _download_and_cache_drive_file(self, file_info: Dict) -> Dict[str, Any]:
        """Download a file from Drive and cache it locally."""
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        file_id = file_info['id']
        file_name = file_info['name']
        
        # Check if already cached
        cache_path = self.cache_dir / file_name
        if cache_path.exists():
            logger.debug(f"File already cached: {file_name}")
        else:
            # Download the file
            logger.info(f"Downloading: {file_name}")
            request = self.drive_service.files().get_media(fileId=file_id)
            
            with open(cache_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download {int(status.progress() * 100)}%")
        
        # Create asset record
        asset_id = hashlib.md5(file_id.encode()).hexdigest()
        asset = {
            "id": asset_id,
            "name": file_name,
            "path": str(cache_path),
            "driveFileId": file_id,
            "metadata": {
                "size": file_info.get('size'),
                "mimeType": file_info.get('mimeType')
            }
        }
        
        return asset
    
    async def ingest_from_local(
        self,
        folder_path: str,
        max_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """Ingest videos from local folder."""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder not found: {folder_path}")
        
        logger.info(f"Ingesting from local folder: {folder_path}")
        
        # Find video files
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
        video_files = []
        for ext in video_extensions:
            video_files.extend(folder.glob(f"*{ext}"))
            video_files.extend(folder.glob(f"*{ext.upper()}"))
        
        if max_files:
            video_files = video_files[:max_files]
        
        logger.info(f"Found {len(video_files)} video files")
        
        ingested = []
        for video_path in video_files:
            try:
                # Create asset record
                asset_id = hashlib.md5(str(video_path).encode()).hexdigest()
                asset = {
                    "id": asset_id,
                    "name": video_path.name,
                    "path": str(video_path),
                    "driveFileId": None,
                    "metadata": {
                        "size": video_path.stat().st_size
                    }
                }
                
                self.storage.store_asset(asset)
                ingested.append(asset)
            except Exception as e:
                logger.error(f"Failed to ingest {video_path}: {e}")
                continue
        
        return {
            "total_found": len(video_files),
            "ingested": len(ingested),
            "assets": [a["id"] for a in ingested]
        }
