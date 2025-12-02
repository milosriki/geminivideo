"""
Real Google Drive API Integration - Agent 22
Production-grade implementation with service account, OAuth, webhooks, and batch operations.
NO MOCK DATA - All real API calls.
"""

import io
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, BinaryIO
from datetime import datetime, timedelta
import json

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


@dataclass
class DriveFile:
    """Represents a Google Drive file with metadata."""

    id: str
    name: str
    mime_type: str
    size: int
    created_time: str
    modified_time: str
    parents: List[str] = field(default_factory=list)
    web_view_link: str = ""

    # Video-specific metadata (optional)
    duration_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Additional metadata
    version: Optional[int] = None
    md5_checksum: Optional[str] = None
    trashed: bool = False

    @classmethod
    def from_api_response(cls, file_dict: Dict[str, Any]) -> 'DriveFile':
        """Create DriveFile from Google Drive API response."""
        video_metadata = file_dict.get('videoMediaMetadata', {})

        return cls(
            id=file_dict['id'],
            name=file_dict['name'],
            mime_type=file_dict.get('mimeType', ''),
            size=int(file_dict.get('size', 0)),
            created_time=file_dict.get('createdTime', ''),
            modified_time=file_dict.get('modifiedTime', ''),
            parents=file_dict.get('parents', []),
            web_view_link=file_dict.get('webViewLink', ''),
            duration_ms=video_metadata.get('durationMillis'),
            width=video_metadata.get('width'),
            height=video_metadata.get('height'),
            version=int(file_dict.get('version', 0)),
            md5_checksum=file_dict.get('md5Checksum'),
            trashed=file_dict.get('trashed', False)
        )

    def is_video(self) -> bool:
        """Check if file is a video."""
        return self.mime_type.startswith('video/')

    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.size / (1024 * 1024)

    def __repr__(self) -> str:
        return f"DriveFile(name={self.name}, size={self.size_mb():.2f}MB, mime={self.mime_type})"


