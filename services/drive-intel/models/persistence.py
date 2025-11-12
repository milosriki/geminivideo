"""
Persistence layer - in-memory storage with interface ready for Firestore swap
"""
from typing import List, Optional, Dict
from .asset import Asset, Clip


class PersistenceLayer:
    """
    In-memory persistence layer
    Interface designed to be easily swapped with Firestore or other DB
    """
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.clips: Dict[str, Clip] = {}
    
    def save_asset(self, asset: Asset) -> Asset:
        """Save or update an asset"""
        self.assets[asset.id] = asset
        # Index all clips
        for clip in asset.clips:
            self.clips[clip.id] = clip
        return asset
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Retrieve an asset by ID"""
        return self.assets.get(asset_id)
    
    def list_assets(self, skip: int = 0, limit: int = 100) -> List[Asset]:
        """List all assets with pagination"""
        asset_list = list(self.assets.values())
        return asset_list[skip:skip + limit]
    
    def save_clip(self, clip: Clip) -> Clip:
        """Save or update a clip"""
        self.clips[clip.id] = clip
        return clip
    
    def get_clip(self, clip_id: str) -> Optional[Clip]:
        """Retrieve a clip by ID"""
        return self.clips.get(clip_id)
    
    def list_clips(self, asset_id: Optional[str] = None) -> List[Clip]:
        """List all clips, optionally filtered by asset_id"""
        clips = list(self.clips.values())
        if asset_id:
            clips = [c for c in clips if c.asset_id == asset_id]
        return clips
    
    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset and its clips"""
        if asset_id in self.assets:
            # Delete associated clips
            asset = self.assets[asset_id]
            for clip in asset.clips:
                if clip.id in self.clips:
                    del self.clips[clip.id]
            del self.assets[asset_id]
            return True
        return False
