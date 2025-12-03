"""
Training Scheduler - Automated model retraining
Continuously improves the model with fresh data from Meta insights
"""
import logging
import schedule
import time
import threading
from typing import Optional
from src.data_loader import get_data_loader
from src.ctr_model import ctr_predictor
from src.feature_engineering import feature_extractor

logger = logging.getLogger(__name__)


class TrainingScheduler:
    """Automated model retraining scheduler"""
    
    def __init__(self, interval_hours: int = 24, min_samples: int = 100):
        """
        Initialize training scheduler
        
        Args:
            interval_hours: Hours between retraining runs
            min_samples: Minimum samples required to trigger retraining
        """
        self.interval_hours = interval_hours
        self.min_samples = min_samples
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
    
    def retrain_model(self):
        """Retrain model with latest data"""
        logger.info("🔄 Starting scheduled model retraining...")
        
        try:
            data_loader = get_data_loader()
            
            if data_loader is None:
                logger.warning("Data loader not available, skipping retraining")
                return
            
            # Get stats first
            stats = data_loader.get_stats()
            logger.info(f"Training data stats: {stats}")
            
            if stats.get('videos_with_min_impressions', 0) < self.min_samples:
                logger.info(f"Not enough training samples ({stats.get('videos_with_min_impressions', 0)} < {self.min_samples}), skipping")
                return
            
            # Fetch training data
            X, y = data_loader.fetch_training_data(min_impressions=100)
            
            if X is None or len(X) < self.min_samples:
                logger.warning(f"Insufficient training data ({len(X) if X is not None else 0} samples)")
                return
            
            # Train model
            logger.info(f"Training model with {len(X)} samples...")
            metrics = ctr_predictor.train(
                X, y, 
                feature_names=feature_extractor.feature_names
            )
            
            logger.info(f"✅ Model retrained successfully!")
            logger.info(f"   Test Accuracy: {metrics['test_accuracy']:.2%}")
            logger.info(f"   Test R²: {metrics['test_r2']:.4f}")
            logger.info(f"   Test RMSE: {metrics['test_rmse']:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Error during scheduled retraining: {e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        logger.info(f"Starting training scheduler (every {self.interval_hours} hours)")
        
        # Schedule the job
        schedule.every(self.interval_hours).hours.do(self.retrain_model)
        
        # Run in background thread
        self.is_running = True
        self.thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.thread.start()
        
        logger.info("✅ Training scheduler started")
    
    def _run_schedule(self):
        """Background thread that runs the scheduler"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Training scheduler stopped")


# Global instance
training_scheduler = TrainingScheduler(interval_hours=24, min_samples=100)
