"""
Agent 2: Database Persistence Layer for AdState
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
import asyncpg
from ..battle_hardened_sampler import AdState

logger = logging.getLogger(__name__)


class AdStateRepository:
    """Repository for persisting AdState to PostgreSQL"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def save(self, ad_state: AdState) -> None:
        """Save or update AdState"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ad_states (
                    ad_id, impressions, clicks, spend,
                    pipeline_value, cash_revenue, age_hours, last_updated
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (ad_id) DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    spend = EXCLUDED.spend,
                    pipeline_value = EXCLUDED.pipeline_value,
                    cash_revenue = EXCLUDED.cash_revenue,
                    age_hours = EXCLUDED.age_hours,
                    last_updated = EXCLUDED.last_updated
            """, 
                ad_state.ad_id,
                ad_state.impressions,
                ad_state.clicks,
                ad_state.spend,
                ad_state.pipeline_value,
                ad_state.cash_revenue,
                ad_state.age_hours,
                ad_state.last_updated
            )
    
    async def get(self, ad_id: str) -> Optional[AdState]:
        """Get AdState by ad_id"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM ad_states WHERE ad_id = $1
            """, ad_id)
            
            if not row:
                return None
            
            return AdState(
                ad_id=row['ad_id'],
                impressions=row['impressions'],
                clicks=row['clicks'],
                spend=row['spend'],
                pipeline_value=row['pipeline_value'],
                cash_revenue=row['cash_revenue'],
                age_hours=row['age_hours'],
                last_updated=row['last_updated']
            )
    
    async def get_all_active(self, account_id: Optional[str] = None) -> List[AdState]:
        """Get all active ads, optionally filtered by account"""
        async with self.pool.acquire() as conn:
            if account_id:
                rows = await conn.fetch("""
                    SELECT * FROM ad_states 
                    WHERE account_id = $1 AND status = 'active'
                """, account_id)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM ad_states WHERE status = 'active'
                """)
            
            return [
                AdState(
                    ad_id=row['ad_id'],
                    impressions=row['impressions'],
                    clicks=row['clicks'],
                    spend=row['spend'],
                    pipeline_value=row['pipeline_value'],
                    cash_revenue=row['cash_revenue'],
                    age_hours=row['age_hours'],
                    last_updated=row['last_updated']
                )
                for row in rows
            ]
    
    async def update_from_meta(self, ad_id: str, insights: dict) -> None:
        """Update AdState from Meta Insights API response"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE ad_states SET
                    impressions = $2,
                    clicks = $3,
                    spend = $4,
                    last_updated = $5
                WHERE ad_id = $1
            """,
                ad_id,
                insights.get('impressions', 0),
                insights.get('clicks', 0),
                insights.get('spend', 0.0),
                datetime.now(timezone.utc)
            )
    
    async def update_from_hubspot(self, ad_id: str, pipeline_data: dict) -> None:
        """Update AdState from HubSpot pipeline data"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE ad_states SET
                    pipeline_value = $2,
                    cash_revenue = $3,
                    last_updated = $4
                WHERE ad_id = $1
            """,
                ad_id,
                pipeline_data.get('pipeline_value', 0.0),
                pipeline_data.get('cash_revenue', 0.0),
                datetime.now(timezone.utc)
            )

