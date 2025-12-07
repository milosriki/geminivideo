"""Test FAISS winner index for creative pattern learning.

Tests the WinnerIndex's ability to store winning ad patterns and find similar creatives
using semantic embeddings.
"""
import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
import sys

# Add rag service to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "services" / "rag"))


@pytest.fixture
def temp_index_path():
    """Create temporary directory for index storage."""
    temp_dir = tempfile.mkdtemp(prefix="test_winner_index_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
def test_winner_index_initialization(temp_index_path):
    """Test WinnerIndex initialization."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_winners",
        use_gcs=False  # Use local storage for testing
    )

    assert index.dimension == 384  # all-MiniLM-L6-v2 dimension
    assert index.index.ntotal == 0  # Empty initially
    assert len(index.winners) == 0


@pytest.mark.integration
def test_add_winner_above_threshold(temp_index_path):
    """Test adding a winner above CTR threshold."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_add_winner",
        use_gcs=False
    )

    ad_data = {
        "hook": "Stop scrolling! This will change your business forever.",
        "body": "Watch how we helped 100+ businesses scale to 7 figures.",
        "cta": "Book your free strategy call now",
        "platform": "meta"
    }

    # Add winner with good CTR (5%)
    success = index.add_winner(ad_data, ctr=0.05, min_ctr=0.03)

    assert success == True
    assert index.index.ntotal == 1
    assert len(index.winners) == 1
    assert index.winners[0]["ctr"] == 0.05


@pytest.mark.integration
def test_add_winner_below_threshold(temp_index_path):
    """Test that winners below CTR threshold are rejected."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_threshold",
        use_gcs=False
    )

    ad_data = {
        "hook": "Generic ad copy",
        "body": "Nothing special here",
        "cta": "Click here"
    }

    # Try to add with low CTR (2%)
    success = index.add_winner(ad_data, ctr=0.02, min_ctr=0.03)

    assert success == False
    assert index.index.ntotal == 0
    assert len(index.winners) == 0


@pytest.mark.integration
def test_find_similar_winners(temp_index_path):
    """Test finding similar winning ads."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_search",
        use_gcs=False
    )

    # Add some winning ads
    winners = [
        {
            "data": {
                "hook": "Transform your business with AI automation",
                "body": "See how we helped 500+ companies save 20 hours/week",
                "cta": "Book a demo"
            },
            "ctr": 0.045
        },
        {
            "data": {
                "hook": "Scale your SaaS to $1M ARR",
                "body": "Our proven framework helped 200+ SaaS founders",
                "cta": "Join the waitlist"
            },
            "ctr": 0.052
        },
        {
            "data": {
                "hook": "Lose 20 pounds in 90 days",
                "body": "Science-backed fitness program",
                "cta": "Start your transformation"
            },
            "ctr": 0.038
        }
    ]

    for w in winners:
        index.add_winner(w["data"], ctr=w["ctr"], min_ctr=0.03)

    # Search for similar to business/automation query
    query = "AI automation for business productivity"
    results = index.find_similar(query, k=2)

    assert len(results) <= 2
    assert len(results) > 0

    # First result should be business-related (higher similarity)
    top_result = results[0]
    assert "data" in top_result
    assert "ctr" in top_result
    assert "similarity" in top_result

    # Similarity should be reasonable (not negative, not > 1)
    assert 0 <= top_result["similarity"] <= 1


