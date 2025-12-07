"""Test BattleHardenedSampler mode switching and decision logic.

Tests the blended scoring algorithm that shifts from CTR (early) to Pipeline ROAS (later)
based on ad age and impression volume.
"""
import pytest
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add ml-service to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "services" / "ml-service"))

from src.battle_hardened_sampler import BattleHardenedSampler, AdState


@pytest.mark.integration
def test_early_phase_ctr_dominance():
    """Test that early phase (0-6 hours) relies 100% on CTR."""
    sampler = BattleHardenedSampler()

    # Create early-stage ad (2 hours old)
    ad = AdState(
        ad_id="ad_early",
        impressions=500,
        clicks=25,  # 5% CTR
        spend=10.0,
        pipeline_value=5.0,  # Poor ROAS (0.5x)
        cash_revenue=0.0,
        age_hours=2.0,
        last_updated=datetime.now(timezone.utc)
    )

    # Get blended score
    blended_score = sampler._calculate_blended_score(ad, creative_dna_scores=None)

    # Should be 100% CTR weighted (age < 6 hours)
    assert blended_score["ctr_weight"] == 1.0
    assert blended_score["roas_weight"] == 0.0

    # Despite poor ROAS, blended score should be decent due to good CTR
    assert blended_score["blended_score"] > 0.5


@pytest.mark.integration
def test_middle_phase_blended_scoring():
    """Test that middle phase (6-24 hours) uses blended CTR + ROAS."""
    sampler = BattleHardenedSampler()

    # Create mid-stage ad (12 hours old)
    ad = AdState(
        ad_id="ad_mid",
        impressions=2000,
        clicks=60,  # 3% CTR
        spend=50.0,
        pipeline_value=150.0,  # Good ROAS (3.0x)
        cash_revenue=0.0,
        age_hours=12.0,
        last_updated=datetime.now(timezone.utc)
    )

    blended_score = sampler._calculate_blended_score(ad, creative_dna_scores=None)

    # Should have moderate blending (between 0.7 and 1.0 CTR weight)
    assert 0.7 <= blended_score["ctr_weight"] < 1.0
    assert 0.0 < blended_score["roas_weight"] <= 0.3

    # Both CTR and ROAS should contribute
    assert blended_score["normalized_ctr"] > 0.0
    assert blended_score["normalized_roas"] > 0.0


@pytest.mark.integration
def test_mature_phase_roas_dominance():
    """Test that mature phase (72+ hours) relies heavily on Pipeline ROAS."""
    sampler = BattleHardenedSampler()

    # Create mature ad (4 days old)
    ad = AdState(
        ad_id="ad_mature",
        impressions=10000,
        clicks=200,  # 2% CTR (declining)
        spend=500.0,
        pipeline_value=2000.0,  # Excellent ROAS (4.0x)
        cash_revenue=500.0,
        age_hours=96.0,  # 4 days
        last_updated=datetime.now(timezone.utc)
    )

    blended_score = sampler._calculate_blended_score(ad, creative_dna_scores=None)

    # Should be heavily ROAS weighted (age > 72 hours)
    assert blended_score["ctr_weight"] < 0.3
    assert blended_score["roas_weight"] > 0.7

    # Good ROAS should dominate the score
    assert blended_score["blended_score"] > 0.7


@pytest.mark.integration
def test_ad_fatigue_decay():
    """Test that high impression volume triggers fatigue decay."""
    sampler = BattleHardenedSampler(decay_constant=0.0001)

    # Create fatigued ad (many impressions)
    ad_fresh = AdState(
        ad_id="ad_fresh",
        impressions=1000,
        clicks=50,  # 5% CTR
        spend=20.0,
        pipeline_value=60.0,
        cash_revenue=0.0,
        age_hours=24.0,
        last_updated=datetime.now(timezone.utc)
    )

    ad_fatigued = AdState(
        ad_id="ad_fatigued",
        impressions=50000,  # Very high impressions
        clicks=2500,  # Same 5% CTR
        spend=1000.0,
        pipeline_value=3000.0,
        cash_revenue=0.0,
        age_hours=24.0,
        last_updated=datetime.now(timezone.utc)
    )

    score_fresh = sampler._calculate_blended_score(ad_fresh)
    score_fatigued = sampler._calculate_blended_score(ad_fatigued)

    # Fatigued ad should have lower decay factor
    assert score_fatigued["decay_factor"] < score_fresh["decay_factor"]

    # Final score should be lower for fatigued ad despite same CTR/ROAS
    assert score_fatigued["final_score"] < score_fresh["final_score"]


@pytest.mark.integration
def test_creative_dna_boost():
    """Test that creative DNA similarity provides score boost."""
    sampler = BattleHardenedSampler()

    ad = AdState(
        ad_id="ad_dna_boost",
        impressions=1000,
        clicks=30,  # 3% CTR
        spend=50.0,
        pipeline_value=150.0,
        cash_revenue=0.0,
        age_hours=24.0,
        last_updated=datetime.now(timezone.utc)
    )

    # Score without DNA boost
    score_no_boost = sampler._calculate_blended_score(ad, creative_dna_scores=None)

    # Score with high DNA similarity
    score_with_boost = sampler._calculate_blended_score(
        ad,
        creative_dna_scores={"ad_dna_boost": 0.95}  # 95% similar to winner
    )

    # DNA boost should increase final score
    assert score_with_boost["dna_boost"] > score_no_boost["dna_boost"]
    assert score_with_boost["final_score"] > score_no_boost["final_score"]

    # DNA boost should be up to 20% (1.0 + 0.95 * 0.2 = 1.19)
    assert score_with_boost["dna_boost"] <= 1.2


