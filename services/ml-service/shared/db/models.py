from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Text, ForeignKey, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    status = Column(String, default="draft")
    budget_daily = Column(Numeric(10, 2))
    target_audience = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    videos = relationship("Video", back_populates="campaign")

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    title = Column(String)
    description = Column(Text)
    script_content = Column(JSON)
    video_url = Column(String)
    thumbnail_url = Column(String)
    status = Column(String, default="processing")
    duration_seconds = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_platform_id = Column(String)

    campaign = relationship("Campaign", back_populates="videos")
    scenes = relationship("Scene", back_populates="video")
    metrics = relationship("PerformanceMetric", back_populates="video")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"))
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    description = Column(Text)
    visual_tags = Column(JSON)
    emotion_score = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="scenes")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"))
    platform = Column(String, default="meta")
    date = Column(Date, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0.0)
    ctr = Column(Numeric(5, 4))
    conversions = Column(Integer, default=0)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    video = relationship("Video", back_populates="metrics")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String)
    entity_id = Column(UUID(as_uuid=True))
    action = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Prediction(Base):
    """
    ML Prediction tracking for model validation and ROI verification.

    Stores all predictions made by the ML models and later updates with
    actual performance data for accuracy measurement and continuous improvement.
    """
    __tablename__ = "predictions"

    id = Column(String, primary_key=True)  # UUID as string
    video_id = Column(String, nullable=False, index=True)
    ad_id = Column(String, nullable=False)
    platform = Column(String, nullable=False, index=True)

    # Predicted metrics
    predicted_ctr = Column(Float, nullable=False)
    predicted_roas = Column(Float, nullable=False)
    predicted_conversion = Column(Float, nullable=False)

    # Actual metrics (populated later)
    actual_ctr = Column(Float, nullable=True)
    actual_roas = Column(Float, nullable=True)
    actual_conversion = Column(Float, nullable=True)

    # Additional performance data
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    spend = Column(Numeric(10, 2), nullable=True)

    # Model metadata
    council_score = Column(Float, nullable=False)  # AI council confidence
    hook_type = Column(String, nullable=False, index=True)
    template_type = Column(String, nullable=False)
    metadata = Column(JSON, default={})  # Additional context and calculated metrics

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    actuals_fetched_at = Column(DateTime(timezone=True), nullable=True)