@pytest.mark.integration
def test_empty_index_search(temp_index_path):
    """Test searching empty index returns empty results."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_empty",
        use_gcs=False
    )

    results = index.find_similar("any query", k=5)

    assert len(results) == 0


@pytest.mark.integration
def test_persistence_save_and_load(temp_index_path):
    """Test that index persists to disk and can be reloaded."""
    from winner_index import WinnerIndex

    index_path = f"{temp_index_path}/persistent.index"

    # Create index and add winner
    index1 = WinnerIndex(
        index_path=index_path,
        namespace="test_persist",
        use_gcs=False
    )

    ad_data = {
        "hook": "Amazing offer inside",
        "body": "Limited time special",
        "cta": "Claim now"
    }

    index1.add_winner(ad_data, ctr=0.045, min_ctr=0.03)

    # Verify saved
    assert index1.index.ntotal == 1
    assert len(index1.winners) == 1

    # Create new index instance (should load from disk)
    index2 = WinnerIndex(
        index_path=index_path,
        namespace="test_persist",
        use_gcs=False
    )

    # Verify loaded
    assert index2.index.ntotal == 1
    assert len(index2.winners) == 1
    assert index2.winners[0]["ctr"] == 0.045


@pytest.mark.integration
def test_semantic_similarity_quality(temp_index_path):
    """Test that semantic similarity actually works (similar ads score higher)."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_semantic",
        use_gcs=False
    )

    # Add semantically different ads
    index.add_winner({
        "hook": "Transform your marketing with AI",
        "body": "Automated campaigns that convert",
        "cta": "Start free trial"
    }, ctr=0.04, min_ctr=0.03)

    index.add_winner({
        "hook": "Best pizza in New York",
        "body": "Fresh ingredients, wood-fired oven",
        "cta": "Order now"
    }, ctr=0.05, min_ctr=0.03)

    # Search with marketing query
    results = index.find_similar("AI marketing automation tools", k=2)

    assert len(results) == 2

    # First result should be marketing-related (higher similarity)
    # Second should be pizza-related (lower similarity)
    marketing_sim = results[0]["similarity"]
    pizza_sim = results[1]["similarity"]

    # Marketing ad should be more similar to marketing query
    assert marketing_sim > pizza_sim


@pytest.mark.integration
def test_multiple_winners_batch_add(temp_index_path):
    """Test adding multiple winners in batch."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_batch",
        use_gcs=False
    )

    # Add 10 winners
    for i in range(10):
        ad_data = {
            "hook": f"Amazing offer {i}",
            "body": f"Benefit {i} and benefit {i+1}",
            "cta": f"Click here {i}"
        }
        index.add_winner(ad_data, ctr=0.03 + (i * 0.002), min_ctr=0.03)

    assert index.index.ntotal == 10
    assert len(index.winners) == 10


@pytest.mark.integration
def test_k_limit_in_search(temp_index_path):
    """Test that k parameter limits search results correctly."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_k_limit",
        use_gcs=False
    )

    # Add 5 winners
    for i in range(5):
        index.add_winner({
            "hook": f"Hook {i}",
            "body": f"Body {i}",
            "cta": f"CTA {i}"
        }, ctr=0.04, min_ctr=0.03)

    # Search with k=3
    results = index.find_similar("test query", k=3)

    assert len(results) == 3

    # Search with k=10 (should return all 5)
    results = index.find_similar("test query", k=10)

    assert len(results) == 5


@pytest.mark.integration
def test_winner_metadata_preservation(temp_index_path):
    """Test that all ad metadata is preserved."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_metadata",
        use_gcs=False
    )

    ad_data = {
        "hook": "Special hook",
        "body": "Special body",
        "cta": "Special CTA",
        "platform": "meta",
        "audience": "25-45",
        "custom_field": "custom_value"
    }

    index.add_winner(ad_data, ctr=0.055, min_ctr=0.03)

    # Search and verify metadata
    results = index.find_similar("special", k=1)

    assert len(results) == 1
    result_data = results[0]["data"]

    assert result_data["hook"] == "Special hook"
    assert result_data["platform"] == "meta"
    assert result_data["custom_field"] == "custom_value"
    assert results[0]["ctr"] == 0.055


@pytest.mark.integration
def test_embedding_dimension_consistency(temp_index_path):
    """Test that embeddings are consistently 384 dimensions."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_dimension",
        use_gcs=False
    )

    # Add winner
    index.add_winner({
        "hook": "Test hook",
        "body": "Test body",
        "cta": "Test CTA"
    }, ctr=0.04, min_ctr=0.03)

    # Verify dimension
    assert index.dimension == 384
    assert index.index.d == 384


@pytest.mark.integration
def test_special_characters_in_text(temp_index_path):
    """Test handling of special characters and emojis."""
    from winner_index import WinnerIndex

    index = WinnerIndex(
        index_path=f"{temp_index_path}/winners.index",
        namespace="test_special_chars",
        use_gcs=False
    )

    ad_data = {
        "hook": "🚀 Transform your business today!",
        "body": "Special offer: 50% off → Limited time ★★★",
        "cta": "Click here → Get started"
    }

    # Should handle special chars without crashing
    success = index.add_winner(ad_data, ctr=0.045, min_ctr=0.03)

    assert success == True

    # Should be searchable
    results = index.find_similar("transform business", k=1)
    assert len(results) == 1
