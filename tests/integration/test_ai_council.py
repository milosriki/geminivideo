"""
Integration Tests for AI Council (Council of Titans)
Tests the 4-model ensemble scoring system with real AI calls.

Coverage:
- Council evaluation with all 4 models
- Structured output schemas
- Prompt caching performance
- Score consistency and variation
- Model availability checks
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add titan-core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "titan-core"))

# Import Council components
try:
    from ai_council.council_of_titans import (
        CouncilOfTitans,
        ScoreSchema,
        OpenAIModelType
    )
    COUNCIL_AVAILABLE = True
except ImportError as e:
    COUNCIL_AVAILABLE = False
    pytest.skip(f"AI Council not available: {e}", allow_module_level=True)


@pytest.fixture
def council():
    """Create Council instance"""
    return CouncilOfTitans()


@pytest.fixture
def test_scripts():
    """Sample scripts for testing"""
    return {
        "high_quality": """
            Stop scrolling! In the next 30 seconds, I'm going to show you how busy professionals
            are losing 20lbs in 90 days without spending hours at the gym.

            Here's the secret: It's not about doing more exercise. It's about doing the RIGHT exercise.

            Our Elite Fitness program combines:
            - 15-minute targeted workouts
            - Personalized meal plans
            - 1-on-1 coaching

            Book your free transformation call now. Limited spots available.
        """,
        "medium_quality": """
            Want to lose weight? Our fitness program can help you get in shape.
            We offer workout plans and diet advice. Sign up today to learn more.
        """,
        "low_quality": """
            Fitness. Join our gym. Get fit. Call now.
        """,
        "with_hook": """
            WAIT! Before you scroll past this, answer one question:
            What would your life look like if you had unlimited energy every day?

            That's exactly what our 90-day transformation delivers.
            Click the link below to book your free call.
        """
    }


class TestCouncilEvaluation:
    """Test Council of Titans evaluation functionality"""

    @pytest.mark.asyncio
    async def test_evaluate_script_basic(self, council, test_scripts):
        """Test basic script evaluation"""
        result = await council.evaluate_script(
            script=test_scripts["high_quality"],
            visual_features={"has_human_face": True, "hook_type": "pattern_interrupt"}
        )

        # Check response structure
        assert "final_score" in result
        assert "breakdown" in result
        assert "verdict" in result
        assert "council_members" in result

        # Validate score
        assert 0 <= result["final_score"] <= 100

        # Check breakdown has all models
        breakdown = result["breakdown"]
        assert "gemini_2_0_thinking" in breakdown
        assert "openai" in breakdown
        assert "claude_3_5" in breakdown
        assert "deep_ctr" in breakdown

        # All individual scores should be valid
        for model, score in breakdown.items():
            assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_evaluate_different_quality_scripts(self, council, test_scripts):
        """Test that Council differentiates between quality levels"""
        results = {}

        for quality_level, script in test_scripts.items():
            result = await council.evaluate_script(script=script)
            results[quality_level] = result["final_score"]

        # High quality should score better than low quality
        assert results["high_quality"] > results["low_quality"]

    @pytest.mark.asyncio
    async def test_score_consistency(self, council, test_scripts):
        """Test that same script gets consistent scores"""
        script = test_scripts["high_quality"]

        # Evaluate same script twice
        result1 = await council.evaluate_script(script=script)
        await asyncio.sleep(1)  # Small delay
        result2 = await council.evaluate_script(script=script)

        # Scores should be similar (within 10 points due to AI variability)
        assert abs(result1["final_score"] - result2["final_score"]) < 10

    @pytest.mark.asyncio
    async def test_visual_features_impact(self, council, test_scripts):
        """Test that visual features affect DeepCTR score"""
        script = test_scripts["medium_quality"]

        # Test with no visual features
        result1 = await council.evaluate_script(script=script)

        # Test with positive visual features
        result2 = await council.evaluate_script(
            script=script,
            visual_features={
                "has_human_face": True,
                "hook_type": "pattern_interrupt",
                "high_contrast": True,
                "fast_paced": True
            }
        )

        # DeepCTR score should be higher with better features
        assert result2["breakdown"]["deep_ctr"] > result1["breakdown"]["deep_ctr"]


class TestIndividualModels:
    """Test individual Council models"""

    @pytest.mark.asyncio
    async def test_gemini_critique(self, council, test_scripts):
        """Test Gemini 2.0 Flash Thinking model"""
        result = await council.get_gemini_critique(test_scripts["high_quality"])

        assert "score" in result
        assert "source" in result
        assert 0 <= result["score"] <= 100
        assert "Gemini" in result["source"]

    @pytest.mark.asyncio
    async def test_openai_o1_critique(self, council, test_scripts):
        """Test OpenAI o1 reasoning model"""
        result = await council.get_openai_o1_critique(
            test_scripts["high_quality"],
            mode="mini"  # Use mini for faster testing
        )

        assert "score" in result
        assert "source" in result
        assert 0 <= result["score"] <= 100

        # Check reasoning tokens are tracked
        if "reasoning_tokens" in result:
            assert result["reasoning_tokens"] >= 0

    @pytest.mark.asyncio
    async def test_gpt4o_mini_critique(self, council, test_scripts):
        """Test GPT-4o-mini structured output"""
        result = await council.get_gpt4o_critique_simple(test_scripts["high_quality"])

        assert "score" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "source" in result

        # Validate structured response
        assert 0 <= result["score"] <= 100
        assert 0 <= result["confidence"] <= 1
        assert len(result["reasoning"]) > 0

    @pytest.mark.asyncio
    async def test_claude_critique(self, council, test_scripts):
        """Test Claude 3.5 Sonnet evaluation"""
        result = await council.get_claude_critique(test_scripts["high_quality"])

        assert "score" in result
        assert "source" in result
        assert 0 <= result["score"] <= 100
        assert "Claude" in result["source"]


class TestStructuredOutputs:
    """Test structured output schemas"""

    def test_simple_score_schema(self):
        """Test simple score schema structure"""
        schema = ScoreSchema.get_simple_score_schema()

        assert schema["type"] == "json_schema"
        assert "json_schema" in schema

        json_schema = schema["json_schema"]
        assert json_schema["strict"] is True
        assert "schema" in json_schema

        # Check required fields
        properties = json_schema["schema"]["properties"]
        assert "score" in properties
        assert "confidence" in properties
        assert "reasoning" in properties

    def test_detailed_critique_schema(self):
        """Test detailed critique schema structure"""
        schema = ScoreSchema.get_detailed_critique_schema()

        properties = schema["json_schema"]["schema"]["properties"]

        # Check all dimensions are present
        required_dimensions = [
            "overall_score",
            "hook_strength",
            "emotional_resonance",
            "cta_clarity",
            "pacing_score",
            "viral_potential"
        ]

        for dimension in required_dimensions:
            assert dimension in properties

    def test_vision_analysis_schema(self):
        """Test vision analysis schema structure"""
        schema = ScoreSchema.get_vision_analysis_schema()

        properties = schema["json_schema"]["schema"]["properties"]

        # Check vision-specific fields
        assert "visual_score" in properties
        assert "has_human_face" in properties
        assert "scene_description" in properties
        assert "composition_quality" in properties


class TestPromptCaching:
    """Test prompt caching performance"""

    @pytest.mark.asyncio
    async def test_caching_enabled(self, council):
        """Test that caching is enabled"""
        assert council.caching_enabled is True

    @pytest.mark.asyncio
    async def test_cache_metrics_tracking(self, council, test_scripts):
        """Test that cache metrics are tracked"""
        # Reset metrics
        council.reset_cache_metrics()

        # Make multiple calls to same model
        for _ in range(3):
            await council.get_gpt4o_critique_simple(test_scripts["high_quality"])
            await asyncio.sleep(0.5)

        # Get cache metrics
        metrics = council.get_cache_metrics()

        # Should have metrics data
        assert metrics is not None
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_cached_tokens_reported(self, council, test_scripts):
        """Test that cached tokens are reported in responses"""
        # First call (no cache)
        result1 = await council.get_gpt4o_critique_simple(test_scripts["high_quality"])

        # Second call (should use cache)
        await asyncio.sleep(1)
        result2 = await council.get_gpt4o_critique_simple(test_scripts["high_quality"])

        # Check if cache tokens are tracked
        if "cached_tokens" in result2:
            # Second call should potentially have cached tokens
            assert result2["cached_tokens"] >= 0


class TestDeepCTRScoring:
    """Test DeepCTR heuristic scoring"""

    def test_calculate_deep_ctr_score_basic(self, council):
        """Test DeepCTR calculation with basic features"""
        visual_features = {
            "has_human_face": True,
            "hook_type": "pattern_interrupt"
        }

        score = council._calculate_deep_ctr_score(visual_features)

        assert 0 <= score <= 100
        assert score > 50  # Should be above base with good features

    def test_calculate_deep_ctr_score_all_features(self, council):
        """Test DeepCTR with all positive features"""
        visual_features = {
            "has_human_face": True,
            "hook_type": "pattern_interrupt",
            "high_contrast": True,
            "fast_paced": True,
            "text_overlays": True,
            "scene_count": 5
        }

        score = council._calculate_deep_ctr_score(visual_features)

        assert score > 70  # Should be high with all features

    def test_calculate_deep_ctr_score_minimal(self, council):
        """Test DeepCTR with minimal features"""
        visual_features = {}

        score = council._calculate_deep_ctr_score(visual_features)

        assert 0 <= score <= 100
        assert score >= 50  # Base score


class TestOpenAIModelSelection:
    """Test OpenAI model selection strategy"""

    def test_select_reasoning_model(self):
        """Test selection of o1 for reasoning tasks"""
        model = OpenAIModelType.select_for_task("reasoning")
        assert model == "o1"

    def test_select_vision_model(self):
        """Test selection of GPT-4o for vision tasks"""
        model = OpenAIModelType.select_for_task("vision")
        assert model == "gpt-4o-2024-11-20"

    def test_select_scoring_model(self):
        """Test selection of GPT-4o-mini for scoring"""
        model = OpenAIModelType.select_for_task("scoring")
        assert model == "gpt-4o-mini"

    def test_select_fast_model(self):
        """Test selection of o1-mini for fast tasks"""
        model = OpenAIModelType.select_for_task("fast")
        assert model == "o1-mini"


class TestEvaluationModes:
    """Test different evaluation modes"""

    @pytest.mark.asyncio
    async def test_evaluate_with_o1(self, council, test_scripts):
        """Test evaluation using o1 reasoning model"""
        result = await council.evaluate_script(
            script=test_scripts["high_quality"],
            use_o1=True
        )

        assert "final_score" in result
        assert "breakdown" in result

        # Check that OpenAI model was used
        assert "openai" in result["breakdown"]

    @pytest.mark.asyncio
    async def test_evaluate_with_vision(self, council, test_scripts):
        """Test evaluation with vision analysis"""
        # Note: This test requires an actual image file
        # Using a placeholder path for structure testing
        result = await council.evaluate_script(
            script=test_scripts["high_quality"],
            image_path="/tmp/test_thumbnail.jpg"  # Would need real file
        )

        assert "final_score" in result

        # If vision analysis succeeded, check for vision data
        if "vision_analysis" in result:
            vision = result["vision_analysis"]
            assert "visual_score" in vision
            assert "has_human_face" in vision

    @pytest.mark.asyncio
    async def test_detailed_critique(self, council, test_scripts):
        """Test detailed critique with o1"""
        result = await council.evaluate_with_detailed_critique(
            test_scripts["high_quality"]
        )

        assert "detailed_analysis" in result or "error" in result

        if "detailed_analysis" in result:
            assert len(result["detailed_analysis"]) > 100  # Should be detailed


class TestErrorHandling:
    """Test error handling in Council"""

    @pytest.mark.asyncio
    async def test_evaluate_empty_script(self, council):
        """Test handling of empty script"""
        result = await council.evaluate_script(script="")

        # Should still return a result (even if score is low)
        assert "final_score" in result

    @pytest.mark.asyncio
    async def test_evaluate_very_long_script(self, council):
        """Test handling of very long script"""
        long_script = "Test script. " * 1000  # Very long

        result = await council.evaluate_script(script=long_script)

        assert "final_score" in result

    @pytest.mark.asyncio
    async def test_model_fallback(self, council):
        """Test that Council handles model failures gracefully"""
        # This will test if fallback scores are used when models fail
        result = await council.evaluate_script(
            script="Test script for fallback",
            visual_features={}
        )

        # Should always return a score
        assert "final_score" in result
        assert 0 <= result["final_score"] <= 100


class TestWeightedScoring:
    """Test weighted scoring algorithm"""

    @pytest.mark.asyncio
    async def test_weighted_calculation(self, council, test_scripts):
        """Test that final score uses correct weights"""
        result = await council.evaluate_script(script=test_scripts["high_quality"])

        # Extract individual scores
        breakdown = result["breakdown"]
        gemini_score = breakdown["gemini_2_0_thinking"]
        openai_score = breakdown["openai"]
        claude_score = breakdown["claude_3_5"]
        deep_ctr_score = breakdown["deep_ctr"]

        # Calculate expected weighted score
        # Weights: Gemini (40%), Claude (30%), OpenAI (20%), DeepCTR (10%)
        expected_score = (
            gemini_score * 0.40 +
            claude_score * 0.30 +
            openai_score * 0.20 +
            deep_ctr_score * 0.10
        )

        # Should match (within rounding)
        assert abs(result["final_score"] - expected_score) < 0.5

    @pytest.mark.asyncio
    async def test_approval_threshold(self, council, test_scripts):
        """Test approval verdict based on threshold"""
        result = await council.evaluate_script(script=test_scripts["high_quality"])

        # Verdict should match score vs threshold (85)
        if result["final_score"] > 85:
            assert result["verdict"] == "APPROVE"
        else:
            assert result["verdict"] == "REJECT"


class TestConcurrentEvaluation:
    """Test concurrent evaluation performance"""

    @pytest.mark.asyncio
    async def test_parallel_evaluations(self, council, test_scripts):
        """Test multiple scripts evaluated in parallel"""
        scripts = [
            test_scripts["high_quality"],
            test_scripts["medium_quality"],
            test_scripts["low_quality"]
        ]

        # Evaluate all in parallel
        tasks = [
            council.evaluate_script(script=script)
            for script in scripts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
            assert "final_score" in result
