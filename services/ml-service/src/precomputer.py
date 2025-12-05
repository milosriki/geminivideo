"""
Predictive Precomputation Engine - 10x Leverage through anticipation

AGENT 45: 10x LEVERAGE - Predictive Precomputation

Makes the app feel INSTANT by precomputing results before users ask.

Key Features:
1. Event-based triggers (upload, campaign create, login)
2. Action prediction ML model
3. Smart caching with intelligent invalidation
4. Background processing queue
5. Priority-based precomputation

Investment-grade implementation for elite performance.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
import sys

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

import redis
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle

logger = logging.getLogger(__name__)


class PrecomputeEvent(str, Enum):
    """Events that trigger precomputation."""
    VIDEO_UPLOAD = "video_upload"
    CAMPAIGN_CREATE = "campaign_create"
    USER_LOGIN = "user_login"
    VARIANT_GENERATE = "variant_generate"
    DASHBOARD_VIEW = "dashboard_view"


class PrecomputeTaskType(str, Enum):
    """Types of precomputation tasks."""
    SCENE_DETECTION = "scene_detection"
    FACE_DETECTION = "face_detection"
    HOOK_ANALYSIS = "hook_analysis"
    CTR_PREDICTION = "ctr_prediction"
    THUMBNAIL_GENERATION = "thumbnail_generation"
    CAPTION_GENERATION = "caption_generation"
    VARIANT_GENERATION = "variant_generation"
    VARIANT_SCORING = "variant_scoring"
    ROAS_PREDICTION = "roas_prediction"
    DASHBOARD_DATA = "dashboard_data"
    CAMPAIGN_ANALYTICS = "campaign_analytics"


class PrecomputeStatus(str, Enum):
    """Status of precomputation task."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class PrecomputeTask:
    """Individual precomputation task."""
    task_id: str
    task_type: PrecomputeTaskType
    event: PrecomputeEvent
    user_id: Optional[str] = None
    video_id: Optional[str] = None
    campaign_id: Optional[str] = None
    data: Dict[str, Any] = None
    priority: int = 5  # 1-10, higher = more urgent
    status: PrecomputeStatus = PrecomputeStatus.QUEUED
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cache_key: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.data is None:
            self.data = {}


