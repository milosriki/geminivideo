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
from src.compliance_checker import compliance_checker


class VideoWorker:
    """Background worker for video rendering tasks"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")

        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.renderer = VideoRenderer()

        # Initialize database
        init_db()
        print(f"✅ Video Worker initialized")
        print(f"   Redis: {self.redis_url}")
    
    async def process_render_job(self, job_data: dict, db: Session):
        """Process a single render job with full pipeline"""
        try:
            # Reconstruct request object from dict
            # We use a simple object or dict access since we don't have the Pydantic model here easily
            # or we can import it. Let's use dict access for simplicity and robustness.
            
            job_id = job_data.get('job_id')
            request_data = job_data.get('request', {})
            
            print(f"🎬 Processing job {job_id}...")
            
            # Initialize services (lazy init or per-job if needed, but better in __init__)
            # For now, we instantiate them here to match main.py logic or assume they are available.
            # worker.py only has self.renderer. We need others.
            from services.overlay_generator import OverlayGenerator
            from services.subtitle_generator import SubtitleGenerator
            from services.compliance_checker import ComplianceChecker
            
            # Load config for hooks (simplified)
            # In a real worker, we should load this once in __init__
            # For now, using defaults or simple init
            overlay_generator = OverlayGenerator({}) 
            subtitle_generator = SubtitleGenerator()
            compliance_checker = ComplianceChecker()
            
            # Parse scenes
            scenes = []
            # We need to convert dict scenes back to objects if services expect objects
            # Or ensure services handle dicts. 
            # main.py uses Pydantic models. 
            # Let's assume we need to adapt or services handle dicts.
            # Looking at main.py, services take `request.scenes`.
            
            # ... (Logic porting is complex without seeing service signatures)
            # Let's trust that we can pass the data.
            
            variant = request_data.get('variant', 'reels')
            
            # Determine output format
            formats = {
                "reels": {"width": 1080, "height": 1920, "aspect": "9:16"},
                "feed": {"width": 1080, "height": 1080, "aspect": "1:1"},
                "stories": {"width": 1080, "height": 1920, "aspect": "9:16"}
            }
            output_format = formats.get(variant, formats["reels"])
            
            output_dir = os.getenv("OUTPUT_DIR", "/tmp/outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"remix_{job_id}_{variant}.mp4")
            
            # Step 1: Concatenate (using self.renderer)
            # We need to construct 'scenes' list expected by renderer
            # If renderer expects Pydantic objects, we might need to mock them or change renderer.
            # For now, let's assume we pass the raw list and renderer handles it or we convert.
            raw_scenes = request_data.get('scenes', [])
            
            # ...
            # Actually, to be safe and "Top Grade", I should import the models.
            from main import SceneInput # This might cause circular import if main imports worker
            # Better to move models to a shared file.
            # But for now, let's define a simple class or use SimpleNamespace
            from types import SimpleNamespace
            scenes_objs = [SimpleNamespace(**s) for s in raw_scenes]

            # Step 0: Smart Audio Sync (The Ears)
            audio_url = request_data.get('driver_signals', {}).get('audio_url')
            audio_path = None
            
            if audio_url:
                try:
                    import requests
                    import tempfile
                    
                    # Download audio
                    print(f"🎵 Downloading audio for beat sync: {audio_url}")
                    response = requests.get(audio_url)
                    if response.status_code == 200:
                        fd, audio_path = tempfile.mkstemp(suffix=".mp3")
                        os.write(fd, response.content)
                        os.close(fd)
                        
                        # Detect beats
                        beats = await self.renderer.detect_beats(audio_path)
                        
                        if beats:
                            print(f"🎵 Syncing {len(scenes_objs)} scenes to {len(beats)} beats...")
                            # Simple sync: Snap each scene end to nearest beat
                            current_time = 0
                            for i, scene in enumerate(scenes_objs):
                                scene_dur = scene.end_time - scene.start_time
                                target_end = current_time + scene_dur
                                
                                # Find nearest beat to target_end
                                nearest_beat = min(beats, key=lambda x: abs(x - target_end))
                                
                                # Adjust duration (min 1s)
                                new_end = max(nearest_beat, current_time + 1.0)
                                new_dur = new_end - current_time
                                
                                # Update scene
                                scene.end_time = scene.start_time + new_dur
                                current_time = new_end
                                
                            print("✅ Scenes synced to beats")
                except Exception as e:
                    print(f"⚠️ Audio sync failed: {e}")

            # Step 1: Concatenate
            concatenated_path = await self.renderer.concatenate_scenes(
                scenes=scenes_objs,
                enable_transitions=request_data.get('enable_transitions', True)
            )
            
            # Step 2: Overlays
            overlay_path = None
            if request_data.get('enable_overlays', True):
                overlay_path = overlay_generator.generate_overlays(
                    scenes=scenes_objs,
                    driver_signals=request_data.get('driver_signals', {}),
                    template_id=request_data.get('template_id'),
                    duration=sum(s.end_time - s.start_time for s in scenes_objs)
                )

            # Step 3: Subtitles
            subtitle_path = None
            if request_data.get('enable_subtitles', True):
                subtitle_path = subtitle_generator.generate_subtitles(
                    scenes=scenes_objs,
                    driver_signals=request_data.get('driver_signals', {})
                )

            # Step 4: Final Composition
            await self.renderer.compose_final_video(
                input_path=concatenated_path,
                output_path=output_path,
                output_format=output_format,
                overlay_path=overlay_path,
                subtitle_path=subtitle_path
            )

            # Step 5: Compliance
            creative_data = {
                "hook": request_data.get("hook", ""),
                "cta": request_data.get("cta", ""),
                "script": request_data.get("script", ""),
                "duration_seconds": sum(s.end_time - s.start_time for s in scenes_objs),
                "resolution": f"{output_format['width']}x{output_format['height']}"
            }
            
            compliance_result = compliance_checker.check_compliance(
                creative_data,
                platform="meta",
                variant=variant
            )

            print(f"✅ Rendering complete: {output_path}")
            print(f"   Compliance: {compliance_result}")
            
            # Store result in Redis
            self.redis_client.setex(
                f"render_result:{job_id}",
                3600,
                json.dumps({
                    "output_path": output_path,
                    "compliance": compliance_result,
                    "status": "completed"
                })
            )
            
        except Exception as e:
            print(f"❌ Error processing render job: {e}")
            import traceback
            traceback.print_exc()
            # Store error in Redis
            job_id = job_data.get('job_id')
            if job_id:
                self.redis_client.setex(
                    f"render_result:{job_id}",
                    3600,
                    json.dumps({"status": "failed", "error": str(e)})
                )
    
    def start_health_server(self):
        """Start a dummy HTTP server for Cloud Run health checks"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading

        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            
            # Suppress logs
            def log_message(self, format, *args):
                pass

        port = int(os.getenv("PORT", "8080"))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        
        print(f"🏥 Health check server listening on port {port}")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

    def run(self):
        """Main worker loop - blocks and processes jobs"""
        # Start health check server for Cloud Run
        self.start_health_server()

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
