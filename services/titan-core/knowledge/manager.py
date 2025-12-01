"""
Knowledge Base Manager with Hot-Reload Capability
Agent 14: Knowledge Base Hot-Reload Engineer

Provides versioned knowledge management with automatic hot-reload,
callback notifications, and support for multiple storage backends.
"""
import os
import json
import hashlib
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """Information about a knowledge base version"""
    version_id: str
    category: str
    timestamp: datetime
    checksum: str
    size_bytes: int
    description: str = ""
    author: str = ""
    is_active: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'VersionInfo':
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class StorageBackend:
    """Base class for storage backends"""

    def save(self, path: str, data: bytes) -> bool:
        raise NotImplementedError

    def load(self, path: str) -> Optional[bytes]:
        raise NotImplementedError

    def delete(self, path: str) -> bool:
        raise NotImplementedError

    def list_files(self, prefix: str) -> List[str]:
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        raise NotImplementedError


class LocalFileSystemBackend(StorageBackend):
    """Local file system storage backend"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        return self.base_path / path

    def save(self, path: str, data: bytes) -> bool:
        try:
            full_path = self._get_full_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(data)
            return True
        except Exception as e:
            logger.error(f"Failed to save to {path}: {e}")
            return False

    def load(self, path: str) -> Optional[bytes]:
        try:
            full_path = self._get_full_path(path)
            if full_path.exists():
                return full_path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Failed to load from {path}: {e}")
            return None

    def delete(self, path: str) -> bool:
        try:
            full_path = self._get_full_path(path)
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
            return False

    def list_files(self, prefix: str) -> List[str]:
        try:
            prefix_path = self._get_full_path(prefix)
            if prefix_path.is_dir():
                return [str(p.relative_to(self.base_path)) for p in prefix_path.rglob('*') if p.is_file()]
            return []
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return []

    def exists(self, path: str) -> bool:
        return self._get_full_path(path).exists()


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend (placeholder for future implementation)"""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        # TODO: Initialize GCS client
        logger.warning("GCS backend not fully implemented - using local fallback")

    def save(self, path: str, data: bytes) -> bool:
        # TODO: Implement GCS upload
        logger.warning("GCS save not implemented")
        return False

    def load(self, path: str) -> Optional[bytes]:
        # TODO: Implement GCS download
        logger.warning("GCS load not implemented")
        return None

    def delete(self, path: str) -> bool:
        # TODO: Implement GCS delete
        logger.warning("GCS delete not implemented")
        return False

    def list_files(self, prefix: str) -> List[str]:
        # TODO: Implement GCS list
        logger.warning("GCS list not implemented")
        return []

    def exists(self, path: str) -> bool:
        # TODO: Implement GCS exists
        logger.warning("GCS exists not implemented")
        return False


