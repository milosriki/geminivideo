"""Test ad_change_history queue functionality.

This tests the SafeExecutor's ad change tracking and queue system.
"""
import pytest
from datetime import datetime, timedelta
import asyncpg
import os


@pytest.fixture
async def db_pool():
    """Create database connection pool for testing."""
    database_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/geminivideo_test")
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest.mark.integration
@pytest.mark.requires_db
async def test_insert_pending_change(db_pool):
    """Test inserting a pending ad change."""
    async with db_pool.acquire() as conn:
        # Insert a new ad change
        result = await conn.fetchrow("""
            INSERT INTO ad_change_history
            (tenant_id, campaign_id, ad_id, change_type, old_value, new_value, triggered_by, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, status, created_at
        """,
            "test_tenant",
            "campaign_123",
            "ad_456",
            "BUDGET_INCREASE",
            '{"budget": 100}',
            '{"budget": 150}',
            "battle_hardened",
            "Strong performance - scaling up"
        )

        assert result['status'] == 'pending'
        assert result['id'] is not None
        assert result['created_at'] is not None

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE id = $1", result['id'])


@pytest.mark.integration
@pytest.mark.requires_db
async def test_claim_pending_change_with_skip_locked(db_pool):
    """Test claiming a pending change with FOR UPDATE SKIP LOCKED.

    This tests race condition prevention - multiple workers trying to claim
    the same pending change should not conflict.
    """
    async with db_pool.acquire() as conn:
        # Insert test change
        change_id = await conn.fetchval("""
            INSERT INTO ad_change_history
            (tenant_id, campaign_id, ad_id, change_type, old_value, new_value, triggered_by, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            "test_tenant",
            "campaign_789",
            "ad_101",
            "BUDGET_INCREASE",
            '{"budget": 50}',
            '{"budget": 75}',
            "thompson_sampler",
            "Good CTR - increasing budget"
        )

        # Claim the change using FOR UPDATE SKIP LOCKED
        claimed = await conn.fetchrow("""
            UPDATE ad_change_history
            SET status = 'executing', started_at = NOW()
            WHERE id = (
                SELECT id FROM ad_change_history
                WHERE status = 'pending'
                AND id = $1
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING id, status
        """, change_id)

        assert claimed is not None
        assert claimed['status'] == 'executing'

        # Verify we can't claim again (should be locked)
        claimed_again = await conn.fetchrow("""
            SELECT id FROM ad_change_history
            WHERE status = 'pending' AND id = $1
            FOR UPDATE SKIP LOCKED
        """, change_id)

        assert claimed_again is None  # Already claimed

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE id = $1", change_id)


@pytest.mark.integration
@pytest.mark.requires_db
async def test_execute_flow_complete(db_pool):
    """Test complete flow: INSERT → CLAIM → EXECUTE → COMPLETE."""
    async with db_pool.acquire() as conn:
        # Step 1: INSERT pending change
        change_id = await conn.fetchval("""
            INSERT INTO ad_change_history
            (tenant_id, campaign_id, ad_id, change_type, old_value, new_value,
             triggered_by, reason, ml_confidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
            "test_tenant",
            "campaign_555",
            "ad_777",
            "BUDGET_INCREASE",
            '{"budget": 200}',
            '{"budget": 300}',
            "battle_hardened",
            "Excellent Pipeline ROAS (4.5x) - scaling aggressively",
            0.92
        )

        # Verify pending status
        status = await conn.fetchval(
            "SELECT status FROM ad_change_history WHERE id = $1",
            change_id
        )
        assert status == 'pending'

        # Step 2: CLAIM the change
        await conn.execute("""
            UPDATE ad_change_history
            SET status = 'executing', started_at = NOW()
            WHERE id = $1
        """, change_id)

        status = await conn.fetchval(
            "SELECT status FROM ad_change_history WHERE id = $1",
            change_id
        )
        assert status == 'executing'

        # Step 3: EXECUTE (simulate Meta API call)
        execution_start = datetime.utcnow()
        # ... actual Meta API call would happen here ...
        execution_end = datetime.utcnow()
        execution_duration = int((execution_end - execution_start).total_seconds() * 1000)

        # Step 4: COMPLETE
        await conn.execute("""
            UPDATE ad_change_history
            SET status = 'completed',
                completed_at = NOW(),
                execution_duration_ms = $2,
                meta_response = $3
            WHERE id = $1
        """,
            change_id,
            execution_duration,
            '{"success": true, "new_budget": 300}'
        )

        # Verify completion
        result = await conn.fetchrow("""
            SELECT status, completed_at, execution_duration_ms
            FROM ad_change_history
            WHERE id = $1
        """, change_id)

        assert result['status'] == 'completed'
        assert result['completed_at'] is not None
        assert result['execution_duration_ms'] is not None

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE id = $1", change_id)


@pytest.mark.integration
@pytest.mark.requires_db
async def test_rate_limit_tracking(db_pool):
    """Test rate limiting - track changes per campaign per hour."""
    async with db_pool.acquire() as conn:
        campaign_id = "campaign_rate_limit_test"

        # Insert 3 changes in quick succession
        for i in range(3):
            await conn.execute("""
                INSERT INTO ad_change_history
                (tenant_id, campaign_id, ad_id, change_type, old_value, new_value,
                 triggered_by, reason, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                "test_tenant",
                campaign_id,
                f"ad_{i}",
                "BUDGET_INCREASE",
                f'{{"budget": {100 + i*10}}}',
                f'{{"budget": {150 + i*10}}}',
                "auto_scaler",
                f"Change {i}",
                "completed"
            )

        # Query recent changes using the view
        recent_changes = await conn.fetchval("""
            SELECT changes_last_hour
            FROM v_campaign_activity_summary
            WHERE campaign_id = $1
        """, campaign_id)

        assert recent_changes == 3

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE campaign_id = $1", campaign_id)


@pytest.mark.integration
@pytest.mark.requires_db
async def test_velocity_check_tracking(db_pool):
    """Test budget velocity - track budget changes in last 6 hours."""
    async with db_pool.acquire() as conn:
        campaign_id = "campaign_velocity_test"

        # Insert budget changes
        changes = [
            (100, 125, "BUDGET_INCREASE"),
            (125, 150, "BUDGET_INCREASE"),
            (150, 125, "BUDGET_DECREASE"),
        ]

        for old_budget, new_budget, change_type in changes:
            await conn.execute("""
                INSERT INTO ad_change_history
                (tenant_id, campaign_id, change_type, old_value, new_value,
                 triggered_by, reason, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                "test_tenant",
                campaign_id,
                change_type,
                f'{{"budget": {old_budget}}}',
                f'{{"budget": {new_budget}}}',
                "auto_scaler",
                "Velocity test",
                "completed"
            )

        # Query budget changes in last 6 hours
        budget_changes = await conn.fetchval("""
            SELECT budget_changes_last_6h
            FROM v_campaign_activity_summary
            WHERE campaign_id = $1
        """, campaign_id)

        assert budget_changes == 3

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE campaign_id = $1", campaign_id)


@pytest.mark.integration
@pytest.mark.requires_db
async def test_safety_check_failures(db_pool):
    """Test safety check failure tracking."""
    async with db_pool.acquire() as conn:
        # Insert a blocked change
        blocked_id = await conn.fetchval("""
            INSERT INTO ad_change_history
            (tenant_id, campaign_id, ad_id, change_type, old_value, new_value,
             triggered_by, reason, status, rate_limit_passed, velocity_check_passed)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """,
            "test_tenant",
            "campaign_blocked",
            "ad_999",
            "BUDGET_INCREASE",
            '{"budget": 500}',
            '{"budget": 1000}',
            "manual",
            "Manual override attempt",
            "blocked",
            False,  # rate_limit_passed
            False   # velocity_check_passed
        )

        # Query safety check failures
        failures = await conn.fetch("""
            SELECT * FROM v_safety_check_failures
            WHERE id = $1
        """, blocked_id)

        assert len(failures) == 1
        assert failures[0]['failure_reason'] in ['RATE_LIMIT', 'VELOCITY_LIMIT', 'BLOCKED']

        # Cleanup
        await conn.execute("DELETE FROM ad_change_history WHERE id = $1", blocked_id)
