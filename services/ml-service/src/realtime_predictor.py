"""
Real-time Prediction Streaming
Agent 75 - Live CTR/ROAS predictions via WebSocket and SSE

Features:
- WebSocket server for live predictions
- Server-Sent Events (SSE) support
- Redis Pub/Sub for scaling across instances
- Prediction batching for efficiency
- Automatic triggers on data changes
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import redis.asyncio as redis
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionTriggerType(Enum):
    """Types of events that trigger prediction updates"""
    NEW_IMPRESSION = "new_impression"
    NEW_CONVERSION = "new_conversion"
    COMPETITOR_CHANGE = "competitor_change"
    BUDGET_CHANGE = "budget_change"
    CREATIVE_UPDATE = "creative_update"
    SCHEDULE_REFRESH = "schedule_refresh"


@dataclass
class PredictionUpdate:
    """Real-time prediction update"""
    campaign_id: str
    predicted_ctr: float
    predicted_roas: float
    confidence: float
    trigger_type: str
    timestamp: str
    metrics: Dict[str, Any]
    confidence_interval: Dict[str, float]
    change_from_previous: Optional[Dict[str, float]] = None
    recommendations: Optional[List[str]] = None


@dataclass
class StreamClient:
    """Client connection info"""
    client_id: str
    user_id: Optional[str]
    campaign_ids: Set[str]
    connection_type: str  # 'websocket' or 'sse'
    connected_at: datetime
    last_update: datetime
    update_count: int = 0


class PredictionBatcher:
    """Batches predictions for efficiency"""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.5):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_predictions: List[Dict[str, Any]] = []
        self.last_batch_time = time.time()
        self.lock = asyncio.Lock()

    async def add_prediction_request(self, request: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Add prediction request to batch.
        Returns batch if ready to process.
        """
        async with self.lock:
            self.pending_predictions.append(request)

            # Check if we should process the batch
            should_process = (
                len(self.pending_predictions) >= self.batch_size or
                (time.time() - self.last_batch_time) >= self.batch_timeout
            )

            if should_process and self.pending_predictions:
                batch = self.pending_predictions.copy()
                self.pending_predictions = []
                self.last_batch_time = time.time()
                return batch

            return None

    async def flush(self) -> List[Dict[str, Any]]:
        """Force flush all pending predictions"""
        async with self.lock:
            batch = self.pending_predictions.copy()
            self.pending_predictions = []
            self.last_batch_time = time.time()
            return batch


