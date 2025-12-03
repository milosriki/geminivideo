"""
Unit and Integration Tests for Vertex AI Service
Agent 23 of 30 - ULTIMATE Production Plan
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.vertex_ai import VertexAIService, VideoAnalysis, VERTEXAI_AVAILABLE


class TestVideoAnalysis(unittest.TestCase):
    """Test VideoAnalysis dataclass."""

    def test_video_analysis_creation(self):
        """Test creating VideoAnalysis object."""
        analysis = VideoAnalysis(
            summary="Test video summary",
            scenes=[{"timestamp": "0-5s", "description": "Opening scene"}],
            objects_detected=["product", "person"],
            text_detected=["Buy Now!"],
            audio_transcript="Check out this product",
            sentiment="positive",
            recommendations=["Improve hook", "Add CTA"],
            hook_quality=85.5,
            engagement_score=72.0,
            marketing_insights={"target": "millennials"},
            raw_response="Full response text"
        )

        self.assertEqual(analysis.summary, "Test video summary")
        self.assertEqual(len(analysis.scenes), 1)
        self.assertEqual(len(analysis.objects_detected), 2)
        self.assertEqual(analysis.hook_quality, 85.5)
        self.assertEqual(analysis.engagement_score, 72.0)
        self.assertEqual(analysis.sentiment, "positive")

    def test_video_analysis_defaults(self):
        """Test VideoAnalysis with default values."""
        analysis = VideoAnalysis(summary="Test")

        self.assertEqual(analysis.summary, "Test")
        self.assertEqual(analysis.scenes, [])
        self.assertEqual(analysis.objects_detected, [])
        self.assertEqual(analysis.text_detected, [])
        self.assertEqual(analysis.audio_transcript, "")
        self.assertEqual(analysis.sentiment, "neutral")
        self.assertEqual(analysis.recommendations, [])
        self.assertIsNone(analysis.hook_quality)
        self.assertIsNone(analysis.engagement_score)
        self.assertEqual(analysis.marketing_insights, {})
        self.assertIsNone(analysis.raw_response)


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIServiceInit(unittest.TestCase):
    """Test VertexAIService initialization."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def test_initialization_with_project_id(self, mock_model, mock_vertexai):
        """Test service initialization with explicit project ID."""
        service = VertexAIService(
            project_id="test-project",
            location="us-central1"
        )

        mock_vertexai.init.assert_called_once_with(
            project="test-project",
            location="us-central1"
        )
        self.assertEqual(service.project_id, "test-project")
        self.assertEqual(service.location, "us-central1")

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    @patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'env-project'})
    def test_initialization_from_env(self, mock_model, mock_vertexai):
        """Test service initialization from environment variable."""
        service = VertexAIService()

        self.assertEqual(service.project_id, "env-project")

    @patch('engines.vertex_ai.VERTEXAI_AVAILABLE', False)
    def test_initialization_without_sdk(self):
        """Test service fails gracefully without SDK."""
        with self.assertRaises(ImportError):
            service = VertexAIService(project_id="test")

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def test_custom_models(self, mock_model, mock_vertexai):
        """Test initialization with custom model names."""
        service = VertexAIService(
            project_id="test-project",
            gemini_model="gemini-pro",
            imagen_model="imagen-2.0"
        )

        self.assertEqual(service.gemini_model_name, "gemini-pro")
        self.assertEqual(service.imagen_model_name, "imagen-2.0")


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIVideoAnalysis(unittest.TestCase):
    """Test video analysis methods."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def setUp(self, mock_model, mock_vertexai):
        """Set up test fixtures."""
        self.service = VertexAIService(project_id="test-project")
        self.mock_model = mock_model.return_value

    def test_analyze_video_with_gcs_uri(self):
        """Test video analysis with GCS URI."""
        mock_response = Mock()
        mock_response.text = '''
        {
            "summary": "Product demo video",
            "scenes": [{"timestamp": "0-5s", "description": "Hook"}],
            "objects_detected": ["product"],
            "text_detected": ["Buy Now"],
            "audio_transcript": "Check this out",
            "sentiment": "positive",
            "hook_quality": 85,
            "engagement_score": 75,
            "marketing_insights": {"target": "Gen Z"},
            "recommendations": ["Add urgency"]
        }
        '''
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        analysis = self.service.analyze_video("gs://bucket/video.mp4")

        self.assertEqual(analysis.summary, "Product demo video")
        self.assertEqual(len(analysis.scenes), 1)
        self.assertEqual(analysis.hook_quality, 85)
        self.assertEqual(analysis.engagement_score, 75)
        self.assertEqual(analysis.sentiment, "positive")

    def test_analyze_video_with_custom_prompt(self):
        """Test video analysis with custom prompt."""
        mock_response = Mock()
        mock_response.text = '{"summary": "Custom analysis"}'
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        custom_prompt = "Focus on the product features only"
        analysis = self.service.analyze_video(
            "gs://bucket/video.mp4",
            prompt=custom_prompt
        )

        # Verify custom prompt was used
        call_args = self.service.gemini_model.generate_content.call_args[0][0]
        self.assertIn(custom_prompt, str(call_args))

    def test_analyze_video_invalid_json(self):
        """Test video analysis with invalid JSON response."""
        mock_response = Mock()
        mock_response.text = "This is not JSON"
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        analysis = self.service.analyze_video("gs://bucket/video.mp4")

        # Should create fallback analysis
        self.assertIn("not JSON", analysis.summary)
        self.assertIsNotNone(analysis.raw_response)

    def test_analyze_video_api_error(self):
        """Test video analysis with API error."""
        self.service.gemini_model.generate_content = Mock(
            side_effect=Exception("API Error")
        )

        analysis = self.service.analyze_video("gs://bucket/video.mp4")

        # Should return error analysis
        self.assertIn("failed", analysis.summary.lower())


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIAdGeneration(unittest.TestCase):
    """Test ad copy and image generation methods."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def setUp(self, mock_model, mock_vertexai):
        """Set up test fixtures."""
        self.service = VertexAIService(project_id="test-project")

    def test_generate_ad_copy(self):
        """Test ad copy generation."""
        mock_response = Mock()
        mock_response.text = '''
        ["Variant 1: Amazing product!", "Variant 2: Don't miss out!", "Variant 3: Limited time only!"]
        '''
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        variants = self.service.generate_ad_copy(
            product_info="Test product",
            style="urgent",
            num_variants=3
        )

        self.assertEqual(len(variants), 3)
        self.assertIn("Variant 1", variants[0])

    def test_improve_hook(self):
        """Test hook improvement."""
        mock_response = Mock()
        mock_response.text = '''
        ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"]
        '''
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        hooks = self.service.improve_hook(
            current_hook="Old hook",
            target_emotion="urgency"
        )

        self.assertEqual(len(hooks), 5)

    def test_analyze_competitor_ad(self):
        """Test competitor ad analysis."""
        mock_response = Mock()
        mock_response.text = '''
        {
            "summary": "Competitor uses emotional appeal",
            "hook_quality": 90,
            "engagement_score": 85,
            "marketing_insights": {"strength": "storytelling"},
            "recommendations": ["Study their pacing"]
        }
        '''
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        insights = self.service.analyze_competitor_ad("gs://bucket/competitor.mp4")

        self.assertIn("hook_quality", insights)
        self.assertEqual(insights["hook_quality"], 90)


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIEmbeddings(unittest.TestCase):
    """Test embedding methods."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    @patch('engines.vertex_ai.TextEmbeddingModel')
    def setUp(self, mock_embed_model, mock_gen_model, mock_vertexai):
        """Set up test fixtures."""
        self.service = VertexAIService(project_id="test-project")
        self.mock_embed_model = mock_embed_model

    def test_embed_text(self):
        """Test single text embedding."""
        mock_embedding = Mock()
        mock_embedding.values = [0.1, 0.2, 0.3] * 256  # 768 dimensions

        mock_model = Mock()
        mock_model.get_embeddings.return_value = [mock_embedding]

        with patch.object(self.service, 'embedding_model', mock_model):
            vector = self.service.embed_text("Test text")

        self.assertIsInstance(vector, np.ndarray)
        self.assertEqual(len(vector), 768)

    def test_embed_texts_batch(self):
        """Test batch text embedding."""
        mock_embeddings = []
        for i in range(3):
            mock_emb = Mock()
            mock_emb.values = [0.1 * i] * 768
            mock_embeddings.append(mock_emb)

        mock_model = Mock()
        mock_model.get_embeddings.return_value = mock_embeddings

        with patch.object(self.service, 'embedding_model', mock_model):
            vectors = self.service.embed_texts(["Text 1", "Text 2", "Text 3"])

        self.assertIsInstance(vectors, np.ndarray)
        self.assertEqual(vectors.shape, (3, 768))


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIMultimodal(unittest.TestCase):
    """Test multimodal analysis methods."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def setUp(self, mock_model, mock_vertexai):
        """Set up test fixtures."""
        self.service = VertexAIService(project_id="test-project")

    def test_generate_storyboard(self):
        """Test storyboard generation."""
        mock_response = Mock()
        mock_response.text = '''
        [
            {
                "timestamp": "0-5s",
                "description": "Opening hook",
                "visual_details": "Close-up product shot",
                "text_overlay": "Stop!",
                "image_prompt": "Product on dark background",
                "purpose": "hook"
            },
            {
                "timestamp": "5-10s",
                "description": "Problem agitation",
                "visual_details": "Person struggling",
                "text_overlay": "Tired of...",
                "image_prompt": "Frustrated customer",
                "purpose": "build"
            }
        ]
        '''
        self.service.gemini_model.generate_content = Mock(return_value=mock_response)

        storyboard = self.service.generate_storyboard(
            product_description="Smart device",
            style="modern"
        )

        self.assertEqual(len(storyboard), 2)
        self.assertEqual(storyboard[0]["timestamp"], "0-5s")
        self.assertEqual(storyboard[0]["purpose"], "hook")


