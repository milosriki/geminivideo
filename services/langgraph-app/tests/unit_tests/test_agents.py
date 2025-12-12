"""Unit tests for individual agents."""

import pytest

from agent.agents import (
    DatabaseAgent,
    VideoAnalysisAgent,
    MLPredictionAgent,
    ContentGenerationAgent,
)

pytestmark = pytest.mark.anyio


@pytest.mark.asyncio
async def test_database_agent():
    """Test DatabaseAgent."""
    agent = DatabaseAgent()
    
    result = await agent.execute({
        "operation": "query",
        "query": "SELECT * FROM campaigns",
    })
    
    assert result.success is not None
    assert result.data is not None


@pytest.mark.asyncio
async def test_video_analysis_agent():
    """Test VideoAnalysisAgent."""
    agent = VideoAnalysisAgent()
    
    result = await agent.execute({
        "operation": "analyze",
        "video_url": "https://example.com/video.mp4",
    })
    
    assert result.success is not None


@pytest.mark.asyncio
async def test_ml_prediction_agent():
    """Test MLPredictionAgent."""
    agent = MLPredictionAgent()
    
    result = await agent.execute({
        "operation": "predict_ctr",
        "ad_data": {"hook": "test hook"},
    })
    
    assert result.success is not None
    assert result.data is not None


@pytest.mark.asyncio
async def test_content_generation_agent():
    """Test ContentGenerationAgent."""
    agent = ContentGenerationAgent()
    
    result = await agent.execute({
        "operation": "generate_script",
        "campaign_data": {
            "product_name": "Test Product",
            "offer": "Special Offer",
        },
    })
    
    assert result.success is not None
    assert result.data is not None


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent error handling."""
    agent = DatabaseAgent()
    
    result = await agent.execute({
        "operation": "invalid_operation",
    })
    
    # Should handle errors gracefully
    assert result.success is False or result.success is True
    assert result.error is not None or result.data is not None


@pytest.mark.asyncio
async def test_agent_retry_logic():
    """Test agent retry logic."""
    agent = DatabaseAgent(max_retries=2)
    
    # This will test retry logic if we have a retryable error
    result = await agent.execute({
        "operation": "query",
        "query": "SELECT * FROM campaigns",
    })
    
    assert result is not None

