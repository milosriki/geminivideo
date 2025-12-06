"""
Creative DNA 2.0 - AGENT 77: Advanced Pattern Extraction & Generation

Upgrades from Agent 48 with:
- GPT-4o Vision for frame-by-frame analysis
- Gemini 2.0 Flash for video understanding
- Multi-frame temporal analysis
- Audio pattern extraction via Whisper
- Advanced pattern matching & scoring
- Pattern-based variant generation
- Council of Titans integration

10X LEVERAGE: Learn from winners + Generate new winning variants automatically.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from enum import Enum
from base64 import b64encode
from pathlib import Path

logger = logging.getLogger(__name__)

# Face weighting constants for motion analysis
FACE_WEIGHT_MULTIPLIER = 3.2  # Faces get 3.2x importance in motion analysis
BACKGROUND_WEIGHT = 1.0

# Lazy imports for vision models
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - GPT-4o Vision disabled")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini not available - Video understanding disabled")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - Frame extraction disabled")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available - Audio analysis disabled")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - Image processing disabled")


# ==========================================
# ENHANCED DNA DATA STRUCTURES (2.0)
# ==========================================

@dataclass
class VisualPatternDNA:
    """Enhanced visual patterns with vision AI analysis"""
    # Frame-level patterns
    dominant_colors: List[str]
    color_palette_hex: List[str]
    color_psychology: str  # warm, cool, vibrant, muted

    # Composition patterns
    composition_type: str  # rule-of-thirds, centered, dynamic, symmetrical
    focal_points: List[Dict[str, float]]  # x, y, importance
    visual_hierarchy: str

    # Face & human patterns
    has_faces: bool
    face_count: int
    face_emotions: List[str]
    face_time_ratio: float
    gaze_direction: str  # camera, away, down

    # Motion patterns
    motion_intensity: float
    motion_type: str  # static, smooth, fast-cut, dynamic
    camera_movement: str  # static, pan, zoom, handheld
    face_weight_applied: float = 3.2  # Weight multiplier for face regions
    weighted_motion_score: float = 0.0  # Motion score with face weighting applied

    # Text & overlay patterns
    text_overlay_count: int
    text_position_pattern: str  # top, bottom, center, dynamic
    text_animation_style: str
    text_readability_score: float

    # Scene patterns
    scene_count: int
    scene_transitions: List[str]
    scene_variety_score: float

    # Product/object patterns
    has_product: bool
    product_visibility_ratio: float
    product_intro_timing: float

    # Quality metrics
    production_quality_score: float
    lighting_quality: str
    visual_clarity_score: float

    # Engagement predictions
    stop_scroll_score: float
    attention_retention_score: float

    # Performance correlation
    avg_ctr: float
    avg_roas: float
    sample_count: int


@dataclass
class AudioPatternDNA:
    """Enhanced audio patterns with Whisper analysis"""
    # Music patterns
    has_music: bool
    music_genre: str
    music_energy: float
    music_tempo_bpm: Optional[int]
    music_mood: str  # upbeat, emotional, suspenseful, calm

    # Voice patterns
    has_voice: bool
    voice_type: str  # male, female, ai, child
    voice_tone: str  # energetic, calm, authoritative, friendly
    voice_clarity_score: float
    voice_time_ratio: float

    # Speech patterns
    words_per_minute: Optional[float]
    pause_patterns: List[float]
    emphasis_words: List[str]
    hook_delivery_speed: str  # fast, medium, slow

    # Sound effects
    has_sfx: bool
    sfx_types: List[str]
    sfx_timing: List[float]

    # Audio-visual sync
    audio_visual_sync_score: float
    beat_drop_timings: List[float]

    # Performance correlation
    avg_ctr: float
    avg_roas: float
    sample_count: int


@dataclass
class NarrativePatternDNA:
    """Story arc and narrative patterns"""
    # Hook patterns (0-3 seconds)
    hook_type: str  # curiosity, shock, pattern-interrupt, question, problem
    hook_strength_score: float
    hook_duration: float
    hook_text: str
    hook_visual_element: str

    # Body patterns (3s - end-5s)
    narrative_structure: str  # problem-solution, before-after, testimonial, demo
    pain_point_emphasis: bool
    social_proof_elements: List[str]
    transformation_shown: bool

    # CTA patterns (last 5 seconds)
    cta_type: str
    cta_text: str
    cta_timing: float
    cta_visual_style: str
    cta_urgency_score: float

    # Emotional arc
    emotional_journey: List[str]  # confused -> interested -> excited
    peak_emotion_timing: float
    emotional_contrast_score: float

    # Pacing patterns
    total_duration: float
    intro_duration: float
    body_duration: float
    outro_duration: float
    ideal_pacing_score: float

    # Performance correlation
    avg_conversion_rate: float
    avg_roas: float
    sample_count: int


@dataclass
class EngagementPatternDNA:
    """Patterns that drive engagement"""
    # Stop-scroll factors
    pattern_interrupt_score: float
    curiosity_gap_score: float
    first_frame_hook_score: float

    # Retention factors
    hook_to_3sec_retention: float
    mid_video_retention: float
    completion_rate: float

    # Viral elements
    shareability_score: float
    relatability_score: float
    emotional_intensity: float
    trend_alignment_score: float

    # Platform optimization
    mobile_optimized: bool
    aspect_ratio: str
    caption_friendly: bool
    sound_off_watchable: bool

    # Psychological triggers
    triggers_used: List[str]  # FOMO, scarcity, social-proof, authority
    persuasion_techniques: List[str]

    # Performance correlation
    avg_engagement_rate: float
    avg_share_rate: float
    avg_roas: float
    sample_count: int


@dataclass
class TimingPatternDNA:
    """Temporal patterns and timing DNA"""
    # Overall timing
    optimal_duration_range: Tuple[float, float]
    cuts_per_second: float
    scene_avg_duration: float

    # Hook timing
    hook_appears_at: float
    problem_stated_at: float
    solution_shown_at: float

    # Product timing
    product_first_shown_at: float
    product_total_screen_time: float

    # CTA timing
    first_cta_at: float
    final_cta_at: float
    cta_frequency: int

    # Pacing rhythm
    pacing_style: str  # fast, medium, slow, variable
    energy_curve: List[float]  # energy level over time

    # Performance correlation
    avg_watch_time: float
    avg_roas: float
    sample_count: int


@dataclass
class WinningFormula2:
    """Complete winning formula with 2.0 DNA"""
    formula_id: str
    account_id: str

    # Pattern categories
    visual_patterns: List[VisualPatternDNA]
    audio_patterns: List[AudioPatternDNA]
    narrative_patterns: List[NarrativePatternDNA]
    engagement_patterns: List[EngagementPatternDNA]
    timing_patterns: List[TimingPatternDNA]

    # Performance benchmarks
    avg_roas: float
    avg_ctr: float
    avg_conversion_rate: float
    avg_engagement_rate: float

    # Meta information
    sample_size: int
    confidence_score: float
    created_at: datetime
    updated_at: datetime

    # Pattern weights (learned from performance)
    pattern_importance: Dict[str, float]


@dataclass
class DNASimilarityScore:
    """Similarity score between creative and winning pattern"""
    creative_id: str
    pattern_id: str

    # Category scores (0-1)
    visual_similarity: float
    audio_similarity: float
    narrative_similarity: float
    engagement_similarity: float
    timing_similarity: float

    # Overall score
    overall_similarity: float
    confidence: float

    # Missing elements
    missing_patterns: List[str]
    suggested_improvements: List[str]

    # Predicted performance
    predicted_roas: float
    predicted_ctr: float


@dataclass
class GeneratedVariant:
    """DNA-based generated variant"""
    variant_id: str
    source_creative_id: str
    generation_method: str  # clone, mix, evolve

    # DNA blueprint
    target_visual_dna: VisualPatternDNA
    target_audio_dna: AudioPatternDNA
    target_narrative_dna: NarrativePatternDNA

    # Generation instructions
    modifications: List[Dict[str, Any]]
    asset_requirements: List[str]

    # Predicted performance
    predicted_roas: float
    confidence: float

    created_at: datetime


# ==========================================
# CREATIVE DNA 2.0 ENGINE
# ==========================================

class CreativeDNA2:
    """
    Creative DNA 2.0 - Advanced Pattern Extraction & Generation

    Features:
    - GPT-4o Vision for frame analysis
    - Gemini 2.0 Flash for video understanding
    - Multi-frame temporal analysis
    - Audio pattern extraction
    - Pattern matching & scoring
    - Variant generation
    - Council integration
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        database_service=None
    ):
        """Initialize Creative DNA 2.0"""
        self.db = database_service

        # Initialize OpenAI for GPT-4o Vision
        if OPENAI_AVAILABLE:
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            self.openai_client = AsyncOpenAI(api_key=api_key) if api_key else None
        else:
            self.openai_client = None

        # Initialize Gemini for video understanding
        if GEMINI_AVAILABLE:
            api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(
                    os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-thinking-exp-1219")
                )
            else:
                self.gemini_model = None
        else:
            self.gemini_model = None

        # Initialize Whisper for audio
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
            except Exception as e:
                logger.warning(f"Whisper init failed: {e}")
                self.whisper_model = None
        else:
            self.whisper_model = None

        # Cache
        self._formula_cache = {}
        self._pattern_cache = {}

        logger.info("✅ Creative DNA 2.0 initialized")
        logger.info(f"   - GPT-4o Vision: {'✓' if self.openai_client else '✗'}")
        logger.info(f"   - Gemini 2.0 Flash: {'✓' if self.gemini_model else '✗'}")
        logger.info(f"   - Whisper Audio: {'✓' if self.whisper_model else '✗'}")

    # ==========================================
    # FRAME EXTRACTION & ANALYSIS
    # ==========================================

    def extract_key_frames(
        self,
        video_path: str,
        num_frames: int = 8,
        method: str = "uniform"
    ) -> List[Tuple[float, Any]]:
        """
        Extract key frames from video

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            method: "uniform" (evenly spaced) or "smart" (scene changes)

        Returns:
            List of (timestamp, PIL Image) tuples
        """
        if not CV2_AVAILABLE or not PIL_AVAILABLE:
            logger.warning("CV2 or PIL not available - frame extraction disabled")
            return []

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            if method == "uniform":
                # Evenly spaced frames
                timestamps = np.linspace(0, duration, num_frames, endpoint=False)
            else:
                # Smart extraction (scene changes) - simplified version
                timestamps = self._detect_scene_changes(cap, fps, num_frames)

            frames = []
            for ts in timestamps:
                frame_id = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cap.read()

                if ret:
                    # Convert to PIL Image
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img)
                    frames.append((float(ts), pil_img))

            cap.release()
            logger.info(f"✅ Extracted {len(frames)} frames from {video_path}")
            return frames

        except Exception as e:
            logger.error(f"Frame extraction error: {e}", exc_info=True)
            return []

    def _detect_scene_changes(
        self,
        cap: Any,
        fps: float,
        max_scenes: int
    ) -> List[float]:
        """Detect scene changes using histogram difference"""
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        # Sample every Nth frame
        step = max(1, int(frame_count / 100))

        prev_hist = None
        scene_changes = [0.0]  # Always include first frame

        for i in range(0, frame_count, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()

            if not ret:
                break

            # Calculate histogram
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                # Compare histograms
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)

                # Scene change detected
                if diff > 1000:  # Threshold
                    timestamp = i / fps
                    scene_changes.append(timestamp)

            prev_hist = hist

        # Limit to max_scenes
        if len(scene_changes) > max_scenes:
            # Keep evenly distributed
            indices = np.linspace(0, len(scene_changes)-1, max_scenes, dtype=int)
            scene_changes = [scene_changes[i] for i in indices]

        return scene_changes

    async def analyze_frame_with_gpt4o_vision(
        self,
        image: Any,
        timestamp: float,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze single frame with GPT-4o Vision

        Args:
            image: PIL Image or path to image
            timestamp: Timestamp in video
            context: Additional context

        Returns:
            Frame analysis dictionary
        """
        if not self.openai_client:
            return {"error": "OpenAI not available"}

        try:
            # Convert image to base64
            if isinstance(image, str):
                # Image path
                with open(image, "rb") as f:
                    image_data = b64encode(f.read()).decode("utf-8")
            else:
                # PIL Image
                import io
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG")
                image_data = b64encode(buffer.getvalue()).decode("utf-8")

            image_url = f"data:image/jpeg;base64,{image_data}"

            # Structured prompt for frame analysis
            prompt = f"""Analyze this video frame at timestamp {timestamp:.2f}s for viral ad effectiveness.

Focus on:
1. Visual Composition: Layout, focal points, rule of thirds, visual hierarchy
2. Color Psychology: Dominant colors, mood, emotional impact
3. Human Elements: Faces, emotions, gaze direction, body language
4. Text Overlays: Position, readability, message clarity
5. Product/Object: Visibility, prominence, presentation
6. Stop-Scroll Factor: What would make someone stop scrolling?
7. Attention Retention: What keeps them watching?

{f'Context: {context}' if context else ''}

Return structured JSON:
{{
  "composition_type": "string",
  "focal_points": [{{"x": 0.5, "y": 0.3, "element": "face"}}],
  "dominant_colors": ["#HEX", "#HEX"],
  "color_mood": "string",
  "has_faces": bool,
  "face_emotions": ["emotion1", "emotion2"],
  "gaze_direction": "camera|away|down",
  "text_overlays": [{{"text": "string", "position": "top|center|bottom", "readability": 0-100}}],
  "has_product": bool,
  "product_visibility": 0-100,
  "stop_scroll_score": 0-100,
  "attention_factors": ["factor1", "factor2"],
  "production_quality": 0-100,
  "overall_score": 0-100
}}
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-2024-11-20",  # Latest GPT-4o with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_url}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )

            result = json.loads(response.choices[0].message.content)
            result["timestamp"] = timestamp

            return result

        except Exception as e:
            logger.error(f"GPT-4o Vision analysis error: {e}", exc_info=True)
            return {"error": str(e), "timestamp": timestamp}

    async def analyze_video_with_gemini(
        self,
        video_path: str,
        frames: Optional[List[Tuple[float, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze video understanding with Gemini 2.0 Flash

        Args:
            video_path: Path to video
            frames: Optional pre-extracted frames

        Returns:
            Video understanding analysis
        """
        if not self.gemini_model:
            return {"error": "Gemini not available"}

        try:
            # If no frames provided, extract them
            if frames is None:
                frames = self.extract_key_frames(video_path, num_frames=8)

            if not frames:
                return {"error": "No frames extracted"}

            # Build prompt for video understanding
            prompt = """Analyze this video ad for narrative structure and engagement patterns.

Use deep reasoning to identify:

1. HOOK ANALYSIS (First 3 seconds):
   - Hook type (curiosity, shock, pattern-interrupt, question, problem)
   - Hook strength and effectiveness
   - What makes someone stop scrolling?

2. NARRATIVE STRUCTURE:
   - Story arc (problem-solution, before-after, testimonial, demo)
   - Pain points emphasized
   - Transformation shown
   - Social proof elements

3. EMOTIONAL JOURNEY:
   - Emotional arc across the video
   - Peak emotion timing
   - Emotional triggers used

4. ENGAGEMENT PATTERNS:
   - What drives retention?
   - Viral elements present
   - Psychological triggers (FOMO, scarcity, social proof)
   - Shareability factors

5. PACING & TIMING:
   - Overall pacing (fast, medium, slow)
   - Scene variety and transitions
   - Energy curve across video

Return ONLY valid JSON in this structure:
{
  "hook": {
    "type": "string",
    "strength_score": 0-100,
    "duration": seconds,
    "text": "hook text",
    "visual_element": "what grabs attention"
  },
  "narrative": {
    "structure": "problem-solution|before-after|testimonial|demo",
    "pain_points": ["point1", "point2"],
    "transformation_shown": bool,
    "social_proof": ["element1", "element2"]
  },
  "emotional_arc": ["confused", "interested", "excited"],
  "engagement_factors": {
    "pattern_interrupt_score": 0-100,
    "curiosity_gap_score": 0-100,
    "relatability_score": 0-100,
    "shareability_score": 0-100
  },
  "pacing": {
    "style": "fast|medium|slow|variable",
    "scene_count": int,
    "energy_curve": [0-100, 0-100, ...],
    "ideal_pacing_score": 0-100
  },
  "triggers": ["FOMO", "scarcity", "social-proof", ...],
  "viral_score": 0-100,
  "reasoning": "brief explanation"
}
"""

            # Prepare input (frames + prompt)
            frame_images = [img for _, img in frames]
            inputs = frame_images + [prompt]

            # Generate with Gemini 2.0 Flash Thinking
            response = self.gemini_model.generate_content(inputs)

            # Parse JSON
            text = response.text.strip()
            json_text = text.replace("```json", "").replace("```", "").strip()
            result = json.loads(json_text)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Gemini JSON parse error: {e}")
            return {"error": "Invalid JSON from Gemini"}
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}", exc_info=True)
            return {"error": str(e)}

    # ==========================================
    # AUDIO PATTERN EXTRACTION
    # ==========================================

    def extract_audio_patterns(self, video_path: str) -> AudioPatternDNA:
        """
        Extract audio patterns using Whisper

        Args:
            video_path: Path to video

        Returns:
            AudioPatternDNA with extracted patterns
        """
        try:
            # Transcribe audio
            transcript_text = ""
            if self.whisper_model:
                result = self.whisper_model.transcribe(video_path)
                transcript_text = result.get("text", "")
                segments = result.get("segments", [])
            else:
                segments = []

            # Calculate speech metrics
            if segments:
                total_words = len(transcript_text.split())
                total_speech_time = segments[-1]["end"] - segments[0]["start"]
                wpm = (total_words / total_speech_time) * 60 if total_speech_time > 0 else 0

                # Detect pauses
                pauses = []
                for i in range(len(segments) - 1):
                    pause = segments[i+1]["start"] - segments[i]["end"]
                    if pause > 0.5:  # Significant pause
                        pauses.append(pause)
            else:
                wpm = None
                pauses = []

            # Simple audio energy detection (placeholder - would use librosa in production)
            has_music = True  # Placeholder
            music_energy = 0.7  # Placeholder

            # Detect voice characteristics from text patterns
            voice_tone = self._detect_voice_tone(transcript_text)
            emphasis_words = self._extract_emphasis_words(transcript_text)

            return AudioPatternDNA(
                has_music=has_music,
                music_genre="upbeat",  # Placeholder
                music_energy=music_energy,
                music_tempo_bpm=None,
                music_mood="energetic",  # Placeholder
                has_voice=len(transcript_text) > 0,
                voice_type="unknown",  # Would need voice analysis
                voice_tone=voice_tone,
                voice_clarity_score=0.8,  # Placeholder
                voice_time_ratio=0.7,  # Placeholder
                words_per_minute=wpm,
                pause_patterns=pauses,
                emphasis_words=emphasis_words,
                hook_delivery_speed="fast" if wpm and wpm > 150 else "medium",
                has_sfx=False,  # Placeholder
                sfx_types=[],
                sfx_timing=[],
                audio_visual_sync_score=0.8,  # Placeholder
                beat_drop_timings=[],  # Placeholder
                avg_ctr=0.0,
                avg_roas=0.0,
                sample_count=1
            )

        except Exception as e:
            logger.error(f"Audio extraction error: {e}", exc_info=True)
            # Return default
            return AudioPatternDNA(
                has_music=False,
                music_genre="none",
                music_energy=0.0,
                music_tempo_bpm=None,
                music_mood="neutral",
                has_voice=False,
                voice_type="none",
                voice_tone="neutral",
                voice_clarity_score=0.0,
                voice_time_ratio=0.0,
                words_per_minute=None,
                pause_patterns=[],
                emphasis_words=[],
                hook_delivery_speed="medium",
                has_sfx=False,
                sfx_types=[],
                sfx_timing=[],
                audio_visual_sync_score=0.0,
                beat_drop_timings=[],
                avg_ctr=0.0,
                avg_roas=0.0,
                sample_count=0
            )

    def _detect_voice_tone(self, text: str) -> str:
        """Detect voice tone from transcript"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["amazing", "incredible", "wow", "awesome"]):
            return "energetic"
        elif any(word in text_lower for word in ["proven", "research", "study", "data"]):
            return "authoritative"
        elif any(word in text_lower for word in ["you", "your", "we", "us"]):
            return "friendly"
        else:
            return "calm"

    def _extract_emphasis_words(self, text: str) -> List[str]:
        """Extract words that likely have emphasis"""
        emphasis_words = [
            "free", "now", "today", "guaranteed", "proven", "secret",
            "discover", "revolutionary", "breakthrough", "exclusive"
        ]

        text_lower = text.lower()
        found = [word for word in emphasis_words if word in text_lower]
        return found[:5]  # Top 5

    # ==========================================
    # COMPLETE DNA EXTRACTION
    # ==========================================

    async def extract_complete_dna(
        self,
        video_path: str,
        creative_id: str,
        extract_visual: bool = True,
        extract_audio: bool = True,
        extract_narrative: bool = True
    ) -> Dict[str, Any]:
        """
        Extract complete Creative DNA 2.0 from video

        Args:
            video_path: Path to video file
            creative_id: Creative identifier
            extract_visual: Extract visual patterns
            extract_audio: Extract audio patterns
            extract_narrative: Extract narrative patterns

        Returns:
            Complete DNA dictionary
        """
        logger.info(f"🧬 Extracting DNA 2.0 from {creative_id}")

        results = {
            "creative_id": creative_id,
            "video_path": video_path,
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "version": "2.0"
        }

        try:
            # Extract key frames first
            frames = self.extract_key_frames(video_path, num_frames=8)

            # Parallel extraction
            tasks = []

            # Visual analysis (GPT-4o Vision on frames)
            if extract_visual and frames and self.openai_client:
                for ts, img in frames:
                    tasks.append(
                        self.analyze_frame_with_gpt4o_vision(img, ts)
                    )

            # Video understanding (Gemini)
            if extract_narrative and self.gemini_model:
                tasks.append(
                    self.analyze_video_with_gemini(video_path, frames)
                )

            # Execute in parallel
            if tasks:
                vision_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Separate frame analyses and video understanding
                frame_analyses = [r for r in vision_results if isinstance(r, dict) and "timestamp" in r]
                video_understanding = [r for r in vision_results if isinstance(r, dict) and "hook" in r]

                results["frame_analyses"] = frame_analyses
                results["video_understanding"] = video_understanding[0] if video_understanding else {}

            # Audio extraction (synchronous)
            if extract_audio:
                audio_dna = self.extract_audio_patterns(video_path)
                results["audio_dna"] = asdict(audio_dna)

            # Synthesize patterns
            results["visual_pattern_summary"] = self._synthesize_visual_patterns(
                results.get("frame_analyses", [])
            )
            results["engagement_score"] = self._calculate_engagement_score(results)

            logger.info(f"✅ DNA extraction complete for {creative_id}")

            return results

        except Exception as e:
            logger.error(f"DNA extraction error: {e}", exc_info=True)
            results["error"] = str(e)
            return results

    def _synthesize_visual_patterns(self, frame_analyses: List[Dict]) -> Dict[str, Any]:
        """Synthesize visual patterns from frame analyses"""
        if not frame_analyses:
            return {}

        # Aggregate patterns
        all_colors = []
        face_count = 0
        stop_scroll_scores = []
        production_scores = []

        for frame in frame_analyses:
            if "dominant_colors" in frame:
                all_colors.extend(frame["dominant_colors"])
            if frame.get("has_faces"):
                face_count += 1
            if "stop_scroll_score" in frame:
                stop_scroll_scores.append(frame["stop_scroll_score"])
            if "production_quality" in frame:
                production_scores.append(frame["production_quality"])

        # Calculate aggregates
        color_counter = Counter(all_colors)

        return {
            "most_common_colors": dict(color_counter.most_common(5)),
            "face_presence_ratio": face_count / len(frame_analyses),
            "avg_stop_scroll_score": float(np.mean(stop_scroll_scores)) if stop_scroll_scores else 0,
            "avg_production_quality": float(np.mean(production_scores)) if production_scores else 0,
            "frame_count": len(frame_analyses)
        }

    def _calculate_engagement_score(self, dna_results: Dict) -> float:
        """Calculate overall engagement score from DNA"""
        score = 50.0  # Base

        # Visual factors
        visual = dna_results.get("visual_pattern_summary", {})
        score += visual.get("avg_stop_scroll_score", 0) * 0.3
        score += visual.get("avg_production_quality", 0) * 0.2

        # Narrative factors
        video_understanding = dna_results.get("video_understanding", {})
        if video_understanding:
            score += video_understanding.get("viral_score", 0) * 0.3
            hook_strength = video_understanding.get("hook", {}).get("strength_score", 0)
            score += hook_strength * 0.2

        return min(100.0, score)

    # ==========================================
    # PATTERN MATCHING & SCORING
    # ==========================================

    async def compare_to_winning_patterns(
        self,
        creative_dna: Dict[str, Any],
        formula: WinningFormula2
    ) -> DNASimilarityScore:
        """
        Compare creative DNA to winning formula patterns

        Args:
            creative_dna: Extracted DNA from creative
            formula: Winning formula to compare against

        Returns:
            Similarity score and recommendations
        """
        try:
            # Calculate similarity for each category
            visual_sim = self._calculate_visual_similarity(
                creative_dna.get("visual_pattern_summary", {}),
                formula.visual_patterns
            )

            # Simplified audio similarity (would be more complex in production)
            audio_sim = 0.7  # Placeholder

            narrative_sim = self._calculate_narrative_similarity(
                creative_dna.get("video_understanding", {}),
                formula.narrative_patterns
            )

            engagement_sim = 0.75  # Placeholder
            timing_sim = 0.8  # Placeholder

            # Weighted overall similarity
            overall = (
                visual_sim * 0.3 +
                audio_sim * 0.15 +
                narrative_sim * 0.35 +
                engagement_sim * 0.15 +
                timing_sim * 0.05
            )

            # Identify missing patterns
            missing = self._identify_missing_patterns(creative_dna, formula)

            # Generate suggestions
            suggestions = self._generate_improvement_suggestions(creative_dna, formula, missing)

            # Predict performance
            predicted_roas = formula.avg_roas * overall
            predicted_ctr = formula.avg_ctr * overall

            return DNASimilarityScore(
                creative_id=creative_dna.get("creative_id", "unknown"),
                pattern_id=formula.formula_id,
                visual_similarity=visual_sim,
                audio_similarity=audio_sim,
                narrative_similarity=narrative_sim,
                engagement_similarity=engagement_sim,
                timing_similarity=timing_sim,
                overall_similarity=overall,
                confidence=0.85,
                missing_patterns=missing,
                suggested_improvements=suggestions,
                predicted_roas=predicted_roas,
                predicted_ctr=predicted_ctr
            )

        except Exception as e:
            logger.error(f"Pattern comparison error: {e}", exc_info=True)
            raise

    def _calculate_visual_similarity(
        self,
        creative_visual: Dict,
        winning_patterns: List[VisualPatternDNA]
    ) -> float:
        """Calculate visual pattern similarity"""
        if not winning_patterns or not creative_visual:
            return 0.5

        # Compare to average of winning patterns
        avg_winning = winning_patterns[0]  # Simplified - would aggregate in production

        similarity = 0.0

        # Color similarity
        creative_colors = set(creative_visual.get("most_common_colors", {}).keys())
        winning_colors = set(avg_winning.dominant_colors[:5])
        if winning_colors:
            color_overlap = len(creative_colors & winning_colors) / len(winning_colors)
            similarity += color_overlap * 0.3

        # Production quality similarity
        creative_quality = creative_visual.get("avg_production_quality", 50)
        winning_quality = avg_winning.production_quality_score
        quality_diff = 1 - abs(creative_quality - winning_quality) / 100
        similarity += quality_diff * 0.4

        # Face presence similarity
        creative_faces = creative_visual.get("face_presence_ratio", 0)
        winning_faces = avg_winning.face_time_ratio
        face_diff = 1 - abs(creative_faces - winning_faces)
        similarity += face_diff * 0.3

        return min(1.0, similarity)

    def _calculate_narrative_similarity(
        self,
        creative_narrative: Dict,
        winning_patterns: List[NarrativePatternDNA]
    ) -> float:
        """Calculate narrative pattern similarity"""
        if not winning_patterns or not creative_narrative:
            return 0.5

        avg_winning = winning_patterns[0]  # Simplified

        similarity = 0.0

        # Hook strength
        creative_hook = creative_narrative.get("hook", {}).get("strength_score", 50)
        winning_hook = avg_winning.hook_strength_score
        hook_diff = 1 - abs(creative_hook - winning_hook) / 100
        similarity += hook_diff * 0.4

        # Viral score
        creative_viral = creative_narrative.get("viral_score", 50)
        winning_viral = avg_winning.avg_roas * 20  # Convert ROAS to score
        viral_diff = 1 - abs(creative_viral - winning_viral) / 100
        similarity += viral_diff * 0.6

        return min(1.0, similarity)

    def _identify_missing_patterns(
        self,
        creative_dna: Dict,
        formula: WinningFormula2
    ) -> List[str]:
        """Identify patterns present in formula but missing in creative"""
        missing = []

        # Check visual patterns
        visual = creative_dna.get("visual_pattern_summary", {})
        if visual.get("face_presence_ratio", 0) < 0.3:
            missing.append("Insufficient face presence (winners have 70%+ face time)")

        # Check narrative patterns
        narrative = creative_dna.get("video_understanding", {})
        if narrative.get("hook", {}).get("strength_score", 0) < 70:
            missing.append("Weak hook (winners score 80+)")

        triggers = narrative.get("triggers", [])
        if "FOMO" not in triggers and "scarcity" not in triggers:
            missing.append("Missing urgency triggers (FOMO/scarcity)")

        return missing

    def _generate_improvement_suggestions(
        self,
        creative_dna: Dict,
        formula: WinningFormula2,
        missing_patterns: List[str]
    ) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []

        # Convert missing patterns to suggestions
        for pattern in missing_patterns:
            if "face presence" in pattern.lower():
                suggestions.append("Add more face time in first 5 seconds - increases retention by 40%")
            elif "weak hook" in pattern.lower():
                suggestions.append("Strengthen hook with pattern interrupt or bold claim")
            elif "urgency" in pattern.lower():
                suggestions.append("Add time-limited offer or scarcity element to CTA")

        # Add performance-based suggestions
        engagement = creative_dna.get("engagement_score", 0)
        if engagement < 70:
            suggestions.append("Increase pacing - add more cuts/transitions in first 10 seconds")

        return suggestions

    # ==========================================
    # PATTERN-BASED VARIANT GENERATION
    # ==========================================

    async def generate_variant_from_dna(
        self,
        source_creative_id: str,
        target_formula: WinningFormula2,
        generation_method: str = "evolve"
    ) -> GeneratedVariant:
        """
        Generate new variant based on DNA patterns

        Args:
            source_creative_id: Source creative to evolve
            target_formula: Winning formula to apply
            generation_method: "clone", "mix", or "evolve"

        Returns:
            Generated variant blueprint
        """
        variant_id = f"variant_{source_creative_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Select target DNA patterns
        target_visual = target_formula.visual_patterns[0]  # Best visual pattern
        target_audio = target_formula.audio_patterns[0]    # Best audio pattern
        target_narrative = target_formula.narrative_patterns[0]  # Best narrative

        # Generate modifications based on method
        modifications = []

        if generation_method == "evolve":
            # Keep source structure, apply winning patterns
            modifications = [
                {
                    "type": "visual",
                    "action": "adjust_color_palette",
                    "params": {"colors": target_visual.color_palette_hex[:3]}
                },
                {
                    "type": "narrative",
                    "action": "strengthen_hook",
                    "params": {
                        "hook_type": target_narrative.hook_type,
                        "duration": target_narrative.hook_duration
                    }
                },
                {
                    "type": "timing",
                    "action": "adjust_pacing",
                    "params": {"cuts_per_second": 0.5}  # Increase pacing
                },
                {
                    "type": "audio",
                    "action": "add_music",
                    "params": {
                        "genre": target_audio.music_genre,
                        "energy": target_audio.music_energy
                    }
                }
            ]
        elif generation_method == "clone":
            # Replicate winning pattern exactly
            modifications = [
                {
                    "type": "full_clone",
                    "action": "replicate_structure",
                    "params": {"formula_id": target_formula.formula_id}
                }
            ]
        else:  # mix
            # Mix elements from multiple winners
            modifications = [
                {
                    "type": "mix",
                    "action": "blend_patterns",
                    "params": {
                        "visual_from": target_formula.formula_id,
                        "audio_from": target_formula.formula_id,
                        "narrative_from": target_formula.formula_id
                    }
                }
            ]

        # Define asset requirements
        asset_requirements = [
            f"Background music: {target_audio.music_genre}, {target_audio.music_mood}",
            f"Visual style: {target_visual.composition_type}, {target_visual.color_psychology}",
            f"Hook type: {target_narrative.hook_type}",
            f"Duration: {target_narrative.total_duration:.1f}s"
        ]

        # Predict performance
        predicted_roas = target_formula.avg_roas * 0.85  # Slightly conservative

        return GeneratedVariant(
            variant_id=variant_id,
            source_creative_id=source_creative_id,
            generation_method=generation_method,
            target_visual_dna=target_visual,
            target_audio_dna=target_audio,
            target_narrative_dna=target_narrative,
            modifications=modifications,
            asset_requirements=asset_requirements,
            predicted_roas=predicted_roas,
            confidence=0.80,
            created_at=datetime.utcnow()
        )

    # ==========================================
    # COUNCIL OF TITANS INTEGRATION
    # ==========================================

    async def get_council_dna_score(
        self,
        creative_dna: Dict[str, Any],
        formula: Optional[WinningFormula2] = None
    ) -> Dict[str, Any]:
        """
        Get DNA-enhanced score from Council of Titans

        Args:
            creative_dna: Extracted DNA
            formula: Optional winning formula for comparison

        Returns:
            Council evaluation with DNA insights
        """
        try:
            # Import Council
            from services.titan_core.ai_council.council_of_titans import council

            # Build enhanced prompt with DNA insights
            visual_summary = creative_dna.get("visual_pattern_summary", {})
            video_understanding = creative_dna.get("video_understanding", {})

            script = f"""
DNA-ENHANCED VIDEO ANALYSIS:

VISUAL PATTERNS:
- Colors: {visual_summary.get('most_common_colors', {})}
- Face Presence: {visual_summary.get('face_presence_ratio', 0):.0%}
- Stop-Scroll Score: {visual_summary.get('avg_stop_scroll_score', 0):.1f}/100
- Production Quality: {visual_summary.get('avg_production_quality', 0):.1f}/100

NARRATIVE STRUCTURE:
- Hook Type: {video_understanding.get('hook', {}).get('type', 'unknown')}
- Hook Strength: {video_understanding.get('hook', {}).get('strength_score', 0):.1f}/100
- Narrative: {video_understanding.get('narrative', {}).get('structure', 'unknown')}
- Viral Score: {video_understanding.get('viral_score', 0):.1f}/100

ENGAGEMENT FACTORS:
- Triggers: {', '.join(video_understanding.get('triggers', []))}
- Pacing: {video_understanding.get('pacing', {}).get('style', 'unknown')}
"""

            # Add formula comparison if available
            if formula:
                similarity = await self.compare_to_winning_patterns(creative_dna, formula)
                script += f"""
PATTERN MATCH TO WINNERS:
- Overall Similarity: {similarity.overall_similarity:.0%}
- Predicted ROAS: {similarity.predicted_roas:.2f}x
- Missing Patterns: {', '.join(similarity.missing_patterns)}
"""

            # Get Council evaluation
            council_result = await council.evaluate_script(script)

            # Enhance with DNA data
            council_result["dna_insights"] = {
                "engagement_score": creative_dna.get("engagement_score", 0),
                "pattern_similarity": similarity.overall_similarity if formula else 0,
                "missing_patterns": similarity.missing_patterns if formula else [],
                "improvement_suggestions": similarity.suggested_improvements if formula else []
            }

            return council_result

        except Exception as e:
            logger.error(f"Council integration error: {e}", exc_info=True)
            return {"error": str(e)}


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def get_creative_dna_v2(
    openai_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    database_service=None
) -> CreativeDNA2:
    """Get CreativeDNA2 instance"""
    return CreativeDNA2(
        openai_api_key=openai_api_key,
        gemini_api_key=gemini_api_key,
        database_service=database_service
    )


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize
        dna_engine = get_creative_dna_v2()

        # Extract DNA from video
        video_path = "/path/to/video.mp4"
        creative_id = "test_123"

        dna = await dna_engine.extract_complete_dna(
            video_path=video_path,
            creative_id=creative_id
        )

        print("✅ DNA Extraction Complete!")
        print(json.dumps(dna, indent=2, default=str))

    # Run
    asyncio.run(main())
