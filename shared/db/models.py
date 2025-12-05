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

    videos = relationship("Video", back_populates="campaign", lazy="selectin")

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

    campaign = relationship("Campaign", back_populates="videos", lazy="joined")
    scenes = relationship("Scene", back_populates="video", lazy="selectin")
    metrics = relationship("PerformanceMetric", back_populates="video", lazy="selectin")

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

    video = relationship("Video", back_populates="scenes", lazy="joined")

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

    video = relationship("Video", back_populates="metrics", lazy="joined")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String)
    entity_id = Column(UUID(as_uuid=True))
    action = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Video Agent Models
class RenderJob(Base):
    __tablename__ = "render_jobs"

    job_id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="queued")
    storyboard = Column(JSON, nullable=False)
    output_format = Column(String, default="mp4")
    resolution = Column(String, default="1920x1080")
    fps = Column(Integer, default=30)
    output_path = Column(String)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ML Service - Conversion Hub Models
class UnifiedConversion(Base):
    __tablename__ = "unified_conversions"

    id = Column(String, primary_key=True)
    external_ids = Column(JSON, nullable=False)  # source -> external_id mapping
    contact_email = Column(String)
    contact_id = Column(String)
    value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    conversion_type = Column(String, nullable=False)
    sources = Column(JSON, nullable=False)  # List of source names
    touchpoints = Column(JSON, default=[])  # List of touchpoint dicts
    attributed_campaign_id = Column(String)
    attributed_ad_id = Column(String)
    attribution_model = Column(String, default="last_touch")
    first_touch_at = Column(DateTime(timezone=True), nullable=False)
    converted_at = Column(DateTime(timezone=True), nullable=False)
    is_offline = Column(Boolean, default=False)
    metadata = Column(JSON, default={})
    is_merged = Column(Boolean, default=False)
    merged_into = Column(String)  # ID of conversion this was merged into
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ML Service - Self Learning Models
class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    prediction_id = Column(String, primary_key=True)
    model_type = Column(String, nullable=False)
    predicted_value = Column(Float, nullable=False)
    features = Column(JSON, nullable=False)
    actual_value = Column(Float)
    error = Column(Float)
    error_percentage = Column(Float)
    outcome_recorded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ModelPerformanceHistory(Base):
    __tablename__ = "model_performance_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type = Column(String, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    sample_count = Column(Integer, nullable=False)
    period_days = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type = Column(String, nullable=False)
    drift_type = Column(String, nullable=False)  # data_drift, concept_drift, prediction_drift
    severity = Column(String, nullable=False)  # low, medium, high, critical
    affected_features = Column(JSON, default=[])
    statistical_tests = Column(JSON, default={})
    recommendation = Column(Text)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ABTest(Base):
    __tablename__ = "ab_tests"

    test_id = Column(String, primary_key=True)
    model_type = Column(String, nullable=False)
    model_a_id = Column(String, nullable=False)
    model_b_id = Column(String, nullable=False)
    traffic_split = Column(Float, default=0.5)
    duration_days = Column(Integer, default=7)
    status = Column(String, default="active")  # active, completed, cancelled
    winner = Column(String)
    results = Column(JSON, default={})
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FeatureImportanceHistory(Base):
    __tablename__ = "feature_importance_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type = Column(String, nullable=False)
    feature_name = Column(String, nullable=False)
    importance_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LearningAlert(Base):
    __tablename__ = "learning_alerts"

    alert_id = Column(String, primary_key=True)
    alert_type = Column(String, nullable=False)  # feature_drift, concept_drift, etc.
    model_type = Column(String, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    details = Column(JSON, default={})
    status = Column(String, default="active")  # active, acknowledged, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Drive Intel - FAISS Search Models
class EmbeddingMetadata(Base):
    __tablename__ = "embedding_metadata"

    external_id = Column(String, primary_key=True)
    internal_id = Column(Integer, nullable=False, unique=True)
    metadata = Column(JSON, default={})
    embedding_dimension = Column(Integer)
    index_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
