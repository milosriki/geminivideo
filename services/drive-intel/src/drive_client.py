"""
Google Drive Client - Real integration
Handles authentication and file operations with Google Drive API
"""
import os
import io
import logging
import asyncio
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Scopes for full Drive access (read/write)
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]


@dataclass
class DriveFile:
    """Represents a Google Drive file"""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    parent_folders: Optional[List[str]] = None
    web_view_link: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'mimeType': self.mime_type,
            'size': self.size,
            'createdTime': self.created_time,
            'modifiedTime': self.modified_time,
            'parents': self.parent_folders,
            'webViewLink': self.web_view_link
        }


class GoogleDriveClient:
    """
    Google Drive API Client with support for both Service Account and OAuth authentication
    Provides file listing, download, and upload capabilities
    """

    def __init__(self, credentials_path: Optional[str] = None, use_service_account: bool = False):
        """
        Initialize Google Drive client

        Args:
            credentials_path: Path to credentials file (service account JSON or OAuth client secrets)
            use_service_account: If True, use service account authentication
        """
        self.credentials_path = credentials_path
        self.use_service_account = use_service_account
        self.creds = None
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Drive service with appropriate authentication"""
        try:
            if self.use_service_account:
                # Service Account authentication (for server-to-server)
                self._authenticate_service_account()
            else:
                # OAuth 2.0 authentication (for user access)
                self._authenticate_oauth()

            if self.creds:
                self.service = build('drive', 'v3', credentials=self.creds)
                logger.info("Google Drive service initialized successfully")
            else:
                logger.warning("Failed to initialize credentials")

        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}", exc_info=True)
            raise

    def _authenticate_service_account(self):
        """Authenticate using service account credentials"""
        try:
            credentials_file = self.credentials_path or 'service_account.json'

            if not os.path.exists(credentials_file):
                logger.error(f"Service account file not found: {credentials_file}")
                return

            self.creds = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )
            logger.info(f"Authenticated with service account from {credentials_file}")

        except Exception as e:
            logger.error(f"Service account authentication failed: {e}", exc_info=True)
            raise

    def _authenticate_oauth(self):
        """Authenticate using OAuth 2.0 flow"""
        try:
            token_path = 'token.json'
            credentials_file = self.credentials_path or 'credentials.json'

            # Check for existing token
            if os.path.exists(token_path):
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # Refresh or create new token
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    logger.info("OAuth token refreshed")
                else:
                    # Create new credentials
                    if not os.path.exists(credentials_file):
                        logger.error(f"OAuth credentials file not found: {credentials_file}")
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    logger.info("New OAuth credentials obtained")

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())

        except Exception as e:
            logger.error(f"OAuth authentication failed: {e}", exc_info=True)
            raise

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
        mime_type: Optional[str] = None
    ) -> List[DriveFile]:
        """
        List files from Google Drive

        Args:
            folder_id: Optional folder ID to list files from
            query: Optional custom query string
            page_size: Number of files to return (max 1000)
            mime_type: Optional MIME type filter (e.g., 'video/', 'image/jpeg')

        Returns:
            List of DriveFile objects
        """
        if not self.service:
            logger.error("Drive service not initialized")
            return []

        try:
            # Build query
            query_parts = []
            if query:
                query_parts.append(query)
            else:
                query_parts.append("trashed = false")

            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")

            if mime_type:
                if mime_type.endswith('/'):
                    query_parts.append(f"mimeType contains '{mime_type}'")
                else:
                    query_parts.append(f"mimeType = '{mime_type}'")

            final_query = " and ".join(query_parts)

            # Execute in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=final_query,
                    pageSize=min(page_size, 1000),
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)"
                ).execute()
            )

            items = results.get('files', [])
            files = []

            for item in items:
                drive_file = DriveFile(
                    id=item['id'],
                    name=item['name'],
                    mime_type=item['mimeType'],
                    size=int(item.get('size', 0)) if item.get('size') else None,
                    created_time=item.get('createdTime'),
                    modified_time=item.get('modifiedTime'),
                    parent_folders=item.get('parents', []),
                    web_view_link=item.get('webViewLink')
                )
                files.append(drive_file)

            logger.info(f"Listed {len(files)} files from Google Drive")
            return files

        except HttpError as e:
            logger.error(f"HTTP error while listing files: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Failed to list files: {e}", exc_info=True)
            return []

    async def download_file(self, file_id: str, destination: str) -> str:
        """
        Download file from Google Drive

        Args:
            file_id: Google Drive file ID
            destination: Local path to save the file

        Returns:
            Path to downloaded file

        Raises:
            Exception if download fails
        """
        if not self.service:
            raise Exception("Drive service not initialized")

        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)

            # Get file metadata first
            file_metadata = self.service.files().get(fileId=file_id).execute()
            logger.info(f"Downloading file: {file_metadata.get('name', file_id)}")

            # Download in thread pool
            loop = asyncio.get_event_loop()

            def _download():
                request = self.service.files().get_media(fileId=file_id)
                with io.FileIO(destination, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            progress = int(status.progress() * 100)
                            logger.debug(f"Download progress: {progress}%")

            await loop.run_in_executor(None, _download)

            logger.info(f"Successfully downloaded file to: {destination}")
            return destination

        except HttpError as e:
            logger.error(f"HTTP error while downloading file {file_id}: {e}", exc_info=True)
            raise Exception(f"Failed to download file: {e}")
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}", exc_info=True)
            raise

    async def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Upload file to Google Drive

        Args:
            file_path: Local path to file to upload
            folder_id: Optional folder ID to upload to
            file_name: Optional name for the file in Drive (defaults to local filename)
            mime_type: Optional MIME type (auto-detected if not provided)

        Returns:
            File ID of uploaded file

        Raises:
            Exception if upload fails
        """
        if not self.service:
            raise Exception("Drive service not initialized")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Prepare file metadata
            file_metadata = {
                'name': file_name or os.path.basename(file_path)
            }

            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Create media upload
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )

            logger.info(f"Uploading file: {file_metadata['name']}")

            # Upload in thread pool
            loop = asyncio.get_event_loop()

            def _upload():
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, mimeType, size, webViewLink'
                ).execute()
                return file

            uploaded_file = await loop.run_in_executor(None, _upload)

            logger.info(f"Successfully uploaded file: {uploaded_file.get('name')} (ID: {uploaded_file.get('id')})")
            return uploaded_file.get('id')

        except HttpError as e:
            logger.error(f"HTTP error while uploading file {file_path}: {e}", exc_info=True)
            raise Exception(f"Failed to upload file: {e}")
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}", exc_info=True)
            raise

    def list_videos(self, folder_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List video files from Drive (legacy method for backward compatibility)

        Args:
            folder_id: Optional folder ID to list videos from
            limit: Maximum number of videos to return

        Returns:
            List of video metadata dictionaries
        """
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

    def download_file_sync(self, file_id: str, destination_path: str) -> bool:
        """
        Synchronous download method (legacy for backward compatibility)

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file

        Returns:
            True if successful, False otherwise
        """
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


# Legacy compatibility: DriveClient alias
class DriveClient(GoogleDriveClient):
    """Legacy DriveClient for backward compatibility"""

    def __init__(self):
        super().__init__(use_service_account=False)


# Global instance (legacy compatibility)
drive_client = DriveClient()