class RealtimePredictor:
    """
    Real-time prediction streaming service
    Supports both WebSocket and SSE connections
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        predictor_fn: Optional[Callable] = None
    ):
        """
        Initialize real-time predictor.

        Args:
            redis_url: Redis connection URL for pub/sub
            predictor_fn: Function to call for predictions
        """
        # Redis for pub/sub
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

        # Client management
        self.clients: Dict[str, StreamClient] = {}
        self.client_callbacks: Dict[str, Callable] = {}

        # Prediction function
        self.predictor_fn = predictor_fn or self._default_predictor

        # Batching
        self.batcher = PredictionBatcher(batch_size=10, batch_timeout=0.5)

        # Rate limiting
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # max updates per window

        # Metrics
        self.metrics = {
            "total_clients": 0,
            "total_predictions": 0,
            "total_updates_sent": 0,
            "active_campaigns": set()
        }

        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False

        logger.info("✅ RealtimePredictor initialized")

    async def start(self):
        """Start the real-time predictor service"""
        if self.is_running:
            logger.warning("RealtimePredictor already running")
            return

        self.is_running = True

        # Connect to Redis
        self.redis = redis.from_url(self.redis_url, decode_responses=False)
        self.pubsub = self.redis.pubsub()

        # Subscribe to prediction trigger channels
        await self.pubsub.subscribe(
            "prediction:triggers",
            "prediction:impressions",
            "prediction:conversions",
            "prediction:budget_changes"
        )

        # Start background tasks
        listener_task = asyncio.create_task(self._listen_for_triggers())
        self.background_tasks.add(listener_task)

        batch_processor_task = asyncio.create_task(self._process_batches())
        self.background_tasks.add(batch_processor_task)

        cleanup_task = asyncio.create_task(self._cleanup_stale_clients())
        self.background_tasks.add(cleanup_task)

        logger.info("🚀 RealtimePredictor started with Redis Pub/Sub")

    async def stop(self):
        """Stop the real-time predictor service"""
        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()

        # Close Redis connections
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        logger.info("🛑 RealtimePredictor stopped")

    def register_client(
        self,
        client_id: str,
        callback: Callable,
        user_id: Optional[str] = None,
        campaign_ids: Optional[List[str]] = None,
        connection_type: str = "websocket"
    ):
        """Register a new streaming client"""
        client = StreamClient(
            client_id=client_id,
            user_id=user_id,
            campaign_ids=set(campaign_ids or []),
            connection_type=connection_type,
            connected_at=datetime.utcnow(),
            last_update=datetime.utcnow()
        )

        self.clients[client_id] = client
        self.client_callbacks[client_id] = callback
        self.metrics["total_clients"] += 1

        logger.info(
            f"📱 Client registered: {client_id} "
            f"({connection_type}, campaigns: {len(client.campaign_ids)})"
        )

    def unregister_client(self, client_id: str):
        """Unregister a streaming client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            logger.info(
                f"👋 Client unregistered: {client_id} "
                f"({client.update_count} updates sent)"
            )
            del self.clients[client_id]
            del self.client_callbacks[client_id]

    async def subscribe_to_campaign(self, client_id: str, campaign_id: str):
        """Subscribe client to campaign updates"""
        if client_id in self.clients:
            self.clients[client_id].campaign_ids.add(campaign_id)
            self.metrics["active_campaigns"].add(campaign_id)

            # Send initial prediction
            await self._send_initial_prediction(client_id, campaign_id)

    async def unsubscribe_from_campaign(self, client_id: str, campaign_id: str):
        """Unsubscribe client from campaign updates"""
        if client_id in self.clients:
            self.clients[client_id].campaign_ids.discard(campaign_id)

    async def trigger_prediction_update(
        self,
        campaign_id: str,
        trigger_type: PredictionTriggerType,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Trigger a prediction update for a campaign.
        Publishes to Redis for all instances to process.
        """
        message = {
            "campaign_id": campaign_id,
            "trigger_type": trigger_type.value,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.redis:
            await self.redis.publish(
                "prediction:triggers",
                json.dumps(message)
            )

    async def _listen_for_triggers(self):
        """Listen for prediction triggers on Redis pub/sub"""
        logger.info("👂 Listening for prediction triggers...")

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        campaign_id = data["campaign_id"]
                        trigger_type = data["trigger_type"]
                        metadata = data.get("metadata", {})

                        # Add to batch
                        request = {
                            "campaign_id": campaign_id,
                            "trigger_type": trigger_type,
                            "metadata": metadata
                        }

                        batch = await self.batcher.add_prediction_request(request)

                        # Process batch if ready
                        if batch:
                            await self._process_prediction_batch(batch)

                    except Exception as e:
                        logger.error(f"Error processing trigger message: {e}")

        except asyncio.CancelledError:
            logger.info("Trigger listener cancelled")
        except Exception as e:
            logger.error(f"Error in trigger listener: {e}")

    async def _process_batches(self):
        """Periodically flush pending prediction batches"""
        try:
            while self.is_running:
                await asyncio.sleep(0.5)  # Check every 500ms

                batch = await self.batcher.flush()
                if batch:
                    await self._process_prediction_batch(batch)

        except asyncio.CancelledError:
            logger.info("Batch processor cancelled")

    async def _process_prediction_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of prediction requests"""
        try:
            # Get unique campaign IDs
            campaign_ids = list(set(req["campaign_id"] for req in batch))

            logger.info(f"🔮 Processing prediction batch: {len(campaign_ids)} campaigns")

            # Run predictions (could be parallelized)
            for campaign_id in campaign_ids:
                try:
                    # Get the trigger info
                    trigger_info = next(
                        req for req in batch if req["campaign_id"] == campaign_id
                    )

                    # Generate prediction
                    prediction = await self.predictor_fn(
                        campaign_id,
                        trigger_info["trigger_type"],
                        trigger_info.get("metadata", {})
                    )

                    # Send to subscribed clients
                    await self._broadcast_prediction(campaign_id, prediction)

                    self.metrics["total_predictions"] += 1

                except Exception as e:
                    logger.error(f"Error predicting for campaign {campaign_id}: {e}")

        except Exception as e:
            logger.error(f"Error processing prediction batch: {e}")

    async def _broadcast_prediction(
        self,
        campaign_id: str,
        prediction: PredictionUpdate
    ):
        """Broadcast prediction to all subscribed clients"""
        sent_count = 0

        for client_id, client in list(self.clients.items()):
            if campaign_id in client.campaign_ids:
                # Check rate limit
                if not self._check_rate_limit(client_id):
                    logger.warning(f"Rate limit exceeded for client {client_id}")
                    continue

                try:
                    # Send prediction via callback
                    callback = self.client_callbacks.get(client_id)
                    if callback:
                        await callback(prediction)

                        # Update client stats
                        client.last_update = datetime.utcnow()
                        client.update_count += 1
                        sent_count += 1

                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    # Remove failed client
                    self.unregister_client(client_id)

        if sent_count > 0:
            self.metrics["total_updates_sent"] += sent_count
            logger.debug(f"📤 Sent prediction for {campaign_id} to {sent_count} clients")

    async def _send_initial_prediction(self, client_id: str, campaign_id: str):
        """Send initial prediction when client subscribes"""
        try:
            prediction = await self.predictor_fn(
                campaign_id,
                PredictionTriggerType.SCHEDULE_REFRESH.value,
                {"initial": True}
            )

            callback = self.client_callbacks.get(client_id)
            if callback:
                await callback(prediction)

        except Exception as e:
            logger.error(f"Error sending initial prediction: {e}")

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()

        # Clean old timestamps
        self.rate_limits[client_id] = [
            ts for ts in self.rate_limits[client_id]
            if now - ts < self.rate_limit_window
        ]

        # Check limit
        if len(self.rate_limits[client_id]) >= self.rate_limit_max:
            return False

        # Add current timestamp
        self.rate_limits[client_id].append(now)
        return True

    async def _cleanup_stale_clients(self):
        """Remove clients that haven't been active"""
        try:
            while self.is_running:
                await asyncio.sleep(300)  # Check every 5 minutes

                now = datetime.utcnow()
                stale_clients = []

                for client_id, client in self.clients.items():
                    # Consider stale if no updates in 30 minutes
                    if (now - client.last_update).total_seconds() > 1800:
                        stale_clients.append(client_id)

                for client_id in stale_clients:
                    logger.info(f"🧹 Removing stale client: {client_id}")
                    self.unregister_client(client_id)

        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")

    async def _default_predictor(
        self,
        campaign_id: str,
        trigger_type: str,
        metadata: Dict[str, Any]
    ) -> PredictionUpdate:
        """
        Default prediction function.
        Replace with actual ML model predictions.
        """
        # Simulate prediction delay
        await asyncio.sleep(0.01)

        # Mock prediction
        import random
        base_ctr = 0.025
        base_roas = 2.5

        predicted_ctr = base_ctr + random.uniform(-0.005, 0.005)
        predicted_roas = base_roas + random.uniform(-0.5, 0.5)
        confidence = random.uniform(0.7, 0.95)

        return PredictionUpdate(
            campaign_id=campaign_id,
            predicted_ctr=predicted_ctr,
            predicted_roas=predicted_roas,
            confidence=confidence,
            trigger_type=trigger_type,
            timestamp=datetime.utcnow().isoformat(),
            metrics={
                "impressions_last_hour": random.randint(1000, 5000),
                "clicks_last_hour": random.randint(20, 150),
                "conversions_last_hour": random.randint(2, 15)
            },
            confidence_interval={
                "ctr_lower": predicted_ctr * 0.8,
                "ctr_upper": predicted_ctr * 1.2,
                "roas_lower": predicted_roas * 0.85,
                "roas_upper": predicted_roas * 1.15
            },
            change_from_previous={
                "ctr_change": random.uniform(-0.002, 0.002),
                "roas_change": random.uniform(-0.3, 0.3)
            },
            recommendations=[
                "Consider increasing budget by 10%" if predicted_roas > 2.5 else "Monitor performance",
                "CTR is trending up" if random.random() > 0.5 else "CTR is stable"
            ]
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "is_running": self.is_running,
            "total_clients": len(self.clients),
            "total_predictions": self.metrics["total_predictions"],
            "total_updates_sent": self.metrics["total_updates_sent"],
            "active_campaigns": len(self.metrics["active_campaigns"]),
            "clients": [
                {
                    "client_id": client.client_id,
                    "user_id": client.user_id,
                    "connection_type": client.connection_type,
                    "campaigns": len(client.campaign_ids),
                    "updates_sent": client.update_count,
                    "connected_duration_seconds": (
                        datetime.utcnow() - client.connected_at
                    ).total_seconds()
                }
                for client in list(self.clients.values())
            ]
        }


# Singleton instance
_realtime_predictor: Optional[RealtimePredictor] = None


def get_realtime_predictor() -> RealtimePredictor:
    """Get singleton RealtimePredictor instance"""
    global _realtime_predictor
    if _realtime_predictor is None:
        _realtime_predictor = RealtimePredictor()
    return _realtime_predictor


async def start_realtime_predictor(predictor_fn: Optional[Callable] = None):
    """Start the real-time predictor service"""
    predictor = get_realtime_predictor()
    if predictor_fn:
        predictor.predictor_fn = predictor_fn
    await predictor.start()


async def stop_realtime_predictor():
    """Stop the real-time predictor service"""
    global _realtime_predictor
    if _realtime_predictor:
        await _realtime_predictor.stop()
        _realtime_predictor = None
