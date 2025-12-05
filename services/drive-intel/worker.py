"""
Drive Worker - Background processing for video analysis
Processes jobs from Redis queue asynchronously
"""
import os
import sys
import time
import redis
from sqlalchemy.orm import Session
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import SessionLocal, Asset, Clip, Emotion, init_db
from services.scene_detector import SceneDetectorService
from services.feature_extractor import FeatureExtractorService


class DriveWorker:
    """Background worker for video analysis tasks"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")

        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.scene_detector = SceneDetectorService()
        self.feature_extractor = FeatureExtractorService()

        # Initialize database
        init_db()
        print(f"✅ Drive Worker initialized")
        print(f"   Redis: {self.redis_url}")
        
    def process_analysis_job(self, asset_id: str, db: Session):
        """Process a single analysis job"""
        try:
            # Update status to ANALYZING
            asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
            if not asset:
                print(f"⚠️  Asset {asset_id} not found")
                return
            
            asset.status = "ANALYZING"
            db.commit()
            print(f"📊 Analyzing asset: {asset_id} ({asset.filename})")
            
            # Get video path
            video_path = asset.path
            if not os.path.exists(video_path):
                print(f"⚠️  Video file not found: {video_path}")
                asset.status = "ERROR"
                db.commit()
                return
            
            # Detect scenes
            print(f"   🎬 Detecting scenes...")
            scenes = self.scene_detector.detect_scenes(video_path)
            print(f"   ✅ Found {len(scenes)} scenes")
            
            # Process each scene
            for idx, (start_time, end_time) in enumerate(scenes):
                clip_id = f"{asset_id}_clip_{idx}"
                duration = end_time - start_time
                
                # Extract features
                features = self.feature_extractor.extract_features(
                    video_path, start_time, end_time
                )
                
                # Detect emotion for the clip
                emotion_data = self.detect_emotion_for_clip(
                    video_path, start_time, end_time, db
                )
                
                # Create clip record
                clip = Clip(
                    clip_id=clip_id,
                    asset_id=asset_id,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    scene_score=features.get('motion_score', 0.0),
                    ctr_score=0.0,  # Will be calculated by ML service
                    features=features
                )
                db.merge(clip)
                
                # Save emotion if detected
                if emotion_data:
                    emotion = Emotion(
                        clip_id=clip_id,
                        asset_id=asset_id,
                        timestamp=start_time,
                        emotion=emotion_data['emotion'],
                        emotion_scores=emotion_data.get('scores', {}),
                        confidence=emotion_data.get('confidence', 0.0)
                    )
                    db.add(emotion)
            
            # Update asset status to READY
            asset.status = "READY"
            db.commit()
            print(f"✅ Analysis complete for {asset_id}")
            
        except Exception as e:
            print(f"❌ Error processing asset {asset_id}: {e}")
            import traceback
            traceback.print_exc()

            # Update status to ERROR - reuse asset from initial query to avoid N+1
            try:
                if asset:
                    asset.status = "ERROR"
                    db.commit()
            except NameError:
                # Asset was never fetched (early failure)
                pass
    
    def detect_emotion_for_clip(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float,
        db: Session
    ) -> Optional[dict]:
        """
        Detect emotion using Google Cloud Vision API
        Extracts middle frame and analyzes facial emotions
        """
        try:
            import cv2
            from google.cloud import vision
            
            # Extract middle frame
            mid_time = (start_time + end_time) / 2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(mid_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return None
            
            # Encode frame to bytes
            _, buffer = cv2.imencode('.jpg', frame)
            image_bytes = buffer.tobytes()
            
            # Call Google Vision API
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_bytes)
            response = client.face_detection(image=image)
            
            if response.face_annotations:
                face = response.face_annotations[0]
                
                # Map Google Vision likelihood to emotion
                emotion_scores = {
                    'joy': self._likelihood_to_score(face.joy_likelihood),
                    'sorrow': self._likelihood_to_score(face.sorrow_likelihood),
                    'anger': self._likelihood_to_score(face.anger_likelihood),
                    'surprise': self._likelihood_to_score(face.surprise_likelihood)
                }
                
                # Determine dominant emotion
                dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                confidence = emotion_scores[dominant_emotion]
                
                # Map to simplified emotions
                if dominant_emotion == 'joy' and confidence >= 0.6:
                    emotion = 'happy'
                elif dominant_emotion == 'sorrow' and confidence >= 0.6:
                    emotion = 'sad'
                else:
                    emotion = 'neutral'
                
                return {
                    'emotion': emotion,
                    'scores': emotion_scores,
                    'confidence': confidence
                }
            
            return None
            
        except ImportError:
            print("⚠️  Google Cloud Vision not available, skipping emotion detection")
            return None
        except Exception as e:
            print(f"⚠️  Emotion detection failed: {e}")
            return None
    
    def _likelihood_to_score(self, likelihood) -> float:
        """Convert Google Vision likelihood enum to score 0-1"""
        likelihood_map = {
            0: 0.0,   # UNKNOWN
            1: 0.1,   # VERY_UNLIKELY
            2: 0.3,   # UNLIKELY
            3: 0.5,   # POSSIBLE
            4: 0.7,   # LIKELY
            5: 0.9    # VERY_LIKELY
        }
        return likelihood_map.get(likelihood, 0.0)
    
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
        
        print("🚀 Drive Worker started, waiting for jobs...")
        print("   Queue: analysis_queue")
        
        while True:
            try:
                # Block and wait for job from Redis queue
                result = self.redis_client.blpop('analysis_queue', timeout=5)
                
                if result:
                    queue_name, asset_id = result
                    print(f"\n📥 Received job: {asset_id}")
                    
                    # Process the job
                    db = SessionLocal()
                    try:
                        self.process_analysis_job(asset_id, db)
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
    worker = DriveWorker()
    worker.run()
