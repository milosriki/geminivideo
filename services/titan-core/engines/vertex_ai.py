"""
Vertex AI Integration Service
Real implementation for Gemini, Imagen, and video analysis capabilities.
Agent 23 of 30 - ULTIMATE Production Plan
"""

import os
import base64
import logging
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime
import json
import io

# Try to import Vertex AI libraries, handle gracefully
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Content, ChatSession
    from vertexai.vision_models import ImageGenerationModel, Image as VertexImage
    from vertexai.language_models import TextEmbeddingModel
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    # Create dummy types for type hints when SDK not available
    if TYPE_CHECKING:
        from vertexai.generative_models import ChatSession
        from vertexai.vision_models import ImageGenerationModel
        from vertexai.language_models import TextEmbeddingModel
    else:
        ChatSession = Any
        ImageGenerationModel = Any
        TextEmbeddingModel = Any
    print("⚠️ Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")

try:
    from google.cloud import aiplatform
    AIPLATFORM_AVAILABLE = True
except ImportError:
    AIPLATFORM_AVAILABLE = False
    print("⚠️ AI Platform SDK not available.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available. Image operations will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VideoAnalysis:
    """Structured video analysis results from Gemini."""
    summary: str
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    objects_detected: List[str] = field(default_factory=list)
    text_detected: List[str] = field(default_factory=list)
    audio_transcript: str = ""
    sentiment: str = "neutral"
    recommendations: List[str] = field(default_factory=list)
    hook_quality: Optional[float] = None
    engagement_score: Optional[float] = None
    marketing_insights: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[str] = None


class VertexAIService:
    """
    Vertex AI integration for Gemini, Imagen, and video analysis.

    This service provides real implementations for:
    - Video analysis with Gemini 2.0
    - Image generation with Imagen
    - Text embeddings for similarity search
    - Multimodal analysis
    - Chat capabilities
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        gemini_model: str = "gemini-2.0-flash-exp",
        imagen_model: str = "imagen-3.0-generate-001"
    ):
        """
        Initialize Vertex AI client.

        Args:
            project_id: GCP project ID (defaults to env var GOOGLE_CLOUD_PROJECT)
            location: GCP region (default: us-central1)
            gemini_model: Gemini model version to use
            imagen_model: Imagen model version to use
        """
        if not VERTEXAI_AVAILABLE:
            raise ImportError("Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")

        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("project_id must be provided or GOOGLE_CLOUD_PROJECT must be set")

        self.location = location
        self.gemini_model_name = gemini_model
        self.imagen_model_name = imagen_model

        # Initialize Vertex AI
        try:
            vertexai.init(project=self.project_id, location=self.location)
            logger.info(f"✅ Vertex AI initialized: {self.project_id} @ {self.location}")
        except Exception as e:
            logger.error(f"❌ Vertex AI initialization failed: {e}")
            raise

        # Initialize models
        self.gemini_model = GenerativeModel(self.gemini_model_name)
        logger.info(f"🧠 Gemini model loaded: {self.gemini_model_name}")

        # Imagen model (lazy load on first use)
        self._imagen_model = None

        # Embedding model (lazy load on first use)
        self._embedding_model = None

        # Generation config defaults
        self.default_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

    @property
    def imagen_model(self) -> ImageGenerationModel:
        """Lazy load Imagen model."""
        if self._imagen_model is None:
            try:
                self._imagen_model = ImageGenerationModel.from_pretrained(self.imagen_model_name)
                logger.info(f"🎨 Imagen model loaded: {self.imagen_model_name}")
            except Exception as e:
                logger.error(f"❌ Imagen model loading failed: {e}")
                raise
        return self._imagen_model

    @property
    def embedding_model(self) -> TextEmbeddingModel:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            try:
                self._embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                logger.info("📊 Embedding model loaded: text-embedding-004")
            except Exception as e:
                logger.error(f"❌ Embedding model loading failed: {e}")
                raise
        return self._embedding_model

    # ========================================================================
    # GEMINI ANALYSIS METHODS
    # ========================================================================

    def analyze_video(
        self,
        video_gcs_uri: str,
        prompt: Optional[str] = None
    ) -> VideoAnalysis:
        """
        Analyze video using Gemini 2.0 with multimodal understanding.

        Args:
            video_gcs_uri: GCS URI (gs://bucket/video.mp4) or local file path
            prompt: Custom analysis prompt (optional)

        Returns:
            VideoAnalysis object with structured results
        """
        if not prompt:
            prompt = """
            Analyze this video comprehensively for marketing and advertising purposes:

            1. SUMMARY: Provide a 2-3 sentence overview of the video content.

            2. SCENES: Break down the video into key scenes with timestamps, actions, and emotions.

            3. OBJECTS: List all significant objects, products, or items visible.

            4. TEXT: Extract any text overlays, captions, or visible text.

            5. AUDIO/DIALOGUE: Transcribe any speech or important audio cues.

            6. SENTIMENT: Overall emotional tone (positive/negative/neutral/mixed).

            7. HOOK QUALITY: Rate the first 3 seconds (0-100) for attention-grabbing power.

            8. ENGAGEMENT SCORE: Predict viewer engagement (0-100) based on pacing, visuals, and messaging.

            9. MARKETING INSIGHTS:
               - Target audience
               - Key selling points
               - Call-to-action clarity
               - Production quality
               - Competitive advantages

            10. RECOMMENDATIONS: 3-5 specific improvements for better performance.

            Return your analysis as valid JSON with these exact fields:
            {
                "summary": "...",
                "scenes": [...],
                "objects_detected": [...],
                "text_detected": [...],
                "audio_transcript": "...",
                "sentiment": "...",
                "hook_quality": 0-100,
                "engagement_score": 0-100,
                "marketing_insights": {...},
                "recommendations": [...]
            }
            """

        try:
            # Create video part from GCS URI or file
            if video_gcs_uri.startswith("gs://"):
                video_part = Part.from_uri(video_gcs_uri, mime_type="video/mp4")
            else:
                # Local file - read and encode
                with open(video_gcs_uri, "rb") as f:
                    video_data = f.read()
                video_part = Part.from_data(video_data, mime_type="video/mp4")

            # Generate content
            logger.info(f"🎬 Analyzing video: {video_gcs_uri}")
            response = self.gemini_model.generate_content([video_part, prompt])

            # Parse JSON response
            raw_text = response.text.strip()
            json_text = raw_text.replace("```json", "").replace("```", "").strip()

            try:
                data = json.loads(json_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, extract what we can
                logger.warning("⚠️ Response was not valid JSON, creating structured fallback")
                data = {
                    "summary": raw_text[:500],
                    "raw_response": raw_text
                }

            # Create VideoAnalysis object
            analysis = VideoAnalysis(
                summary=data.get("summary", ""),
                scenes=data.get("scenes", []),
                objects_detected=data.get("objects_detected", []),
                text_detected=data.get("text_detected", []),
                audio_transcript=data.get("audio_transcript", ""),
                sentiment=data.get("sentiment", "neutral"),
                recommendations=data.get("recommendations", []),
                hook_quality=data.get("hook_quality"),
                engagement_score=data.get("engagement_score"),
                marketing_insights=data.get("marketing_insights", {}),
                raw_response=raw_text
            )

            logger.info(f"✅ Video analysis complete: {len(analysis.scenes)} scenes, {len(analysis.objects_detected)} objects")
            return analysis

        except Exception as e:
            logger.error(f"❌ Video analysis failed: {e}")
            # Return minimal analysis with error
            return VideoAnalysis(
                summary=f"Analysis failed: {str(e)}",
                raw_response=str(e)
            )

    def analyze_image(self, image_gcs_uri: str, prompt: str) -> str:
        """
        Analyze a single image with Gemini Vision.

        Args:
            image_gcs_uri: GCS URI or local file path
            prompt: Analysis question/prompt

        Returns:
            Analysis text response
        """
        try:
            # Create image part
            if image_gcs_uri.startswith("gs://"):
                image_part = Part.from_uri(image_gcs_uri, mime_type="image/jpeg")
            else:
                with open(image_gcs_uri, "rb") as f:
                    image_data = f.read()
                # Detect mime type from extension
                mime_type = "image/jpeg"
                if image_gcs_uri.lower().endswith(".png"):
                    mime_type = "image/png"
                elif image_gcs_uri.lower().endswith(".webp"):
                    mime_type = "image/webp"
                image_part = Part.from_data(image_data, mime_type=mime_type)

            logger.info(f"🖼️ Analyzing image: {image_gcs_uri}")
            response = self.gemini_model.generate_content([image_part, prompt])

            return response.text

        except Exception as e:
            logger.error(f"❌ Image analysis failed: {e}")
            return f"Error: {str(e)}"

    def generate_ad_copy(
        self,
        product_info: str,
        style: str,
        num_variants: int = 3
    ) -> List[str]:
        """
        Generate multiple ad copy variants using Gemini.

        Args:
            product_info: Product description and key features
            style: Ad style (e.g., "casual", "professional", "humorous", "urgent")
            num_variants: Number of variants to generate

        Returns:
            List of ad copy variants
        """
        prompt = f"""
        Generate {num_variants} different ad copy variants for this product.

        PRODUCT INFO:
        {product_info}

        STYLE: {style}

        Requirements:
        - Each variant should be 50-100 words
        - Include a strong hook in the first sentence
        - Use direct response language (you, your)
        - End with a clear call-to-action
        - Optimize for social media (Facebook/Instagram)

        Return as JSON array: ["variant1", "variant2", ...]
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            variants = json.loads(text)

            if isinstance(variants, list):
                logger.info(f"✅ Generated {len(variants)} ad copy variants")
                return variants
            else:
                return [text]

        except Exception as e:
            logger.error(f"❌ Ad copy generation failed: {e}")
            return [f"Error generating ad copy: {str(e)}"]

    def improve_hook(
        self,
        current_hook: str,
        target_emotion: str
    ) -> List[str]:
        """
        Generate improved hook variations targeting specific emotion.

        Args:
            current_hook: Current video/ad hook
            target_emotion: Desired emotion (curiosity, urgency, FOMO, excitement, etc.)

        Returns:
            List of improved hook suggestions
        """
        prompt = f"""
        Improve this video hook to better trigger {target_emotion}:

        CURRENT HOOK:
        "{current_hook}"

        TARGET EMOTION: {target_emotion}

        Generate 5 improved variations that:
        1. Work in first 3 seconds of video
        2. Use pattern interrupts
        3. Create immediate {target_emotion}
        4. Are mobile-optimized (short, punchy)
        5. Follow 2025 viral trends

        Return as JSON array: ["hook1", "hook2", ...]
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            hooks = json.loads(text)

            if isinstance(hooks, list):
                logger.info(f"✅ Generated {len(hooks)} improved hooks")
                return hooks
            else:
                return [text]

        except Exception as e:
            logger.error(f"❌ Hook improvement failed: {e}")
            return [current_hook]

    def analyze_competitor_ad(self, video_uri: str) -> Dict[str, Any]:
        """
        Deep analysis of competitor ad to extract winning patterns.

        Args:
            video_uri: GCS URI or local path to competitor video

        Returns:
            Dictionary with competitor insights
        """
        prompt = """
        Perform competitive intelligence analysis on this ad:

        1. HOOK STRATEGY: What pattern interrupt do they use?
        2. STORY ARC: How do they structure the narrative?
        3. PSYCHOLOGICAL TRIGGERS: What emotions/triggers are deployed?
        4. PRODUCTION QUALITY: Estimate production budget tier
        5. TARGET AUDIENCE: Who is this optimized for?
        6. UNIQUE SELLING POINTS: What makes them different?
        7. WEAKNESSES: What could be improved?
        8. ACTIONABLE INSIGHTS: What can we learn/replicate?

        Return valid JSON with these fields.
        """

        analysis = self.analyze_video(video_uri, prompt)

        # Convert VideoAnalysis to dictionary for competitor analysis
        return {
            "summary": analysis.summary,
            "insights": analysis.marketing_insights,
            "recommendations": analysis.recommendations,
            "hook_quality": analysis.hook_quality,
            "engagement_score": analysis.engagement_score,
            "raw_analysis": analysis.raw_response
        }

    # ========================================================================
    # IMAGEN GENERATION METHODS
    # ========================================================================

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        num_images: int = 1
    ) -> List[bytes]:
        """
        Generate images using Imagen 3.

        Args:
            prompt: Image generation prompt
            aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)
            num_images: Number of images to generate

        Returns:
            List of image bytes
        """
        try:
            logger.info(f"🎨 Generating {num_images} image(s): {prompt[:50]}...")

            # Generate images
            images = self.imagen_model.generate_images(
                prompt=prompt,
                number_of_images=num_images,
                aspect_ratio=aspect_ratio,
                add_watermark=False
            )

            # Convert to bytes
            image_bytes_list = []
            for img in images:
                # Convert VertexImage to bytes
                img_bytes = img._image_bytes
                image_bytes_list.append(img_bytes)

            logger.info(f"✅ Generated {len(image_bytes_list)} images")
            return image_bytes_list

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return []

    def edit_image(self, image_bytes: bytes, edit_prompt: str) -> bytes:
        """
        Edit an existing image using Imagen.

        Args:
            image_bytes: Original image bytes
            edit_prompt: Editing instruction

        Returns:
            Edited image bytes
        """
        try:
            logger.info(f"✏️ Editing image: {edit_prompt[:50]}...")

            # Create VertexImage from bytes
            base_image = VertexImage(image_bytes=image_bytes)

            # Edit image
            edited_images = self.imagen_model.edit_image(
                base_image=base_image,
                prompt=edit_prompt,
                number_of_images=1
            )

            if edited_images:
                logger.info("✅ Image edited successfully")
                return edited_images[0]._image_bytes
            else:
                logger.warning("⚠️ No edited image returned")
                return image_bytes

        except Exception as e:
            logger.error(f"❌ Image editing failed: {e}")
            return image_bytes

    # ========================================================================
    # EMBEDDING METHODS
    # ========================================================================

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate text embedding vector.

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            vector = embeddings[0].values
            return np.array(vector)

        except Exception as e:
            logger.error(f"❌ Text embedding failed: {e}")
            return np.zeros(768)  # Default embedding dimension

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batch).

        Args:
            texts: List of input texts

        Returns:
            2D numpy array of embeddings
        """
        try:
            embeddings = self.embedding_model.get_embeddings(texts)
            vectors = [emb.values for emb in embeddings]
            return np.array(vectors)

        except Exception as e:
            logger.error(f"❌ Batch text embedding failed: {e}")
            return np.zeros((len(texts), 768))

    def embed_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Generate image embedding using multimodal model.

        Args:
            image_bytes: Image data

        Returns:
            Embedding vector as numpy array
        """
        try:
            # Use Gemini to generate image description, then embed it
            # (Vertex AI doesn't have direct image embedding yet)
            image_part = Part.from_data(image_bytes, mime_type="image/jpeg")
            response = self.gemini_model.generate_content([
                image_part,
                "Describe this image in detail for semantic search."
            ])

            description = response.text
            return self.embed_text(description)

        except Exception as e:
            logger.error(f"❌ Image embedding failed: {e}")
            return np.zeros(768)

    # ========================================================================
    # MULTIMODAL METHODS
    # ========================================================================

    def multimodal_analysis(
        self,
        video_uri: str,
        images: List[str],
        text_prompt: str
    ) -> str:
        """
        Analyze multiple modalities together (video + images + text).

        Args:
            video_uri: GCS URI or local path to video
            images: List of image URIs/paths
            text_prompt: Analysis question

        Returns:
            Analysis response
        """
        try:
            # Build multimodal content list
            content_parts = []

            # Add video
            if video_uri.startswith("gs://"):
                video_part = Part.from_uri(video_uri, mime_type="video/mp4")
            else:
                with open(video_uri, "rb") as f:
                    video_data = f.read()
                video_part = Part.from_data(video_data, mime_type="video/mp4")
            content_parts.append(video_part)

            # Add images
            for img_uri in images:
                if img_uri.startswith("gs://"):
                    img_part = Part.from_uri(img_uri, mime_type="image/jpeg")
                else:
                    with open(img_uri, "rb") as f:
                        img_data = f.read()
                    img_part = Part.from_data(img_data, mime_type="image/jpeg")
                content_parts.append(img_part)

            # Add text prompt
            content_parts.append(text_prompt)

            logger.info(f"🔀 Multimodal analysis: 1 video + {len(images)} images")
            response = self.gemini_model.generate_content(content_parts)

            return response.text

        except Exception as e:
            logger.error(f"❌ Multimodal analysis failed: {e}")
            return f"Error: {str(e)}"

    def generate_storyboard(
        self,
        product_description: str,
        style: str
    ) -> List[Dict[str, Any]]:
        """
        Generate a video ad storyboard with scene descriptions.

        Args:
            product_description: Product info and key benefits
            style: Visual style (modern, minimalist, energetic, luxury, etc.)

        Returns:
            List of storyboard scenes with descriptions and image prompts
        """
        prompt = f"""
        Create a 6-scene video ad storyboard for this product:

        PRODUCT: {product_description}
        STYLE: {style}

        For each scene (0-5 seconds, 5-10s, 10-15s, 15-20s, 20-25s, 25-30s):
        1. Scene description (what happens)
        2. Visual details (composition, colors, objects)
        3. Text overlay (if any)
        4. Image generation prompt (for Imagen)
        5. Purpose (hook, build, climax, CTA, etc.)

        Return as JSON array of scenes:
        [
          {{
            "timestamp": "0-5s",
            "description": "...",
            "visual_details": "...",
            "text_overlay": "...",
            "image_prompt": "...",
            "purpose": "hook"
          }},
          ...
        ]
        """

        try:
            response = self.gemini_model.generate_content(prompt)
            text = response.text.strip().replace("```json", "").replace("```", "").strip()
            storyboard = json.loads(text)

            logger.info(f"✅ Generated {len(storyboard)} storyboard scenes")
            return storyboard

        except Exception as e:
            logger.error(f"❌ Storyboard generation failed: {e}")
            return []

    # ========================================================================
    # CHAT METHODS
    # ========================================================================

    def start_chat(self, system_instruction: Optional[str] = None) -> ChatSession:
        """
        Start a chat session with Gemini.

        Args:
            system_instruction: Optional system context/instruction

        Returns:
            ChatSession object
        """
        try:
            if system_instruction:
                model = GenerativeModel(
                    self.gemini_model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.gemini_model

            chat = model.start_chat()
            logger.info("💬 Chat session started")
            return chat

        except Exception as e:
            logger.error(f"❌ Chat session failed: {e}")
            raise

    def chat(self, chat_session: ChatSession, message: str) -> str:
        """
        Send a message in an existing chat session.

        Args:
            chat_session: Active ChatSession
            message: User message

        Returns:
            Assistant response
        """
        try:
            response = chat_session.send_message(message)
            return response.text

        except Exception as e:
            logger.error(f"❌ Chat message failed: {e}")
            return f"Error: {str(e)}"