class KnowledgeBaseManager:
    """
    Knowledge Base Manager with Hot-Reload Capability

    Features:
    - Versioned storage with automatic checksums
    - Hot-reload with callback notifications
    - Multiple storage backends (local, GCS)
    - Atomic updates with rollback capability
    - Category-based organization
    """

    CATEGORIES = [
        'brand_guidelines',
        'competitor_analysis',
        'industry_benchmarks',
        'hook_templates',
        'storyboard_templates',
        'winning_patterns'
    ]

    def __init__(self, storage_backend: Optional[StorageBackend] = None):
        """
        Initialize Knowledge Base Manager

        Args:
            storage_backend: Storage backend to use (defaults to local filesystem)
        """
        if storage_backend is None:
            # Default to local filesystem storage
            base_path = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"
            storage_backend = LocalFileSystemBackend(str(base_path))

        self.storage = storage_backend
        self._versions: Dict[str, List[VersionInfo]] = defaultdict(list)
        self._active_versions: Dict[str, str] = {}  # category -> version_id
        self._cached_data: Dict[str, Dict[str, Any]] = {}  # category -> data
        self._subscribers: Dict[str, Callable] = {}  # subscription_id -> callback
        self._lock = threading.RLock()

        # Load version metadata
        self._load_metadata()

        logger.info(f"KnowledgeBaseManager initialized with {len(self._versions)} categories")

    def _compute_checksum(self, data: bytes) -> str:
        """Compute SHA256 checksum of data"""
        return hashlib.sha256(data).hexdigest()

    def _get_version_path(self, category: str, version_id: str) -> str:
        """Get storage path for a specific version"""
        return f"{category}/versions/{version_id}.json"

    def _get_metadata_path(self, category: str) -> str:
        """Get storage path for metadata"""
        return f"{category}/metadata.json"

    def _load_metadata(self):
        """Load all version metadata from storage"""
        with self._lock:
            for category in self.CATEGORIES:
                metadata_path = self._get_metadata_path(category)
                data = self.storage.load(metadata_path)

                if data:
                    try:
                        metadata = json.loads(data.decode('utf-8'))
                        self._versions[category] = [
                            VersionInfo.from_dict(v) for v in metadata.get('versions', [])
                        ]
                        self._active_versions[category] = metadata.get('active_version', '')
                        logger.info(f"Loaded {len(self._versions[category])} versions for {category}")
                    except Exception as e:
                        logger.error(f"Failed to load metadata for {category}: {e}")
                else:
                    logger.info(f"No metadata found for {category}, starting fresh")

    def _save_metadata(self, category: str):
        """Save version metadata to storage"""
        with self._lock:
            metadata = {
                'category': category,
                'versions': [v.to_dict() for v in self._versions[category]],
                'active_version': self._active_versions.get(category, ''),
                'last_updated': datetime.utcnow().isoformat()
            }

            metadata_path = self._get_metadata_path(category)
            data = json.dumps(metadata, indent=2).encode('utf-8')

            if not self.storage.save(metadata_path, data):
                raise IOError(f"Failed to save metadata for {category}")

    def _validate_category(self, category: str):
        """Validate that category is supported"""
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {self.CATEGORIES}")

    def _validate_knowledge_data(self, category: str, data: dict) -> bool:
        """
        Validate knowledge data structure

        Basic validation - can be extended based on category requirements
        """
        if not isinstance(data, dict):
            raise ValueError("Knowledge data must be a dictionary")

        # Category-specific validation
        if category == 'brand_guidelines':
            required_keys = ['brand_name', 'voice', 'values']
            if not all(k in data for k in required_keys):
                raise ValueError(f"brand_guidelines requires: {required_keys}")

        elif category == 'hook_templates':
            if 'templates' not in data or not isinstance(data['templates'], list):
                raise ValueError("hook_templates requires 'templates' list")

        elif category == 'storyboard_templates':
            if 'templates' not in data or not isinstance(data['templates'], list):
                raise ValueError("storyboard_templates requires 'templates' list")

        elif category == 'winning_patterns':
            if 'patterns' not in data or not isinstance(data['patterns'], list):
                raise ValueError("winning_patterns requires 'patterns' list")

        return True

    def upload_knowledge(
        self,
        category: str,
        data: dict,
        description: str = "",
        author: str = "system"
    ) -> str:
        """
        Upload new knowledge version

        Args:
            category: Knowledge category
            data: Knowledge data dictionary
            description: Version description
            author: Author name

        Returns:
            Version ID
        """
        self._validate_category(category)
        self._validate_knowledge_data(category, data)

        with self._lock:
            # Generate version ID
            timestamp = datetime.utcnow()
            version_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Serialize and compute checksum
            data_bytes = json.dumps(data, indent=2).encode('utf-8')
            checksum = self._compute_checksum(data_bytes)

            # Check for duplicates
            for version in self._versions[category]:
                if version.checksum == checksum:
                    logger.warning(f"Duplicate data detected for {category}, using existing version {version.version_id}")
                    return version.version_id

            # Save to storage
            version_path = self._get_version_path(category, version_id)
            if not self.storage.save(version_path, data_bytes):
                raise IOError(f"Failed to save knowledge to storage")

            # Create version info
            version_info = VersionInfo(
                version_id=version_id,
                category=category,
                timestamp=timestamp,
                checksum=checksum,
                size_bytes=len(data_bytes),
                description=description,
                author=author,
                is_active=False
            )

            # Update metadata
            self._versions[category].append(version_info)
            self._versions[category].sort(key=lambda v: v.timestamp, reverse=True)

            # Auto-activate if first version
            if not self._active_versions.get(category):
                self._activate_version(category, version_id)

            self._save_metadata(category)

            logger.info(f"Uploaded knowledge: {category} v{version_id}")
            return version_id

    def download_knowledge(self, category: str, version: str = 'latest') -> Optional[dict]:
        """
        Download knowledge data

        Args:
            category: Knowledge category
            version: Version ID or 'latest' for active version

        Returns:
            Knowledge data dictionary or None
        """
        self._validate_category(category)

        with self._lock:
            # Determine version to load
            if version == 'latest':
                version_id = self._active_versions.get(category)
                if not version_id:
                    logger.warning(f"No active version for {category}")
                    return None
            else:
                version_id = version

            # Check cache
            cache_key = f"{category}:{version_id}"
            if cache_key in self._cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return self._cached_data[cache_key]

            # Load from storage
            version_path = self._get_version_path(category, version_id)
            data_bytes = self.storage.load(version_path)

            if not data_bytes:
                logger.error(f"Failed to load knowledge: {category} v{version_id}")
                return None

            # Parse and cache
            data = json.loads(data_bytes.decode('utf-8'))
            self._cached_data[cache_key] = data

            logger.debug(f"Loaded knowledge: {category} v{version_id}")
            return data

    def list_versions(self, category: str) -> List[VersionInfo]:
        """
        List all versions for a category

        Args:
            category: Knowledge category

        Returns:
            List of version info objects
        """
        self._validate_category(category)

        with self._lock:
            return self._versions[category].copy()

    def delete_version(self, category: str, version: str) -> bool:
        """
        Delete a specific version

        Args:
            category: Knowledge category
            version: Version ID

        Returns:
            True if deleted successfully
        """
        self._validate_category(category)

        with self._lock:
            # Cannot delete active version
            if self._active_versions.get(category) == version:
                raise ValueError("Cannot delete active version. Activate another version first.")

            # Find and remove version
            version_info = None
            for i, v in enumerate(self._versions[category]):
                if v.version_id == version:
                    version_info = self._versions[category].pop(i)
                    break

            if not version_info:
                logger.warning(f"Version not found: {category} v{version}")
                return False

            # Delete from storage
            version_path = self._get_version_path(category, version)
            self.storage.delete(version_path)

            # Clear from cache
            cache_key = f"{category}:{version}"
            self._cached_data.pop(cache_key, None)

            # Save metadata
            self._save_metadata(category)

            logger.info(f"Deleted version: {category} v{version}")
            return True

    def _activate_version(self, category: str, version: str):
        """Internal method to activate a version"""
        # Update active version
        old_version = self._active_versions.get(category)
        self._active_versions[category] = version

        # Update is_active flags
        for v in self._versions[category]:
            v.is_active = (v.version_id == version)

        # Clear cache for category (force reload)
        cache_keys_to_clear = [k for k in self._cached_data.keys() if k.startswith(f"{category}:")]
        for key in cache_keys_to_clear:
            del self._cached_data[key]

        # Notify subscribers
        self._notify_subscribers(category, version, old_version)

    def activate_version(self, category: str, version: str) -> bool:
        """
        Activate a specific version

        Args:
            category: Knowledge category
            version: Version ID to activate

        Returns:
            True if activated successfully
        """
        self._validate_category(category)

        with self._lock:
            # Verify version exists
            version_exists = any(v.version_id == version for v in self._versions[category])
            if not version_exists:
                raise ValueError(f"Version {version} not found for {category}")

            self._activate_version(category, version)
            self._save_metadata(category)

            logger.info(f"Activated version: {category} v{version}")
            return True

    def subscribe_to_updates(self, callback: Callable[[str, str, Optional[str]], None]) -> str:
        """
        Subscribe to knowledge updates

        Args:
            callback: Function(category, new_version, old_version) to call on updates

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())

        with self._lock:
            self._subscribers[subscription_id] = callback

        logger.info(f"New subscription: {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from updates

        Args:
            subscription_id: Subscription ID

        Returns:
            True if unsubscribed successfully
        """
        with self._lock:
            if subscription_id in self._subscribers:
                del self._subscribers[subscription_id]
                logger.info(f"Unsubscribed: {subscription_id}")
                return True
            return False

    def _notify_subscribers(self, category: str, new_version: str, old_version: Optional[str]):
        """Notify all subscribers of an update"""
        with self._lock:
            subscribers = list(self._subscribers.items())

        for sub_id, callback in subscribers:
            try:
                callback(category, new_version, old_version)
            except Exception as e:
                logger.error(f"Subscriber {sub_id} callback failed: {e}")

    def trigger_reload(self, category: str) -> bool:
        """
        Manually trigger reload of a category

        Args:
            category: Knowledge category

        Returns:
            True if reloaded successfully
        """
        self._validate_category(category)

        with self._lock:
            version_id = self._active_versions.get(category)
            if not version_id:
                logger.warning(f"No active version to reload for {category}")
                return False

            # Clear cache
            cache_key = f"{category}:{version_id}"
            self._cached_data.pop(cache_key, None)

            # Reload from storage
            data = self.download_knowledge(category, version_id)

            if data:
                # Notify subscribers
                self._notify_subscribers(category, version_id, version_id)
                logger.info(f"Reloaded: {category} v{version_id}")
                return True

            return False

    def get_current_version(self, category: str) -> Optional[str]:
        """
        Get current active version ID

        Args:
            category: Knowledge category

        Returns:
            Version ID or None
        """
        self._validate_category(category)
        return self._active_versions.get(category)

    def reload_all(self) -> Dict[str, str]:
        """
        Reload all categories

        Returns:
            Dictionary of category -> version ID that was reloaded
        """
        results = {}

        for category in self.CATEGORIES:
            if self.trigger_reload(category):
                results[category] = self._active_versions[category]

        logger.info(f"Reloaded {len(results)} categories")
        return results

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all categories

        Returns:
            Dictionary with status information for each category
        """
        status = {}

        with self._lock:
            for category in self.CATEGORIES:
                active_version = self._active_versions.get(category)
                versions = self._versions[category]

                # Find active version info
                active_info = None
                if active_version:
                    active_info = next((v for v in versions if v.version_id == active_version), None)

                status[category] = {
                    'active_version': active_version,
                    'active_timestamp': active_info.timestamp.isoformat() if active_info else None,
                    'total_versions': len(versions),
                    'latest_version': versions[0].version_id if versions else None,
                    'cached': f"{category}:{active_version}" in self._cached_data if active_version else False
                }

        return status


# Singleton instance
_manager: Optional[KnowledgeBaseManager] = None


def get_manager() -> KnowledgeBaseManager:
    """Get or create singleton KnowledgeBaseManager instance"""
    global _manager
    if _manager is None:
        _manager = KnowledgeBaseManager()
    return _manager


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize manager
    manager = KnowledgeBaseManager()

    # Example: Upload brand guidelines
    brand_data = {
        "brand_name": "FitPro",
        "voice": "energetic and motivational",
        "values": ["authenticity", "results-driven", "community"],
        "tone": "direct but empathetic",
        "keywords": ["transformation", "proven", "science-backed"],
        "avoid": ["gimmicks", "quick fixes", "unrealistic promises"]
    }

    version_id = manager.upload_knowledge(
        category="brand_guidelines",
        data=brand_data,
        description="Initial brand guidelines",
        author="marketing_team"
    )
    print(f"Uploaded version: {version_id}")

    # Example: Subscribe to updates
    def on_update(category, new_version, old_version):
        print(f"Knowledge updated: {category} {old_version} -> {new_version}")

    sub_id = manager.subscribe_to_updates(on_update)

    # Example: List versions
    versions = manager.list_versions("brand_guidelines")
    print(f"\nVersions: {len(versions)}")
    for v in versions:
        print(f"  - {v.version_id} ({v.timestamp}) [active: {v.is_active}]")

    # Example: Download latest
    data = manager.download_knowledge("brand_guidelines")
    print(f"\nCurrent brand: {data.get('brand_name')}")

    # Example: Get status
    status = manager.get_all_status()
    print(f"\nStatus:")
    for category, info in status.items():
        print(f"  {category}: {info['total_versions']} versions, active: {info['active_version']}")
