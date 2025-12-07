import logging
import json
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CAPIFeedbackLoop:
    def __init__(self, db_session):
        self.db = db_session

    async def process_capi_event(self, event_data: Dict[str, Any]):
        """
        Process a CAPI event (e.g. conversion) and update the Thompson Sampler.
        """
        try:
            logger.info(f"Processing CAPI event: {event_data.get('event_name')}")
            
            # Extract relevant data
            event_name = event_data.get('event_name')
            event_id = event_data.get('event_id')
            user_data = event_data.get('user_data', {})
            custom_data = event_data.get('custom_data', {})
            
            # Extract ad/campaign info (assuming passed in custom_data or url parameters)
            # In a real scenario, we might match via fbp/fbc to a click, but here we assume
            # the pixel/CAPI sends back the ad_id or variant_id if possible.
            # Fallback: we might need to look up the user session.
            
            variant_id = custom_data.get('variant_id') or custom_data.get('ad_id')
            
            if not variant_id:
                logger.warning("No variant_id found in CAPI event, skipping Thompson update")
                return
            
            # Calculate Reward
            # Purchase = value, Lead = fixed value, etc.
            reward = 0.0
            if event_name == 'Purchase':
                reward = float(custom_data.get('value', 0.0))
            elif event_name == 'Lead':
                reward = 10.0 # Fixed value for lead
            elif event_name == 'ViewContent':
                reward = 0.1
            
            # Calculate Cost (if available)
            # CAPI usually doesn't send cost, but we might have it from the ad spend sync.
            # For the feedback loop, we might use an estimated cost or 0 if unknown.
            cost = float(custom_data.get('ad_spend', 0.0))
            
            # Update Thompson Sampler
            from src.thompson_sampler import thompson_optimizer
            
            # Ensure variant is registered
            if variant_id not in thompson_optimizer.bandits:
                thompson_optimizer.register_variant(variant_id)
                
            # Update bandit
            thompson_optimizer.update(
                variant_id=variant_id,
                reward=reward,
                cost=cost,
                metrics={
                    'conversions': 1 if event_name in ['Purchase', 'Lead'] else 0,
                    'revenue': reward
                }
            )
            
            logger.info(f"Updated Thompson Sampler for {variant_id}: reward={reward}, cost={cost}")
            
            # Trigger Retraining if needed
            # (Logic to check if we have enough new data)
            # ...
            
        except Exception as e:
            logger.error(f"Error processing CAPI event: {e}")
            raise

    async def _get_actuals(self, campaign_id: str, creative_id: str) -> Optional[Dict]:
        """Get actual performance data for a campaign/creative"""
        try:
            # Query actuals from database (PerformanceMetric table)
            # We aggregate metrics for the given campaign/creative
            from sqlalchemy import select, func
            from db.models import PerformanceMetric, Video
            
            # Find video ID for this creative/campaign
            # Assuming creative_id maps to Video.id or we join via Campaign
            
            # Query metrics
            query = select(
                func.sum(PerformanceMetric.impressions).label('impressions'),
                func.sum(PerformanceMetric.clicks).label('clicks'),
                func.sum(PerformanceMetric.conversions).label('conversions'),
                func.sum(PerformanceMetric.spend).label('spend'),
                func.sum(PerformanceMetric.revenue).label('revenue')
            ).join(Video, PerformanceMetric.video_id == Video.id)\
             .where(Video.campaign_id == campaign_id)
            
            if creative_id:
                # If creative_id is provided, filter by it (assuming it's video_id)
                query = query.where(Video.id == creative_id)
                
            result = await self.db.execute(query)
            metrics = result.first()
            
            if not metrics or not metrics.impressions:
                return None
                
            # Calculate rates
            impressions = metrics.impressions or 0
            clicks = metrics.clicks or 0
            conversions = metrics.conversions or 0
            spend = float(metrics.spend or 0)
            revenue = float(metrics.revenue or 0)
            
            ctr = clicks / impressions if impressions > 0 else 0.0
            roas = revenue / spend if spend > 0 else 0.0
            
            return {
                'ctr': ctr,
                'roas': roas,
                'conversions': conversions,
                'revenue': revenue,
                'spend': spend,
                'impressions': impressions,
                'clicks': clicks
            }
            
        except Exception as e:
            logger.error(f"Error getting actuals for {campaign_id}: {e}")
            return None

    async def _execute_retrain(self, training_data: Dict) -> Dict:
        """Execute actual model retraining"""
        try:
            from src.main import ctr_predictor, feature_extractor
            
            # We need X (features) and y (targets)
            # Currently training_data['features'] is empty because match_predictions_to_actuals 
            # doesn't fetch features. We need to fetch features for each pair.
            # For now, we'll trigger the standard data loader which fetches everything fresh from DB
            
            from src.data_loader import get_data_loader
            data_loader = get_data_loader()
            
            if not data_loader:
                return {'status': 'failed', 'reason': 'no data loader'}
                
            # Fetch fresh training data from DB (which now includes the new actuals we just verified)
            X, y = data_loader.fetch_training_data(min_impressions=10)
            
            if X is None or len(X) < 50:
                return {'status': 'skipped', 'reason': 'insufficient data'}
                
            # Train model
            metrics = ctr_predictor.train(X, y, feature_names=feature_extractor.feature_names)
            
            return {
                'model_version': f"v{datetime.now().strftime('%Y%m%d_%H%M')}",
                'samples': len(X),
                'metrics': metrics,
                'status': 'trained'
            }
            
        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def daily_thompson_optimization_job(self):
        """
        Daily job to:
        1. Identify losers (low CTR/ROAS with high confidence)
        2. Reallocate budget to winners
        3. Suggest new creative angles based on winners
        """
        try:
            logger.info("Starting daily Thompson Sampling optimization...")
            from src.thompson_sampler import thompson_optimizer
            
            # 1. Get all variants
            variants = thompson_optimizer.get_all_variants()
            
            losers = []
            winners = []
            
            for variant_id, stats in variants.items():
                # Check for statistical significance (simplified)
                # In real world, we'd use the beta distribution properties
                impressions = stats.get('impressions', 0)
                if impressions < 1000:
                    continue # Not enough data
                    
                ctr = stats.get('ctr', 0.0)
                roas = stats.get('roas', 0.0)
                
                # Thresholds (should be dynamic)
                if ctr < 0.005 and roas < 0.5:
                    losers.append(variant_id)
                elif ctr > 0.015 and roas > 2.0:
                    winners.append(variant_id)
            
            logger.info(f"Identified {len(losers)} losers and {len(winners)} winners")
            
            # 2. Action: Pause losers / Decrease budget
            # We would call the Ad Platform API here
            # For now, we just log the recommendation
            for loser in losers:
                logger.info(f"RECOMMENDATION: Pause variant {loser} (Low Performance)")
                
            # 3. Action: Scale winners
            for winner in winners:
                logger.info(f"RECOMMENDATION: Scale variant {winner} (High Performance)")
                
            return {
                'losers': losers,
                'winners': winners,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error in daily optimization job: {e}")
            return {'status': 'failed', 'error': str(e)}
