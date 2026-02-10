"""
Video Worker - Background processing for video rendering
Processes render jobs from Redis queue asynchronously
"""
import os
import sys
import time
import json
import asyncio
import tempfile
import traceback
from types import SimpleNamespace
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# Third-party imports
import redis
import aiohttp
import aiofiles
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import SessionLocal, Clip, init_db
from services.renderer import VideoRenderer
from services.overlay_generator import OverlayGenerator
from services.subtitle_generator import SubtitleGenerator
from services.compliance_checker import ComplianceChecker

# Try to import Pro modules (70,000+ lines of Hollywood-grade video code)
try:
    from pro.winning_ads_generator import WinningAdsGenerator
    from pro.voice_generator import VoiceGenerator
    from pro.ai_video_generator import AIVideoGenerator
    from pro.auto_captions import AutoCaptioner
    from pro.color_grading import ColorGrader
    from pro.smart_crop import SmartCropper
    from pro.audio_mixer import AudioMixer
    from pro.timeline_engine import TimelineEngine
    from pro.motion_graphics import MotionGraphicsEngine
    from pro.transitions_library import TransitionsLibrary
    PRO_MODULES_AVAILABLE = True
    print("✅ Pro modules loaded successfully (70,000+ lines activated)")
except ImportError as e:
    PRO_MODULES_AVAILABLE = False
    print(f"⚠️ Pro modules not available: {e}")
    print("Running in basic mode")


def get_video_generator():
    """Get the appropriate video generator based on Pro module availability."""
    if PRO_MODULES_AVAILABLE:
        return AIVideoGenerator()
    else:
        # Fallback to basic generator
        return VideoRenderer()


