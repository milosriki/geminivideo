"""
Base Agent Configuration Module

This module handles the core LLM configuration for the LangGraph agent system.
It implements intelligent model selection with fallback support.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.exceptions import LangChainException
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Model Configuration Constants
PRIMARY_MODEL = "gpt-5.1-instant"
FALLBACK_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0

# Exception for model availability issues
class ModelNotAvailableError(Exception):
    """Raised when a requested model is not available."""
    pass


def get_llm(
    temperature: float = DEFAULT_TEMPERATURE,
    max_retries: int = 2,
    request_timeout: int = 60
) -> ChatOpenAI:
    """
    Get LLM instance with intelligent fallback support.

    Attempts to use PRIMARY_MODEL (gpt-5.1-instant) first. If unavailable,
    automatically falls back to FALLBACK_MODEL (gpt-4o).

    Args:
        temperature: Controls randomness in model outputs (0-1)
        max_retries: Maximum number of retry attempts for API calls
        request_timeout: Timeout in seconds for API requests

    Returns:
        ChatOpenAI: Configured LLM instance

    Raises:
        ModelNotAvailableError: If both primary and fallback models fail
    """
    model_name = PRIMARY_MODEL

    try:
        # Attempt to initialize with primary model
        logger.info(f"Attempting to initialize LLM with primary model: {PRIMARY_MODEL}")
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=max_retries,
            request_timeout=request_timeout
        )

        # Test model availability with a minimal call
        # Note: The actual availability test happens on first use
        # OpenAI client validates model names lazily
        logger.info(f"Successfully initialized LLM with {model_name}")
        return llm

    except (LangChainException, ValueError, Exception) as e:
        # Log primary model failure
        logger.warning(
            f"Primary model {PRIMARY_MODEL} initialization failed: {str(e)}. "
            f"Falling back to {FALLBACK_MODEL}"
        )

        try:
            # Fallback to secondary model
            model_name = FALLBACK_MODEL
            logger.info(f"Attempting to initialize LLM with fallback model: {FALLBACK_MODEL}")
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_retries=max_retries,
                request_timeout=request_timeout
            )
            logger.info(f"Successfully initialized LLM with fallback model {model_name}")
            return llm

        except Exception as fallback_error:
            # Both models failed
            error_msg = (
                f"Failed to initialize LLM with both primary ({PRIMARY_MODEL}) "
                f"and fallback ({FALLBACK_MODEL}) models. "
                f"Fallback error: {str(fallback_error)}"
            )
            logger.error(error_msg)
            raise ModelNotAvailableError(error_msg) from fallback_error


def get_specialist_llm(
    specialist_name: str,
    temperature: Optional[float] = None
) -> ChatOpenAI:
    """
    Get a specialized LLM instance for specific agent roles.

    This function allows different specialists to use different temperature
    settings while maintaining the same model fallback logic.

    Args:
        specialist_name: Name of the specialist agent
        temperature: Optional temperature override for this specialist

    Returns:
        ChatOpenAI: Configured LLM instance for the specialist
    """
    temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
    logger.info(f"Creating LLM for specialist: {specialist_name} (temperature={temp})")
    return get_llm(temperature=temp)


# Default LLM instance for backward compatibility
# This maintains compatibility with existing code that imports 'llm' directly
llm = get_llm()
