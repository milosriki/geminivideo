# Agent 1: Database Architect

## Your Mission
Implement PostgreSQL persistence layer to replace in-memory storage across all services.

## Priority: HIGH (Others depend on you!)

## Tasks

### 1. Database Schema Design
Create `shared/db/schema.sql`:
```sql
-- Assets table
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    size_bytes BIGINT,
    duration_seconds FLOAT,
    resolution TEXT,
    format TEXT,
    ingested_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'processing',
    source TEXT
);

-- Clips table
CREATE TABLE clips (
    clip_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets(asset_id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    duration FLOAT NOT NULL,
    scene_score FLOAT,
    psychology_score JSONB,
    hook_strength JSONB,
    novelty_score JSONB,
    composite_score FLOAT,
    emotion_data JSONB,
    embedding VECTOR(512),
    thumbnail_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_clips_asset ON clips(asset_id);
CREATE INDEX idx_clips_score ON clips(composite_score DESC);

-- Predictions table
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY,
    clip_id UUID REFERENCES clips(clip_id),
    predicted_ctr FLOAT,
    predicted_band TEXT,
    actual_ctr FLOAT,
    ad_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Jobs table
CREATE TABLE render_jobs (
    job_id UUID PRIMARY KEY,
    storyboard JSONB NOT NULL,
    status TEXT DEFAULT 'queued',
    output_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### 2. Database Connection
Create `shared/db.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/geminivideo'
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3. Models
Create `shared/models.py`:
```python
from sqlalchemy import Column, String, Float, Integer, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from .db import Base

class Asset(Base):
    __tablename__ = "assets"
    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    size_bytes = Column(BigInteger)
    duration_seconds = Column(Float)
    resolution = Column(String)
    format = Column(String)
    ingested_at = Column(DateTime, server_default=func.now())
    status = Column(String, default='processing')
    source = Column(String)

class Clip(Base):
    __tablename__ = "clips"
    clip_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.asset_id', ondelete='CASCADE'))
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    scene_score = Column(Float)
    psychology_score = Column(JSONB)
    hook_strength = Column(JSONB)
    novelty_score = Column(JSONB)
    composite_score = Column(Float)
    emotion_data = Column(JSONB)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clip_id = Column(UUID(as_uuid=True), ForeignKey('clips.clip_id'))
    predicted_ctr = Column(Float)
    predicted_band = Column(String)
    actual_ctr = Column(Float)
    ad_id = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class RenderJob(Base):
    __tablename__ = "render_jobs"
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storyboard = Column(JSONB, nullable=False)
    status = Column(String, default='queued')
    output_url = Column(String)
    error_message = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
```

### 4. Docker Compose
Update `docker-compose.yml`:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: geminivideo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./shared/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql

volumes:
  postgres_data:
```

### 5. Update Drive Intel Service
Replace in-memory dicts in `services/drive-intel/src/main.py`:
```python
from shared.db import get_db
from shared.models import Asset, Clip
from sqlalchemy.orm import Session

@app.post("/ingest/local/folder")
async def ingest_local_folder(request: IngestRequest, db: Session = Depends(get_db)):
    asset = Asset(
        path=request.path,
        filename=request.path.split("/")[-1],
        size_bytes=10485760,
        duration_seconds=30.0,
        resolution="1920x1080",
        format="mp4",
        status="processing"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Trigger processing with asset.asset_id
    return {"asset_id": str(asset.asset_id), "status": "processing"}
```

## Dependencies
- `pip install sqlalchemy psycopg2-binary`
- PostgreSQL 15 running (Docker)

## Deliverables
- [ ] `shared/db/schema.sql` created
- [ ] `shared/db.py` with connection
- [ ] `shared/models.py` with all models
- [ ] `docker-compose.yml` with Postgres
- [ ] Drive Intel service updated to use DB
- [ ] Gateway API updated to use DB
- [ ] Video Agent updated to use DB
- [ ] Tests pass

## Branch
`agent-1-database-persistence`

## Blockers
None - you're first!

## Who Depends On You
- Agent 3 (needs DB for predictions)
- Agent 8 (needs DB for Drive integration)
- All agents (eventually need persistence)
