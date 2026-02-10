"""
Unified Data Models for Gemini Video Ecosystem.
Shared across: ml-service, drive-intel, titan-core.
"""
from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON, DateTime, Date, Boolean, Numeric, Index, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, nullable=False, index=True)

    filename = Column(String, nullable=False)
    originalName = Column(String, nullable=False)
    mimeType = Column(String, nullable=False)
    fileSize = Column(Integer, nullable=False) # Prisma uses BigInt, SQLAlchemy Integer maps to handling huge ints in Py3

    gcsUrl = Column(String, unique=True, nullable=False)
    gcsBucket = Column(String, nullable=False)
    gcsPath = Column(String, nullable=False)
    thumbnailUrl = Column(String, nullable=True)

    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    bitrate = Column(Integer, nullable=True)
    codec = Column(String, nullable=True)

    status = Column(String, default="PENDING", index=True) # Enum in Prisma: PENDING, PROCESSING, READY, FAILED, ARCHIVED
    processingError = Column(String, nullable=True)

    metadata_ = Column("metadata", JSON, default={}) # 'metadata' is reserved in SQLAlchemy

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    deletedAt = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    clips = relationship("Clip", back_populates="asset", cascade="all, delete-orphan")
    metrics = relationship("PerformanceMetric", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_assets_userId', 'userId'),
        Index('idx_assets_status', 'status'),
        Index('idx_assets_gcsUrl', 'gcsUrl'),
    )


class Clip(Base):
    __tablename__ = "clips"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assetId = Column(String, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)

    startTime = Column(Float, nullable=False)
    endTime = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    clipUrl = Column(String, nullable=True)
    thumbnailUrl = Column(String, nullable=True)

    # AI-detected features
    features = Column(JSON, default={})
    faceCount = Column(Integer, nullable=True)
    hasText = Column(Boolean, default=False)
    hasSpeech = Column(Boolean, default=False)
    hasMusic = Column(Boolean, default=False)

    # Scoring
    score = Column(Float, nullable=True)
    viralScore = Column(Float, nullable=True)
    engagementScore = Column(Float, nullable=True)
    brandSafetyScore = Column(Float, nullable=True)

    rank = Column(Integer, nullable=True)
    status = Column(String, default="PENDING") # Enum in Prisma

    metadata_ = Column("metadata", JSON, default={})

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    deletedAt = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="clips")
    predictions = relationship("Prediction", back_populates="clip", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_clips_assetId', 'assetId'),
        Index('idx_clips_score', 'score'),
    )


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String, ForeignKey("assets.id")) # Maps to assetId but kept for compatibility logic
    platform = Column(String, default="meta")
    date = Column(Date, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0.0)
    revenue = Column(Numeric(10, 2), default=0.0)
    roas = Column(Numeric(10, 2), default=0.0)
    ctr = Column(Numeric(5, 4))
    conversions = Column(Integer, default=0)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset", back_populates="metrics")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True)
    clip_id = Column(String, ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, index=True) # Maps to clipId
    ad_id = Column(String, nullable=False)
    platform = Column(String, nullable=False, index=True)

    predicted_ctr = Column(Float, nullable=False)
    predicted_roas = Column(Float, nullable=False)
    predicted_conversion = Column(Float, nullable=False)

    actual_ctr = Column(Float, nullable=True)
    actual_roas = Column(Float, nullable=True)
    actual_conversion = Column(Float, nullable=True)

    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    spend = Column(Numeric(10, 2), nullable=True)
    
    council_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    hook_type = Column(String, nullable=False, index=True)
    template_type = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    deletedAt = Column(DateTime(timezone=True))

    clip = relationship("Clip", back_populates="predictions")
