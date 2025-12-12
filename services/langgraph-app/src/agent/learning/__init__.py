"""Learning system for unlimited knowledge."""

from agent.learning.auto_discover import AutoDiscovery, auto_discovery
from agent.learning.background_learner import BackgroundLearner, background_learner
from agent.learning.learning_middleware import (
    LearningMiddleware,
    learning_middleware,
)
from agent.learning.semantic_search import SemanticSearch, semantic_search

__all__ = [
    "AutoDiscovery",
    "auto_discovery",
    "LearningMiddleware",
    "learning_middleware",
    "BackgroundLearner",
    "background_learner",
    "SemanticSearch",
    "semantic_search",
]

