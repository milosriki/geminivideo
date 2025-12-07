import pytest
import asyncio
import asyncpg
import json
from datetime import datetime

# DB Connection string (mock or env)
DB_DSN = "postgresql://postgres:postgres@localhost:5432/geminivideo"

@pytest.mark.asyncio
async def test_pending_ad_changes_flow():
    """
    Test the SafeExecutor job queue table:
    INSERT -> CLAIM (SKIP LOCKED) -> EXECUTE -> UPDATE STATUS
    """
    try:
        conn = await asyncpg.connect(DB_DSN)
    except Exception:
        pytest.skip("Database not available")
        return

    try:
        # 1. Insert a pending change
        row_id = await conn.fetchval("""
            INSERT INTO pending_ad_changes (
                tenant_id, ad_entity_id, entity_type, change_type, 
                current_value, requested_value, status
            ) VALUES (
                $1, $2, 'ad', 'budget_update', 
                '{"budget": 100}'::jsonb, '{"budget": 200}'::jsonb, 'pending'
            ) RETURNING id
        """, "00000000-0000-0000-0000-000000000000", "ad_123")
        
        assert row_id is not None
        
        # 2. Claim the change (Worker 1)
        # This simulates the 'claim_pending_ad_change' function logic
        claimed = await conn.fetchrow("""
            UPDATE pending_ad_changes
            SET status = 'claimed', claimed_by = 'worker_1', claimed_at = NOW()
            WHERE id = (
                SELECT id FROM pending_ad_changes
                WHERE status = 'pending'
                ORDER BY earliest_execute_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, claimed_by
        """)
        
        assert claimed is not None
        assert claimed['id'] == row_id
        assert claimed['claimed_by'] == 'worker_1'
        
        # 3. Verify Worker 2 cannot claim it
        claimed_2 = await conn.fetchrow("""
            UPDATE pending_ad_changes
            SET status = 'claimed', claimed_by = 'worker_2', claimed_at = NOW()
            WHERE id = (
                SELECT id FROM pending_ad_changes
                WHERE status = 'pending'
                ORDER BY earliest_execute_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id
        """)
        
        assert claimed_2 is None # Should be nothing left to claim
        
        # 4. Mark executed
        await conn.execute("""
            UPDATE pending_ad_changes
            SET status = 'executed', executed_at = NOW()
            WHERE id = $1
        """, row_id)
        
        # 5. Verify final state
        final_status = await conn.fetchval("SELECT status FROM pending_ad_changes WHERE id = $1", row_id)
        assert final_status == 'executed'

    finally:
        await conn.close()
