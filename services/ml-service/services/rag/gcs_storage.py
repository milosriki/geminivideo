"""
Google Cloud Storage service for persistent pattern storage.

Replaces /tmp storage with cloud-based persistence while maintaining
local fallback for development environments.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not installed. Using local fallback.")


class GCSPatternStore:
    """
    Persistent storage for knowledge patterns using Google Cloud Storage.

    Environment Variables:
        GCS_BUCKET: GCS bucket name for pattern storage
        GOOGLE_APPLICATION_CREDENTIALS: Path to GCS service account key

    Falls back to local file storage if GCS is not configured.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        local_fallback_dir: str = "/tmp/gcs_fallback"
    ):
        """
        Initialize GCS pattern store.

        Args:
            bucket_name: GCS bucket name (defaults to GCS_BUCKET env var)
            local_fallback_dir: Local directory for fallback storage
        """
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET")
        self.local_fallback_dir = Path(local_fallback_dir)
        self.use_gcs = False
        self.client = None
        self.bucket = None

        # Try to initialize GCS
        if GCS_AVAILABLE and self.bucket_name:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                self.use_gcs = True
                logger.info(f"GCS storage initialized with bucket: {self.bucket_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize GCS: {e}. Using local fallback.")
                self.use_gcs = False
        else:
            if not GCS_AVAILABLE:
                logger.info("GCS not available. Using local fallback.")
            elif not self.bucket_name:
                logger.info("GCS_BUCKET not set. Using local fallback.")

        # Ensure local fallback directory exists
        self.local_fallback_dir.mkdir(parents=True, exist_ok=True)

    def store_patterns(
        self,
        patterns: List[Dict[str, Any]],
        namespace: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store patterns to GCS or local fallback.

        Args:
            patterns: List of pattern dictionaries to store
            namespace: Namespace/key for the patterns (e.g., 'winners', 'hooks')
            metadata: Optional metadata to store alongside patterns

        Returns:
            bool: True if successful, False otherwise
        """
        data = {
            "patterns": patterns,
            "metadata": metadata or {},
            "count": len(patterns)
        }

        if self.use_gcs:
            return self._store_to_gcs(data, namespace)
        else:
            return self._store_to_local(data, namespace)

    def load_patterns(
        self,
        namespace: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Load patterns from GCS or local fallback.

        Args:
            namespace: Namespace/key for the patterns
            limit: Maximum number of patterns to return

        Returns:
            List of pattern dictionaries
        """
        if self.use_gcs:
            data = self._load_from_gcs(namespace)
        else:
            data = self._load_from_local(namespace)

        if not data:
            return []

        patterns = data.get("patterns", [])

        if limit and limit > 0:
            patterns = patterns[:limit]

        return patterns

    def store_binary(
        self,
        file_path: str,
        namespace: str,
        blob_name: str
    ) -> bool:
        """
        Store binary file (e.g., FAISS index) to GCS.

        Args:
            file_path: Local path to binary file
            namespace: Namespace for organization
            blob_name: Name for the blob in GCS

        Returns:
            bool: True if successful, False otherwise
        """
        gcs_path = f"{namespace}/{blob_name}"

        if self.use_gcs:
            try:
                blob = self.bucket.blob(gcs_path)
                blob.upload_from_filename(file_path)
                logger.info(f"Uploaded binary to GCS: {gcs_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to upload binary to GCS: {e}")
                return False
        else:
            # Local fallback: copy file
            try:
                local_path = self.local_fallback_dir / namespace / blob_name
                local_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(file_path, local_path)
                logger.info(f"Copied binary to local: {local_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to copy binary locally: {e}")
                return False

    def load_binary(
        self,
        namespace: str,
        blob_name: str,
        destination_path: str
    ) -> bool:
        """
        Load binary file from GCS to local path.

        Args:
            namespace: Namespace for organization
            blob_name: Name of the blob in GCS
            destination_path: Local path to save the file

        Returns:
            bool: True if successful, False otherwise
        """
        gcs_path = f"{namespace}/{blob_name}"

        if self.use_gcs:
            try:
                blob = self.bucket.blob(gcs_path)
                if not blob.exists():
                    logger.warning(f"Binary not found in GCS: {gcs_path}")
                    return False
                blob.download_to_filename(destination_path)
                logger.info(f"Downloaded binary from GCS: {gcs_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to download binary from GCS: {e}")
                return False
        else:
            # Local fallback: copy file
            try:
                local_path = self.local_fallback_dir / namespace / blob_name
                if not local_path.exists():
                    logger.warning(f"Binary not found locally: {local_path}")
                    return False
                import shutil
                shutil.copy2(local_path, destination_path)
                logger.info(f"Copied binary from local: {local_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to copy binary locally: {e}")
                return False

    def exists(self, namespace: str, blob_name: Optional[str] = None) -> bool:
        """
        Check if a pattern namespace or blob exists.

        Args:
            namespace: Namespace to check
            blob_name: Optional specific blob name (for binary files)

        Returns:
            bool: True if exists, False otherwise
        """
        if blob_name:
            gcs_path = f"{namespace}/{blob_name}"
        else:
            gcs_path = f"{namespace}/patterns.json"

        if self.use_gcs:
            try:
                blob = self.bucket.blob(gcs_path)
                return blob.exists()
            except Exception as e:
                logger.error(f"Failed to check GCS existence: {e}")
                return False
        else:
            local_path = self.local_fallback_dir / gcs_path
            return local_path.exists()

    def _store_to_gcs(self, data: Dict[str, Any], namespace: str) -> bool:
        """Store JSON data to GCS."""
        try:
            blob = self.bucket.blob(f"{namespace}/patterns.json")
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type="application/json"
            )
            logger.info(f"Stored {data['count']} patterns to GCS: {namespace}")
            return True
        except Exception as e:
            logger.error(f"Failed to store to GCS: {e}")
            return False

    def _load_from_gcs(self, namespace: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from GCS."""
        try:
            blob = self.bucket.blob(f"{namespace}/patterns.json")
            if not blob.exists():
                logger.info(f"No patterns found in GCS: {namespace}")
                return None

            data = json.loads(blob.download_as_text())
            logger.info(f"Loaded {data.get('count', 0)} patterns from GCS: {namespace}")
            return data
        except Exception as e:
            logger.error(f"Failed to load from GCS: {e}")
            return None

    def _store_to_local(self, data: Dict[str, Any], namespace: str) -> bool:
        """Store JSON data to local fallback."""
        try:
            local_path = self.local_fallback_dir / f"{namespace}.json"
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Stored {data['count']} patterns locally: {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store locally: {e}")
            return False

    def _load_from_local(self, namespace: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from local fallback."""
        try:
            local_path = self.local_fallback_dir / f"{namespace}.json"
            if not local_path.exists():
                logger.info(f"No patterns found locally: {local_path}")
                return None

            with open(local_path, 'r') as f:
                data = json.load(f)

            logger.info(f"Loaded {data.get('count', 0)} patterns locally: {local_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load locally: {e}")
            return None


# Singleton instance
gcs_store = GCSPatternStore()