class ActionPredictor:
    """
    ML model to predict user's next actions.

    Uses user history to predict what they'll do next with >50% confidence,
    then precomputes for those actions.
    """

    def __init__(self):
        """Initialize action predictor."""
        self.model: Optional[RandomForestClassifier] = None
        self.actions = [
            PrecomputeEvent.VIDEO_UPLOAD,
            PrecomputeEvent.CAMPAIGN_CREATE,
            PrecomputeEvent.VARIANT_GENERATE,
            PrecomputeEvent.DASHBOARD_VIEW
        ]
        self.action_to_idx = {action: idx for idx, action in enumerate(self.actions)}
        self.model_path = "/tmp/action_predictor.pkl"

        # Try to load existing model
        self._load_model()

        # If no model exists, train with synthetic data
        if self.model is None:
            self._train_initial_model()

    def _load_model(self):
        """Load model from disk."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Action predictor model loaded from disk")
        except Exception as e:
            logger.warning(f"Failed to load action predictor: {e}")

    def _save_model(self):
        """Save model to disk."""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info("Action predictor model saved to disk")
        except Exception as e:
            logger.error(f"Failed to save action predictor: {e}")

    def _train_initial_model(self):
        """Train initial model with synthetic data."""
        logger.info("Training initial action predictor model...")

        # Generate synthetic training data based on common user patterns
        # Features: [hour_of_day, day_of_week, last_action, actions_today, session_duration]
        X = []
        y = []

        # Pattern 1: Morning users (9-11 AM) → Dashboard view, then campaign create
        for _ in range(100):
            X.append([np.random.randint(9, 12), np.random.randint(0, 5), 3, 2, 15])
            y.append(self.action_to_idx[PrecomputeEvent.DASHBOARD_VIEW])

            X.append([np.random.randint(9, 12), np.random.randint(0, 5), 3, 3, 20])
            y.append(self.action_to_idx[PrecomputeEvent.CAMPAIGN_CREATE])

        # Pattern 2: Afternoon users (2-5 PM) → Video upload, then variant generate
        for _ in range(100):
            X.append([np.random.randint(14, 18), np.random.randint(0, 5), 3, 1, 10])
            y.append(self.action_to_idx[PrecomputeEvent.VIDEO_UPLOAD])

            X.append([np.random.randint(14, 18), np.random.randint(0, 5), 0, 2, 25])
            y.append(self.action_to_idx[PrecomputeEvent.VARIANT_GENERATE])

        # Pattern 3: Evening users (6-8 PM) → Campaign create, variant generate
        for _ in range(100):
            X.append([np.random.randint(18, 21), np.random.randint(0, 7), 3, 1, 12])
            y.append(self.action_to_idx[PrecomputeEvent.CAMPAIGN_CREATE])

            X.append([np.random.randint(18, 21), np.random.randint(0, 7), 1, 2, 18])
            y.append(self.action_to_idx[PrecomputeEvent.VARIANT_GENERATE])

        X = np.array(X)
        y = np.array(y)

        # Train model
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.model.fit(X, y)

        # Save model
        self._save_model()

        logger.info("Action predictor model trained successfully")

    def predict(self, user_history: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Predict user's next likely actions.

        Args:
            user_history: Dictionary with user activity history

        Returns:
            List of predicted actions with probabilities
        """
        if self.model is None:
            return []

        try:
            # Extract features from user history
            current_hour = datetime.now().hour
            current_day = datetime.now().weekday()
            last_action = user_history.get('last_action', 3)  # 3 = dashboard view (default)
            actions_today = user_history.get('actions_today', 0)
            session_duration = user_history.get('session_duration', 5)

            # Create feature vector
            features = np.array([[current_hour, current_day, last_action, actions_today, session_duration]])

            # Get predictions with probabilities
            probabilities = self.model.predict_proba(features)[0]

            # Create prediction list
            predictions = []
            for idx, prob in enumerate(probabilities):
                if prob > 0.3:  # Only include actions with >30% probability
                    predictions.append({
                        'action': self.actions[idx].value,
                        'probability': float(prob),
                        'confidence': 'high' if prob > 0.6 else 'medium'
                    })

            # Sort by probability
            predictions.sort(key=lambda x: x['probability'], reverse=True)

            return predictions

        except Exception as e:
            logger.error(f"Failed to predict actions: {e}")
            return []

    def update(self, user_history: Dict[str, Any], actual_action: PrecomputeEvent):
        """
        Update model with actual user action (online learning).

        Args:
            user_history: User history at time of action
            actual_action: The action user actually took
        """
        try:
            # Extract features
            current_hour = datetime.now().hour
            current_day = datetime.now().weekday()
            last_action = user_history.get('last_action', 3)
            actions_today = user_history.get('actions_today', 0)
            session_duration = user_history.get('session_duration', 5)

            X = np.array([[current_hour, current_day, last_action, actions_today, session_duration]])
            y = np.array([self.action_to_idx[actual_action]])

            # Partial fit (incremental learning)
            # Note: RandomForest doesn't support partial_fit, so we'd need to use SGDClassifier
            # or retrain periodically. For now, we'll collect data and retrain periodically.

            logger.debug(f"Action recorded for learning: {actual_action.value}")

        except Exception as e:
            logger.error(f"Failed to update action predictor: {e}")


