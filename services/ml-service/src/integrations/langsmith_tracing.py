"""
LangSmith Tracing Integration

Provides distributed tracing and observability for AI/ML operations using LangSmith.
Enables tracking, debugging, and monitoring of LLM calls, chains, and agents.
"""

from langsmith import Client
from langsmith.wrappers import wrap_openai, wrap_anthropic
from functools import wraps
import os
import asyncio
from typing import Any, Callable, Optional, Dict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangSmith configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "geminivideo-ml-service")
LANGSMITH_ENABLED = os.getenv("LANGSMITH_ENABLED", "false").lower() == "true"

# Initialize LangSmith client
client = None
if LANGSMITH_ENABLED and LANGSMITH_API_KEY:
    try:
        client = Client(api_key=LANGSMITH_API_KEY)
        logger.info(f"LangSmith client initialized for project: {LANGSMITH_PROJECT}")
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith client: {e}")
        client = None
else:
    logger.warning("LangSmith is disabled or API key is missing")


def trace_ai_call(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace AI function calls with LangSmith

    Args:
        name: Name of the trace/operation
        metadata: Additional metadata to attach to the trace

    Usage:
        @trace_ai_call("generate_video_script")
        async def generate_script(prompt: str):
            # Your AI call here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED or client is None:
                # If tracing is disabled, just run the function
                return await func(*args, **kwargs)

            trace_metadata = {
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }

            try:
                with client.trace(
                    name=name,
                    project_name=LANGSMITH_PROJECT,
                    metadata=trace_metadata,
                ) as trace:
                    result = await func(*args, **kwargs)
                    trace.end(outputs={"result": str(result)[:1000]})  # Limit output size
                    return result
            except Exception as e:
                logger.error(f"Error in traced function {name}: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED or client is None:
                # If tracing is disabled, just run the function
                return func(*args, **kwargs)

            trace_metadata = {
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {}),
            }

            try:
                with client.trace(
                    name=name,
                    project_name=LANGSMITH_PROJECT,
                    metadata=trace_metadata,
                ) as trace:
                    result = func(*args, **kwargs)
                    trace.end(outputs={"result": str(result)[:1000]})  # Limit output size
                    return result
            except Exception as e:
                logger.error(f"Error in traced function {name}: {e}")
                raise

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def trace_llm_call(model: str, provider: str = "openai"):
    """
    Decorator specifically for LLM API calls with automatic provider wrapping

    Args:
        model: Model name (e.g., "gpt-4", "claude-3-opus")
        provider: LLM provider ("openai" or "anthropic")

    Usage:
        @trace_llm_call(model="gpt-4", provider="openai")
        async def call_openai(prompt: str):
            # Your OpenAI call here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED or client is None:
                return await func(*args, **kwargs)

            metadata = {
                "model": model,
                "provider": provider,
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }

            try:
                with client.trace(
                    name=f"llm_call_{provider}_{model}",
                    project_name=LANGSMITH_PROJECT,
                    metadata=metadata,
                ) as trace:
                    result = await func(*args, **kwargs)
                    trace.end(outputs={"result": str(result)[:1000]})
                    return result
            except Exception as e:
                logger.error(f"Error in LLM call {provider}/{model}: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not LANGSMITH_ENABLED or client is None:
                return func(*args, **kwargs)

            metadata = {
                "model": model,
                "provider": provider,
                "function": func.__name__,
                "timestamp": datetime.utcnow().isoformat(),
            }

            try:
                with client.trace(
                    name=f"llm_call_{provider}_{model}",
                    project_name=LANGSMITH_PROJECT,
                    metadata=metadata,
                ) as trace:
                    result = func(*args, **kwargs)
                    trace.end(outputs={"result": str(result)[:1000]})
                    return result
            except Exception as e:
                logger.error(f"Error in LLM call {provider}/{model}: {e}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def create_run(
    name: str,
    inputs: Dict[str, Any],
    run_type: str = "chain",
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Create a manual LangSmith run for tracking custom operations

    Args:
        name: Name of the run
        inputs: Input parameters
        run_type: Type of run ("llm", "chain", "tool", "retriever", etc.)
        metadata: Additional metadata

    Returns:
        Run context manager
    """
    if not LANGSMITH_ENABLED or client is None:
        return None

    return client.trace(
        name=name,
        project_name=LANGSMITH_PROJECT,
        inputs=inputs,
        run_type=run_type,
        metadata=metadata or {},
    )


def log_feedback(
    run_id: str,
    score: float,
    feedback_key: str = "user_feedback",
    comment: Optional[str] = None,
):
    """
    Log feedback for a specific run

    Args:
        run_id: ID of the run to provide feedback for
        score: Numerical score (0.0 - 1.0)
        feedback_key: Key identifying the type of feedback
        comment: Optional text comment
    """
    if not LANGSMITH_ENABLED or client is None:
        logger.warning("LangSmith feedback logging is disabled")
        return

    try:
        client.create_feedback(
            run_id=run_id,
            key=feedback_key,
            score=score,
            comment=comment,
        )
        logger.info(f"Feedback logged for run {run_id}")
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")


# Export wrapped clients for common providers
def get_wrapped_openai_client():
    """Get OpenAI client wrapped with LangSmith tracing"""
    if not LANGSMITH_ENABLED:
        return None
    try:
        import openai
        return wrap_openai(openai.Client())
    except ImportError:
        logger.warning("OpenAI package not installed")
        return None


def get_wrapped_anthropic_client():
    """Get Anthropic client wrapped with LangSmith tracing"""
    if not LANGSMITH_ENABLED:
        return None
    try:
        import anthropic
        return wrap_anthropic(anthropic.Anthropic())
    except ImportError:
        logger.warning("Anthropic package not installed")
        return None


__all__ = [
    "client",
    "trace_ai_call",
    "trace_llm_call",
    "create_run",
    "log_feedback",
    "get_wrapped_openai_client",
    "get_wrapped_anthropic_client",
]