class VideoWorker:
    """Background worker for video rendering tasks"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")

        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.renderer = VideoRenderer()
        
        # Initialize helper services
        # Note: Ideally these should be initialized once per worker, 
        # but if they hold request-specific state, they might need to be per-job.
        # Assuming stateless or safe to reuse for now based on typical usage.
        self.overlay_generator = OverlayGenerator({}) 
        self.subtitle_generator = SubtitleGenerator()
        self.compliance_checker = ComplianceChecker()

        # Initialize database
        init_db()
        print(f"✅ Video Worker initialized")
        print(f"   Redis: {self.redis_url}")
    
    async def _download_audio(self, audio_url: str) -> Optional[str]:
        """
        Download audio from URL to a temporary file.
        Includes SSRF protection (basic scheme check) and resource management.
        Returns path to temp file or None if failed.
        """
        if not audio_url:
            return None

        # SSRF Protection: Scheme check
        parsed = urlparse(audio_url)
        if parsed.scheme not in ('http', 'https'):
            print(f"⚠️ Invalid audio URL scheme: {audio_url}")
            return None
            
        # SSRF Protection: Localhost/Private IP check needed for high security 
        # (Skipped for now, but recommended for future)

        try:
            print(f"🎵 Downloading audio for beat sync: {audio_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        # Use delete=False so we can close the file handle but keep the file 
                        # for the renderer to use. Caller MUST unlink.
                        fd, audio_path = tempfile.mkstemp(suffix=".mp3")
                        os.close(fd) # Close file descriptor immediately
                        
                        async with aiofiles.open(audio_path, mode='wb') as f:
                            await f.write(await response.read())
                            
                        return audio_path
                    else:
                        print(f"⚠️ Failed to download audio (status {response.status}): {audio_url}")
                        return None
        except Exception as e:
            print(f"⚠️ Audio download failed: {e}")
            return None

    def _parse_scenes(self, raw_scenes: List[Any]) -> List[SimpleNamespace]:
        """Safely parse raw scenes into objects."""
        scenes_objs = []
        if not raw_scenes:
            return []
            
        for i, s in enumerate(raw_scenes):
            try:
                if isinstance(s, dict):
                    scenes_objs.append(SimpleNamespace(**s))
                else:
                    print(f"⚠️ Warning: Skipping invalid scene at index {i} (not a dict)")
            except Exception as e:
                print(f"⚠️ Error parsing scene at index {i}: {e}")
                
        return scenes_objs

    async def _process_render_job(self, job_data: dict, db: Session):
        """Process a single render job with full pipeline"""
        job_id = job_data.get('job_id')
        request_data = job_data.get('request', {})
        print(f"🎬 Processing job {job_id}...")

        audio_path = None
        
        try:
            # 1. Parse Scenes
            scenes_objs = self._parse_scenes(request_data.get('scenes', []))
            if not scenes_objs:
                raise ValueError("No valid scenes provided")

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
            
            # 2. Smart Audio Sync (The Ears)
            audio_url = request_data.get('driver_signals', {}).get('audio_url')
            
            # Download audio safely
            audio_path = await self._download_audio(audio_url)
            
            if audio_path:
                try:
                    # Detect beats
                    beats = await self.renderer.detect_beats(audio_path)
                    
                    if beats:
                        print(f"🎵 Syncing {len(scenes_objs)} scenes to {len(beats)} beats...")
                        # Simple sync: Snap each scene end to nearest beat
                        current_time = 0
                        for i, scene in enumerate(scenes_objs):
                            # Ensure scene has start/end time attributes
                            if not hasattr(scene, 'start_time') or not hasattr(scene, 'end_time'):
                                continue
                                
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
                    print(f"⚠️ Audio sync processing failed: {e}")

            # 3. Concatenate
            concatenated_path = await self.renderer.concatenate_scenes(
                scenes=scenes_objs,
                enable_transitions=request_data.get('enable_transitions', True)
            )
            
            # 4. Overlays
            overlay_path = None
            if request_data.get('enable_overlays', True):
                try:
                    overlay_path = self.overlay_generator.generate_overlays(
                        scenes=scenes_objs,
                        driver_signals=request_data.get('driver_signals', {}),
                        template_id=request_data.get('template_id'),
                        duration=sum((s.end_time - s.start_time) for s in scenes_objs if hasattr(s, 'end_time') and hasattr(s, 'start_time'))
                    )
                except Exception as e:
                    print(f"⚠️ Overlay generation failed: {e}")

            # 5. Subtitles
            subtitle_path = None
            if request_data.get('enable_subtitles', True):
                try:
                    subtitle_path = self.subtitle_generator.generate_subtitles(
                        scenes=scenes_objs,
                        driver_signals=request_data.get('driver_signals', {})
                    )
                except Exception as e:
                    print(f"⚠️ Subtitle generation failed: {e}")

            # 6. Final Composition
            await self.renderer.compose_final_video(
                input_path=concatenated_path,
                output_path=output_path,
                output_format=output_format,
                overlay_path=overlay_path,
                subtitle_path=subtitle_path
            )

            # 7. Compliance
            # Note: Compliance checking might be CPU intensive or sync. 
            # If strictly sync, consider running in executor.
            try:
                creative_data = {
                    "hook": request_data.get("hook", ""),
                    "cta": request_data.get("cta", ""),
                    "script": request_data.get("script", ""),
                    "duration_seconds": sum((s.end_time - s.start_time) for s in scenes_objs if hasattr(s, 'end_time') and hasattr(s, 'start_time')),
                    "resolution": f"{output_format['width']}x{output_format['height']}"
                }
                
                compliance_result = self.compliance_checker.check_compliance(
                    creative_data,
                    platform="meta",
                    variant=variant
                )
            except Exception as e:
                print(f"⚠️ Compliance check failed: {e}")
                compliance_result = {"status": "error", "error": str(e)}

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
            traceback.print_exc()
            # Store error in Redis
            if job_id:
                self.redis_client.setex(
                    f"render_result:{job_id}",
                    3600,
                    json.dumps({"status": "failed", "error": str(e)})
                )
        finally:
            # Resource cleanup
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    print(f"🧹 Cleaned up temporary audio: {audio_path}")
                except OSError as e:
                    print(f"⚠️ Failed to delete temp audio {audio_path}: {e}")
    
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

    async def _worker_loop(self):
        """Async worker loop"""
        print("🚀 Video Worker started, waiting for jobs...")
        print("   Queue: render_queue")
        
        while True:
            try:
                # Use Redis blocking pop compatible with async if available, 
                # or run sync blpop in executor to avoid blocking the loop
                # loop = asyncio.get_running_loop()
                # result = await loop.run_in_executor(None, self.redis_client.blpop, 'render_queue', 5)
                
                # For simplicity and since we are processing one job at a time per worker instance here anyway:
                # We can just use the sync call, but it blocks heartbeats.
                # Better: usage of run_in_executor
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: self.redis_client.blpop('render_queue', timeout=5))
                
                if result:
                    queue_name, job_json = result
                    print(f"\n📥 Received render job")
                    
                    try:
                        job_data = json.loads(job_json)
                        
                        # Process the job
                        db = SessionLocal()
                        try:
                            await self._process_render_job(job_data, db)
                        finally:
                            db.close()
                    except json.JSONDecodeError:
                        print("❌ Failed to decode job JSON")
                else:
                    # Timeout
                    pass
                    
            except KeyboardInterrupt:
                print("\n🛑 Worker stopped by user")
                break
            except Exception as e:
                print(f"❌ Worker error: {e}")
                traceback.print_exc()
                await asyncio.sleep(1)

    def run(self):
        """Main entry point"""
        # Start health check server for Cloud Run
        self.start_health_server()
        
        # Run async loop
        try:
            asyncio.run(self._worker_loop())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    worker = VideoWorker()
    worker.run()
