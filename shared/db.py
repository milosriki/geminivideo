"""
Database configuration and models
Provides SQLAlchemy setup for PostgreSQL persistence
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from typing import Optional

# Database URL from environment or default to local PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=10, pool_recycle=120)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Asset(Base):
    """Video asset model"""
    __tablename__ = "assets"

    asset_id = Column(String, primary_key=True, index=True)
    path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    resolution = Column(String)
    format = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing", index=True)
    source = Column(String, default="local")
    metadata = Column(JSON, default={})


class Clip(Base):
    """Video clip/scene model"""
    __tablename__ = "clips"

    clip_id = Column(String, primary_key=True, index=True)
    asset_id = Column(String, nullable=False, index=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    scene_score = Column(Float, default=0.0)
    ctr_score = Column(Float, default=0.0, index=True)  # CTR prediction score
    thumbnail_url = Column(String)
    features = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class Emotion(Base):
    """Emotion detection results for clips"""
    __tablename__ = "emotions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clip_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, nullable=False, index=True)
    timestamp = Column(Float, nullable=False)  # Timestamp within video
    emotion = Column(String, nullable=False)  # dominant emotion
    emotion_scores = Column(JSON)  # All emotion scores
    confidence = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let caller handle it


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
