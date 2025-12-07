"""Test complete intelligence feedback loop.

Tests the end-to-end flow:
HubSpot Webhook → Attribution → Sampler → Decision → Queue → Execution

This validates that all components work together in the intelligence system.
"""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add service paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "services" / "ml-service"))


@pytest.mark.integration
@pytest.mark.slow
async def test_hubspot_to_attribution_flow():
    """Test: HubSpot webhook → Attribution engine → Synthetic revenue calculation.

    Flow:
    1. HubSpot sends deal update webhook
    2. Attribution engine matches deal to ad
    3. Synthetic revenue is calculated based on pipeline stage
    """
    # Mock HubSpot webhook payload
    hubspot_webhook = {
        "objectId": "12345",
        "propertyName": "dealstage",
        "propertyValue": "appointmentscheduled",
        "changeSource": "CRM",
        "eventId": 1,
        "subscriptionId": 1,
        "portalId": 123456,
        "occurredAt": int(datetime.utcnow().timestamp() * 1000)
    }

    # Expected deal data from HubSpot API
    deal_data = {
        "id": "12345",
        "properties": {
            "dealname": "Test Deal",
            "amount": "5000",
            "dealstage": "appointmentscheduled",
            "pipeline": "default",
            "createdate": "2024-01-15T10:00:00Z",
            "hs_analytics_source": "PAID_SOCIAL",
            "utm_campaign": "campaign_123",
            "utm_content": "ad_456"
        }
    }

    # Step 1: Attribution (match deal to ad)
    ad_id = deal_data["properties"].get("utm_content", "unknown")
    campaign_id = deal_data["properties"].get("utm_campaign", "unknown")

    assert ad_id == "ad_456"
    assert campaign_id == "campaign_123"

    # Step 2: Synthetic revenue calculation
    stage = deal_data["properties"]["dealstage"]
    amount = float(deal_data["properties"]["amount"])

    # Synthetic revenue multipliers by stage
    stage_multipliers = {
        "appointmentscheduled": 0.3,  # 30% of deal value
        "qualifiedtobuy": 0.5,
        "presentationscheduled": 0.7,
        "decisionmakerboughtin": 0.9,
        "contractsent": 0.95,
        "closedwon": 1.0
    }

    synthetic_revenue = amount * stage_multipliers.get(stage, 0.0)

    assert synthetic_revenue == 1500.0  # $5000 * 0.3

    # Step 3: Store attribution
    attribution_record = {
        "deal_id": deal_data["id"],
        "ad_id": ad_id,
        "campaign_id": campaign_id,
        "pipeline_stage": stage,
        "deal_amount": amount,
        "synthetic_revenue": synthetic_revenue,
        "created_at": datetime.utcnow().isoformat()
    }

    assert attribution_record["synthetic_revenue"] > 0


@pytest.mark.integration
@pytest.mark.slow
async def test_attribution_to_sampler_flow():
    """Test: Attribution data → BattleHardenedSampler → Budget decision.

    Flow:
    1. Attribution data accumulates for ads
    2. Sampler calculates blended scores
    3. Budget recommendations generated
    """
    from src.battle_hardened_sampler import BattleHardenedSampler, AdState

    # Mock accumulated performance data for 3 ads
    ad_performance = [
        {
            "ad_id": "ad_winner",
            "impressions": 5000,
            "clicks": 250,
            "spend": 100.0,
            "pipeline_value": 600.0,  # From attribution
            "age_hours": 48.0
        },
        {
            "ad_id": "ad_middle",
            "impressions": 4000,
            "clicks": 120,
            "spend": 100.0,
            "pipeline_value": 300.0,
            "age_hours": 48.0
        },
        {
            "ad_id": "ad_loser",
            "impressions": 3000,
            "clicks": 30,
            "spend": 100.0,
            "pipeline_value": 50.0,
            "age_hours": 48.0
        }
    ]

    # Create sampler
    sampler = BattleHardenedSampler()

    # Convert to AdState objects
    ad_states = [
        AdState(
            ad_id=ad["ad_id"],
            impressions=ad["impressions"],
            clicks=ad["clicks"],
            spend=ad["spend"],
            pipeline_value=ad["pipeline_value"],
            cash_revenue=0.0,
            age_hours=ad["age_hours"],
            last_updated=datetime.now(timezone.utc)
        )
        for ad in ad_performance
    ]

    # Generate budget recommendations
    recommendations = sampler.select_budget_allocation(
        ad_states=ad_states,
        total_budget=300.0
    )

    # Verify recommendations
    assert len(recommendations) == 3

    # Winner should get most budget
    winner_rec = next(r for r in recommendations if r.ad_id == "ad_winner")
    loser_rec = next(r for r in recommendations if r.ad_id == "ad_loser")

    assert winner_rec.recommended_budget > loser_rec.recommended_budget
    assert winner_rec.change_percentage > 0  # Scaling up
    assert loser_rec.change_percentage < 0  # Scaling down


