import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_models():
    try:
        logger.info("Verifying models.py...")
        from shared.db.models import Asset, Clip, PerformanceMetric, Prediction
        logger.info("Successfully imported Asset, Clip, PerformanceMetric, Prediction")
        
        # Check specific fields
        assert hasattr(PerformanceMetric, 'roas'), "PerformanceMetric missing 'roas'"
        assert hasattr(Prediction, 'confidence'), "Prediction missing 'confidence'"
        logger.info("Field verification successful")
        return True
    except Exception as e:
        logger.error(f"Model verification failed: {e}")
        return False

def verify_data_loader():
    try:
        logger.info("Verifying data_loader.py...")
        from src.data_loader import TrainingDataLoader, get_data_loader
        
        # We can't easily test DB connection without env vars, but we can test import and class definition
        assert TrainingDataLoader is not None
        logger.info("Successfully imported TrainingDataLoader")
        return True
    except Exception as e:
        logger.error(f"Data Loader verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting refactor verification...")
    
    models_ok = verify_models()
    loader_ok = verify_data_loader()
    
    if models_ok and loader_ok:
        logger.info("VERIFICATION SUCCESSFUL: Refactor appears syntactically correct.")
        sys.exit(0)
    else:
        logger.error("VERIFICATION FAILED")
        sys.exit(1)
