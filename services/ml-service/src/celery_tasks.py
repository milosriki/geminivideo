"""
Agent 3 & 4: Celery Tasks
"""
import logging
from typing import Dict, Any
from .celery_app import celery_app
from .battle_hardened_sampler import get_battle_hardened_sampler
from .synthetic_revenue import get_synthetic_revenue_calculator
from .hubspot_attribution import get_hubspot_attribution_service
from .winner_index import get_winner_index
from .creative_dna import get_creative_dna

logger = logging.getLogger(__name__)


@celery_app.task(name='process_hubspot_webhook')
def process_hubspot_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 3: Process HubSpot webhook asynchronously
    
    Flow:
    1. Calculate synthetic revenue
    2. Attribute to ad click
    3. Send feedback to BattleHardenedSampler
    """
    import asyncio
    import httpx
    import os
    
    async def _process():
        try:
            # Extract deal stage change
            deal_id = webhook_payload.get('dealId')
            stage_to = webhook_payload.get('stageTo')
            stage_from = webhook_payload.get('stageFrom')
            deal_value = webhook_payload.get('dealValue')
            tenant_id = webhook_payload.get('tenantId')
            
            # Calculate synthetic revenue (using actual interface)
            calc = get_synthetic_revenue_calculator()
            result = calc.calculate_stage_change(
                tenant_id=tenant_id,
                stage_from=stage_from,
                stage_to=stage_to,
                deal_value=deal_value
            )
            
            # Attribute to ad (using actual interface)
            attribution_service = get_hubspot_attribution_service()
            
            # Create conversion data
            from .hubspot_attribution import ConversionData
            from datetime import datetime, timezone
            
            conversion = ConversionData(
                conversion_id=deal_id,
                conversion_type=f'deal_{stage_to}',
                conversion_value=result.calculated_value,
                fingerprint_hash=webhook_payload.get('fingerprint_hash'),
                ip_address=webhook_payload.get('ip_address'),
                user_agent=webhook_payload.get('user_agent'),
                conversion_timestamp=datetime.now(timezone.utc),
                fbclid=webhook_payload.get('fbclid'),
                click_id=webhook_payload.get('click_id')
            )
            
            # Use correct method signature - needs tenant_id
            attribution_result = attribution_service.attribute_conversion(
                tenant_id=tenant_id,
                conversion_data=conversion
            )
            
            # Send feedback to BattleHardenedSampler via HTTP (since it's in another service)
            if attribution_result.success and attribution_result.ad_id:
                ml_service_url = os.getenv('ML_SERVICE_URL', 'http://ml-service:8003')
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{ml_service_url}/api/ml/battle-hardened/feedback",
                        json={
                            'ad_id': attribution_result.ad_id,
                            'actual_pipeline_value': result.calculated_value,
                            'actual_spend': webhook_payload.get('attributed_spend', 0)
                        },
                        timeout=10.0
                    )
                
                logger.info(
                    f"HubSpot webhook processed: ad={attribution_result.ad_id}, "
                    f"pipeline_value=${result.calculated_value}"
                )
            
            return {
                'status': 'success',
                'synthetic_revenue': result.calculated_value,
                'attribution': attribution_result.success,
                'ad_id': attribution_result.ad_id if attribution_result.success else None
            }
        
        except Exception as e:
            logger.error(f"Error processing HubSpot webhook: {e}", exc_info=True)
            raise
    
    return asyncio.run(_process())


@celery_app.task(name='monitor_fatigue')
def monitor_all_ads_fatigue() -> Dict[str, Any]:
    """
    Agent 4: Monitor all ads for fatigue (periodic task)
    """
    import asyncio
    import asyncpg
    import os
    from .fatigue_detector import detect_fatigue
    from .db.ad_state_repository import AdStateRepository
    
    async def _monitor():
        try:
            # Get all active ads
            pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
            repo = AdStateRepository(pool)
            ads = await repo.get_all_active()
            
            fatigued_ads = []
            
            for ad in ads:
                # Get metrics history (simplified - would fetch from DB)
                metrics_history = [
                    {
                        'ctr': ad.clicks / max(ad.impressions, 1),
                        'frequency': 1.0,  # Would get from Meta
                        'cpm': (ad.spend / max(ad.impressions, 1)) * 1000 if ad.impressions > 0 else 0,
                        'impressions': ad.impressions
                    }
                ]
                
                # Use existing detect_fatigue function
                result = detect_fatigue(ad.ad_id, metrics_history)
                
                if result.status in ['FATIGUING', 'SATURATED', 'AUDIENCE_EXHAUSTED']:
                    fatigued_ads.append({
                        'ad_id': ad.ad_id,
                        'status': result.status,
                        'reason': result.reason
                    })
                    
                    # Queue to SafeExecutor if critical
                    if result.status == 'AUDIENCE_EXHAUSTED':
                        async with pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO pending_ad_changes (ad_id, action, current_budget, target_budget, reason)
                                VALUES ($1, 'pause', $2, 0, $3)
                            """, ad.ad_id, ad.spend, result.reason)
            
            await pool.close()
            
            logger.info(f"Fatigue monitoring complete: {len(fatigued_ads)} fatigued ads found")
            
            return {
                'status': 'success',
                'fatigued_count': len(fatigued_ads),
                'fatigued_ads': fatigued_ads
            }
        
        except Exception as e:
            logger.error(f"Error monitoring fatigue: {e}", exc_info=True)
            raise
    
    # Run async function in sync context
    return asyncio.run(_monitor())


@celery_app.task(name='auto_index_winner')
def auto_index_winner(ad_id: str, creative_dna: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 7: Auto-index winner to RAG
    """
    import asyncio
    import numpy as np
    
    async def _index():
        try:
            # Try to import embedding service (may not exist yet)
            try:
                from .rag.embedding_service import generate_creative_dna_embedding
                embedding = await generate_creative_dna_embedding(creative_dna)
            except ImportError:
                # Fallback: generate simple embedding from hash
                import hashlib
                text = f"{creative_dna.get('hook_type', '')} {creative_dna.get('visual_style', '')}"
                hash_obj = hashlib.sha256(text.encode())
                seed = int(hash_obj.hexdigest()[:8], 16)
                np.random.seed(seed)
                embedding = np.random.rand(768).tolist()
                logger.warning(f"Using fallback embedding for {ad_id}")
            
            # Add to winner index (existing sync interface)
            index = get_winner_index()
            success = index.add_winner(
                ad_id=ad_id,
                embedding=np.array(embedding),
                metadata=creative_dna
            )
            
            if success:
                index.persist()  # Save to disk
                logger.info(f"Winner auto-indexed: {ad_id}")
                return {'status': 'success', 'ad_id': ad_id}
            else:
                return {'status': 'failed', 'ad_id': ad_id, 'reason': 'FAISS not available'}
        
        except Exception as e:
            logger.error(f"Error auto-indexing winner: {e}", exc_info=True)
            raise
    
    return asyncio.run(_index())