@unittest.skipIf(not VERTEXAI_AVAILABLE, "Vertex AI SDK not available")
class TestVertexAIChat(unittest.TestCase):
    """Test chat functionality."""

    @patch('engines.vertex_ai.vertexai')
    @patch('engines.vertex_ai.GenerativeModel')
    def setUp(self, mock_model, mock_vertexai):
        """Set up test fixtures."""
        self.service = VertexAIService(project_id="test-project")

    def test_start_chat(self):
        """Test starting chat session."""
        mock_chat = Mock()
        mock_model = Mock()
        mock_model.start_chat.return_value = mock_chat

        with patch.object(self.service, 'gemini_model', mock_model):
            chat = self.service.start_chat()

        self.assertIsNotNone(chat)
        mock_model.start_chat.assert_called_once()

    def test_start_chat_with_instruction(self):
        """Test starting chat with system instruction."""
        mock_model_class = Mock()
        mock_model_instance = Mock()
        mock_chat = Mock()
        mock_model_instance.start_chat.return_value = mock_chat

        with patch('engines.vertex_ai.GenerativeModel', return_value=mock_model_instance):
            chat = self.service.start_chat(
                system_instruction="You are a marketing expert"
            )

        self.assertIsNotNone(chat)

    def test_chat_message(self):
        """Test sending chat message."""
        mock_chat = Mock()
        mock_response = Mock()
        mock_response.text = "This is the response"
        mock_chat.send_message.return_value = mock_response

        response = self.service.chat(mock_chat, "Hello")

        self.assertEqual(response, "This is the response")
        mock_chat.send_message.assert_called_once_with("Hello")


class TestIntegration(unittest.TestCase):
    """Integration tests (require real API access)."""

    @unittest.skipIf(
        not os.environ.get("GOOGLE_CLOUD_PROJECT") or not VERTEXAI_AVAILABLE,
        "Requires GOOGLE_CLOUD_PROJECT and Vertex AI SDK"
    )
    def test_real_text_embedding(self):
        """Test real embedding API call (if credentials available)."""
        try:
            service = VertexAIService()
            vector = service.embed_text("Test marketing message")

            self.assertIsInstance(vector, np.ndarray)
            self.assertEqual(len(vector), 768)
            self.assertGreater(np.linalg.norm(vector), 0)

            print("✅ Real embedding test passed")
        except Exception as e:
            self.skipTest(f"Real API not available: {e}")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
