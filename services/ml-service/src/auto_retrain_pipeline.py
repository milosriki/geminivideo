"""
Auto-Retraining Pipeline

Automatically retrains ML models when:
1. Accuracy drops below threshold
2. Enough new data accumulated
3. Scheduled daily/weekly
4. Concept drift detected

This is how the system gets smarter every day.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)

class RetrainTrigger(Enum):
    SCHEDULED = "scheduled"
    ACCURACY_DROP = "accuracy_drop"
    DATA_THRESHOLD = "data_threshold"
    DRIFT_DETECTED = "drift_detected"
    MANUAL = "manual"

class RetrainStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RetrainJob:
    """A model retraining job"""
    job_id: str
    model_type: str
    trigger: RetrainTrigger
    status: RetrainStatus

    # Configuration
    config: Dict = field(default_factory=dict)

    # Data
    training_samples: int = 0
    validation_samples: int = 0

    # Results
    old_accuracy: float = 0.0
    new_accuracy: float = 0.0
    improvement: float = 0.0

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error
    error: Optional[str] = None

@dataclass
class RetrainConfig:
    """Configuration for retraining"""
    # Thresholds
    min_accuracy_threshold: float = 0.6
    min_samples_for_retrain: int = 100
    max_samples_per_retrain: int = 10000

    # Schedule
    daily_retrain_hour: int = 2  # 2 AM
    weekly_retrain_day: int = 0  # Monday

    # Validation
    validation_split: float = 0.2
    min_improvement_threshold: float = 0.01  # 1% improvement required

    # Rollback
    enable_auto_rollback: bool = True
    rollback_accuracy_threshold: float = 0.5

class AutoRetrainPipeline:
    """
    Automated model retraining pipeline.

    Features:
    - Scheduled retraining (daily/weekly)
    - Triggered retraining (accuracy drop, drift)
    - Validation before deployment
    - Automatic rollback on failure
    - Training history tracking
    """

    def __init__(self, config: RetrainConfig = None):
        self.config = config or RetrainConfig()
        self.jobs: Dict[str, RetrainJob] = {}
        self.training_history: List[RetrainJob] = []
        self.model_versions: Dict[str, str] = {}  # model_type -> current_version

    async def check_retrain_needed(self, model_type: str,
                                    accuracy_tracker: Any = None) -> Tuple[bool, RetrainTrigger, str]:
        """Check if model needs retraining"""

        # Check accuracy if tracker provided
        if accuracy_tracker:
            should_retrain, reason = accuracy_tracker.should_retrain(model_type)
            if should_retrain:
                return True, RetrainTrigger.ACCURACY_DROP, reason

        # Check data accumulation
        new_data_count = await self._get_new_data_count(model_type)
        if new_data_count >= self.config.min_samples_for_retrain:
            return True, RetrainTrigger.DATA_THRESHOLD, f"{new_data_count} new samples available"

        # Check scheduled time
        if self._is_scheduled_time():
            return True, RetrainTrigger.SCHEDULED, "Scheduled daily retrain"

        return False, RetrainTrigger.MANUAL, "No retrain needed"

    async def start_retrain(self, model_type: str,
                            trigger: RetrainTrigger,
                            config: Dict = None) -> RetrainJob:
        """Start a retraining job"""
        job_id = f"retrain_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job = RetrainJob(
            job_id=job_id,
            model_type=model_type,
            trigger=trigger,
            status=RetrainStatus.PENDING,
            config=config or {}
        )

        self.jobs[job_id] = job

        # Start async retraining
        asyncio.create_task(self._execute_retrain(job))

        logger.info(f"Started retrain job: {job_id}")
        return job

    async def _execute_retrain(self, job: RetrainJob):
        """Execute the retraining pipeline"""
        try:
            job.status = RetrainStatus.RUNNING
            job.started_at = datetime.now()

            # Step 1: Load training data
            logger.info(f"[{job.job_id}] Loading training data...")
            train_data, val_data = await self._load_training_data(job.model_type)
            job.training_samples = len(train_data) if train_data else 0
            job.validation_samples = len(val_data) if val_data else 0

            # Step 2: Get current model accuracy
            logger.info(f"[{job.job_id}] Evaluating current model...")
            job.old_accuracy = await self._evaluate_model(job.model_type, val_data)

            # Step 3: Train new model
            logger.info(f"[{job.job_id}] Training new model...")
            new_model = await self._train_model(job.model_type, train_data, job.config)

            # Step 4: Validate new model
            logger.info(f"[{job.job_id}] Validating new model...")
            job.new_accuracy = await self._evaluate_model(job.model_type, val_data, new_model)
            job.improvement = job.new_accuracy - job.old_accuracy

            # Step 5: Deploy or rollback
            if job.new_accuracy >= job.old_accuracy - 0.02:  # Allow 2% tolerance
                logger.info(f"[{job.job_id}] Deploying new model (accuracy: {job.new_accuracy:.2%})")
                await self._deploy_model(job.model_type, new_model)
                job.status = RetrainStatus.COMPLETED
            else:
                logger.warning(f"[{job.job_id}] New model worse than old, keeping current model")
                job.status = RetrainStatus.COMPLETED
                job.error = f"New model accuracy ({job.new_accuracy:.2%}) worse than old ({job.old_accuracy:.2%})"

            job.completed_at = datetime.now()

        except Exception as e:
            logger.error(f"[{job.job_id}] Retrain failed: {e}")
            job.status = RetrainStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()

        finally:
            self.training_history.append(job)

    async def _load_training_data(self, model_type: str) -> Tuple[List, List]:
        """Load training data from database"""
        # Would load from actual database
        # Return train, validation splits
        return [], []

    async def _evaluate_model(self, model_type: str, val_data: List,
                               model: Any = None) -> float:
        """Evaluate model accuracy"""
        # Would run actual evaluation
        return 0.75  # Placeholder

    async def _train_model(self, model_type: str, train_data: List,
                           config: Dict) -> Any:
        """Train a new model"""
        # Would train actual model
        logger.info(f"Training {model_type} model with {len(train_data)} samples")
        return None  # Placeholder

    async def _deploy_model(self, model_type: str, model: Any):
        """Deploy trained model to production"""
        version = f"v{datetime.now().strftime('%Y%m%d_%H%M')}"
        self.model_versions[model_type] = version
        logger.info(f"Deployed {model_type} version {version}")

    async def _get_new_data_count(self, model_type: str) -> int:
        """Get count of new training data since last retrain"""
        # Would query database
        return 0

    def _is_scheduled_time(self) -> bool:
        """Check if current time is scheduled retrain time"""
        now = datetime.now()
        return now.hour == self.config.daily_retrain_hour

    def get_job_status(self, job_id: str) -> Optional[RetrainJob]:
        """Get status of a retrain job"""
        return self.jobs.get(job_id)

    def get_training_history(self, model_type: str = None,
                              limit: int = 10) -> List[Dict]:
        """Get training history"""
        history = self.training_history

        if model_type:
            history = [j for j in history if j.model_type == model_type]

        history.sort(key=lambda j: j.created_at, reverse=True)

        return [
            {
                'job_id': j.job_id,
                'model_type': j.model_type,
                'trigger': j.trigger.value,
                'status': j.status.value,
                'old_accuracy': j.old_accuracy,
                'new_accuracy': j.new_accuracy,
                'improvement': j.improvement,
                'training_samples': j.training_samples,
                'created_at': j.created_at.isoformat(),
                'duration_seconds': (j.completed_at - j.started_at).total_seconds() if j.started_at and j.completed_at else None
            }
            for j in history[:limit]
        ]

    def get_current_versions(self) -> Dict[str, str]:
        """Get current model versions"""
        return self.model_versions.copy()

    async def run_scheduled_check(self):
        """Run scheduled check for all models"""
        model_types = ['ctr_predictor', 'roas_predictor', 'hook_classifier']

        for model_type in model_types:
            should_retrain, trigger, reason = await self.check_retrain_needed(model_type)

            if should_retrain:
                logger.info(f"Triggering retrain for {model_type}: {reason}")
                await self.start_retrain(model_type, trigger)

    def get_pipeline_status(self) -> Dict:
        """Get overall pipeline status"""
        running_jobs = [j for j in self.jobs.values() if j.status == RetrainStatus.RUNNING]

        return {
            'active_jobs': len(running_jobs),
            'total_jobs': len(self.jobs),
            'total_retrains': len(self.training_history),
            'current_versions': self.model_versions,
            'config': {
                'min_accuracy_threshold': self.config.min_accuracy_threshold,
                'min_samples_for_retrain': self.config.min_samples_for_retrain,
                'daily_retrain_hour': self.config.daily_retrain_hour
            }
        }


# Scheduled runner
async def run_daily_retrain():
    """Run daily retraining check"""
    pipeline = AutoRetrainPipeline()
    await pipeline.run_scheduled_check()
