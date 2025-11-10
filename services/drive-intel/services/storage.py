"""
In-memory storage service for assets and clips.
"""
from typing import Dict, List, Optional, Any
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class StorageService:
    """In-memory storage service."""
    
    def __init__(self):
        self._assets: Dict[str, Dict[str, Any]] = {}
        self._clips: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = Lock()
        logger.info("Storage service initialized (in-memory)")
    
    def store_asset(self, asset: Dict[str, Any]) -> None:
        """Store an asset."""
        with self._lock:
            self._assets[asset["id"]] = asset
            logger.debug(f"Stored asset: {asset['id']}")
    
    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get an asset by ID."""
        return self._assets.get(asset_id)
    
    def get_all_assets(self) -> List[Dict[str, Any]]:
        """Get all assets."""
        return list(self._assets.values())
    
    def store_clips(self, asset_id: str, clips: List[Dict[str, Any]]) -> None:
        """Store clips for an asset."""
        with self._lock:
            self._clips[asset_id] = clips
            logger.debug(f"Stored {len(clips)} clips for asset: {asset_id}")
    
    def get_clips(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get clips for an asset."""
        return self._clips.get(asset_id, [])
    
    def get_all_clips(self) -> List[Dict[str, Any]]:
        """Get all clips across all assets."""
        all_clips = []
        for clips in self._clips.values():
            all_clips.extend(clips)
        return all_clips
