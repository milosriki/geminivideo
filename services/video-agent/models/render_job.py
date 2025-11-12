"""
Render job models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RenderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderJob(BaseModel):
    """Render job status and metadata"""
    id: str
    status: RenderStatus
    request: Dict[str, Any]
    progress: float = 0.0
    output_path: Optional[str] = None
    compliance: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
