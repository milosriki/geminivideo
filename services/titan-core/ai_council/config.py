"""
AI Council Configuration
Environment variables and model settings
"""

import os

# Gemini Models
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-thinking-exp")
GEMINI_FLASH_MODEL_ID = os.getenv("GEMINI_FLASH_MODEL_ID", "gemini-2.0-flash-exp")
GEMINI_PRO_MODEL_ID = os.getenv("GEMINI_PRO_MODEL_ID", "gemini-1.5-pro")

# API Settings
API_VERSION = os.getenv("GEMINI_API_VERSION", "v1")

# Council Weights
COUNCIL_WEIGHTS = {
    "gemini": 0.40,  # Gemini 2.0 Flash Thinking
    "claude": 0.30,  # Claude 3.5 Sonnet
    "gpt4": 0.20,    # GPT-4o
    "deep_ctr": 0.10  # DeepCTR heuristics
}

# Oracle Engine Weights
ORACLE_ENGINE_WEIGHTS = {
    "DeepFM": 0.15,
    "DCN": 0.15,
    "XGBoost": 0.15,
    "LightGBM": 0.12,
    "CatBoost": 0.12,
    "NeuralNet": 0.12,
    "RandomForest": 0.10,
    "GradientBoost": 0.09
}

# Historical Baselines (from $2M ad spend data)
HISTORICAL_AVG_ROAS = 2.4
HISTORICAL_AVG_CTR = 0.024
HISTORICAL_AVG_CVR = 0.031

# Approval Threshold
APPROVAL_THRESHOLD = 85  # Score must be > 85 to approve

# Blueprint Generation
DEFAULT_NUM_VARIATIONS = 50
DEFAULT_DURATION_SECONDS = 30
