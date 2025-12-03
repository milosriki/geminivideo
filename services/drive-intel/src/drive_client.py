"""
Google Drive Client - Real integration
Handles authentication and file operations with Google Drive API
"""
import os
import logging
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveClient:
    """Real Google Drive Client"""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Google Drive"""
        try:
            # Check for existing token
            token_path = 'token.json'
            if os.path.exists(token_path):
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                
            # Refresh or create new token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # In a real server environment, we'd use a service account
                    # For this "desktop/local" hybrid, we use client secrets
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("credentials.json not found. Drive integration will fail.")
                        return

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("✅ Google Drive Service authenticated")
            
        except Exception as e:
            logger.error(f"Drive authentication failed: {e}")

    def list_videos(self, folder_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List video files from Drive"""
        if not self.service:
            logger.error("Drive service not initialized")
            return []
            
        try:
            query = "mimeType contains 'video/' and trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = self.service.files().list(
                q=query,
                pageSize=limit,
                fields="nextPageToken, files(id, name, mimeType, size, videoMediaMetadata, createdTime)"
            ).execute()
            
            items = results.get('files', [])
            videos = []
            
            for item in items:
                metadata = item.get('videoMediaMetadata', {})
                videos.append({
                    "asset_id": item['id'],
                    "filename": item['name'],
                    "size_bytes": int(item.get('size', 0)),
                    "duration_seconds": float(metadata.get('durationMillis', 0)) / 1000.0,
                    "resolution": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
                    "format": item['mimeType'].split('/')[-1],
                    "ingested_at": item['createdTime'],
                    "source": "google_drive",
                    "status": "ready"
                })
                
            return videos
            
        except Exception as e:
            logger.error(f"Failed to list videos: {e}")
            return []

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """Download file from Drive"""
        if not self.service:
            return False
            
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}%.")
                
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

# Global instance
drive_client = DriveClient()
