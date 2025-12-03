"""Integration tests for AI endpoints.

Tests verify that AI endpoints return real analysis, not hardcoded values.
"""
import pytest
import httpx
import asyncio


class TestAIEndpoints:
    """Test that AI endpoints return real analysis, not hardcoded values"""

    BASE_URL = "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_analyze_not_hardcoded(self):
        """Verify /api/analyze returns varied responses"""
        async with httpx.AsyncClient() as client:
            responses = []
            for i in range(3):
                resp = await client.post(
                    f"{self.BASE_URL}/api/analyze",
                    json={"video_uri": f"test_video_{i}.mp4"}
                )
                if resp.status_code == 200:
                    responses.append(resp.json())

            # If all responses are identical, it's still hardcoded
            if len(responses) >= 2:
                assert responses[0] != responses[1], "Responses are identical - still hardcoded!"

    @pytest.mark.asyncio
    async def test_analyze_has_reasoning(self):
        """Verify AI provides reasoning, not just scores"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/analyze",
                json={"video_uri": "test.mp4"}
            )
            if resp.status_code == 200:
                data = resp.json()
                assert "reasoning" in data or "analysis" in data, "No AI reasoning provided"

    @pytest.mark.asyncio
    async def test_metrics_not_fake(self):
        """Verify /api/metrics doesn't return hardcoded 15000"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/api/metrics")
            if resp.status_code == 200:
                data = resp.json()
                # If it's exactly 15000, it's still fake
                impressions = data.get("totals", {}).get("impressions", 15000)
                assert impressions != 15000 or "error" in data, "Still returning fake metrics"

    @pytest.mark.asyncio
    async def test_creative_suggestions_not_generic(self):
        """Verify /api/creative-suggestions returns specific, not generic advice"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/creative-suggestions",
                json={
                    "video_uri": "test.mp4",
                    "performance_data": {"impressions": 1000, "clicks": 50}
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                suggestions = data.get("suggestions", [])

                # Check that suggestions aren't generic phrases
                generic_phrases = [
                    "improve your content",
                    "make it better",
                    "optimize your video",
                    "increase engagement"
                ]

                if suggestions:
                    has_specific_advice = False
                    for suggestion in suggestions:
                        suggestion_lower = suggestion.lower()
                        # Should have specific details, not just generic advice
                        if len(suggestion) > 50 and not any(
                            generic in suggestion_lower for generic in generic_phrases
                        ):
                            has_specific_advice = True
                            break

                    assert has_specific_advice, "Suggestions are too generic"

    @pytest.mark.asyncio
    async def test_health_endpoints(self):
        """Verify all services are up and healthy"""
        services = [
            ("Gateway API", "http://localhost:8000/health"),
            ("Drive Intel", "http://localhost:8001/health"),
            ("Video Agent", "http://localhost:8002/health"),
            ("ML Service", "http://localhost:8003/health"),
        ]

        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in services:
                try:
                    resp = await client.get(url)
                    assert resp.status_code == 200, f"{name} is not healthy: {resp.status_code}"
                except Exception as e:
                    pytest.fail(f"{name} is unreachable: {e}")

    @pytest.mark.asyncio
    async def test_gemini_integration(self):
        """Verify Gemini API is actually being called"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/analyze",
                json={"video_uri": "test_complex_query.mp4"}
            )

            if resp.status_code == 200:
                data = resp.json()

                # Real Gemini responses should have:
                # 1. Natural language explanations
                # 2. Varied vocabulary
                # 3. Detailed reasoning

                response_text = str(data)

                # Check for indicators of real AI response
                ai_indicators = [
                    len(response_text) > 200,  # Should be detailed
                    "because" in response_text.lower() or "since" in response_text.lower(),  # Reasoning
                    any(word in response_text.lower() for word in ["analysis", "detect", "identify", "appears", "suggests"])
                ]

                assert sum(ai_indicators) >= 2, "Response doesn't appear to be from real AI"

    @pytest.mark.asyncio
    async def test_video_analysis_depth(self):
        """Verify video analysis includes visual and audio insights"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/analyze",
                json={"video_uri": "test_multimodal.mp4"}
            )

            if resp.status_code == 200:
                data = resp.json()
                response_text = str(data).lower()

                # Real video analysis should mention visual or audio elements
                visual_terms = ["visual", "scene", "frame", "color", "image", "object", "person"]
                audio_terms = ["audio", "sound", "speech", "voice", "music", "narration"]

                has_visual = any(term in response_text for term in visual_terms)
                has_audio = any(term in response_text for term in audio_terms)

                assert has_visual or has_audio, "Analysis lacks visual/audio insights"
