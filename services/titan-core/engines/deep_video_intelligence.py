import os
import json
import time
import google.generativeai as genai
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Try to import heavy libraries, handle failure gracefully
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available. Visual motion analysis will be disabled.")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️ MediaPipe not available. Pose detection will be disabled.")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper not available. Audio transcription will be disabled.")

from backend.services.supabase_connector import supabase_connector

# PRO-GRADE SCORING RUBRIC (2025 Winning Patterns)
PRO_GRADE_SCORING_RUBRIC = """
Score video 0-100 based on 2025 winning patterns:

+20 High energy transformation (before/after)
+15 Under 3-second hook
+15 Direct response language (you, your problem)
+10 Social proof (testimonials, results)
+10 Urgency/scarcity
+10 Clear CTA
+10 Professional production quality
+8 Mobile-optimized (9:16)
+7 Emotional trigger (pain/agitation)
+5 Trending audio/visual style

Current winning hooks this week: {real_time_hooks}
"""

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

class DeepVideoIntelligence:
    def __init__(self):
        # Use the thinking model for deep reasoning
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-thinking-exp-1219")
        self.vision_model = genai.GenerativeModel(self.model_name)
        
        # Initialize MediaPipe Pose if available
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5
            )
        else:
            self.pose = None
        
        # Initialize Whisper if available
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                print("🎙️ WHISPER: Initialized")
            except Exception as e:
                print(f"⚠️ Whisper Init Error: {e}")
                self.whisper_model = None
        else:
            self.whisper_model = None

        print(f"🧠 DEEP VIDEO INTELLIGENCE: Initialized (Gemini 2.0: Active, CV2: {CV2_AVAILABLE}, MP: {MEDIAPIPE_AVAILABLE})")

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Performs deep multi-layer analysis of the video.
        """
        if not os.path.exists(video_path):
            return {"error": "Video file not found"}

        print(f"🕵️‍♀️ DEEP SCAN: Analyzing {video_path}...")

        # Layer 1: Technical Analysis (MediaPipe/CV2)
        technical = self._technical_analysis(video_path)
        
        # Layer 2: Semantic Understanding (Gemini Vision)
        # If CV2 failed to get scene changes, we pass empty list or defaults
        semantic = self._semantic_analysis(video_path, technical.get('scene_changes', []))
        
        # Layer 3: Ad Psychology (Gemini + Whisper)
        psychology = self._psychology_analysis(video_path, semantic)
        
        # Calculate composite score
        ad_score = self._calculate_ad_score(technical, semantic, psychology)
        
        result = {
            "technical_metrics": technical,
            "semantic_analysis": semantic,
            "psychological_profile": psychology,
            "visual_score": ad_score, # Keeping 'visual_score' key for compatibility
            "deep_ad_score": ad_score
        }
        
        # Persist to Supabase
        try:
            supabase_connector.save_analysis(video_path, result)
        except Exception as e:
            print(f"⚠️ Supabase Save Failed: {e}")
        
        return result

    def _technical_analysis(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts objective metrics: motion energy, pose correctness (basic), scene changes.
        """
        if not CV2_AVAILABLE:
            return {
                "duration_sec": 0,
                "fps": 0,
                "avg_motion_energy": 0.0,
                "is_high_energy": False,
                "scene_changes": [],
                "note": "OpenCV not available"
            }

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            energy_scores = []
            prev_landmarks = None
            
            # Process every Nth frame for speed
            step = int(fps / 2) if fps > 0 else 15 # 2 checks per second
            
            for i in range(0, frame_count, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_energy = 0.0
                
                if MEDIAPIPE_AVAILABLE and self.pose:
                    # Convert to RGB for MediaPipe
                    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.pose.process(image_rgb)
                    
                    if results.pose_landmarks:
                        # Calculate simple motion energy based on landmark movement
                        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark])
                        if prev_landmarks is not None:
                            diff = np.linalg.norm(landmarks - prev_landmarks, axis=1)
                            current_energy = np.mean(diff) * 100 # Scale up
                        prev_landmarks = landmarks
                
                energy_scores.append(current_energy)
                
            cap.release()
            
            avg_energy = np.mean(energy_scores) if energy_scores else 0
            
            return {
                "duration_sec": duration,
                "fps": fps,
                "avg_motion_energy": float(avg_energy),
                "is_high_energy": avg_energy > 5.0,
                "scene_changes": [0, 3, duration/2, duration-3] if duration > 6 else [0, duration/2] # Placeholder
            }
        except Exception as e:
            print(f"⚠️ Technical Analysis Error: {e}")
            return {"error": str(e)}

    def _extract_frames(self, video_path: str, timestamps: List[float]) -> List[Any]:
        """Extracts frames at specific timestamps."""
        if not CV2_AVAILABLE:
            return []
            
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            for ts in timestamps:
                frame_id = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cap.read()
                if ret:
                    # Convert to PIL Image for Gemini
                    from PIL import Image
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img)
                    frames.append(pil_img)
            cap.release()
        except Exception as e:
            print(f"⚠️ Frame Extraction Error: {e}")
            
        return frames

    def _semantic_analysis(self, video_path: str, key_timestamps: List[float]) -> Dict[str, Any]:
        """
        Uses Gemini 2.0 to understand WHAT is happening in key frames.
        """
        # If no timestamps or CV2 missing, try to upload video file directly to Gemini API if supported
        # For now, we'll assume if CV2 is missing, we skip visual semantic analysis or use a text-only fallback
        
        frames = self._extract_frames(video_path, key_timestamps)
        
        if not frames:
             # Fallback: Try to use Gemini Thinking on just the filename/context if visual extraction fails
             return {"narrative": "Visual analysis skipped (OpenCV missing)", "error": "No frames extracted"}

        # Prepare prompt for Gemini
        prompt = """
        Analyze these key frames from a video ad.
        For each frame, identify:
        1. The action taking place.
        2. The emotion displayed.
        3. Any text overlay visible.
        
        Then, summarize the visual narrative arc:
        - What is the hook?
        - What is the conflict/pain?
        - What is the resolution/transformation?
        
        Return valid JSON.
        """
        
        try:
            # Gemini 2.0 supports list of images + text
            inputs = frames + [prompt]
            response = self.vision_model.generate_content(inputs)
            
            # Parse JSON from response
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"❌ Semantic Analysis Error: {e}")
            return {"error": str(e), "narrative": "Analysis failed"}

    def _psychology_analysis(self, video_path: str, semantic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes transcript + visual context for psychological triggers using the Pro-Grade Rubric.
        """
        transcript_text = ""
        if self.whisper_model:
            try:
                result = self.whisper_model.transcribe(video_path)
                transcript_text = result["text"]
            except Exception as e:
                print(f"⚠️ Transcription failed: {e}")
        
        # Use Andromeda Logic for Prompt Generation
        from backend_core.engines.andromeda_prompts import get_andromeda_roas_prompt
        
        ad_data = {
            "transcript": transcript_text,
            "visual_summary": semantic_data,
            "real_time_hooks": "Pattern Interrupts, ASMR Unboxing, 'Stop Scrolling' text"
        }
        
        prompt = get_andromeda_roas_prompt(ad_data)
        
        try:
            response = self.vision_model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            # Fallback if Gemini fails
            print(f"⚠️ Psychology Analysis Error: {e}")
            return {"error": str(e), "predicted_roas_score": 50}

    def _calculate_ad_score(self, technical, semantic, psychology) -> float:
        """
        Returns the score calculated by the LLM based on the Pro-Grade Rubric.
        """
        # The LLM now does the heavy lifting with the rubric
        if "predicted_roas_score" in psychology:
            return float(psychology["predicted_roas_score"])
        if "Final Score" in psychology:
            return float(psychology["Final Score"])
        if "score" in psychology:
            return float(psychology["score"])
            
        # Fallback if JSON structure varies
        return 50.0
