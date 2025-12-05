"""
Test Cross-Account Learning System
Agent 49 - Unit Tests for Network Effects

This test suite verifies:
1. Niche detection
2. Insight extraction
3. Wisdom aggregation
4. Pattern sharing
5. Privacy preservation
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock

from src.cross_learner import (
    CrossAccountLearner,
    AccountInsights,
    NicheWisdom,
    NicheCategory
)


class MockDBSession:
    """Mock database session for testing."""

    def __init__(self):
        self.executed_queries = []

    async def execute(self, query, *args):
        """Mock execute method."""
        self.executed_queries.append((query, args))
        # Return mock result
        return MockResult()

    async def commit(self):
        """Mock commit."""
        pass

    async def rollback(self):
        """Mock rollback."""
        pass


class MockResult:
    """Mock query result."""

    def __init__(self, data=None):
        self.data = data or []

    def scalars(self):
        """Return scalars."""
        return MockScalars(self.data)

    def scalar_one_or_none(self):
        """Return single scalar or None."""
        return self.data[0] if self.data else None

    def first(self):
        """Return first result."""
        return self.data[0] if self.data else None


class MockScalars:
    """Mock scalars result."""

    def __init__(self, data):
        self.data = data

    def all(self):
        """Return all results."""
        return self.data


async def test_niche_detection_keyword():
    """Test keyword-based niche detection."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    # Test fitness detection
    titles = ["10 Minute Workout", "Build Muscle Fast", "Gym Routine"]
    descriptions = ["Get fit with this workout", "Exercise daily"]

    niche, confidence = learner._keyword_niche_detection(titles, descriptions)

    assert niche == NicheCategory.FITNESS.value
    assert confidence > 0.0
    print(f"✓ Fitness detection: {niche} ({confidence:.2f})")



async def test_niche_detection_beauty():
    """Test beauty niche detection."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    titles = ["Skincare Routine", "Makeup Tutorial", "Beauty Tips"]
    descriptions = ["Best cosmetics for your skin"]

    niche, confidence = learner._keyword_niche_detection(titles, descriptions)

    assert niche == NicheCategory.BEAUTY.value
    print(f"✓ Beauty detection: {niche} ({confidence:.2f})")



async def test_account_insights_creation():
    """Test AccountInsights dataclass."""
    insights = AccountInsights(
        account_id="test_123",
        niche="fitness",
        confidence=0.85,
        top_hook_types=[{"hook_type": "question", "count": 5}],
        optimal_duration_range=(15.0, 30.0),
        best_posting_times=[9, 12, 17],
        effective_cta_styles=["learn_more", "shop_now"],
        visual_preferences=["fast_cuts"],
        avg_ctr=0.023,
        avg_conversion_rate=0.034,
        avg_roas=3.2,
        total_campaigns=10,
        total_conversions=50,
        account_age_days=90,
        opted_in=True,
        extracted_at=datetime.now()
    )

    assert insights.account_id == "test_123"
    assert insights.niche == "fitness"
    assert insights.avg_ctr == 0.023
    assert len(insights.best_posting_times) == 3

    # Test to_dict conversion
    insights_dict = insights.to_dict()
    assert "account_id" in insights_dict
    assert "extracted_at" in insights_dict

    print(f"✓ AccountInsights created successfully")



async def test_niche_wisdom_creation():
    """Test NicheWisdom dataclass."""
    wisdom = NicheWisdom(
        niche="fitness",
        sample_size=25,
        top_hook_types=[{"hook_type": "question", "frequency": 15}],
        optimal_duration=(15.0, 30.0),
        peak_hours=[9, 12, 17],
        proven_cta_styles=[{"style": "learn_more", "success_rate": 75}],
        winning_visual_patterns=[{"pattern": "fast_cuts", "frequency": 20}],
        niche_avg_ctr=0.021,
        niche_avg_conversion_rate=0.032,
        niche_avg_roas=3.5,
        confidence_score=0.88,
        last_updated=datetime.now()
    )

    assert wisdom.niche == "fitness"
    assert wisdom.sample_size == 25
    assert wisdom.confidence_score == 0.88

    # Test to_dict conversion
    wisdom_dict = wisdom.to_dict()
    assert "niche" in wisdom_dict
    assert "last_updated" in wisdom_dict

    print(f"✓ NicheWisdom created successfully")



async def test_pattern_aggregation():
    """Test pattern aggregation functions."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    # Test hook type aggregation
    winners = [
        {"campaign_id": "1", "ctr": 0.025},
        {"campaign_id": "2", "ctr": 0.022},
        {"campaign_id": "3", "ctr": 0.021}
    ]

    hook_types = learner._aggregate_hook_types(winners)
    assert isinstance(hook_types, list)
    print(f"✓ Hook types aggregated: {len(hook_types)} types")

    # Test duration range calculation
    duration_range = learner._calculate_duration_range(winners)
    assert isinstance(duration_range, tuple)
    assert len(duration_range) == 2
    print(f"✓ Duration range calculated: {duration_range}")

    # Test posting times aggregation
    posting_times = learner._aggregate_posting_times(winners)
    assert isinstance(posting_times, list)
    print(f"✓ Posting times aggregated: {posting_times}")



