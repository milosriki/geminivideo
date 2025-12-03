"""
Real Google Cloud Storage Implementation for Knowledge Persistence
Agent 1 of 30: GCS Storage Implementation

Provides production-grade GCS storage with retry logic, error handling,
and comprehensive blob management capabilities.
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound, Conflict
from google.api_core import retry
from google.api_core.exceptions import (
    ServiceUnavailable,
    InternalServerError,
    TooManyRequests,
    DeadlineExceeded
)

logger = logging.getLogger(__name__)


class GCSKnowledgeStore:
    """
    Real Google Cloud Storage implementation for knowledge persistence.

    Features:
    - Automatic retry logic for transient failures
    - Comprehensive error handling
    - Support for JSON and binary data
    - Blob lifecycle management (upload, download, delete, copy)
    - Metadata operations
    - Signed URL generation for temporary access
    - Public URL generation for permanent access

    Args:
        bucket_name: GCS bucket name
        credentials_path: Optional path to service account JSON credentials
        project_id: Optional GCP project ID
        create_bucket: If True, creates bucket if it doesn't exist
        location: Bucket location (default: 'US')
        storage_class: Bucket storage class (default: 'STANDARD')
    """

    # Retry configuration for transient failures
    DEFAULT_RETRY = retry.Retry(
        initial=1.0,
        maximum=10.0,
        multiplier=2.0,
        deadline=60.0,
        predicate=retry.if_exception_type(
            ServiceUnavailable,
            InternalServerError,
            TooManyRequests,
            DeadlineExceeded
        )
    )

    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        create_bucket: bool = False,
        location: str = 'US',
        storage_class: str = 'STANDARD'
    ):
        """Initialize GCS client and bucket connection."""
        self.bucket_name = bucket_name
        self.location = location
        self.storage_class = storage_class

        # Initialize GCS client
        try:
            if credentials_path and os.path.exists(credentials_path):
                logger.info(f"Initializing GCS client with credentials from {credentials_path}")
                self.client = storage.Client.from_service_account_json(
                    credentials_path,
                    project=project_id
                )
            elif project_id:
                logger.info(f"Initializing GCS client for project {project_id}")
                self.client = storage.Client(project=project_id)
            else:
                # Use default credentials (Application Default Credentials)
                logger.info("Initializing GCS client with default credentials")
                self.client = storage.Client()

        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

        # Get or create bucket
        try:
            self.bucket = self.client.bucket(bucket_name)

            if not self.bucket.exists():
                if create_bucket:
                    logger.info(f"Creating bucket {bucket_name}")
                    self.bucket = self.client.create_bucket(
                        bucket_name,
                        location=location
                    )
                    self.bucket.storage_class = storage_class
                    self.bucket.patch()
                    logger.info(f"Bucket {bucket_name} created successfully")
                else:
                    raise ValueError(
                        f"Bucket {bucket_name} does not exist. "
                        f"Set create_bucket=True to create it automatically."
                    )
            else:
                logger.info(f"Connected to existing bucket {bucket_name}")

        except Exception as e:
            logger.error(f"Failed to initialize bucket {bucket_name}: {e}")
            raise

    def upload(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = 'application/octet-stream',
        metadata: Optional[Dict[str, str]] = None,
        make_public: bool = False
    ) -> str:
        """
        Upload data to GCS, return public URL.

        Args:
            blob_name: Path/name of the blob in GCS
            data: Binary data to upload
            content_type: MIME type of the data
            metadata: Optional custom metadata
            make_public: If True, make blob publicly accessible

        Returns:
            Public URL of the uploaded blob

        Raises:
            GoogleCloudError: If upload fails after retries
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.metadata = metadata or {}

            # Upload with retry logic
            blob.upload_from_string(
                data,
                content_type=content_type,
                retry=self.DEFAULT_RETRY
            )

            if make_public:
                blob.make_public()

            public_url = blob.public_url
            logger.info(
                f"Uploaded {len(data)} bytes to {blob_name} "
                f"(content_type: {content_type})"
            )
            return public_url

        except GoogleCloudError as e:
            logger.error(f"Failed to upload {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading {blob_name}: {e}")
            raise GoogleCloudError(f"Upload failed: {e}")

    def upload_json(
        self,
        blob_name: str,
        data: Dict[str, Any],
        indent: int = 2,
        metadata: Optional[Dict[str, str]] = None,
        make_public: bool = False
    ) -> str:
        """
        Upload JSON data to GCS.

        Args:
            blob_name: Path/name of the blob in GCS
            data: Dictionary to serialize as JSON
            indent: JSON indentation (default: 2)
            metadata: Optional custom metadata
            make_public: If True, make blob publicly accessible

        Returns:
            Public URL of the uploaded blob
        """
        try:
            json_bytes = json.dumps(data, indent=indent).encode('utf-8')

            # Add JSON metadata
            json_metadata = metadata or {}
            json_metadata['data_type'] = 'json'
            json_metadata['uploaded_at'] = datetime.utcnow().isoformat()

            return self.upload(
                blob_name=blob_name,
                data=json_bytes,
                content_type='application/json',
                metadata=json_metadata,
                make_public=make_public
            )
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode JSON for {blob_name}: {e}")
            raise ValueError(f"Invalid JSON data: {e}")

    def download(self, blob_name: str) -> bytes:
        """
        Download blob content.

        Args:
            blob_name: Path/name of the blob in GCS

        Returns:
            Binary content of the blob

        Raises:
            NotFound: If blob doesn't exist
            GoogleCloudError: If download fails
        """
        try:
            blob = self.bucket.blob(blob_name)

            if not blob.exists():
                raise NotFound(f"Blob {blob_name} not found in {self.bucket_name}")

            # Download with retry logic
            data = blob.download_as_bytes(retry=self.DEFAULT_RETRY)
            logger.info(f"Downloaded {len(data)} bytes from {blob_name}")
            return data

        except NotFound:
            logger.warning(f"Blob not found: {blob_name}")
            raise
        except GoogleCloudError as e:
            logger.error(f"Failed to download {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading {blob_name}: {e}")
            raise GoogleCloudError(f"Download failed: {e}")

    def download_json(self, blob_name: str) -> Dict[str, Any]:
        """
        Download and parse JSON blob.

        Args:
            blob_name: Path/name of the blob in GCS

        Returns:
            Parsed JSON data as dictionary

        Raises:
            NotFound: If blob doesn't exist
            ValueError: If blob content is not valid JSON
        """
        try:
            data = self.download(blob_name)
            return json.loads(data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {blob_name}: {e}")
            raise ValueError(f"Invalid JSON in blob {blob_name}: {e}")

    def list_blobs(
        self,
        prefix: str = '',
        delimiter: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[str]:
        """
        List all blobs with given prefix.

        Args:
            prefix: Filter blobs by prefix
            delimiter: Use delimiter to emulate directory structure
            max_results: Maximum number of results to return

        Returns:
            List of blob names
        """
        try:
            blobs = self.client.list_blobs(
                self.bucket_name,
                prefix=prefix,
                delimiter=delimiter,
                max_results=max_results
            )

            blob_names = [blob.name for blob in blobs]
            logger.info(f"Listed {len(blob_names)} blobs with prefix '{prefix}'")
            return blob_names

        except GoogleCloudError as e:
            logger.error(f"Failed to list blobs with prefix '{prefix}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing blobs: {e}")
            raise GoogleCloudError(f"List operation failed: {e}")

    def delete(self, blob_name: str, ignore_missing: bool = False) -> bool:
        """
        Delete a blob.

        Args:
            blob_name: Path/name of the blob to delete
            ignore_missing: If True, don't raise error if blob doesn't exist

        Returns:
            True if deleted successfully

        Raises:
            NotFound: If blob doesn't exist and ignore_missing=False
        """
        try:
            blob = self.bucket.blob(blob_name)

            if not blob.exists():
                if ignore_missing:
                    logger.info(f"Blob {blob_name} doesn't exist, ignoring")
                    return False
                else:
                    raise NotFound(f"Blob {blob_name} not found")

            blob.delete(retry=self.DEFAULT_RETRY)
            logger.info(f"Deleted blob {blob_name}")
            return True

        except NotFound:
            if not ignore_missing:
                logger.warning(f"Blob not found: {blob_name}")
                raise
            return False
        except GoogleCloudError as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting {blob_name}: {e}")
            raise GoogleCloudError(f"Delete failed: {e}")

    def exists(self, blob_name: str) -> bool:
        """
        Check if blob exists.

        Args:
            blob_name: Path/name of the blob

        Returns:
            True if blob exists
        """
        try:
            blob = self.bucket.blob(blob_name)
            exists = blob.exists()
            logger.debug(f"Blob {blob_name} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking existence of {blob_name}: {e}")
            return False

    def get_metadata(self, blob_name: str) -> Dict[str, Any]:
        """
        Get blob metadata (size, created, updated, content_type).

        Args:
            blob_name: Path/name of the blob

        Returns:
            Dictionary with metadata

        Raises:
            NotFound: If blob doesn't exist
        """
        try:
            blob = self.bucket.blob(blob_name)

            if not blob.exists():
                raise NotFound(f"Blob {blob_name} not found")

            # Reload to get latest metadata
            blob.reload()

            metadata = {
                'name': blob.name,
                'bucket': blob.bucket.name,
                'size_bytes': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'generation': blob.generation,
                'metageneration': blob.metageneration,
                'etag': blob.etag,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'custom_metadata': blob.metadata or {},
                'public_url': blob.public_url
            }

            logger.debug(f"Retrieved metadata for {blob_name}")
            return metadata

        except NotFound:
            logger.warning(f"Blob not found: {blob_name}")
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for {blob_name}: {e}")
            raise GoogleCloudError(f"Metadata retrieval failed: {e}")

    def copy(
        self,
        source_blob: str,
        dest_blob: str,
        dest_bucket: Optional[str] = None
    ) -> str:
        """
        Copy blob to new location.

        Args:
            source_blob: Source blob name
            dest_blob: Destination blob name
            dest_bucket: Optional destination bucket (defaults to same bucket)

        Returns:
            Public URL of the destination blob

        Raises:
            NotFound: If source blob doesn't exist
        """
        try:
            source = self.bucket.blob(source_blob)

            if not source.exists():
                raise NotFound(f"Source blob {source_blob} not found")

            # Determine destination bucket
            if dest_bucket:
                dest_bucket_obj = self.client.bucket(dest_bucket)
            else:
                dest_bucket_obj = self.bucket

            # Copy with retry
            destination = self.bucket.copy_blob(
                source,
                dest_bucket_obj,
                dest_blob,
                retry=self.DEFAULT_RETRY
            )

            logger.info(f"Copied {source_blob} to {dest_blob}")
            return destination.public_url

        except NotFound:
            logger.warning(f"Source blob not found: {source_blob}")
            raise
        except Exception as e:
            logger.error(f"Failed to copy {source_blob} to {dest_blob}: {e}")
            raise GoogleCloudError(f"Copy failed: {e}")

    def get_signed_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60,
        method: str = 'GET',
        content_type: Optional[str] = None
    ) -> str:
        """
        Generate signed URL for temporary access.

        Args:
            blob_name: Path/name of the blob
            expiration_minutes: URL expiration time in minutes
            method: HTTP method (GET, PUT, DELETE)
            content_type: Content type for PUT requests

        Returns:
            Signed URL string
        """
        try:
            blob = self.bucket.blob(blob_name)

            # Calculate expiration
            expiration = timedelta(minutes=expiration_minutes)

            # Generate signed URL
            url = blob.generate_signed_url(
                version='v4',
                expiration=expiration,
                method=method,
                content_type=content_type
            )

            logger.info(
                f"Generated signed URL for {blob_name} "
                f"(expires in {expiration_minutes} minutes)"
            )
            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            raise GoogleCloudError(f"Signed URL generation failed: {e}")

    def batch_delete(self, blob_names: List[str], ignore_missing: bool = True) -> Dict[str, bool]:
        """
        Delete multiple blobs in batch.

        Args:
            blob_names: List of blob names to delete
            ignore_missing: If True, don't raise error for missing blobs

        Returns:
            Dictionary mapping blob names to deletion success status
        """
        results = {}

        for blob_name in blob_names:
            try:
                success = self.delete(blob_name, ignore_missing=ignore_missing)
                results[blob_name] = success
            except Exception as e:
                logger.error(f"Failed to delete {blob_name} in batch: {e}")
                results[blob_name] = False

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Batch delete: {successful}/{len(blob_names)} successful")
        return results

    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get information about the bucket.

        Returns:
            Dictionary with bucket information
        """
        try:
            self.bucket.reload()

            return {
                'name': self.bucket.name,
                'location': self.bucket.location,
                'storage_class': self.bucket.storage_class,
                'created': self.bucket.time_created.isoformat() if self.bucket.time_created else None,
                'versioning_enabled': self.bucket.versioning_enabled,
                'lifecycle_rules': [dict(rule) for rule in (self.bucket.lifecycle_rules or [])],
                'labels': self.bucket.labels or {},
                'project_id': self.client.project
            }
        except Exception as e:
            logger.error(f"Failed to get bucket info: {e}")
            raise GoogleCloudError(f"Bucket info retrieval failed: {e}")
