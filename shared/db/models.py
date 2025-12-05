from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Text, ForeignKey, Date, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
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


# Drive Intel - FAISS Search Models (Legacy - migrating to pgvector)
class EmbeddingMetadata(Base):
    __tablename__ = "embedding_metadata"

    external_id = Column(String, primary_key=True)
    internal_id = Column(Integer, nullable=False, unique=True)
    metadata = Column(JSON, default={})
    embedding_dimension = Column(Integer)
    index_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Vector Database Models (Agent 39 - pgvector)
class CreativeEmbedding(Base):
    """Store creative/blueprint embeddings for similarity search."""
    __tablename__ = "creative_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creative_id = Column(String, nullable=False, unique=True, index=True)
    creative_type = Column(String, nullable=False)  # blueprint, video, hook

    # Text embedding (text-embedding-3-large = 3072 dimensions)
    text_embedding = Column(Vector(3072))

    # Visual embedding (CLIP = 512 dimensions)
    visual_embedding = Column(Vector(512))

    # Metadata
    campaign_id = Column(String, index=True)
    hook_text = Column(Text)
    hook_type = Column(String)

    # Performance metrics (for learning from winners)
    council_score = Column(Float)
    predicted_roas = Column(Float)
    actual_roas = Column(Float)
    impressions = Column(Integer)
    conversions = Column(Integer)

    # Additional metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Create indexes for vector similarity search
    __table_args__ = (
        Index('idx_creative_text_embedding', 'text_embedding', postgresql_using='ivfflat', postgresql_ops={'text_embedding': 'vector_cosine_ops'}),
        Index('idx_creative_visual_embedding', 'visual_embedding', postgresql_using='ivfflat', postgresql_ops={'visual_embedding': 'vector_cosine_ops'}),
    )


class HookEmbedding(Base):
    """Store hook embeddings for finding similar performing hooks."""
    __tablename__ = "hook_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hook_id = Column(String, nullable=False, unique=True, index=True)
    hook_text = Column(Text, nullable=False)
    hook_type = Column(String)  # pain_agitation, curiosity, social_proof, etc.

    # Embedding vector (text-embedding-3-large)
    embedding = Column(Vector(3072), nullable=False)

    # Product/vertical context
    product_category = Column(String)
    target_avatar = Column(String)
    pain_points = Column(JSON, default=[])

    # Performance data
    avg_ctr = Column(Float)
    avg_roas = Column(Float)
    total_impressions = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    success_rate = Column(Float)  # % of campaigns where this hook worked

    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_hook_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )


class KnowledgeBaseVector(Base):
    """Store marketing knowledge vectors for RAG-powered generation."""
    __tablename__ = "knowledge_base_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String, nullable=False, unique=True, index=True)
    content_type = Column(String, nullable=False)  # best_practice, case_study, pattern, technique

    # Content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)

    # Embedding (text-embedding-3-large)
    embedding = Column(Vector(3072), nullable=False)

    # Categorization
    category = Column(String)  # hook_writing, script_structure, visual_design, etc.
    tags = Column(JSON, default=[])

    # Quality/relevance signals
    confidence_score = Column(Float)  # How confident we are in this knowledge
    usage_count = Column(Integer, default=0)  # How many times used in generation
    success_rate = Column(Float)  # Success rate when applied

    # Source tracking
    source = Column(String)  # manual, learned, competitor_analysis
    source_url = Column(String)

    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_knowledge_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
        Index('idx_knowledge_category', 'category'),
    )


class ProductEmbedding(Base):
    """Store product/offer embeddings for finding similar winning patterns."""
    __tablename__ = "product_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String, nullable=False, unique=True, index=True)

    # Product info
    product_name = Column(String, nullable=False)
    product_description = Column(Text)
    offer = Column(String)

    # Embedding (text-embedding-3-large)
    embedding = Column(Vector(3072), nullable=False)

    # Target audience
    target_avatar = Column(String)
    pain_points = Column(JSON, default=[])
    desires = Column(JSON, default=[])

    # Historical performance
    total_campaigns = Column(Integer, default=0)
    avg_roas = Column(Float)
    best_hook_types = Column(JSON, default=[])  # List of hook types that worked
    best_creative_patterns = Column(JSON, default=[])  # List of successful patterns

    # Similar products (for cold start)
    similar_products = Column(JSON, default=[])  # List of {product_id, similarity_score}

    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_product_embedding', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )


class SemanticCacheEntry(Base):
    """
    Semantic cache for AI operations with embedding-based similarity matching.

    AGENT 46: 10x LEVERAGE - Semantic Caching

    Instead of exact match caching, use embedding similarity to reuse results:
    - "Score this fitness ad" ≈ "Rate this gym advertisement" → Cache hit!
    - 80%+ cache hit rate possible
    - Massive cost savings on AI operations

    Use cases:
    - Creative scoring (hook scores, council votes)
    - Hook analysis and classification
    - CTR prediction
    - Script generation
    """
    __tablename__ = "semantic_cache_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_id = Column(String, nullable=False, unique=True, index=True)

    # Query information
    query_type = Column(String, nullable=False, index=True)  # creative_score, hook_analysis, ctr_prediction, etc.
    query_text = Column(Text, nullable=False)
    query_hash = Column(String, index=True)  # Hash for exact match optimization

    # Embedding for semantic similarity search (text-embedding-3-large)
    query_embedding = Column(Vector(3072), nullable=False)

    # Cached result
    result = Column(JSON, nullable=False)  # The cached computation result
    result_type = Column(String)  # Type of result (score, analysis, prediction, etc.)

    # Cache metadata
    ttl_seconds = Column(Integer)  # Time-to-live (null = no expiration)
    expires_at = Column(DateTime(timezone=True))  # Computed expiration time

    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True))

    # Performance metrics
    compute_time_ms = Column(Float)  # How long original computation took
    avg_similarity_on_hit = Column(Float)  # Average similarity score when cache hit

    # Metadata
    metadata = Column(JSON, default={})  # Additional context (model version, etc.)
    is_warmed = Column(Boolean, default=False)  # Pre-populated during cache warming

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for fast semantic search
    __table_args__ = (
        Index('idx_semantic_cache_embedding', 'query_embedding', postgresql_using='ivfflat', postgresql_ops={'query_embedding': 'vector_cosine_ops'}),
        Index('idx_semantic_cache_type_hash', 'query_type', 'query_hash'),
        Index('idx_semantic_cache_expires', 'expires_at'),
        Index('idx_semantic_cache_access', 'access_count'),
    )
