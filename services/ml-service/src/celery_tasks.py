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
    try:
        # Extract deal stage change
        deal_id = webhook_payload.get('dealId')
        stage_to = webhook_payload.get('stageTo')
        deal_value = webhook_payload.get('dealValue')
        tenant_id = webhook_payload.get('tenantId')
        
        # Calculate synthetic revenue
        calc = get_synthetic_revenue_calculator()
        result = calc.calculate(
            stage_id=stage_to,
            deal_amount=deal_value
        )
        
        # Attribute to ad (simplified - would use actual attribution service)
        attribution = get_hubspot_attribution_service()
        attribution_result = attribution.attribute_conversion(
            tenant_id=tenant_id,
            conversion_id=deal_id,
            conversion_value=result.final_synthetic_value,
            conversion_type=f'deal_{stage_to}'
        )
        
        # Send feedback to BattleHardenedSampler
        if attribution_result.success and attribution_result.ad_id:
            sampler = get_battle_hardened_sampler()
            sampler.register_feedback(
                ad_id=attribution_result.ad_id,
                actual_pipeline_value=result.final_synthetic_value,
                actual_spend=attribution_result.attributed_spend or 0
            )
            
            logger.info(
                f"HubSpot webhook processed: ad={attribution_result.ad_id}, "
                f"pipeline_value=${result.final_synthetic_value}"
            )
        
        return {
            'status': 'success',
            'synthetic_revenue': result.final_synthetic_value,
            'attribution': attribution_result.success
        }
    
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {e}", exc_info=True)
        raise


@celery_app.task(name='monitor_fatigue')
def monitor_all_ads_fatigue() -> Dict[str, Any]:
    """
    Agent 4: Monitor all ads for fatigue (periodic task)
    """
    try:
        from .fatigue_detector import FatigueDetector
        from .db.ad_state_repository import AdStateRepository
        import asyncpg
        import os
        
        # Get all active ads
        pool = asyncpg.create_pool(os.getenv('DATABASE_URL'))
        repo = AdStateRepository(pool)
        ads = await repo.get_all_active()
        
        detector = FatigueDetector()
        fatigued_ads = []
        
        for ad in ads:
            result = detector.analyze(ad)
            if result.fatigue_level in ['high', 'critical']:
                fatigued_ads.append({
                    'ad_id': ad.ad_id,
                    'fatigue_level': result.fatigue_level,
                    'recommendation': result.recommendation
                })
                
                # Queue to SafeExecutor if critical
                if result.fatigue_level == 'critical':
                    # Queue pause action
                    await pool.execute("""
                        INSERT INTO pending_ad_changes (ad_id, action, current_budget, target_budget)
                        VALUES ($1, 'pause', $2, 0)
                    """, ad.ad_id, ad.spend)
        
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


@celery_app.task(name='auto_index_winner')
def auto_index_winner(ad_id: str, creative_dna: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 7: Auto-index winner to RAG
    """
    try:
        from .rag.embedding_service import generate_creative_dna_embedding
        
        # Generate embedding
        embedding = await generate_creative_dna_embedding(creative_dna)
        
        # Add to winner index
        index = get_winner_index()
        await index.add_winner(
            ad_id=ad_id,
            embedding=embedding,
            metadata=creative_dna
        )
        
        logger.info(f"Winner auto-indexed: {ad_id}")
        
        return {'status': 'success', 'ad_id': ad_id}
    
    except Exception as e:
        logger.error(f"Error auto-indexing winner: {e}", exc_info=True)
        raise

