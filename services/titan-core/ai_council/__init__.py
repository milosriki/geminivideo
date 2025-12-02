"""
AI COUNCIL - Merged from video-edit repo
Combines AI prediction/evaluation with PRO-GRADE video processing

Components:
1. Council of Titans - 4-model ensemble script evaluation
2. Oracle Agent - 8-engine ROAS prediction
3. Director Agent - Ad blueprint generation with Reflexion
4. VEO Director - AI video generation via Vertex AI
5. Learning Loop - Purchase signal feedback
"""

from .council_of_titans import CouncilOfTitans, council
from .oracle_agent import OracleAgent, EnsemblePredictionResult
from .director_agent import DirectorAgentV2, AdBlueprint, BlueprintGenerationRequest
from .learning_loop import LearningLoop

__all__ = [
    'CouncilOfTitans',
    'council',
    'OracleAgent',
    'EnsemblePredictionResult',
    'DirectorAgentV2',
    'AdBlueprint',
    'BlueprintGenerationRequest',
    'LearningLoop',
]
