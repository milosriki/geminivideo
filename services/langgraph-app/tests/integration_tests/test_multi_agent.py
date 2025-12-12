"""Integration tests for multi-agent system."""

import pytest

from agent import graph

pytestmark = pytest.mark.anyio


@pytest.mark.langsmith
async def test_multi_agent_analyze_campaign():
    """Test campaign analysis workflow."""
    inputs = {
        "input_data": {
            "operation": "analyze_campaign",
            "campaign_id": "test_campaign_123",
            "ad_data": {"hook": "test hook", "visual_score": 0.8},
        }
    }
    
    result = await graph.graph.ainvoke(inputs)
    
    assert result is not None
    assert "results" in result
    assert "agent_results" in result.get("results", {})
    assert result.get("results", {}).get("success") is not None


@pytest.mark.langsmith
async def test_multi_agent_generate_content():
    """Test content generation workflow."""
    inputs = {
        "input_data": {
            "operation": "generate_content",
            "campaign_data": {
                "product_name": "Test Product",
                "offer": "Special Offer",
                "pain_points": ["pain1", "pain2"],
            },
        }
    }
    
    result = await graph.graph.ainvoke(inputs)
    
    assert result is not None
    assert "results" in result


@pytest.mark.langsmith
async def test_multi_agent_optimize_budget():
    """Test budget optimization workflow."""
    inputs = {
        "input_data": {
            "operation": "optimize_budget",
            "ad_states": [
                {"ad_id": "ad1", "ctr": 0.045, "pipeline_value": 1000},
                {"ad_id": "ad2", "ctr": 0.042, "pipeline_value": 800},
            ],
        }
    }
    
    result = await graph.graph.ainvoke(inputs)
    
    assert result is not None
    assert "results" in result


@pytest.mark.langsmith
async def test_multi_agent_full_pipeline():
    """Test full end-to-end pipeline."""
    inputs = {
        "input_data": {
            "operation": "full_pipeline",
            "video_url": "https://example.com/video.mp4",
            "campaign_data": {
                "product_name": "Test Product",
                "offer": "Special Offer",
            },
            "ad_data": {"hook": "test hook"},
        }
    }
    
    result = await graph.graph.ainvoke(inputs)
    
    assert result is not None
    assert "results" in result


@pytest.mark.langsmith
async def test_multi_agent_error_handling():
    """Test error handling."""
    inputs = {
        "input_data": {
            "operation": "invalid_operation",
        }
    }
    
    result = await graph.graph.ainvoke(inputs)
    
    # Should handle errors gracefully
    assert result is not None
    assert "results" in result


@pytest.mark.langsmith
async def test_multi_agent_parallel_execution():
    """Test parallel agent execution."""
    inputs = {
        "input_data": {
            "operation": "full_pipeline",
            "video_url": "https://example.com/video.mp4",
            "campaign_data": {"product_name": "Test"},
        }
    }
    
    context = {"strategy": "parallel"}
    
    result = await graph.graph.ainvoke(inputs, config={"configurable": context})
    
    assert result is not None
    assert "results" in result

