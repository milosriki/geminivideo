from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Text, ForeignKey, Date, Numeric, Index
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

    assets = relationship("Asset", back_populates="campaign")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)  # UUID as string
    user_id = Column(String, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    
    # File info
    filename = Column(String)
    original_name = Column(String)
    mime_type = Column(String)
    file_size = Column(Integer)  # BigInt in Prisma
    
    # Storage
    gcs_url = Column(String, unique=True)
    gcs_bucket = Column(String)
    gcs_path = Column(String)
    thumbnail_url = Column(String)
    
    # Metadata
    duration = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    bitrate = Column(Integer)
    codec = Column(String)
    
    status = Column(String, default="PENDING")
    processing_error = Column(String)
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))

    campaign = relationship("Campaign", back_populates="assets")
    clips = relationship("Clip", back_populates="asset")
    metrics = relationship("PerformanceMetric", back_populates="asset")

class Clip(Base):
    __tablename__ = "clips"

    id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("assets.id"))
    
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float)
    
    clip_url = Column(String)
    thumbnail_url = Column(String)
    
    # AI features
    features = Column(JSON, default={})
    face_count = Column(Integer)
    has_text = Column(Boolean, default=False)
    has_speech = Column(Boolean, default=False)
    has_music = Column(Boolean, default=False)
    
    # Scoring
    score = Column(Float)
    viral_score = Column(Float)
    engagement_score = Column(Float)
    brand_safety_score = Column(Float)
    
    rank = Column(Integer)
    status = Column(String, default="PENDING")
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))

    asset = relationship("Asset", back_populates="clips")
    predictions = relationship("Prediction", back_populates="clip")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String, ForeignKey("assets.id"))  # Changed from video_id
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
    clip_id = Column(String, nullable=False, index=True)
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
    confidence = Column(Float, nullable=True)
    hook_type = Column(String, nullable=False, index=True)
    template_type = Column(String, nullable=False)
    metadata = Column(JSON, default={})  # Additional context and calculated metrics

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    actuals_fetched_at = Column(DateTime(timezone=True), nullable=True)


class AccountInsight(Base):
    """
    Cross-Account Learning: Anonymized insights from account performance.

    Stores aggregated patterns and benchmarks from accounts for cross-learning.
    Privacy-preserving: No actual content, only patterns and metrics.
    """
    __tablename__ = "account_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False, index=True)
    niche = Column(String, nullable=False, index=True)
    niche_confidence = Column(Float, default=0.0)

    # Anonymized patterns (JSON)
    top_hook_types = Column(JSON, default=[])
    optimal_duration_range = Column(JSON, default={})  # {min: X, max: Y}
    best_posting_times = Column(JSON, default=[])  # Array of hours
    effective_cta_styles = Column(JSON, default=[])
    visual_preferences = Column(JSON, default=[])

    # Performance benchmarks (aggregated, not raw)
    avg_ctr = Column(Float, default=0.0)
    avg_conversion_rate = Column(Float, default=0.0)
    avg_roas = Column(Float, default=0.0)

    # Metadata
    total_campaigns = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    account_age_days = Column(Integer, default=0)
    opted_in = Column(Boolean, default=True)

    # Timestamps
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_account_opted', 'niche', 'opted_in'),
        Index('idx_account_extracted', 'account_id', 'extracted_at'),
    )


class NichePattern(Base):
    """
    Cross-Account Learning: Aggregated patterns for each niche.

    Stores niche-wide insights aggregated from multiple accounts.
    Updated periodically as new account insights are extracted.
    """
    __tablename__ = "niche_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    niche = Column(String, nullable=False, unique=True, index=True)
    sample_size = Column(Integer, default=0)  # Number of contributing accounts

    # Aggregated patterns (JSON)
    top_hook_types = Column(JSON, default=[])
    optimal_duration = Column(JSON, default={})  # {min: X, max: Y}
    peak_hours = Column(JSON, default=[])
    proven_cta_styles = Column(JSON, default=[])
    winning_visual_patterns = Column(JSON, default=[])

    # Benchmark metrics
    niche_avg_ctr = Column(Float, default=0.0)
    niche_avg_conversion_rate = Column(Float, default=0.0)
    niche_avg_roas = Column(Float, default=0.0)

    # Quality metrics
    confidence_score = Column(Float, default=0.0)

    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_niche_sample', 'niche', 'sample_size'),
    )


class CrossLearningEvent(Base):
    """
    Cross-Account Learning: Track when accounts benefit from cross-learning.

    Logs when niche wisdom is applied to accounts and tracks results.
    """
    __tablename__ = "cross_learning_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False, index=True)
    niche = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # 'wisdom_applied', 'insight_extracted', 'pattern_shared'

    # Details
    wisdom_applied = Column(JSON, default={})
    results = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_account_created', 'account_id', 'created_at'),
        Index('idx_niche_event', 'niche', 'event_type'),
    )


class CreativeFormula(Base):
    """
    Creative DNA Formula storage for winning pattern replication.

    Stores extracted patterns from winning creatives that can be applied
    to new creatives for compounding success. (Agent 48)
    """
    __tablename__ = "creative_formulas"

    formula_id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False, unique=True, index=True)

    # Formula data stored as JSON
    formula_data = Column(JSON, nullable=False)

    # Metadata
    sample_size = Column(Integer, nullable=False)  # Number of winners analyzed
    min_roas_threshold = Column(Float, nullable=False, default=3.0)

    # Performance benchmarks
    avg_roas = Column(Float, nullable=True)
    avg_ctr = Column(Float, nullable=True)
    avg_conversion_rate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CreativeDNAExtraction(Base):
    """
    Individual creative DNA extraction records.

    Tracks DNA extracted from each creative for analysis and comparison.
    """
    __tablename__ = "creative_dna_extractions"

    extraction_id = Column(String, primary_key=True)
    creative_id = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)

    # DNA components stored as JSON
    hook_dna = Column(JSON)
    visual_dna = Column(JSON)
    audio_dna = Column(JSON)
    pacing_dna = Column(JSON)
    copy_dna = Column(JSON)
    cta_dna = Column(JSON)

    # Performance metrics at time of extraction
    ctr = Column(Float)
    roas = Column(Float)
    conversion_rate = Column(Float)

    # Timestamps
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())


class DNAApplication(Base):
    """
    Track DNA applications to new creatives.

    Records when DNA suggestions were applied to creatives and their results.
    """
    __tablename__ = "dna_applications"

    application_id = Column(String, primary_key=True)
    creative_id = Column(String, nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)
    formula_id = Column(String, nullable=False)

    # Suggestions provided
    suggestions = Column(JSON, nullable=False)
    suggestions_count = Column(Integer, default=0)

    # Application results
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    # Performance before/after
    performance_before = Column(JSON)
    performance_after = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
