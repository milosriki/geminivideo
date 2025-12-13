"""
Core agent module for LangGraph application.

This module provides base agent functionality and model configuration.
"""

from src.agent.core.base_agent import (
    llm,
    get_llm,
    get_specialist_llm,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
    ModelNotAvailableError,
)

__all__ = [
    "llm",
    "get_llm",
    "get_specialist_llm",
    "PRIMARY_MODEL",
    "FALLBACK_MODEL",
    "ModelNotAvailableError",
]
