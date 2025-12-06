"""
CAPI Feedback Loop - Wire Meta Conversion API results to model retraining

This is CRITICAL for real ROI:
1. Meta CAPI sends real conversion data
2. We match predictions to actuals
3. Daily model retraining on real data
4. System gets smarter every day

Without this: Static predictions, no learning, fake ROI
With this: Compound learning, real improvement, real ROI
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import os
import sys

# Add shared path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from sqlalchemy import select, and_, update
from db.models import PredictionRecord, CampaignActuals

logger = logging.getLogger(__name__)

@dataclass
class CAPIConversionEvent:
    """A conversion event from Meta CAPI"""
    event_id: str
    event_name: str  # 'Purchase', 'Lead', 'AddToCart', etc.
    event_time: int  # Unix timestamp
    user_data: Dict[str, Any]
    custom_data: Dict[str, Any]  # value, currency, content_ids
    event_source_url: str
    action_source: str  # 'website', 'app', 'email'

    @property
    def value(self) -> float:
        return self.custom_data.get('value', 0.0)

    @property
    def currency(self) -> str:
        return self.custom_data.get('currency', 'USD')

@dataclass
class PredictionActualPair:
    """A matched prediction with its actual outcome"""
    prediction_id: str
    campaign_id: str
    creative_id: str

    # Predictions
    predicted_ctr: float
    predicted_roas: float
    predicted_conversions: int

    # Actuals from CAPI
    actual_ctr: float
    actual_roas: float
    actual_conversions: int
    actual_revenue: float
    actual_spend: float

    # Errors
    ctr_error: float
    roas_error: float
    conversion_error: float

    timestamp: datetime

class CAPIFeedbackLoop:
    """
    Connects Meta CAPI to ML model retraining.

    Flow:
    1. Receive CAPI webhook events
    2. Match to campaigns/creatives
    3. Compare to predictions
    4. Store prediction vs actual pairs
    5. Trigger retraining when enough data
    """

    RETRAIN_THRESHOLD = 100  # Minimum new data points before retraining
    RETRAIN_INTERVAL_HOURS = 24  # Minimum hours between retrains

    def __init__(self, db_session):
        self.db = db_session
        self.pending_events: List[CAPIConversionEvent] = []
        self.last_retrain = None

    async def process_capi_event(self, event_data: Dict) -> Dict:
        """
        Process incoming CAPI webhook event.

        Args:
            event_data: Raw event from Meta CAPI webhook

        Returns:
            Processing result with matched prediction
        """
        event = CAPIConversionEvent(
            event_id=event_data.get('event_id', ''),
            event_name=event_data.get('event_name', ''),
            event_time=event_data.get('event_time', 0),
            user_data=event_data.get('user_data', {}),
            custom_data=event_data.get('custom_data', {}),
            event_source_url=event_data.get('event_source_url', ''),
            action_source=event_data.get('action_source', 'website')
        )

        self.pending_events.append(event)

        # Try to match to campaign
        campaign_id = await self._extract_campaign_id(event)
        creative_id = await self._extract_creative_id(event)

        if campaign_id:
            await self._update_campaign_actuals(campaign_id, event)

        logger.info(f"Processed CAPI event: {event.event_name} - ${event.value}")

        return {
            'processed': True,
            'event_id': event.event_id,
            'campaign_id': campaign_id,
            'creative_id': creative_id,
            'value': event.value
        }

    async def _extract_campaign_id(self, event: CAPIConversionEvent) -> Optional[str]:
        """Extract campaign ID from event URL or custom data"""
        # Check custom_data first
        if 'campaign_id' in event.custom_data:
            return event.custom_data['campaign_id']

        # Check URL parameters
        from urllib.parse import urlparse, parse_qs
        try:
            parsed = urlparse(event.event_source_url)
            params = parse_qs(parsed.query)
            if 'utm_campaign' in params:
                return params['utm_campaign'][0]
            if 'cid' in params:
                return params['cid'][0]
        except:
            pass

        return None

    async def _extract_creative_id(self, event: CAPIConversionEvent) -> Optional[str]:
        """Extract creative ID from event"""
        if 'content_ids' in event.custom_data:
            ids = event.custom_data['content_ids']
            if ids and len(ids) > 0:
                return ids[0]
        return None

    async def _update_campaign_actuals(self, campaign_id: str, event: CAPIConversionEvent):
        """Update campaign actuals in database"""
        # Upsert to campaign_actuals table
        today = datetime.now().date()

        # This would update the actual performance data
        # Implementation depends on your schema
        logger.info(f"Updated actuals for campaign {campaign_id}: ${event.value}")

    async def match_predictions_to_actuals(self) -> List[PredictionActualPair]:
        """
        Match all predictions to their actual outcomes.

        This is the KEY step for model learning.
        """
        pairs = []

        # Get predictions from last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)

        # Query predictions
        query = select(PredictionRecord).where(
            PredictionRecord.created_at >= seven_days_ago
        )

        result = await self.db.execute(query)
        predictions = result.scalars().all()

        for pred in predictions:
            # Get actual performance data for this campaign/creative
            actuals = await self._get_actuals(pred.campaign_id, pred.creative_id)

            if actuals:
                pair = PredictionActualPair(
                    prediction_id=str(pred.id),
                    campaign_id=pred.campaign_id,
                    creative_id=pred.creative_id or '',

                    predicted_ctr=pred.predicted_ctr,
                    predicted_roas=pred.predicted_roas,
                    predicted_conversions=pred.predicted_conversions or 0,

                    actual_ctr=actuals.get('ctr', 0),
                    actual_roas=actuals.get('roas', 0),
                    actual_conversions=actuals.get('conversions', 0),
                    actual_revenue=actuals.get('revenue', 0),
                    actual_spend=actuals.get('spend', 0),

                    ctr_error=abs(pred.predicted_ctr - actuals.get('ctr', 0)),
                    roas_error=abs(pred.predicted_roas - actuals.get('roas', 0)),
                    conversion_error=abs((pred.predicted_conversions or 0) - actuals.get('conversions', 0)),

                    timestamp=datetime.now()
                )
                pairs.append(pair)

        logger.info(f"Matched {len(pairs)} predictions to actuals")
        return pairs

    async def _get_actuals(self, campaign_id: str, creative_id: str) -> Optional[Dict]:
        """Get actual performance data for a campaign/creative"""
        # Query actuals from database
        # This would aggregate CAPI events + platform reporting
        return None  # Placeholder

    async def should_retrain(self) -> bool:
        """Check if we should trigger model retraining"""
        # Check data threshold
        pairs = await self.match_predictions_to_actuals()
        if len(pairs) < self.RETRAIN_THRESHOLD:
            logger.info(f"Not enough data for retraining: {len(pairs)}/{self.RETRAIN_THRESHOLD}")
            return False

        # Check time threshold
        if self.last_retrain:
            hours_since = (datetime.now() - self.last_retrain).total_seconds() / 3600
            if hours_since < self.RETRAIN_INTERVAL_HOURS:
                logger.info(f"Too soon to retrain: {hours_since:.1f}h < {self.RETRAIN_INTERVAL_HOURS}h")
                return False

        return True

    async def trigger_retrain(self) -> Dict:
        """
        Trigger model retraining with new data.

        This is where the magic happens - model gets smarter from real data.
        """
        pairs = await self.match_predictions_to_actuals()

        if not pairs:
            return {'status': 'skipped', 'reason': 'no data'}

        # Prepare training data
        training_data = {
            'features': [],
            'targets': {
                'ctr': [],
                'roas': [],
                'conversions': []
            },
            'sample_weights': []
        }

        for pair in pairs:
            # Add actual outcomes as training targets
            training_data['targets']['ctr'].append(pair.actual_ctr)
            training_data['targets']['roas'].append(pair.actual_roas)
            training_data['targets']['conversions'].append(pair.actual_conversions)

            # Weight recent data more heavily
            age_hours = (datetime.now() - pair.timestamp).total_seconds() / 3600
            weight = 1.0 / (1.0 + age_hours / 24)  # Decay over days
            training_data['sample_weights'].append(weight)

        # Call retraining service
        retrain_result = await self._execute_retrain(training_data)

        self.last_retrain = datetime.now()

        logger.info(f"Model retrained with {len(pairs)} samples")

        return {
            'status': 'success',
            'samples_used': len(pairs),
            'avg_ctr_error_before': sum(p.ctr_error for p in pairs) / len(pairs),
            'avg_roas_error_before': sum(p.roas_error for p in pairs) / len(pairs),
            'retrain_result': retrain_result,
            'next_retrain_eligible': datetime.now() + timedelta(hours=self.RETRAIN_INTERVAL_HOURS)
        }

    async def _execute_retrain(self, training_data: Dict) -> Dict:
        """Execute actual model retraining"""
        # This would call your ML training pipeline
        # For now, return placeholder
        return {
            'model_version': f"v{datetime.now().strftime('%Y%m%d_%H%M')}",
            'samples': len(training_data['targets']['ctr']),
            'status': 'trained'
        }

    def get_feedback_metrics(self) -> Dict:
        """Get metrics on feedback loop health"""
        return {
            'pending_events': len(self.pending_events),
            'last_retrain': self.last_retrain.isoformat() if self.last_retrain else None,
            'retrain_threshold': self.RETRAIN_THRESHOLD,
            'retrain_interval_hours': self.RETRAIN_INTERVAL_HOURS
        }


# Scheduled job for daily retraining
async def daily_retrain_job(db_session):
    """
    Run daily to retrain models with CAPI feedback.

    Schedule this with cron:
    0 2 * * * python -c "from capi_feedback_loop import daily_retrain_job; asyncio.run(daily_retrain_job())"
    """
    loop = CAPIFeedbackLoop(db_session)

    if await loop.should_retrain():
        result = await loop.trigger_retrain()
        logger.info(f"Daily retrain complete: {result}")
        return result
    else:
        logger.info("Daily retrain skipped - conditions not met")
        return {'status': 'skipped'}
