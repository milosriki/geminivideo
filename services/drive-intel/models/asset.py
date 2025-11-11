"""
Data models for assets and clips
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


class ClipFeatures(BaseModel):
    """Features extracted from a video clip"""
    motion_score: float = 0.0
    objects: List[str] = Field(default_factory=list)
    object_counts: Dict[str, int] = Field(default_factory=dict)
    text_detected: List[str] = Field(default_factory=list)
    transcript: str = ""
    embedding: Optional[List[float]] = None
    technical_quality: float = 0.0
    

class Clip(BaseModel):
    """A video scene/clip extracted from an asset"""
    id: str
    asset_id: str
    start_time: float
    end_time: float
    duration: float
    features: ClipFeatures
    score: float = 0.0
    rank: Optional[int] = None
    

class Asset(BaseModel):
    """A video asset (original source file)"""
    id: str
    filename: str
    filepath: str
    duration: float
    resolution: Tuple[int, int]
    fps: float
    file_size: int
    clips: List[Clip] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
