"""Utility functions for LLM calls."""

from langchain_core.messages import HumanMessage


def create_llm_messages(prompt: str) -> list:
    """Create LLM messages from a prompt string."""
    return [HumanMessage(content=prompt)]