async def test_privacy_preservation():
    """Test that privacy is preserved in insights."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    # Create mock insights
    insights = AccountInsights(
        account_id="test_123",
        niche="fitness",
        confidence=0.85,
        top_hook_types=[{"hook_type": "question", "count": 5}],
        optimal_duration_range=(15.0, 30.0),
        best_posting_times=[9, 12, 17],
        effective_cta_styles=["learn_more"],
        visual_preferences=["fast_cuts"],
        avg_ctr=0.023,
        avg_conversion_rate=0.034,
        avg_roas=3.2,
        total_campaigns=10,
        total_conversions=50,
        account_age_days=90,
        opted_in=True,
        extracted_at=datetime.now()
    )

    insights_dict = insights.to_dict()

    # Verify no sensitive content is included
    assert "campaign_names" not in insights_dict
    assert "video_urls" not in insights_dict
    assert "customer_data" not in insights_dict
    assert "specific_content" not in insights_dict

    # Verify only patterns and aggregates are included
    assert "top_hook_types" in insights_dict
    assert "avg_ctr" in insights_dict
    assert "niche" in insights_dict

    print("✓ Privacy preservation verified")



async def test_wisdom_confidence_calculation():
    """Test wisdom confidence calculation."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    # Create mock insights
    insights_list = [
        AccountInsights(
            account_id=f"test_{i}",
            niche="fitness",
            confidence=0.8 + (i * 0.02),  # Varying confidence
            top_hook_types=[],
            optimal_duration_range=(15.0, 30.0),
            best_posting_times=[],
            effective_cta_styles=[],
            visual_preferences=[],
            avg_ctr=0.02,
            avg_conversion_rate=0.03,
            avg_roas=3.0,
            total_campaigns=10,
            total_conversions=50,
            account_age_days=90,
            opted_in=True,
            extracted_at=datetime.now()
        )
        for i in range(10)
    ]

    confidence = learner._calculate_wisdom_confidence(insights_list)
    assert 0.0 <= confidence <= 1.0
    print(f"✓ Wisdom confidence calculated: {confidence:.2f}")



async def test_rank_by_frequency():
    """Test ranking items by frequency."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    items_lists = [
        [{"hook_type": "question"}, {"hook_type": "pain_point"}],
        [{"hook_type": "question"}, {"hook_type": "curiosity"}],
        [{"hook_type": "question"}, {"hook_type": "pain_point"}]
    ]

    ranked = learner._rank_by_frequency(items_lists)
    assert isinstance(ranked, list)
    assert len(ranked) > 0

    # "question" should be most frequent
    if ranked:
        assert "question" in ranked[0]["item"]

    print(f"✓ Frequency ranking working: {len(ranked)} items ranked")



async def test_average_range():
    """Test averaging duration ranges."""
    db_session = MockDBSession()
    learner = CrossAccountLearner(db_session=db_session)

    ranges = [
        (10.0, 20.0),
        (15.0, 25.0),
        (12.0, 22.0)
    ]

    avg_range = learner._average_range(ranges)
    assert isinstance(avg_range, tuple)
    assert len(avg_range) == 2
    assert avg_range[0] > 0
    assert avg_range[1] > avg_range[0]

    print(f"✓ Range averaging working: {avg_range}")


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  CROSS-ACCOUNT LEARNING - Test Suite")
    print("  Agent 49 - Network Effects Testing")
    print("=" * 80 + "\n")

    # Run async tests
    asyncio.run(test_niche_detection_keyword())
    asyncio.run(test_niche_detection_beauty())
    asyncio.run(test_account_insights_creation())
    asyncio.run(test_niche_wisdom_creation())
    asyncio.run(test_pattern_aggregation())
    asyncio.run(test_privacy_preservation())
    asyncio.run(test_wisdom_confidence_calculation())
    asyncio.run(test_rank_by_frequency())
    asyncio.run(test_average_range())

    print("\n" + "=" * 80)
    print("  All Tests Passed! ✓")
    print("  Cross-Account Learning System Ready for Production")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_tests()
