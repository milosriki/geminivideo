import sys
import os
import traceback

# Add ML Service to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'services/ml-service')))

# Mock XGBoost first
from unittest.mock import Mock
try:
    import xgboost
except Exception:
    mock_xgb = Mock()
    mock_xgb.XGBClassifier = Mock
    mock_xgb.XGBRegressor = Mock
    mock_xgb.DMatrix = Mock
    sys.modules['xgboost'] = mock_xgb
    print("WARNING: XGBoost mocked in debug script")

print("Attempting to import src.feature_engineering...")
try:
    from src.feature_engineering import feature_extractor
    print("SUCCESS: src.feature_engineering imported")
except Exception:
    traceback.print_exc()

print("Attempting to import src.ctr_model...")
try:
    from src.ctr_model import ctr_predictor
    print("SUCCESS: src.ctr_model imported")
except Exception:
    traceback.print_exc()

print("Attempting to import src.thompson_sampler...")
try:
    from src.thompson_sampler import thompson_optimizer
    print("SUCCESS: src.thompson_sampler imported")
except Exception:
    traceback.print_exc()

print("Attempting to import src.main...")
try:
    from src.main import app
    print("SUCCESS: src.main imported")
except Exception:
    traceback.print_exc()
