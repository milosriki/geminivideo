"""
Video Worker - Background processing for video rendering
Processes render jobs from Redis queue asynchronously
"""
import os
import sys
import time
import json
import redis
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import SessionLocal, Clip, init_db
from services.renderer import VideoRenderer


class VideoWorker:
    """Background worker for video rendering tasks"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.renderer = VideoRenderer()
        
        # Initialize database
        init_db()
        print(f"✅ Video Worker initialized")
        print(f"   Redis: {self.redis_url}")
    
    async def process_render_job(self, job_data: dict, db: Session):
        """Process a single render job"""
        try:
            clip_ids = job_data.get('clip_ids', [])
            
            print(f"🎬 Rendering {len(clip_ids)} clips...")
            
            # Fetch clips from database
            clips = []
            for clip_id in clip_ids:
                clip = db.query(Clip).filter(Clip.clip_id == clip_id).first()
                if clip:
                    clips.append(clip)
            
            if not clips:
                print(f"⚠️  No clips found for rendering")
                return
            
            # Render the video
            result_path = await self.renderer.concatenate_scenes(
                clips, 
                enable_transitions=job_data.get('enable_transitions', True)
            )
            
            print(f"✅ Rendering complete: {result_path}")
            
            # Store result path in Redis for retrieval
            job_id = job_data.get('job_id')
            if job_id:
                self.redis_client.setex(
                    f"render_result:{job_id}",
                    3600,  # 1 hour expiry
                    result_path
                )
            
        except Exception as e:
            print(f"❌ Error processing render job: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main worker loop - blocks and processes jobs"""
        print("🚀 Video Worker started, waiting for jobs...")
        print("   Queue: render_queue")
        
        import asyncio
        
        while True:
            try:
                # Block and wait for job from Redis queue
                result = self.redis_client.blpop('render_queue', timeout=5)
                
                if result:
                    queue_name, job_json = result
                    print(f"\n📥 Received render job")
                    
                    # Parse job data
                    job_data = json.loads(job_json)
                    
                    # Process the job
                    db = SessionLocal()
                    try:
                        asyncio.run(self.process_render_job(job_data, db))
                    finally:
                        db.close()
                else:
                    # Timeout - just loop again
                    pass
                    
            except KeyboardInterrupt:
                print("\n🛑 Worker stopped by user")
                break
            except Exception as e:
                print(f"❌ Worker error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)  # Avoid tight loop on persistent errors


if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()