class GoogleDriveService:
    """
    Real Google Drive API integration with comprehensive functionality.

    Features:
    - Service account and OAuth 2.0 authentication
    - File listing, searching, downloading
    - Batch operations
    - Folder watching with webhooks
    - Storage quota management
    """

    # API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly',
        'https://www.googleapis.com/auth/drive.file'
    ]

    # Video MIME types
    VIDEO_MIME_TYPES = [
        'video/mp4',
        'video/mpeg',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-matroska',
        'video/webm'
    ]

    def __init__(self, credentials_path: str = None, credentials: Credentials = None):
        """
        Initialize Google Drive service.

        Args:
            credentials_path: Path to service account JSON or OAuth client secrets
            credentials: Pre-configured Credentials object (optional)
        """
        self.service = None
        self.credentials = credentials
        self.credentials_path = credentials_path

        if not credentials and not credentials_path:
            raise ValueError(
                "Either 'credentials' or 'credentials_path' must be provided. "
                "Get credentials from: https://console.cloud.google.com/apis/credentials"
            )

        if credentials:
            self._build_service(credentials)
            logger.info("Google Drive service initialized with provided credentials")
        elif credentials_path:
            self.authenticate(credentials_path)

    def _build_service(self, credentials: Credentials) -> None:
        """Build the Google Drive API service."""
        try:
            self.service = build('drive', 'v3', credentials=credentials)
            self.credentials = credentials
            logger.info("Google Drive API service built successfully")
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            raise

    def authenticate(self, credentials_path: str) -> None:
        """
        Authenticate with service account credentials.

        Args:
            credentials_path: Path to service account JSON file
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )
            self._build_service(credentials)
            logger.info(f"Authenticated with service account: {credentials_path}")
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            raise

    def authenticate_oauth(self, token_path: str, credentials_path: str) -> None:
        """
        Authenticate with OAuth 2.0 flow.

        Args:
            token_path: Path to store/load OAuth token
            credentials_path: Path to OAuth client secrets JSON
        """
        creds = None

        # Load existing token
        if Path(token_path).exists():
            try:
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
                logger.info(f"Loaded OAuth token from {token_path}")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh expired token
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired OAuth token")
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                creds = None

        # Run OAuth flow if needed
        if not creds or not creds.valid:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("OAuth 2.0 authentication successful")
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                raise

        # Save token
        try:
            Path(token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Saved OAuth token to {token_path}")
        except Exception as e:
            logger.warning(f"Failed to save token: {e}")

        self._build_service(creds)

    def list_folder(
        self,
        folder_id: str,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> List[DriveFile]:
        """
        List all files in a folder.

        Args:
            folder_id: Google Drive folder ID
            page_size: Number of files per page (max 1000)
            page_token: Token for pagination

        Returns:
            List of DriveFile objects
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                pageSize=min(page_size, 1000),
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, "
                       "modifiedTime, parents, webViewLink, videoMediaMetadata, "
                       "version, md5Checksum, trashed)",
                orderBy="modifiedTime desc"
            ).execute()

            files = [DriveFile.from_api_response(f) for f in results.get('files', [])]
            logger.info(f"Listed {len(files)} files from folder {folder_id}")

            return files

        except HttpError as e:
            logger.error(f"Failed to list folder {folder_id}: {e}")
            raise

    def list_videos(self, folder_id: str, page_size: int = 100) -> List[DriveFile]:
        """
        List all video files in a folder.

        Args:
            folder_id: Google Drive folder ID
            page_size: Number of files per page

        Returns:
            List of DriveFile objects (videos only)
        """
        try:
            query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed=false"

            results = self.service.files().list(
                q=query,
                pageSize=min(page_size, 1000),
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, "
                       "parents, webViewLink, videoMediaMetadata, version, md5Checksum)",
                orderBy="modifiedTime desc"
            ).execute()

            videos = [DriveFile.from_api_response(f) for f in results.get('files', [])]
            logger.info(f"Found {len(videos)} videos in folder {folder_id}")

            return videos

        except HttpError as e:
            logger.error(f"Failed to list videos: {e}")
            raise

    def download_file(self, file_id: str, destination: str) -> str:
        """
        Download file to disk.

        Args:
            file_id: Google Drive file ID
            destination: Local file path

        Returns:
            Path to downloaded file
        """
        try:
            # Get file metadata
            file_metadata = self.get_file_metadata(file_id)
            logger.info(f"Downloading {file_metadata.name} ({file_metadata.size_mb():.2f} MB)")

            # Download file
            request = self.service.files().get_media(fileId=file_id)

            Path(destination).parent.mkdir(parents=True, exist_ok=True)

            with io.FileIO(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.debug(f"Download progress: {progress}%")

            logger.info(f"Downloaded to {destination}")
            return destination

        except HttpError as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            raise

    def download_to_memory(self, file_id: str) -> bytes:
        """
        Download file to memory (returns bytes).

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as bytes
        """
        try:
            request = self.service.files().get_media(fileId=file_id)

            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()

            content = buffer.getvalue()
            logger.info(f"Downloaded {len(content)} bytes to memory")

            return content

        except HttpError as e:
            logger.error(f"Failed to download file {file_id} to memory: {e}")
            raise

    def batch_download(
        self,
        file_ids: List[str],
        destination_dir: str,
        max_workers: int = 4
    ) -> Dict[str, str]:
        """
        Download multiple files in batch.

        Args:
            file_ids: List of Google Drive file IDs
            destination_dir: Directory to save files
            max_workers: Number of parallel downloads (unused, sequential for simplicity)

        Returns:
            Dictionary mapping file_id to local path
        """
        results = {}

        for idx, file_id in enumerate(file_ids, 1):
            try:
                file_metadata = self.get_file_metadata(file_id)
                destination = str(Path(destination_dir) / file_metadata.name)

                logger.info(f"[{idx}/{len(file_ids)}] Downloading {file_metadata.name}")
                local_path = self.download_file(file_id, destination)
                results[file_id] = local_path

            except Exception as e:
                logger.error(f"Failed to download {file_id}: {e}")
                results[file_id] = None

        logger.info(f"Batch download complete: {len([v for v in results.values() if v])}/{len(file_ids)} succeeded")
        return results

    def get_file_metadata(self, file_id: str) -> DriveFile:
        """
        Get detailed file metadata.

        Args:
            file_id: Google Drive file ID

        Returns:
            DriveFile object with metadata
        """
        try:
            file_dict = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, "
                       "parents, webViewLink, videoMediaMetadata, version, "
                       "md5Checksum, trashed"
            ).execute()

            return DriveFile.from_api_response(file_dict)

        except HttpError as e:
            logger.error(f"Failed to get metadata for {file_id}: {e}")
            raise

    def watch_folder(
        self,
        folder_id: str,
        webhook_url: str,
        expiration_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Set up webhook notification for folder changes.

        Args:
            folder_id: Google Drive folder ID to watch
            webhook_url: HTTPS URL to receive notifications
            expiration_hours: How long to watch (max 24 hours)

        Returns:
            Dictionary with channel info (id, resource_id, expiration)
        """
        try:
            # Calculate expiration timestamp
            expiration = int((datetime.utcnow() + timedelta(hours=expiration_hours)).timestamp() * 1000)

            # Create watch request
            body = {
                'id': f"channel-{folder_id}-{int(time.time())}",
                'type': 'web_hook',
                'address': webhook_url,
                'expiration': expiration
            }

            response = self.service.files().watch(
                fileId=folder_id,
                body=body
            ).execute()

            logger.info(f"Started watching folder {folder_id} -> {webhook_url}")
            logger.info(f"Channel ID: {response['id']}, Resource ID: {response['resourceId']}")

            return {
                'channel_id': response['id'],
                'resource_id': response['resourceId'],
                'expiration': response.get('expiration'),
                'webhook_url': webhook_url
            }

        except HttpError as e:
            logger.error(f"Failed to watch folder {folder_id}: {e}")
            raise

    def stop_watch(self, channel_id: str, resource_id: str) -> bool:
        """
        Stop watching a folder.

        Args:
            channel_id: Channel ID from watch_folder
            resource_id: Resource ID from watch_folder

        Returns:
            True if successful
        """
        try:
            body = {
                'id': channel_id,
                'resourceId': resource_id
            }

            self.service.channels().stop(body=body).execute()
            logger.info(f"Stopped watching channel {channel_id}")

            return True

        except HttpError as e:
            logger.error(f"Failed to stop channel {channel_id}: {e}")
            return False

    def create_folder(self, name: str, parent_id: str = None) -> str:
        """
        Create a new folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)

        Returns:
            New folder ID
        """
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()

            logger.info(f"Created folder '{name}' with ID: {folder['id']}")
            return folder['id']

        except HttpError as e:
            logger.error(f"Failed to create folder '{name}': {e}")
            raise

    def move_file(self, file_id: str, new_parent_id: str) -> bool:
        """
        Move file to a different folder.

        Args:
            file_id: File ID to move
            new_parent_id: Destination folder ID

        Returns:
            True if successful
        """
        try:
            # Get current parents
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()

            previous_parents = ','.join(file_metadata.get('parents', []))

            # Move file
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            logger.info(f"Moved file {file_id} to folder {new_parent_id}")
            return True

        except HttpError as e:
            logger.error(f"Failed to move file {file_id}: {e}")
            return False

    def search_files(
        self,
        query: str,
        folder_id: str = None,
        mime_type: str = None,
        max_results: int = 50
    ) -> List[DriveFile]:
        """
        Search for files by name or metadata.

        Args:
            query: Search query (file name)
            folder_id: Limit search to folder (optional)
            mime_type: Filter by MIME type (optional)
            max_results: Maximum results to return

        Returns:
            List of matching DriveFile objects
        """
        try:
            # Build query
            query_parts = [f"name contains '{query}'", "trashed=false"]

            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")

            if mime_type:
                query_parts.append(f"mimeType='{mime_type}'")

            search_query = " and ".join(query_parts)

            results = self.service.files().list(
                q=search_query,
                pageSize=min(max_results, 1000),
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, "
                       "parents, webViewLink, videoMediaMetadata, version, md5Checksum)",
                orderBy="modifiedTime desc"
            ).execute()

            files = [DriveFile.from_api_response(f) for f in results.get('files', [])]
            logger.info(f"Search '{query}' returned {len(files)} results")

            return files

        except HttpError as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_storage_quota(self) -> Dict[str, int]:
        """
        Get storage quota information.

        Returns:
            Dictionary with usage, limit, and usage_in_drive (bytes)
        """
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            quota = about.get('storageQuota', {})

            result = {
                'limit': int(quota.get('limit', 0)),
                'usage': int(quota.get('usage', 0)),
                'usage_in_drive': int(quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(quota.get('usageInDriveTrash', 0))
            }

            # Calculate percentages
            if result['limit'] > 0:
                result['usage_percent'] = (result['usage'] / result['limit']) * 100
            else:
                result['usage_percent'] = 0.0

            logger.info(
                f"Storage: {result['usage'] / 1024**3:.2f} GB / "
                f"{result['limit'] / 1024**3:.2f} GB "
                f"({result['usage_percent']:.1f}%)"
            )

            return result

        except HttpError as e:
            logger.error(f"Failed to get storage quota: {e}")
            raise