@pytest.mark.integration
def test_budget_allocation_softmax():
    """Test that budget allocation uses softmax (no winner takes all)."""
    sampler = BattleHardenedSampler()

    # Create 3 ads with varying performance
    ads = [
        AdState(
            ad_id="ad_winner",
            impressions=5000,
            clicks=250,  # 5% CTR
            spend=100.0,
            pipeline_value=500.0,  # 5.0x ROAS
            cash_revenue=0.0,
            age_hours=48.0,
            last_updated=datetime.now(timezone.utc)
        ),
        AdState(
            ad_id="ad_middle",
            impressions=4000,
            clicks=120,  # 3% CTR
            spend=100.0,
            pipeline_value=300.0,  # 3.0x ROAS
            cash_revenue=0.0,
            age_hours=48.0,
            last_updated=datetime.now(timezone.utc)
        ),
        AdState(
            ad_id="ad_loser",
            impressions=3000,
            clicks=30,  # 1% CTR
            spend=100.0,
            pipeline_value=100.0,  # 1.0x ROAS
            cash_revenue=0.0,
            age_hours=48.0,
            last_updated=datetime.now(timezone.utc)
        ),
    ]

    # Allocate $300 budget
    recommendations = sampler.select_budget_allocation(ads, total_budget=300.0)

    # All ads should get some budget (no zeros due to softmax)
    for rec in recommendations:
        assert rec.recommended_budget > 0

    # Winner should get most budget
    winner_budget = next(r.recommended_budget for r in recommendations if r.ad_id == "ad_winner")
    loser_budget = next(r.recommended_budget for r in recommendations if r.ad_id == "ad_loser")
    assert winner_budget > loser_budget

    # Total should sum to allocated budget
    total_allocated = sum(r.recommended_budget for r in recommendations)
    assert abs(total_allocated - 300.0) < 0.01  # Allow for rounding


@pytest.mark.integration
def test_budget_change_capping():
    """Test that budget changes are capped to max_budget_change_pct."""
    sampler = BattleHardenedSampler(max_budget_change_pct=0.50)  # Max 50% change

    ad = AdState(
        ad_id="ad_huge_winner",
        impressions=10000,
        clicks=800,  # 8% CTR (amazing!)
        spend=200.0,
        pipeline_value=1000.0,  # 5.0x ROAS
        cash_revenue=0.0,
        age_hours=72.0,
        last_updated=datetime.now(timezone.utc)
    )

    # Current budget estimate
    current_budget = 100.0

    # Generate recommendation
    blended_score = sampler._calculate_blended_score(ad)
    rec = sampler._generate_recommendation(
        ad=ad,
        current_budget=current_budget,
        recommended_budget=250.0,  # Would be 150% increase
        blended_score=blended_score
    )

    # Change should be capped at 50%
    assert rec.change_percentage <= 50.0
    assert rec.recommended_budget <= current_budget * 1.5


@pytest.mark.integration
def test_confidence_scoring():
    """Test that confidence increases with more data and age."""
    sampler = BattleHardenedSampler()

    # Low data ad
    ad_low_data = AdState(
        ad_id="ad_low_data",
        impressions=100,  # Low impressions
        clicks=5,
        spend=10.0,
        pipeline_value=30.0,
        cash_revenue=0.0,
        age_hours=6.0,  # Young
        last_updated=datetime.now(timezone.utc)
    )

    # High data ad
    ad_high_data = AdState(
        ad_id="ad_high_data",
        impressions=5000,  # High impressions
        clicks=250,
        spend=500.0,
        pipeline_value=1500.0,
        cash_revenue=0.0,
        age_hours=96.0,  # Mature
        last_updated=datetime.now(timezone.utc)
    )

    recs = sampler.select_budget_allocation(
        [ad_low_data, ad_high_data],
        total_budget=200.0
    )

    low_data_rec = next(r for r in recs if r.ad_id == "ad_low_data")
    high_data_rec = next(r for r in recs if r.ad_id == "ad_high_data")

    # High data ad should have higher confidence
    assert high_data_rec.confidence > low_data_rec.confidence


@pytest.mark.integration
def test_reason_generation():
    """Test that human-readable reasons are generated correctly."""
    sampler = BattleHardenedSampler()

    # Early phase ad with good CTR
    ad_early = AdState(
        ad_id="ad_early_ctr",
        impressions=500,
        clicks=30,  # 6% CTR
        spend=20.0,
        pipeline_value=10.0,
        cash_revenue=0.0,
        age_hours=3.0,
        last_updated=datetime.now(timezone.utc)
    )

    recs = sampler.select_budget_allocation([ad_early], total_budget=100.0)
    rec = recs[0]

    # Reason should mention CTR for early phase
    assert "CTR" in rec.reason or "early" in rec.reason.lower()

    # Mature ad with good ROAS
    ad_mature = AdState(
        ad_id="ad_mature_roas",
        impressions=10000,
        clicks=200,
        spend=500.0,
        pipeline_value=2000.0,  # 4.0x ROAS
        cash_revenue=0.0,
        age_hours=96.0,
        last_updated=datetime.now(timezone.utc)
    )

    recs = sampler.select_budget_allocation([ad_mature], total_budget=100.0)
    rec = recs[0]

    # Reason should mention ROAS for mature phase
    assert "ROAS" in rec.reason or "Pipeline" in rec.reason
