#!/usr/bin/env python3
"""
Database initialization script
Creates tables and optionally seeds with test data
"""

import sys
import os
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from db import init_db, check_db_connection, engine, SessionLocal
from db import Asset, Clip, Emotion
import uuid
from datetime import datetime


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    if not check_db_connection():
        print("❌ Database connection failed!")
        print("Please check your DATABASE_URL environment variable.")
        print("Default: postgresql://geminivideo:geminivideo@localhost:5432/geminivideo")
        return False
    
    try:
        init_db()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def seed_test_data():
    """Seed database with test data"""
    print("\nSeeding test data...")
    
    db = SessionLocal()
    
    try:
        # Create a test asset
        asset_id = str(uuid.uuid4())
        asset = Asset(
            asset_id=asset_id,
            path="/tmp/test_videos/sample.mp4",
            filename="sample.mp4",
            size_bytes=5242880,
            duration_seconds=30.0,
            resolution="1920x1080",
            format="mp4",
            status="completed",
            source="local"
        )
        db.add(asset)
        
        # Create test clips
        emotions = ["happy", "neutral", "surprise", "happy", "neutral"]
        
        for i in range(5):
            clip_id = str(uuid.uuid4())
            start_time = i * 6.0
            end_time = start_time + 6.0
            
            clip = Clip(
                clip_id=clip_id,
                asset_id=asset_id,
                start_time=start_time,
                end_time=end_time,
                duration=6.0,
                scene_score=0.5 + (i * 0.1),
                features={
                    "motion_energy": 0.6 + (i * 0.05),
                    "emotion": emotions[i],
                    "emotion_confidence": 0.7 + (i * 0.05),
                    "scene_index": i
                }
            )
            db.add(clip)
            
            # Add emotion data
            emotion = Emotion(
                clip_id=clip_id,
                asset_id=asset_id,
                timestamp=start_time,
                emotion=emotions[i],
                emotion_scores={
                    "happy": 0.7 if emotions[i] == "happy" else 0.2,
                    "neutral": 0.7 if emotions[i] == "neutral" else 0.2,
                    "surprise": 0.7 if emotions[i] == "surprise" else 0.1
                },
                confidence=0.7 + (i * 0.05)
            )
            db.add(emotion)
        
        db.commit()
        print(f"✅ Test data seeded successfully!")
        print(f"   - Created 1 test asset (ID: {asset_id})")
        print(f"   - Created 5 test clips with emotions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding test data: {e}")
    finally:
        db.close()


def verify_setup():
    """Verify the database setup"""
    print("\nVerifying database setup...")
    
    db = SessionLocal()
    
    try:
        # Count assets
        asset_count = db.query(Asset).count()
        clip_count = db.query(Clip).count()
        emotion_count = db.query(Emotion).count()
        
        print(f"✅ Database verification complete:")
        print(f"   - Assets: {asset_count}")
        print(f"   - Clips: {clip_count}")
        print(f"   - Emotions: {emotion_count}")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
    finally:
        db.close()


def main():
    """Main initialization function"""
    print("=" * 60)
    print("GeminiVideo Database Initialization")
    print("=" * 60)
    
    # Check environment
    db_url = os.getenv("DATABASE_URL", "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo")
    print(f"\nDatabase URL: {db_url}")
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    # Ask about seeding test data
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        seed_test_data()
    else:
        print("\nSkipping test data (use --seed flag to add test data)")
    
    # Verify setup
    verify_setup()
    
    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the Drive Intel service: python -m uvicorn src.main:app --reload --port 8081")
    print("2. Ingest a video: curl -X POST http://localhost:8081/ingest/local/folder ...")
    print("3. View results in the frontend: http://localhost:5173")
    print()


if __name__ == "__main__":
    main()
