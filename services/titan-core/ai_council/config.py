"""
AI Council Configuration
Environment variables and model settings

Updated: December 2025
- OpenAI November 2025 models (o1, gpt-4o-2024-11-20)
- Batch API support
- Vision capabilities
"""

import os

# ============================================================================
# GEMINI MODELS
# ============================================================================
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-thinking-exp-1219")
GEMINI_FLASH_MODEL_ID = os.getenv("GEMINI_FLASH_MODEL_ID", "gemini-2.0-flash-exp")
GEMINI_PRO_MODEL_ID = os.getenv("GEMINI_PRO_MODEL_ID", "gemini-1.5-pro")

# ============================================================================
# OPENAI MODELS (November 2025)
# ============================================================================

# Reasoning Models
OPENAI_O1_MODEL = os.getenv("OPENAI_O1_MODEL", "o1")  # Complex reasoning
OPENAI_O1_MINI_MODEL = os.getenv("OPENAI_O1_MINI_MODEL", "o1-mini")  # Fast reasoning

# GPT-4o Family
OPENAI_GPT4O_LATEST = os.getenv("OPENAI_GPT4O_LATEST", "gpt-4o-2024-11-20")  # Latest multimodal
OPENAI_GPT4O = os.getenv("OPENAI_GPT4O", "gpt-4o")  # Standard production
OPENAI_GPT4O_MINI = os.getenv("OPENAI_GPT4O_MINI", "gpt-4o-mini")  # Cost-optimized

# Model Selection Strategy
OPENAI_DEFAULT_REASONING_MODEL = os.getenv("OPENAI_DEFAULT_REASONING", "o1")  # o1 or o1-mini
OPENAI_DEFAULT_SCORING_MODEL = os.getenv("OPENAI_DEFAULT_SCORING", "gpt-4o-mini")  # gpt-4o-mini
OPENAI_DEFAULT_VISION_MODEL = os.getenv("OPENAI_DEFAULT_VISION", "gpt-4o-2024-11-20")  # gpt-4o-latest

# ============================================================================
# BATCH API SETTINGS (November 2025 Feature)
# ============================================================================
OPENAI_BATCH_ENABLED = os.getenv("OPENAI_BATCH_ENABLED", "false").lower() == "true"
OPENAI_BATCH_COMPLETION_WINDOW = os.getenv("OPENAI_BATCH_WINDOW", "24h")  # 24h turnaround

# ============================================================================
# API SETTINGS
# ============================================================================
API_VERSION = os.getenv("GEMINI_API_VERSION", "v1")

# ============================================================================
# COUNCIL WEIGHTS
# ============================================================================
COUNCIL_WEIGHTS = {
    "gemini": 0.40,  # Gemini 2.0 Flash Thinking (Extended Reasoning)
    "claude": 0.30,  # Claude 3.5 Sonnet (Psychology)
    "openai": 0.20,  # OpenAI (o1 or gpt-4o-mini based on mode)
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