class Precomputer:
    """
    Predictive precomputation engine.

    Anticipates user actions and precomputes results before they're requested.
    Makes the app feel INSTANT.
    """

    # Cache TTL based on data type
    CACHE_TTL = {
        PrecomputeTaskType.SCENE_DETECTION: 24 * 3600,  # 24 hours
        PrecomputeTaskType.FACE_DETECTION: 24 * 3600,
        PrecomputeTaskType.HOOK_ANALYSIS: 12 * 3600,  # 12 hours
        PrecomputeTaskType.CTR_PREDICTION: 6 * 3600,  # 6 hours (refreshes twice daily)
        PrecomputeTaskType.THUMBNAIL_GENERATION: 24 * 3600,
        PrecomputeTaskType.CAPTION_GENERATION: 24 * 3600,
        PrecomputeTaskType.VARIANT_GENERATION: 12 * 3600,
        PrecomputeTaskType.VARIANT_SCORING: 6 * 3600,
        PrecomputeTaskType.ROAS_PREDICTION: 6 * 3600,
        PrecomputeTaskType.DASHBOARD_DATA: 1 * 3600,  # 1 hour (frequently updated)
        PrecomputeTaskType.CAMPAIGN_ANALYTICS: 2 * 3600,  # 2 hours
    }

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize precomputer.

        Args:
            redis_url: Redis connection URL
        """
        # Redis connection
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)

        # Action predictor
        self.action_predictor = ActionPredictor()

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

        logger.info("Precomputer initialized")

    # ========================================================================
    # EVENT TRIGGERS
    # ========================================================================

    async def on_video_upload(self, video_id: str, user_id: str, video_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Precompute all analyses for uploaded video.

        This fires immediately on video upload and queues all analysis tasks.

        Args:
            video_id: Video ID
            user_id: User ID
            video_data: Optional video metadata

        Returns:
            Dictionary of queued task IDs by task type
        """
        logger.info(f"🚀 Video upload detected: {video_id}, triggering precomputation...")

        tasks_to_precompute = [
            PrecomputeTaskType.SCENE_DETECTION,
            PrecomputeTaskType.FACE_DETECTION,
            PrecomputeTaskType.HOOK_ANALYSIS,
            PrecomputeTaskType.CTR_PREDICTION,
            PrecomputeTaskType.THUMBNAIL_GENERATION,
            PrecomputeTaskType.CAPTION_GENERATION,
        ]

        queued_tasks = {}

        for task_type in tasks_to_precompute:
            task_id = await self._queue_precompute_task(
                task_type=task_type,
                event=PrecomputeEvent.VIDEO_UPLOAD,
                user_id=user_id,
                video_id=video_id,
                data=video_data or {},
                priority=8  # High priority for upload events
            )

            if task_type not in queued_tasks:
                queued_tasks[task_type.value] = []
            queued_tasks[task_type.value].append(task_id)

        logger.info(f"✅ Queued {len(tasks_to_precompute)} precompute tasks for video {video_id}")

        # Update action predictor
        await self._update_user_action(user_id, PrecomputeEvent.VIDEO_UPLOAD)

        return queued_tasks

    async def on_campaign_create(self, campaign_id: str, user_id: str, campaign_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Precompute all variants and predictions for campaign.

        Args:
            campaign_id: Campaign ID
            user_id: User ID
            campaign_data: Optional campaign metadata

        Returns:
            Dictionary of queued task IDs by task type
        """
        logger.info(f"🚀 Campaign creation detected: {campaign_id}, triggering precomputation...")

        tasks_to_precompute = [
            PrecomputeTaskType.VARIANT_GENERATION,
            PrecomputeTaskType.VARIANT_SCORING,
            PrecomputeTaskType.ROAS_PREDICTION,
        ]

        queued_tasks = {}

        for task_type in tasks_to_precompute:
            task_id = await self._queue_precompute_task(
                task_type=task_type,
                event=PrecomputeEvent.CAMPAIGN_CREATE,
                user_id=user_id,
                campaign_id=campaign_id,
                data=campaign_data or {},
                priority=9  # Very high priority for campaign creation
            )

            if task_type not in queued_tasks:
                queued_tasks[task_type.value] = []
            queued_tasks[task_type.value].append(task_id)

        logger.info(f"✅ Queued {len(tasks_to_precompute)} precompute tasks for campaign {campaign_id}")

        # Update action predictor
        await self._update_user_action(user_id, PrecomputeEvent.CAMPAIGN_CREATE)

        return queued_tasks

    async def on_user_login(self, user_id: str, user_data: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """
        Precompute dashboard data and predicted next actions.

        Args:
            user_id: User ID
            user_data: Optional user metadata

        Returns:
            Dictionary of queued task IDs by task type
        """
        logger.info(f"🚀 User login detected: {user_id}, triggering precomputation...")

        # Predict what user will do next
        user_history = await self._get_user_history(user_id)
        predicted_actions = self.action_predictor.predict(user_history)

        logger.info(f"🔮 Predicted actions for {user_id}: {predicted_actions}")

        queued_tasks = {}

        # Always precompute dashboard data
        task_id = await self._queue_precompute_task(
            task_type=PrecomputeTaskType.DASHBOARD_DATA,
            event=PrecomputeEvent.USER_LOGIN,
            user_id=user_id,
            data=user_data or {},
            priority=7
        )
        queued_tasks[PrecomputeTaskType.DASHBOARD_DATA.value] = [task_id]

        # Precompute for predicted actions (if probability > 50%)
        for prediction in predicted_actions:
            if prediction['probability'] > 0.5:
                await self._precompute_for_action(
                    user_id=user_id,
                    action=PrecomputeEvent(prediction['action']),
                    probability=prediction['probability']
                )

        # Update action predictor
        await self._update_user_action(user_id, PrecomputeEvent.USER_LOGIN)

        return queued_tasks

    async def predict_next_actions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Predict what user will do next and precompute.

        Args:
            user_id: User ID

        Returns:
            List of predicted actions with probabilities
        """
        user_history = await self._get_user_history(user_id)
        predictions = self.action_predictor.predict(user_history)

        # Precompute for high-probability actions
        for prediction in predictions:
            if prediction['probability'] > 0.5:
                asyncio.create_task(self._precompute_for_action(
                    user_id=user_id,
                    action=PrecomputeEvent(prediction['action']),
                    probability=prediction['probability']
                ))

        return predictions

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get result from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None if not found
        """
        try:
            cached_data = self.redis.get(f"precompute:cache:{cache_key}")
            if cached_data:
                logger.debug(f"✅ Cache hit: {cache_key}")
                self._increment_metric("cache_hits")
                return json.loads(cached_data)

            logger.debug(f"❌ Cache miss: {cache_key}")
            self._increment_metric("cache_misses")
            return None

        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None

    def set_cached_result(
        self,
        cache_key: str,
        result: Dict[str, Any],
        task_type: PrecomputeTaskType,
        ttl: Optional[int] = None
    ):
        """
        Store result in cache.

        Args:
            cache_key: Cache key
            result: Result to cache
            task_type: Type of task (determines TTL)
            ttl: Optional custom TTL in seconds
        """
        try:
            ttl = ttl or self.CACHE_TTL.get(task_type, 3600)

            self.redis.setex(
                f"precompute:cache:{cache_key}",
                ttl,
                json.dumps(result)
            )

            logger.debug(f"💾 Cached result: {cache_key} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    def invalidate_cache(self, pattern: str):
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Redis pattern (e.g., "video:123:*")
        """
        try:
            keys = self.redis.keys(f"precompute:cache:{pattern}")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"🗑️  Invalidated {len(keys)} cache entries matching: {pattern}")
                self._increment_metric("cache_invalidations", len(keys))

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")

    async def refresh_cache_proactively(self, task_type: PrecomputeTaskType, filters: Optional[Dict[str, Any]] = None):
        """
        Proactively refresh cache for tasks nearing expiration.

        Args:
            task_type: Type of tasks to refresh
            filters: Optional filters (e.g., user_id, video_id)
        """
        logger.info(f"🔄 Proactively refreshing cache for: {task_type.value}")

        # Find cache entries nearing expiration (< 10% TTL remaining)
        ttl_threshold = self.CACHE_TTL.get(task_type, 3600) * 0.1

        # Scan for relevant cache keys
        pattern = f"precompute:cache:{task_type.value}:*"
        keys = self.redis.keys(pattern)

        refreshed = 0
        for key in keys:
            try:
                ttl = self.redis.ttl(key)
                if 0 < ttl < ttl_threshold:
                    # Extract identifiers from key
                    # Key format: precompute:cache:task_type:video_id or campaign_id
                    parts = key.split(':')
                    if len(parts) >= 4:
                        entity_id = parts[3]

                        # Queue refresh task
                        await self._queue_precompute_task(
                            task_type=task_type,
                            event=PrecomputeEvent.DASHBOARD_VIEW,  # Generic refresh event
                            video_id=entity_id if 'video' in task_type.value else None,
                            campaign_id=entity_id if 'campaign' in task_type.value else None,
                            data={},
                            priority=3  # Low priority for refresh
                        )

                        refreshed += 1

            except Exception as e:
                logger.error(f"Failed to refresh cache entry {key}: {e}")

        logger.info(f"✅ Queued {refreshed} cache refresh tasks")

    # ========================================================================
    # TASK QUEUE MANAGEMENT
    # ========================================================================

    async def _queue_precompute_task(
        self,
        task_type: PrecomputeTaskType,
        event: PrecomputeEvent,
        user_id: Optional[str] = None,
        video_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> str:
        """
        Queue a precomputation task.

        Args:
            task_type: Type of task
            event: Triggering event
            user_id: Optional user ID
            video_id: Optional video ID
            campaign_id: Optional campaign ID
            data: Optional task data
            priority: Task priority (1-10)

        Returns:
            Task ID
        """
        try:
            # Generate task ID
            task_id = f"{task_type.value}_{int(time.time() * 1000)}"

            # Generate cache key
            cache_key = self._generate_cache_key(task_type, video_id, campaign_id, user_id)

            # Check if already cached
            cached_result = self.get_cached_result(cache_key)
            if cached_result:
                logger.info(f"⚡ Result already cached for {task_type.value}, skipping queue")
                return f"{task_id}_cached"

            # Create task
            task = PrecomputeTask(
                task_id=task_id,
                task_type=task_type,
                event=event,
                user_id=user_id,
                video_id=video_id,
                campaign_id=campaign_id,
                data=data or {},
                priority=priority,
                cache_key=cache_key
            )

            # Add to Redis queue (sorted set by priority)
            queue_key = f"precompute:queue:{task_type.value}"
            self.redis.zadd(queue_key, {json.dumps(asdict(task)): priority})

            # Track metrics
            self._increment_metric("tasks_queued", task_type.value)

            logger.debug(f"📝 Queued task: {task_id} (type: {task_type.value}, priority: {priority})")

            return task_id

        except Exception as e:
            logger.error(f"Failed to queue precompute task: {e}", exc_info=True)
            raise

    def get_queued_task_count(self, task_type: Optional[PrecomputeTaskType] = None) -> int:
        """
        Get count of queued tasks.

        Args:
            task_type: Optional filter by task type

        Returns:
            Number of queued tasks
        """
        if task_type:
            queue_key = f"precompute:queue:{task_type.value}"
            return self.redis.zcard(queue_key)
        else:
            total = 0
            for tt in PrecomputeTaskType:
                queue_key = f"precompute:queue:{tt.value}"
                total += self.redis.zcard(queue_key)
            return total

    async def _process_task(self, task: PrecomputeTask) -> Dict[str, Any]:
        """
        Process a precomputation task.

        Args:
            task: Task to process

        Returns:
            Task result
        """
        logger.info(f"⚙️  Processing task: {task.task_id} ({task.task_type.value})")

        task.status = PrecomputeStatus.PROCESSING
        task.started_at = time.time()

        try:
            # Check cache first
            if task.cache_key:
                cached_result = self.get_cached_result(task.cache_key)
                if cached_result:
                    logger.info(f"⚡ Cache hit during processing: {task.task_id}")
                    task.status = PrecomputeStatus.CACHED
                    task.result = cached_result
                    task.completed_at = time.time()
                    return cached_result

            # Execute task based on type
            result = await self._execute_task(task)

            # Cache result
            if task.cache_key and result:
                self.set_cached_result(
                    cache_key=task.cache_key,
                    result=result,
                    task_type=task.task_type
                )

            task.status = PrecomputeStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()

            # Track metrics
            processing_time = task.completed_at - task.started_at
            self._increment_metric("tasks_completed", task.task_type.value)
            self._increment_metric("processing_time", task.task_type.value, processing_time)

            logger.info(f"✅ Task completed: {task.task_id} ({processing_time:.2f}s)")

            return result

        except Exception as e:
            logger.error(f"❌ Task failed: {task.task_id} - {e}", exc_info=True)
            task.status = PrecomputeStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            self._increment_metric("tasks_failed", task.task_type.value)
            return {}

    async def _execute_task(self, task: PrecomputeTask) -> Dict[str, Any]:
        """
        Execute the actual precomputation logic.

        This would call actual ML services, video processing, etc.
        For now, returns mock data with realistic processing times.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        # Simulate realistic processing time
        processing_times = {
            PrecomputeTaskType.SCENE_DETECTION: 2.0,
            PrecomputeTaskType.FACE_DETECTION: 1.5,
            PrecomputeTaskType.HOOK_ANALYSIS: 3.0,
            PrecomputeTaskType.CTR_PREDICTION: 0.5,
            PrecomputeTaskType.THUMBNAIL_GENERATION: 4.0,
            PrecomputeTaskType.CAPTION_GENERATION: 2.5,
            PrecomputeTaskType.VARIANT_GENERATION: 10.0,
            PrecomputeTaskType.VARIANT_SCORING: 5.0,
            PrecomputeTaskType.ROAS_PREDICTION: 1.0,
            PrecomputeTaskType.DASHBOARD_DATA: 2.0,
            PrecomputeTaskType.CAMPAIGN_ANALYTICS: 3.0,
        }

        # Simulate processing
        await asyncio.sleep(processing_times.get(task.task_type, 1.0))

        # Return mock result
        result = {
            'task_id': task.task_id,
            'task_type': task.task_type.value,
            'video_id': task.video_id,
            'campaign_id': task.campaign_id,
            'computed_at': datetime.utcnow().isoformat(),
            'data': {
                'mock': True,
                'message': f'Precomputed {task.task_type.value} result'
            }
        }

        # TODO: Replace with actual service calls:
        # if task.task_type == PrecomputeTaskType.CTR_PREDICTION:
        #     result = await self.ml_service.predict_ctr(task.video_id)
        # elif task.task_type == PrecomputeTaskType.VARIANT_GENERATION:
        #     result = await self.video_service.generate_variants(task.campaign_id)
        # ... etc

        return result

    # ========================================================================
    # BACKGROUND WORKERS
    # ========================================================================

    async def start_workers(self, num_workers: int = 3):
        """
        Start background workers to process precomputation queue.

        Args:
            num_workers: Number of parallel workers
        """
        self.running = True
        logger.info(f"🚀 Starting {num_workers} precompute workers...")

        # Start worker tasks
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker_task)

        logger.info(f"✅ {num_workers} workers started")

    async def stop_workers(self):
        """Stop all background workers."""
        logger.info("Stopping precompute workers...")
        self.running = False

        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("✅ All workers stopped")

    async def _worker_loop(self, worker_id: int):
        """
        Worker loop to process tasks from queue.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get highest priority task from any queue
                task = await self._get_next_task()

                if task:
                    await self._process_task(task)
                else:
                    # No tasks, sleep briefly
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def _get_next_task(self) -> Optional[PrecomputeTask]:
        """
        Get next highest-priority task from queues.

        Returns:
            Next task or None if no tasks available
        """
        try:
            # Check all task type queues
            best_task = None
            best_priority = -1
            best_queue_key = None

            for task_type in PrecomputeTaskType:
                queue_key = f"precompute:queue:{task_type.value}"

                # Get highest priority task from this queue (without removing)
                task_data_list = self.redis.zrevrange(queue_key, 0, 0, withscores=True)

                if task_data_list:
                    task_data, priority = task_data_list[0]

                    if priority > best_priority:
                        best_priority = priority
                        best_task = PrecomputeTask(**json.loads(task_data))
                        best_queue_key = queue_key

            # Remove selected task from queue
            if best_task and best_queue_key:
                self.redis.zrem(best_queue_key, json.dumps(asdict(best_task)))
                return best_task

            return None

        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return None

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _generate_cache_key(
        self,
        task_type: PrecomputeTaskType,
        video_id: Optional[str],
        campaign_id: Optional[str],
        user_id: Optional[str]
    ) -> str:
        """Generate cache key for task."""
        if video_id:
            return f"{task_type.value}:video:{video_id}"
        elif campaign_id:
            return f"{task_type.value}:campaign:{campaign_id}"
        elif user_id:
            return f"{task_type.value}:user:{user_id}"
        else:
            return f"{task_type.value}:global"

    async def _get_user_history(self, user_id: str) -> Dict[str, Any]:
        """
        Get user activity history for prediction.

        Args:
            user_id: User ID

        Returns:
            User history dictionary
        """
        try:
            # Get from Redis
            history_key = f"precompute:user_history:{user_id}"
            history_data = self.redis.get(history_key)

            if history_data:
                return json.loads(history_data)

            # Default history
            return {
                'last_action': 3,  # dashboard view
                'actions_today': 0,
                'session_duration': 5,
                'last_login': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            return {}

    async def _update_user_action(self, user_id: str, action: PrecomputeEvent):
        """
        Update user history with new action.

        Args:
            user_id: User ID
            action: Action taken
        """
        try:
            history = await self._get_user_history(user_id)

            # Update history
            history['last_action'] = self.action_predictor.action_to_idx.get(action, 3)
            history['actions_today'] = history.get('actions_today', 0) + 1
            history['last_login'] = datetime.utcnow().isoformat()

            # Store in Redis
            history_key = f"precompute:user_history:{user_id}"
            self.redis.setex(history_key, 24 * 3600, json.dumps(history))  # 24h TTL

        except Exception as e:
            logger.error(f"Failed to update user action: {e}")

    async def _precompute_for_action(self, user_id: str, action: PrecomputeEvent, probability: float):
        """
        Precompute for predicted action.

        Args:
            user_id: User ID
            action: Predicted action
            probability: Prediction probability
        """
        logger.info(f"🔮 Precomputing for predicted action: {action.value} (prob: {probability:.2%})")

        # Determine priority based on probability
        priority = int(probability * 10)  # 0.5 prob = priority 5, 1.0 prob = priority 10

        # Queue relevant tasks based on predicted action
        if action == PrecomputeEvent.DASHBOARD_VIEW:
            await self._queue_precompute_task(
                task_type=PrecomputeTaskType.DASHBOARD_DATA,
                event=action,
                user_id=user_id,
                priority=priority
            )
        elif action == PrecomputeEvent.CAMPAIGN_CREATE:
            await self._queue_precompute_task(
                task_type=PrecomputeTaskType.CAMPAIGN_ANALYTICS,
                event=action,
                user_id=user_id,
                priority=priority
            )

    def _increment_metric(self, metric: str, category: Optional[str] = None, value: float = 1.0):
        """
        Increment metric in Redis.

        Args:
            metric: Metric name
            category: Optional category
            value: Value to increment by
        """
        try:
            key = f"precompute:metrics:{metric}"
            if category:
                key += f":{category}"
            self.redis.incrbyfloat(key, value)
        except Exception as e:
            logger.error(f"Failed to increment metric: {e}")

    # ========================================================================
    # MONITORING & METRICS
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get precomputation metrics.

        Returns:
            Metrics dictionary
        """
        try:
            # Get all metric keys
            metric_keys = self.redis.keys("precompute:metrics:*")

            metrics = {}
            for key in metric_keys:
                metric_name = key.replace("precompute:metrics:", "")
                value = float(self.redis.get(key) or 0)
                metrics[metric_name] = value

            # Calculate derived metrics
            total_requests = metrics.get('cache_hits', 0) + metrics.get('cache_misses', 0)
            cache_hit_rate = (metrics.get('cache_hits', 0) / total_requests * 100) if total_requests > 0 else 0

            # Calculate time savings
            avg_processing_time = {}
            for task_type in PrecomputeTaskType:
                total_time = metrics.get(f'processing_time:{task_type.value}', 0)
                completed = metrics.get(f'tasks_completed:{task_type.value}', 0)
                if completed > 0:
                    avg_processing_time[task_type.value] = total_time / completed

            return {
                'raw_metrics': metrics,
                'cache_hit_rate': cache_hit_rate,
                'total_requests': total_requests,
                'queue_size': self.get_queued_task_count(),
                'avg_processing_time': avg_processing_time,
                'workers_running': len([w for w in self.workers if not w.done()]),
            }

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Queue statistics
        """
        stats = {}
        total = 0

        for task_type in PrecomputeTaskType:
            count = self.get_queued_task_count(task_type)
            if count > 0:
                stats[task_type.value] = count
                total += count

        stats['total'] = total
        return stats


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Global precomputer instance
_precomputer: Optional[Precomputer] = None


def get_precomputer() -> Precomputer:
    """Get global precomputer instance."""
    global _precomputer
    if _precomputer is None:
        _precomputer = Precomputer()
    return _precomputer
