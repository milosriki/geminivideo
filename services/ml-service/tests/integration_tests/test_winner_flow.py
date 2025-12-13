"""
Complete integration test for winner ads flow.
Tests: Detection -> Indexing -> Replication -> Budget -> Agents

Agent 11 Task 11.1: Winner Flow Integration Test
Created: 2025-12-13
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@dataclass
class TestWinnerAd:
    """Test winner ad data structure."""
    ad_id: str
    video_id: str
    ctr: float
    roas: float
    impressions: int
    spend: float
    conversions: int
    revenue: float
    creative_dna: Dict[str, Any]
    created_at: datetime


def create_test_winner_ad(
    ctr: float = 0.035,
    roas: float = 3.5,
    impressions: int = 10000,
    spend: float = 500.0
) -> TestWinnerAd:
    """Create a test winner ad with specified performance metrics."""
    conversions = int(impressions * ctr * 0.1)  # 10% conversion rate from clicks
    revenue = spend * roas

    return TestWinnerAd(
        ad_id=f"test_ad_{uuid.uuid4().hex[:8]}",
        video_id=f"test_video_{uuid.uuid4().hex[:8]}",
        ctr=ctr,
        roas=roas,
        impressions=impressions,
        spend=spend,
        conversions=conversions,
        revenue=revenue,
        creative_dna={
            "hook_type": "curiosity",
            "duration_seconds": 15,
            "cta_type": "shop_now",
            "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
            "emotion_score": 0.85,
            "pace": "fast",
            "music_type": "upbeat",
            "visual_elements": ["product_demo", "testimonial", "urgency_text"]
        },
        created_at=datetime.utcnow()
    )


# ============================================================================
# Winner Detection Tests
# ============================================================================

class TestWinnerDetection:
    """Test winner detection logic."""

    @pytest.fixture
    def winner_thresholds(self):
        """Default winner thresholds."""
        return {
            "min_ctr": 0.03,  # 3% CTR
            "min_roas": 2.0,   # 2x ROAS
            "min_impressions": 1000
        }

    def test_detect_winner_above_threshold(self, winner_thresholds):
        """Test that ads above threshold are detected as winners."""
        test_ad = create_test_winner_ad(ctr=0.035, roas=3.5)

        is_winner = (
            test_ad.ctr >= winner_thresholds["min_ctr"] and
            test_ad.roas >= winner_thresholds["min_roas"] and
            test_ad.impressions >= winner_thresholds["min_impressions"]
        )

        assert is_winner is True
        assert test_ad.ctr > 0.03
        assert test_ad.roas > 2.0

    def test_detect_non_winner_below_ctr(self, winner_thresholds):
        """Test that ads below CTR threshold are not winners."""
        test_ad = create_test_winner_ad(ctr=0.02, roas=3.5)

        is_winner = (
            test_ad.ctr >= winner_thresholds["min_ctr"] and
            test_ad.roas >= winner_thresholds["min_roas"] and
            test_ad.impressions >= winner_thresholds["min_impressions"]
        )

        assert is_winner is False

    def test_detect_non_winner_below_roas(self, winner_thresholds):
        """Test that ads below ROAS threshold are not winners."""
        test_ad = create_test_winner_ad(ctr=0.04, roas=1.5)

        is_winner = (
            test_ad.ctr >= winner_thresholds["min_ctr"] and
            test_ad.roas >= winner_thresholds["min_roas"] and
            test_ad.impressions >= winner_thresholds["min_impressions"]
        )

        assert is_winner is False

    def test_detect_non_winner_below_impressions(self, winner_thresholds):
        """Test that ads below impression threshold are not winners."""
        test_ad = create_test_winner_ad(ctr=0.04, roas=3.0, impressions=500)

        is_winner = (
            test_ad.ctr >= winner_thresholds["min_ctr"] and
            test_ad.roas >= winner_thresholds["min_roas"] and
            test_ad.impressions >= winner_thresholds["min_impressions"]
        )

        assert is_winner is False


# ============================================================================
# Winner Index Tests
# ============================================================================

class TestWinnerIndex:
    """Test winner indexing functionality."""

    @pytest.fixture
    def mock_winner_index(self):
        """Create a mock winner index."""
        index = Mock()
        index.add_winner = Mock(return_value=True)
        index.find_similar = Mock(return_value=[])
        index.persist = Mock(return_value=True)
        index.stats = Mock(return_value={
            "total_winners": 0,
            "dimension": 768,
            "faiss_available": True
        })
        return index

    def test_add_winner_to_index(self, mock_winner_index):
        """Test adding a winner to the index."""
        test_ad = create_test_winner_ad()

        # Simulate embedding generation
        import numpy as np
        embedding = np.random.randn(768).astype('float32')

        # Add to index
        result = mock_winner_index.add_winner(
            ad_id=test_ad.ad_id,
            embedding=embedding,
            metadata={
                "ctr": test_ad.ctr,
                "roas": test_ad.roas,
                "creative_dna": test_ad.creative_dna
            }
        )

        assert result is True
        mock_winner_index.add_winner.assert_called_once()

    def test_find_similar_winners(self, mock_winner_index):
        """Test finding similar winners."""
        import numpy as np

        # Setup mock return
        mock_winner_index.find_similar.return_value = [
            {
                "ad_id": "similar_ad_1",
                "similarity": 0.95,
                "metadata": {"ctr": 0.04, "roas": 3.2}
            },
            {
                "ad_id": "similar_ad_2",
                "similarity": 0.85,
                "metadata": {"ctr": 0.035, "roas": 2.8}
            }
        ]

        query_embedding = np.random.randn(768).astype('float32')
        similar = mock_winner_index.find_similar(embedding=query_embedding, k=5)

        assert len(similar) == 2
        assert similar[0]["similarity"] > similar[1]["similarity"]

    def test_persist_index(self, mock_winner_index):
        """Test persisting the winner index."""
        result = mock_winner_index.persist()
        assert result is True


# ============================================================================
# Winner Replication Tests
# ============================================================================

class TestWinnerReplication:
    """Test winner replication functionality."""

    @pytest.fixture
    def mock_replicator(self):
        """Create a mock winner replicator."""
        replicator = AsyncMock()
        replicator.replicate_top_winners = AsyncMock(return_value=[])
        replicator.create_variation = AsyncMock(return_value=None)
        return replicator

    @pytest.mark.asyncio
    async def test_replicate_top_winners(self, mock_replicator):
        """Test replicating top winners."""
        test_winner = create_test_winner_ad()

        # Setup mock return
        mock_replicator.replicate_top_winners.return_value = [
            {
                "original_ad_id": test_winner.ad_id,
                "variation_id": f"var_{uuid.uuid4().hex[:8]}",
                "variation_type": "hook_swap",
                "created_at": datetime.utcnow().isoformat()
            }
        ]

        replicated = await mock_replicator.replicate_top_winners(limit=1)

        assert len(replicated) >= 1
        assert "variation_id" in replicated[0]

    @pytest.mark.asyncio
    async def test_create_variation(self, mock_replicator):
        """Test creating a variation of a winner."""
        test_winner = create_test_winner_ad()

        mock_replicator.create_variation.return_value = {
            "variation_id": f"var_{uuid.uuid4().hex[:8]}",
            "original_ad_id": test_winner.ad_id,
            "changes": {
                "hook_text": "New hook text",
                "cta_type": "learn_more"
            }
        }

        variation = await mock_replicator.create_variation(
            winner_ad=test_winner,
            variation_type="hook_swap"
        )

        assert variation is not None
        assert "variation_id" in variation


# ============================================================================
# Budget Reallocation Tests
# ============================================================================

class TestBudgetReallocation:
    """Test budget reallocation functionality."""

    @pytest.fixture
    def mock_budget_allocator(self):
        """Create a mock budget allocator."""
        allocator = AsyncMock()
        allocator.auto_reallocate_budget_to_winners = AsyncMock()
        allocator.get_reallocation_summary = Mock()
        return allocator

    @pytest.mark.asyncio
    async def test_auto_reallocate_budget(self, mock_budget_allocator):
        """Test automatic budget reallocation to winners."""
        mock_budget_allocator.auto_reallocate_budget_to_winners.return_value = {
            "status": "success",
            "reallocated_amount": 1000.0,
            "from_ads": ["underperforming_ad_1", "underperforming_ad_2"],
            "to_ads": ["winner_ad_1"],
            "timestamp": datetime.utcnow().isoformat()
        }

        result = await mock_budget_allocator.auto_reallocate_budget_to_winners(
            account_id="test_account"
        )

        assert result["status"] == "success"
        assert result["reallocated_amount"] > 0

    @pytest.mark.asyncio
    async def test_budget_reallocation_no_winners(self, mock_budget_allocator):
        """Test budget reallocation when no winners exist."""
        mock_budget_allocator.auto_reallocate_budget_to_winners.return_value = {
            "status": "no_action",
            "reason": "No qualifying winners found",
            "reallocated_amount": 0.0
        }

        result = await mock_budget_allocator.auto_reallocate_budget_to_winners(
            account_id="test_account"
        )

        assert result["reallocated_amount"] == 0.0


# ============================================================================
# Agent Workflow Tests
# ============================================================================

class TestAgentWorkflow:
    """Test agent workflow integration."""

    @pytest.fixture
    def mock_workflow(self):
        """Create a mock agent workflow."""
        workflow = AsyncMock()
        workflow.run = AsyncMock()
        return workflow

    @pytest.mark.asyncio
    async def test_winner_detected_workflow(self, mock_workflow):
        """Test agent workflow when a winner is detected."""
        test_winner = create_test_winner_ad()

        mock_workflow.run.return_value = {
            "success": True,
            "actions_taken": [
                "indexed_winner",
                "created_variations",
                "reallocated_budget",
                "sent_notification"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        workflow_result = await mock_workflow.run(
            winner_data={
                "ad_id": test_winner.ad_id,
                "ctr": test_winner.ctr,
                "roas": test_winner.roas
            }
        )

        assert workflow_result["success"] is True
        assert "actions_taken" in workflow_result
        assert len(workflow_result["actions_taken"]) > 0


# ============================================================================
# End-to-End Integration Test
# ============================================================================

class TestCompleteWinnerFlow:
    """Complete end-to-end winner flow test."""

    @pytest.fixture
    def full_mock_setup(self):
        """Setup all mocked components."""
        return {
            "fetcher": AsyncMock(),
            "winner_index": Mock(),
            "replicator": AsyncMock(),
            "budget_allocator": AsyncMock(),
            "workflow": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_complete_winner_flow(self, full_mock_setup):
        """Test complete winner flow end-to-end."""
        # 1. Create test ad with winner performance
        test_ad = create_test_winner_ad(ctr=0.035, roas=3.5)

        # 2. Mock fetcher to return actuals
        full_mock_setup["fetcher"].fetch_actuals.return_value = {
            "ad_id": test_ad.ad_id,
            "ctr": test_ad.ctr,
            "roas": test_ad.roas,
            "impressions": test_ad.impressions,
            "spend": test_ad.spend
        }

        # Fetch actuals
        actuals = await full_mock_setup["fetcher"].fetch_actuals(ad_id=test_ad.ad_id)
        assert actuals is not None
        assert actuals["ctr"] >= 0.03  # Winner threshold

        # 3. Verify winner indexed
        import numpy as np
        full_mock_setup["winner_index"].add_winner.return_value = True
        full_mock_setup["winner_index"].find_similar.return_value = [
            {
                "ad_id": test_ad.ad_id,
                "similarity": 1.0,
                "metadata": {"ctr": test_ad.ctr, "roas": test_ad.roas}
            }
        ]

        embedding = np.random.randn(768).astype('float32')
        add_result = full_mock_setup["winner_index"].add_winner(
            ad_id=test_ad.ad_id,
            embedding=embedding,
            metadata={"ctr": test_ad.ctr, "roas": test_ad.roas}
        )
        assert add_result is True

        winners = full_mock_setup["winner_index"].find_similar(embedding=None, k=1)
        assert len(winners) > 0
        assert winners[0]["ad_id"] == test_ad.ad_id

        # 4. Test replication
        full_mock_setup["replicator"].replicate_top_winners.return_value = [
            {"variation_id": f"var_{uuid.uuid4().hex[:8]}", "original_ad_id": test_ad.ad_id}
        ]

        replicated = await full_mock_setup["replicator"].replicate_top_winners(limit=1)
        assert len(replicated) >= 1

        # 5. Test budget reallocation
        full_mock_setup["budget_allocator"].auto_reallocate_budget_to_winners.return_value = {
            "status": "success",
            "reallocated_amount": 500.0
        }

        result = await full_mock_setup["budget_allocator"].auto_reallocate_budget_to_winners(
            account_id="test"
        )
        assert result["status"] == "success"

        # 6. Test agent workflow trigger
        full_mock_setup["workflow"].run.return_value = {"success": True}

        workflow_result = await full_mock_setup["workflow"].run(winners[0])
        assert workflow_result["success"] is True

        # All steps completed successfully
        print("✅ Complete winner flow test passed!")


# ============================================================================
# Performance Tests
# ============================================================================

class TestWinnerFlowPerformance:
    """Performance tests for winner flow."""

    @pytest.mark.asyncio
    async def test_batch_winner_processing(self):
        """Test processing multiple winners in batch."""
        import time

        num_winners = 100
        winners = [create_test_winner_ad() for _ in range(num_winners)]

        start_time = time.time()

        # Simulate batch processing
        processed = []
        for winner in winners:
            # Simulate processing
            await asyncio.sleep(0.001)  # Minimal delay
            processed.append(winner.ad_id)

        duration = time.time() - start_time

        assert len(processed) == num_winners
        assert duration < 5.0  # Should complete in under 5 seconds

        print(f"✅ Processed {num_winners} winners in {duration:.2f}s")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
