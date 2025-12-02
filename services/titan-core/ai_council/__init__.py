"""
AI Council - Multi-LLM Ensemble for Winning Ad Generation

Components:
- CouncilOfTitans: 4-model script evaluation (Gemini, Claude, GPT-4o, DeepCTR)
- OracleAgent: 8-engine ROAS prediction
- DirectorAgentV2: Blueprint generation with Reflexion Loop
- LearningLoop: Purchase signal feedback
- UltimatePipeline: End-to-end integration
"""

from .config import (
    GEMINI_MODEL_ID,
    GEMINI_FLASH_MODEL_ID,
    COUNCIL_WEIGHTS,
    ORACLE_ENGINE_WEIGHTS,
    APPROVAL_THRESHOLD
)

from .council_of_titans import CouncilOfTitans, council
from .oracle_agent import OracleAgent, EnsemblePredictionResult
from .director_agent import DirectorAgentV2, AdBlueprint, BlueprintGenerationRequest
from .learning_loop import LearningLoop
from .ultimate_pipeline import UltimatePipeline

__all__ = [
    # Config
    "GEMINI_MODEL_ID",
    "GEMINI_FLASH_MODEL_ID",
    "COUNCIL_WEIGHTS",
    "ORACLE_ENGINE_WEIGHTS",
    "APPROVAL_THRESHOLD",
    # Classes
    "CouncilOfTitans",
    "council",
    "OracleAgent",
    "EnsemblePredictionResult",
    "DirectorAgentV2",
    "AdBlueprint",
    "BlueprintGenerationRequest",
    "LearningLoop",
    "UltimatePipeline"
]