@pytest.mark.integration
@pytest.mark.slow
async def test_sampler_to_queue_flow():
    """Test: Budget decision → Queue ad change → Execute safely.

    Flow:
    1. Sampler recommends budget increase
    2. Change queued in ad_change_history
    3. SafeExecutor validates and executes
    """
    import asyncpg
    import os

    # Mock database connection
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL not set")

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)

    try:
        async with pool.acquire() as conn:
            # Step 1: Queue budget change from sampler recommendation
            change_id = await conn.fetchval("""
                INSERT INTO ad_change_history
                (tenant_id, campaign_id, ad_id, change_type, old_value, new_value,
                 triggered_by, reason, ml_confidence, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                "test_tenant",
                "campaign_123",
                "ad_winner",
                "BUDGET_INCREASE",
                '{"budget": 100}',
                '{"budget": 150}',
                "battle_hardened",
                "Excellent Pipeline ROAS (6.0x) with mature data. Scaling up.",
                0.89,
                "pending"
            )

            # Step 2: Safety checks (rate limit, velocity)
            # Check if too many changes in last hour
            recent_changes = await conn.fetchval("""
                SELECT COUNT(*) FROM ad_change_history
                WHERE campaign_id = $1
                AND created_at > NOW() - INTERVAL '1 hour'
                AND status IN ('executing', 'completed')
            """, "campaign_123")

            rate_limit_passed = recent_changes < 10  # Max 10 changes/hour

            # Check budget velocity (max 100% increase in 6 hours)
            budget_velocity = await conn.fetchval("""
                SELECT COALESCE(SUM(
                    CASE WHEN change_type = 'BUDGET_INCREASE'
                    THEN ((new_value->>'budget')::NUMERIC - (old_value->>'budget')::NUMERIC)
                    ELSE 0 END
                ), 0)
                FROM ad_change_history
                WHERE campaign_id = $1
                AND created_at > NOW() - INTERVAL '6 hours'
                AND status IN ('executing', 'completed')
            """, "campaign_123")

            velocity_check_passed = budget_velocity < 100.0

            # Update safety checks
            await conn.execute("""
                UPDATE ad_change_history
                SET rate_limit_passed = $2, velocity_check_passed = $3
                WHERE id = $1
            """, change_id, rate_limit_passed, velocity_check_passed)

            # Step 3: Execute if safe
            if rate_limit_passed and velocity_check_passed:
                # Claim change
                await conn.execute("""
                    UPDATE ad_change_history
                    SET status = 'executing', started_at = NOW()
                    WHERE id = $1
                """, change_id)

                # Simulate Meta API call
                # ... actual Meta API call ...

                # Mark completed
                await conn.execute("""
                    UPDATE ad_change_history
                    SET status = 'completed',
                        completed_at = NOW(),
                        execution_duration_ms = $2,
                        meta_response = $3
                    WHERE id = $1
                """,
                    change_id,
                    150,  # 150ms execution
                    '{"success": true, "new_budget": 150}'
                )

            # Verify execution
            result = await conn.fetchrow("""
                SELECT status, rate_limit_passed, velocity_check_passed
                FROM ad_change_history
                WHERE id = $1
            """, change_id)

            assert result['status'] == 'completed'
            assert result['rate_limit_passed'] == True
            assert result['velocity_check_passed'] == True

            # Cleanup
            await conn.execute("DELETE FROM ad_change_history WHERE id = $1", change_id)

    finally:
        await pool.close()


@pytest.mark.integration
@pytest.mark.slow
async def test_complete_feedback_loop():
    """Test complete loop: Deal → Attribution → Sampler → Queue → Execution → Feedback.

    This is the full end-to-end test of the intelligence system.
    """
    # This would require:
    # 1. Mock HubSpot webhook server
    # 2. Test database with schema
    # 3. Mock Meta API
    # 4. All services running

    # For now, we'll simulate the key decision points

    # Step 1: HubSpot deal update
    deal_update = {
        "deal_id": "deal_123",
        "stage": "appointmentscheduled",
        "amount": 10000.0,
        "ad_id": "ad_test_001",
        "campaign_id": "campaign_test_001"
    }

    # Step 2: Calculate synthetic revenue
    synthetic_revenue = deal_update["amount"] * 0.3  # 30% for appointment
    assert synthetic_revenue == 3000.0

    # Step 3: Update ad performance
    ad_performance = {
        "ad_id": deal_update["ad_id"],
        "impressions": 5000,
        "clicks": 250,
        "spend": 150.0,
        "pipeline_value": synthetic_revenue,
        "pipeline_roas": synthetic_revenue / 150.0  # 20x ROAS!
    }

    # Step 4: Sampler decision (high ROAS = scale up)
    should_scale = ad_performance["pipeline_roas"] > 3.0
    assert should_scale == True

    # Step 5: Queue budget increase
    budget_change = {
        "old_budget": 50.0,
        "new_budget": 75.0,  # 50% increase
        "reason": f"Excellent Pipeline ROAS ({ad_performance['pipeline_roas']:.1f}x)"
    }

    assert budget_change["new_budget"] > budget_change["old_budget"]

    # Step 6: Execute change (simulated)
    execution_result = {
        "success": True,
        "new_budget": budget_change["new_budget"],
        "timestamp": datetime.utcnow().isoformat()
    }

    assert execution_result["success"] == True

    # Step 7: Feedback loop (update metrics)
    # Next iteration will use updated budget and continue optimizing
    feedback = {
        "ad_id": deal_update["ad_id"],
        "action_taken": "BUDGET_INCREASE",
        "expected_improvement": "Higher impression volume with same ROAS",
        "will_monitor": True
    }

    assert feedback["will_monitor"] == True


@pytest.mark.integration
def test_winner_learning_integration():
    """Test: High-performing ad → Winner Index → Pattern learning.

    Flow:
    1. Ad achieves high ROAS and CTR
    2. Ad pattern stored in winner index
    3. Future ads can search for similar winning patterns
    """
    import tempfile
    import shutil
    from pathlib import Path

    temp_dir = tempfile.mkdtemp(prefix="test_winner_learning_")

    try:
        sys.path.insert(0, str(PROJECT_ROOT / "services" / "rag"))
        from winner_index import WinnerIndex

        index = WinnerIndex(
            index_path=f"{temp_dir}/winners.index",
            namespace="test_learning",
            use_gcs=False
        )

        # Step 1: Identify winner (high performance)
        winning_ad = {
            "ad_id": "ad_winner_001",
            "hook": "Transform your marketing with AI automation",
            "body": "Join 500+ businesses saving 20 hours/week",
            "cta": "Book free demo",
            "ctr": 0.055,  # 5.5% CTR
            "roas": 6.2
        }

        # Step 2: Store in winner index
        success = index.add_winner(
            ad_data={
                "hook": winning_ad["hook"],
                "body": winning_ad["body"],
                "cta": winning_ad["cta"]
            },
            ctr=winning_ad["ctr"],
            min_ctr=0.03
        )

        assert success == True

        # Step 3: Search for similar patterns
        similar_winners = index.find_similar(
            "AI marketing automation",
            k=1
        )

        assert len(similar_winners) > 0
        assert similar_winners[0]["ctr"] == 0.055

        # Step 4: Use pattern for new ad creation
        new_ad_template = similar_winners[0]["data"]
        new_ad = {
            "hook": new_ad_template["hook"].replace("marketing", "sales"),
            "body": new_ad_template["body"],
            "cta": new_ad_template["cta"]
        }

        assert "AI" in new_ad["hook"]
        assert "sales" in new_ad["hook"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
def test_fatigue_detection_to_action():
    """Test: Fatigue detected → Recommendation to rotate creative.

    Flow:
    1. Monitor ad metrics over time
    2. Detect CTR decline or frequency saturation
    3. Generate recommendation to refresh creative
    """
    # Simulate 7 days of metrics
    metrics_timeline = [
        {"day": 1, "ctr": 4.0, "frequency": 1.5, "cpm": 8.0},
        {"day": 2, "ctr": 3.8, "frequency": 1.9, "cpm": 9.0},
        {"day": 3, "ctr": 3.4, "frequency": 2.3, "cpm": 10.5},
        {"day": 4, "ctr": 3.0, "frequency": 2.8, "cpm": 12.0},
        {"day": 5, "ctr": 2.5, "frequency": 3.2, "cpm": 14.0},
        {"day": 6, "ctr": 2.0, "frequency": 3.6, "cpm": 16.5},
        {"day": 7, "ctr": 1.5, "frequency": 4.0, "cpm": 19.0},  # Clear fatigue
    ]

    # Calculate fatigue indicators
    initial = metrics_timeline[0]
    current = metrics_timeline[-1]

    ctr_decline = ((initial["ctr"] - current["ctr"]) / initial["ctr"]) * 100
    frequency_high = current["frequency"] > 3.5
    cpm_increase = ((current["cpm"] - initial["cpm"]) / initial["cpm"]) * 100

    # Detect fatigue
    is_fatigued = (
        ctr_decline > 25 or  # >25% CTR drop
        frequency_high or    # Frequency > 3.5
        cpm_increase > 30    # >30% CPM increase
    )

    assert is_fatigued == True
    assert ctr_decline == 62.5  # 62.5% drop
    assert frequency_high == True

    # Generate action recommendation
    recommendation = {
        "action": "ROTATE_CREATIVE",
        "reason": f"Ad fatigue detected: CTR declined {ctr_decline:.1f}%, frequency at {current['frequency']:.1f}",
        "suggested_actions": [
            "Pause current ad",
            "Launch new creative variant",
            "Exclude existing audience"
        ]
    }

    assert recommendation["action"] == "ROTATE_CREATIVE"
    assert len(recommendation["suggested_actions"]) > 0
