"""
Database Models for Ultimate Pipeline
- SQLAlchemy models
- Async database operations
- Supabase/PostgreSQL compatible
"""

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Optional, Dict, Any
import enum
import os
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo")

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


class RenderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# MODELS
# ============================================================================

class Campaign(Base):
    """Campaign model - tracks ad campaigns"""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # For multi-tenant
    product_name = Column(String, nullable=False)
    offer = Column(String, nullable=False)
    target_avatar = Column(String)
    pain_points = Column(JSON)
    desires = Column(JSON)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)

    # Results
    total_generated = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    blueprints = relationship("Blueprint", back_populates="campaign", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="campaign", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="campaign", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_name": self.product_name,
            "offer": self.offer,
            "target_avatar": self.target_avatar,
            "pain_points": self.pain_points,
            "desires": self.desires,
            "status": self.status.value if self.status else None,
            "total_generated": self.total_generated,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Blueprint(Base):
    """Blueprint model - stores generated ad blueprints"""
    __tablename__ = "blueprints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"))

    # Content
    title = Column(String)
    hook_text = Column(Text)
    hook_type = Column(String)
    script_json = Column(JSON)  # Full blueprint as JSON

    # Scores
    council_score = Column(Float)
    predicted_roas = Column(Float)
    confidence = Column(Float)
    verdict = Column(String)  # APPROVE or REJECT
    rank = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="blueprints")
    videos = relationship("Video", back_populates="blueprint")
    render_jobs = relationship("RenderJob", back_populates="blueprint")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "title": self.title,
            "hook_text": self.hook_text,
            "hook_type": self.hook_type,
            "script_json": self.script_json,
            "council_score": self.council_score,
            "predicted_roas": self.predicted_roas,
            "confidence": self.confidence,
            "verdict": self.verdict,
            "rank": self.rank,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RenderJob(Base):
    """RenderJob model - tracks rendering progress"""
    __tablename__ = "render_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    blueprint_id = Column(String, ForeignKey("blueprints.id", ondelete="CASCADE"))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"))

    # Config
    platform = Column(String)
    quality = Column(String)
    add_captions = Column(Boolean, default=True)
    smart_crop = Column(Boolean, default=True)

    # Status
    status = Column(Enum(RenderStatus), default=RenderStatus.PENDING)
    progress = Column(Float, default=0.0)
    current_stage = Column(String)
    error = Column(Text)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    campaign = relationship("Campaign", back_populates="render_jobs")
    blueprint = relationship("Blueprint", back_populates="render_jobs")
    videos = relationship("Video", back_populates="render_job")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "blueprint_id": self.blueprint_id,
            "campaign_id": self.campaign_id,
            "platform": self.platform,
            "quality": self.quality,
            "add_captions": self.add_captions,
            "smart_crop": self.smart_crop,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Video(Base):
    """Video model - stores rendered video metadata"""
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String, ForeignKey("campaigns.id", ondelete="CASCADE"))
    blueprint_id = Column(String, ForeignKey("blueprints.id", ondelete="CASCADE"))
    render_job_id = Column(String, ForeignKey("render_jobs.id", ondelete="SET NULL"))

    # Storage
    storage_path = Column(String)  # GCS path or local path
    storage_url = Column(String)   # Signed URL

    # Metadata
    duration_seconds = Column(Float)
    resolution = Column(String)
    file_size_bytes = Column(Integer)
    platform = Column(String)

    # Performance (filled by Learning Loop)
    actual_roas = Column(Float)
    impressions = Column(Integer)
    clicks = Column(Integer)
    conversions = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="videos")
    blueprint = relationship("Blueprint", back_populates="videos")
    render_job = relationship("RenderJob", back_populates="videos")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "blueprint_id": self.blueprint_id,
            "render_job_id": self.render_job_id,
            "storage_path": self.storage_path,
            "storage_url": self.storage_url,
            "duration_seconds": self.duration_seconds,
            "resolution": self.resolution,
            "file_size_bytes": self.file_size_bytes,
            "platform": self.platform,
            "actual_roas": self.actual_roas,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# DATABASE ENGINE & SESSION MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages database engine and sessions"""

    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = None
        self.async_session_maker = None

    async def initialize(self):
        """Initialize database engine and create tables"""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Close database engine"""
        if self.engine:
            await self.engine.dispose()

    def get_session(self) -> AsyncSession:
        """Get a new database session"""
        if not self.async_session_maker:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
        return self.async_session_maker()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncSession:
    """Dependency for getting database sessions"""
    async with db_manager.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================================
# REPOSITORY CLASS
# ============================================================================

class CampaignRepository:
    """Repository class for CRUD operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # CAMPAIGN OPERATIONS
    # ========================================================================

    async def create_campaign(self, data: Dict[str, Any]) -> Campaign:
        """Create a new campaign"""
        campaign = Campaign(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            product_name=data["product_name"],
            offer=data["offer"],
            target_avatar=data.get("target_avatar"),
            pain_points=data.get("pain_points", []),
            desires=data.get("desires", []),
            status=CampaignStatus[data.get("status", "DRAFT").upper()]
        )
        self.session.add(campaign)
        await self.session.commit()
        await self.session.refresh(campaign)
        return campaign

    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID"""
        result = await self.session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        user_id: Optional[str] = None,
        status: Optional[CampaignStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Campaign]:
        """List campaigns with optional filters"""
        query = select(Campaign)

        if user_id:
            query = query.where(Campaign.user_id == user_id)
        if status:
            query = query.where(Campaign.status == status)

        query = query.order_by(Campaign.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_campaign(self, campaign_id: str, data: Dict[str, Any]) -> Optional[Campaign]:
        """Update a campaign"""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None

        # Update fields
        for key, value in data.items():
            if key == "status" and isinstance(value, str):
                value = CampaignStatus[value.upper()]
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        campaign.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(campaign)
        return campaign

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign"""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return False

        await self.session.delete(campaign)
        await self.session.commit()
        return True

    # ========================================================================
    # BLUEPRINT OPERATIONS
    # ========================================================================

    async def add_blueprint(self, campaign_id: str, blueprint_data: Dict[str, Any]) -> Blueprint:
        """Add a blueprint to a campaign"""
        blueprint = Blueprint(
            id=blueprint_data.get("id", str(uuid.uuid4())),
            campaign_id=campaign_id,
            title=blueprint_data.get("title"),
            hook_text=blueprint_data.get("hook_text"),
            hook_type=blueprint_data.get("hook_type"),
            script_json=blueprint_data.get("script_json", {}),
            council_score=blueprint_data.get("council_score"),
            predicted_roas=blueprint_data.get("predicted_roas"),
            confidence=blueprint_data.get("confidence"),
            verdict=blueprint_data.get("verdict"),
            rank=blueprint_data.get("rank")
        )
        self.session.add(blueprint)
        await self.session.commit()
        await self.session.refresh(blueprint)
        return blueprint

    async def get_blueprint(self, blueprint_id: str) -> Optional[Blueprint]:
        """Get a blueprint by ID"""
        result = await self.session.execute(
            select(Blueprint).where(Blueprint.id == blueprint_id)
        )
        return result.scalar_one_or_none()

    async def get_blueprints(
        self,
        campaign_id: str,
        approved_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Blueprint]:
        """Get blueprints for a campaign"""
        query = select(Blueprint).where(Blueprint.campaign_id == campaign_id)

        if approved_only:
            query = query.where(Blueprint.verdict == "APPROVE")

        query = query.order_by(Blueprint.rank.asc())

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_blueprint(self, blueprint_id: str, data: Dict[str, Any]) -> Optional[Blueprint]:
        """Update a blueprint"""
        blueprint = await self.get_blueprint(blueprint_id)
        if not blueprint:
            return None

        for key, value in data.items():
            if hasattr(blueprint, key):
                setattr(blueprint, key, value)

        await self.session.commit()
        await self.session.refresh(blueprint)
        return blueprint

    # ========================================================================
    # RENDER JOB OPERATIONS
    # ========================================================================

    async def create_render_job(self, job_data: Dict[str, Any]) -> RenderJob:
        """Create a new render job"""
        render_job = RenderJob(
            id=job_data.get("id", str(uuid.uuid4())),
            blueprint_id=job_data["blueprint_id"],
            campaign_id=job_data["campaign_id"],
            platform=job_data.get("platform", "youtube"),
            quality=job_data.get("quality", "1080p"),
            add_captions=job_data.get("add_captions", True),
            smart_crop=job_data.get("smart_crop", True),
            status=RenderStatus.PENDING
        )
        self.session.add(render_job)
        await self.session.commit()
        await self.session.refresh(render_job)
        return render_job

    async def get_render_job(self, job_id: str) -> Optional[RenderJob]:
        """Get a render job by ID"""
        result = await self.session.execute(
            select(RenderJob).where(RenderJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_render_job(self, job_id: str, data: Dict[str, Any]) -> Optional[RenderJob]:
        """Update a render job"""
        job = await self.get_render_job(job_id)
        if not job:
            return None

        for key, value in data.items():
            if key == "status" and isinstance(value, str):
                value = RenderStatus[value.upper()]
            if hasattr(job, key):
                setattr(job, key, value)

        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_render_jobs(
        self,
        campaign_id: Optional[str] = None,
        blueprint_id: Optional[str] = None,
        status: Optional[RenderStatus] = None
    ) -> List[RenderJob]:
        """Get render jobs with optional filters"""
        query = select(RenderJob)

        if campaign_id:
            query = query.where(RenderJob.campaign_id == campaign_id)
        if blueprint_id:
            query = query.where(RenderJob.blueprint_id == blueprint_id)
        if status:
            query = query.where(RenderJob.status == status)

        query = query.order_by(RenderJob.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    # ========================================================================
    # VIDEO OPERATIONS
    # ========================================================================

    async def create_video(self, video_data: Dict[str, Any]) -> Video:
        """Create a new video record"""
        video = Video(
            id=video_data.get("id", str(uuid.uuid4())),
            campaign_id=video_data["campaign_id"],
            blueprint_id=video_data["blueprint_id"],
            render_job_id=video_data.get("render_job_id"),
            storage_path=video_data.get("storage_path"),
            storage_url=video_data.get("storage_url"),
            duration_seconds=video_data.get("duration_seconds"),
            resolution=video_data.get("resolution"),
            file_size_bytes=video_data.get("file_size_bytes"),
            platform=video_data.get("platform")
        )
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video

    async def get_video(self, video_id: str) -> Optional[Video]:
        """Get a video by ID"""
        result = await self.session.execute(
            select(Video).where(Video.id == video_id)
        )
        return result.scalar_one_or_none()

    async def get_videos(
        self,
        campaign_id: Optional[str] = None,
        blueprint_id: Optional[str] = None
    ) -> List[Video]:
        """Get videos with optional filters"""
        query = select(Video)

        if campaign_id:
            query = query.where(Video.campaign_id == campaign_id)
        if blueprint_id:
            query = query.where(Video.blueprint_id == blueprint_id)

        query = query.order_by(Video.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_video(self, video_id: str, data: Dict[str, Any]) -> Optional[Video]:
        """Update a video record"""
        video = await self.get_video(video_id)
        if not video:
            return None

        for key, value in data.items():
            if hasattr(video, key):
                setattr(video, key, value)

        await self.session.commit()
        await self.session.refresh(video)
        return video

    async def update_video_performance(
        self,
        video_id: str,
        actual_roas: Optional[float] = None,
        impressions: Optional[int] = None,
        clicks: Optional[int] = None,
        conversions: Optional[int] = None
    ) -> Optional[Video]:
        """Update video performance metrics"""
        video = await self.get_video(video_id)
        if not video:
            return None

        if actual_roas is not None:
            video.actual_roas = actual_roas
        if impressions is not None:
            video.impressions = impressions
        if clicks is not None:
            video.clicks = clicks
        if conversions is not None:
            video.conversions = conversions

        await self.session.commit()
        await self.session.refresh(video)
        return video


# ============================================================================
# INITIALIZATION UTILITIES
# ============================================================================

async def init_database(database_url: str = DATABASE_URL):
    """Initialize the database"""
    db_manager.database_url = database_url
    await db_manager.initialize()
    print(f"✅ Database initialized at {database_url}")


async def close_database():
    """Close the database connection"""
    await db_manager.close()
    print("✅ Database connection closed")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def example_usage():
        """Example usage of database operations"""
        # Initialize database
        await init_database()

        # Create a repository instance
        async with db_manager.get_session() as session:
            repo = CampaignRepository(session)

            # Create a campaign
            campaign = await repo.create_campaign({
                "product_name": "Ultimate Fitness App",
                "offer": "50% off first month",
                "target_avatar": "Busy professionals aged 25-40",
                "pain_points": ["No time for gym", "Expensive trainers"],
                "desires": ["Get fit at home", "Flexible schedule"]
            })
            print(f"Created campaign: {campaign.id}")

            # Add a blueprint
            blueprint = await repo.add_blueprint(campaign.id, {
                "title": "Transform Your Body in 30 Days",
                "hook_text": "Stop wasting money on gym memberships...",
                "hook_type": "pain_agitation",
                "script_json": {"scenes": []},
                "council_score": 8.5,
                "predicted_roas": 4.2,
                "confidence": 0.85,
                "verdict": "APPROVE",
                "rank": 1
            })
            print(f"Created blueprint: {blueprint.id}")

            # Create render job
            job = await repo.create_render_job({
                "blueprint_id": blueprint.id,
                "campaign_id": campaign.id,
                "platform": "youtube",
                "quality": "1080p"
            })
            print(f"Created render job: {job.id}")

            # Create video
            video = await repo.create_video({
                "campaign_id": campaign.id,
                "blueprint_id": blueprint.id,
                "render_job_id": job.id,
                "storage_path": "/videos/output.mp4",
                "duration_seconds": 30.5,
                "resolution": "1920x1080",
                "file_size_bytes": 15000000,
                "platform": "youtube"
            })
            print(f"Created video: {video.id}")

            # Get campaign with blueprints
            campaign = await repo.get_campaign(campaign.id)
            blueprints = await repo.get_blueprints(campaign.id, approved_only=True)
            print(f"Campaign has {len(blueprints)} approved blueprints")

        await close_database()

    asyncio.run(example_usage())
