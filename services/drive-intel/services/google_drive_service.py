"""
Google Drive Integration Service
Implements OAuth 2.0 flow and video file ingestion from Google Drive
"""
import os
import io
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from googleapiclient.errors import HttpError
except ImportError:
    logging.error("Google Drive dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    raise

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes for Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

class GoogleDriveService:
    """
    Production-grade Google Drive integration with OAuth 2.0
    """

    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize Google Drive service.

        Args:
            credentials_path: Path to OAuth 2.0 credentials JSON from Google Cloud Console
            token_path: Path to store/load OAuth token (default: ~/.geminivideo/token.json)
        """
        # Get credentials path from env or parameter
        self.credentials_path = credentials_path or os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        if not self.credentials_path:
            raise ValueError(
                "Google Drive credentials not configured. Set GOOGLE_DRIVE_CREDENTIALS env var "
                "or pass credentials_path parameter. Get credentials from: "
                "https://console.cloud.google.com/apis/credentials"
            )

        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

        # Token storage location
        self.token_path = token_path or os.path.expanduser('~/.geminivideo/token.json')
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)

        # Initialize service
        self.service = None
        self._authenticate()

        logger.info("✅ Google Drive service initialized")

    def _authenticate(self) -> None:
        """
        Authenticate with Google Drive using OAuth 2.0.

        - If token exists and is valid, use it
        - If token is expired, refresh it
        - If no token, start OAuth flow
        """
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                logger.info("Loaded existing OAuth token")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired OAuth token")
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                creds = None

        # Start OAuth flow if no valid credentials
        if not creds or not creds.valid:
            logger.info("Starting OAuth 2.0 flow...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                # Run local server flow (for production, use web flow)
                creds = flow.run_local_server(port=0)
                logger.info("✅ OAuth 2.0 authentication successful")
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                raise

        # Save credentials for next run
        try:
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Saved OAuth token to {self.token_path}")
        except Exception as e:
            logger.warning(f"Failed to save token: {e}")

        # Build Drive API service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Google Drive API service built")
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            raise

    def list_video_files(self, folder_id: Optional[str] = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List video files in Google Drive folder.

        Args:
            folder_id: Google Drive folder ID (if None, searches entire Drive)
            max_results: Maximum number of files to return

        Returns:
            List of video file metadata dictionaries
        """
        try:
            # Build query for video files
            query_parts = ["mimeType contains 'video/'", "trashed=false"]

            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")

            query = " and ".join(query_parts)

            # Execute search
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, videoMediaMetadata)",
                orderBy="modifiedTime desc"
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} video files in Drive")

            return files

        except HttpError as error:
            logger.error(f"Google Drive API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to list video files: {e}")
            raise

    def download_video(self, file_id: str, output_path: Optional[str] = None) -> str:
        """
        Download video file from Google Drive.

        Args:
            file_id: Google Drive file ID
            output_path: Local path to save video (if None, uses temp directory)

        Returns:
            Path to downloaded file
        """
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="name, size, mimeType"
            ).execute()

            file_name = file_metadata.get('name', f'{file_id}.mp4')
            file_size = int(file_metadata.get('size', 0))

            logger.info(f"Downloading: {file_name} ({file_size / 1024 / 1024:.2f} MB)")

            # Determine output path
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, file_name)

            # Download file
            request = self.service.files().get_media(fileId=file_id)

            with io.FileIO(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False

                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Download progress: {progress}%")

            logger.info(f"✅ Downloaded to: {output_path}")
            return output_path

        except HttpError as error:
            logger.error(f"Google Drive API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            raise

    def get_folder_metadata(self, folder_id: str) -> Dict[str, Any]:
        """
        Get metadata for a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            Folder metadata dictionary
        """
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, mimeType, createdTime, modifiedTime"
            ).execute()

            # Verify it's a folder
            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {folder_id} is not a folder")

            logger.info(f"Folder: {folder.get('name')}")
            return folder

        except HttpError as error:
            logger.error(f"Google Drive API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to get folder metadata: {e}")
            raise

    def ingest_folder(
        self,
        folder_id: str,
        download_path: Optional[str] = None,
        max_files: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Ingest all video files from a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID
            download_path: Local path to download videos (if None, uses temp)
            max_files: Maximum number of videos to ingest

        Returns:
            List of ingested file information
        """
        try:
            # Verify folder exists
            folder_metadata = self.get_folder_metadata(folder_id)
            logger.info(f"Ingesting videos from folder: {folder_metadata.get('name')}")

            # List video files in folder
            video_files = self.list_video_files(folder_id=folder_id, max_results=max_files)

            if not video_files:
                logger.warning(f"No video files found in folder {folder_id}")
                return []

            # Download each video
            ingested_files = []

            for idx, file_info in enumerate(video_files, 1):
                try:
                    file_id = file_info['id']
                    file_name = file_info['name']

                    logger.info(f"[{idx}/{len(video_files)}] Processing: {file_name}")

                    # Download video
                    local_path = self.download_video(
                        file_id=file_id,
                        output_path=os.path.join(download_path, file_name) if download_path else None
                    )

                    # Extract metadata
                    video_metadata = file_info.get('videoMediaMetadata', {})

                    ingested_files.append({
                        'file_id': file_id,
                        'name': file_name,
                        'local_path': local_path,
                        'size_bytes': int(file_info.get('size', 0)),
                        'mime_type': file_info.get('mimeType'),
                        'duration_ms': video_metadata.get('durationMillis'),
                        'width': video_metadata.get('width'),
                        'height': video_metadata.get('height'),
                        'created_time': file_info.get('createdTime'),
                        'modified_time': file_info.get('modifiedTime')
                    })

                    logger.info(f"✅ Ingested: {file_name}")

                except Exception as e:
                    logger.error(f"Failed to ingest {file_info.get('name')}: {e}")
                    continue

            logger.info(f"✅ Ingested {len(ingested_files)}/{len(video_files)} video files")
            return ingested_files

        except Exception as e:
            logger.error(f"Failed to ingest folder: {e}")
            raise

    def search_videos(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for video files by name or content.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of matching video files
        """
        try:
            # Build search query
            search_query = f"name contains '{query}' and mimeType contains 'video/' and trashed=false"

            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, videoMediaMetadata)",
                orderBy="modifiedTime desc"
            ).execute()

            files = results.get('files', [])
            logger.info(f"Search '{query}': found {len(files)} results")

            return files

        except HttpError as error:
            logger.error(f"Google Drive API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
