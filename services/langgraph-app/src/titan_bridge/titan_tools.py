"""
Titan Tools for LangGraph
==========================

LangGraph-compatible tools that wrap Titan-Core functionality.
These tools can be used by LangGraph agents (CEO, specialists) to
leverage the multi-model evaluation and generation capabilities of Titan.

Tools:
------
1. evaluate_with_council: Call Titan Council for script evaluation
2. generate_with_director: Call Titan Director for creative generation
3. run_antigravity_loop: Run full Titan Antigravity Loop

All tools are async and compatible with LangGraph's tool system.
"""

import os
import sys
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Add titan-core to Python path for imports
TITAN_CORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../titan-core"))
if TITAN_CORE_PATH not in sys.path:
    sys.path.insert(0, TITAN_CORE_PATH)


async def _import_titan_orchestrator():
    """
    Lazy import of Titan orchestrator to avoid circular dependencies
    and handle missing dependencies gracefully.
    """
    try:
        from ai_council.orchestrator import orchestrator
        return orchestrator
    except ImportError as e:
        print(f"❌ Failed to import Titan orchestrator: {e}")
        print("💡 Ensure titan-core dependencies are installed")
        return None


async def _import_titan_council():
    """
    Lazy import of Titan council evaluator.
    """
    try:
        from engines.ensemble import council
        return council
    except ImportError as e:
        print(f"❌ Failed to import Titan council: {e}")
        print("💡 Ensure titan-core dependencies are installed")
        return None


@tool
async def evaluate_with_council(
    script_content: str,
    niche: str = "fitness"
) -> Dict[str, Any]:
    """
    Evaluate a script or content using the Titan Council of multi-model evaluators.

    The Council uses:
    - Gemini 3 Pro (40% weight): Creative reasoning and hook strength
    - Claude 3.5 Sonnet (30% weight): Psychology and emotional triggers
    - GPT-4o (20% weight): Logical structure and coherence
    - DeepCTR (10% weight): Data-driven CTR predictions

    Args:
        script_content: The script, ad copy, or content to evaluate
        niche: Business vertical (fitness, e-commerce, education, finance, entertainment)

    Returns:
        {
            "verdict": "APPROVED" | "NEEDS_REVISION",
            "final_score": float (0-100),
            "breakdown": {
                "gemini_3_pro": float,
                "claude_3_5": float,
                "gpt_4o": float,
                "deep_ctr": float
            },
            "feedback": str (actionable suggestions),
            "confidence": float (0-1),
            "timestamp": str
        }

    Example:
        result = await evaluate_with_council(
            script_content="Hook: Are you tired of yo-yo dieting?...",
            niche="fitness"
        )
        if result["verdict"] == "APPROVED":
            print(f"Great! Score: {result['final_score']}")
    """
    council = await _import_titan_council()

    if council is None:
        return {
            "verdict": "ERROR",
            "final_score": 0,
            "breakdown": {},
            "feedback": "Titan Council not available. Check dependencies.",
            "confidence": 0,
            "timestamp": "",
            "error": "Import failed"
        }

    try:
        result = await council.evaluate_script(script_content, niche)
        return result
    except Exception as e:
        return {
            "verdict": "ERROR",
            "final_score": 0,
            "breakdown": {},
            "feedback": f"Evaluation failed: {str(e)}",
            "confidence": 0,
            "timestamp": "",
            "error": str(e)
        }


@tool
async def generate_with_director(
    video_context: str,
    niche: str = "fitness",
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Generate creative content using the Titan Director (Gemini 3 Pro with extended reasoning).

    The Director creates viral ad scripts with psychological triggers, then
    iteratively improves based on Council feedback until approval or max iterations.

    Args:
        video_context: Context for the video/ad (e.g., "30-day transformation program")
        niche: Business vertical (fitness, e-commerce, education, etc.)
        max_iterations: Maximum improvement iterations (default: 3)

    Returns:
        {
            "status": "APPROVED" | "REJECTED",
            "model_used": str (e.g., "gemini-3-pro-preview"),
            "blueprint": str (generated script/content),
            "council_review": dict (final council evaluation),
            "turns_taken": int,
            "agent_thoughts": list[str]
        }

    Example:
        result = await generate_with_director(
            video_context="High-intensity interval training for busy professionals",
            niche="fitness"
        )
        if result["status"] == "APPROVED":
            print(result["blueprint"])
    """
    orchestrator = await _import_titan_orchestrator()

    if orchestrator is None:
        return {
            "status": "ERROR",
            "model_used": "unknown",
            "blueprint": "",
            "council_review": {},
            "turns_taken": 0,
            "agent_thoughts": [],
            "error": "Titan Orchestrator not available. Check dependencies."
        }

    try:
        # Temporarily override max_iterations in orchestrator
        original_max = orchestrator.max_iterations
        orchestrator.max_iterations = max_iterations

        result = await orchestrator.run(video_context, niche)

        # Restore original setting
        orchestrator.max_iterations = original_max

        return result
    except Exception as e:
        return {
            "status": "ERROR",
            "model_used": "unknown",
            "blueprint": "",
            "council_review": {},
            "turns_taken": 0,
            "agent_thoughts": [],
            "error": str(e)
        }


@tool
async def run_antigravity_loop(
    video_context: str,
    niche: str = "fitness",
    approval_threshold: float = 85.0
) -> Dict[str, Any]:
    """
    Run the full Titan Antigravity Loop: Director generates → Council evaluates → Iterate.

    This is the complete creative-to-production pipeline:
    1. Director (Gemini 3) drafts concept with extended reasoning
    2. Council (4 models) critiques and scores
    3. If score > threshold, APPROVE. Otherwise, Director improves and repeats.

    Args:
        video_context: Creative brief or context (e.g., "New year fitness challenge")
        niche: Business vertical for evaluation criteria
        approval_threshold: Minimum score to approve (default: 85.0)

    Returns:
        {
            "status": "APPROVED" | "REJECTED",
            "final_score": float,
            "iterations": int,
            "blueprint": str (final approved/rejected script),
            "council_history": list[dict] (all evaluation rounds),
            "model_used": str,
            "total_time": float (seconds)
        }

    Example:
        result = await run_antigravity_loop(
            video_context="Transform your body in 90 days - no gym needed",
            niche="fitness",
            approval_threshold=87.0
        )
        print(f"Status: {result['status']} after {result['iterations']} iterations")
    """
    orchestrator = await _import_titan_orchestrator()

    if orchestrator is None:
        return {
            "status": "ERROR",
            "final_score": 0,
            "iterations": 0,
            "blueprint": "",
            "council_history": [],
            "model_used": "unknown",
            "error": "Titan Orchestrator not available. Check dependencies."
        }

    try:
        import time
        start_time = time.time()

        # Temporarily override approval threshold
        original_threshold = orchestrator.approval_threshold
        orchestrator.approval_threshold = approval_threshold

        result = await orchestrator.run(video_context, niche)

        # Restore original setting
        orchestrator.approval_threshold = original_threshold

        end_time = time.time()

        # Enhance result with additional metadata
        enhanced_result = {
            **result,
            "final_score": result.get("council_review", {}).get("final_score", 0),
            "iterations": result.get("turns_taken", 0),
            "total_time": end_time - start_time,
            "council_history": [result.get("council_review", {})] if result.get("council_review") else []
        }

        return enhanced_result
    except Exception as e:
        return {
            "status": "ERROR",
            "final_score": 0,
            "iterations": 0,
            "blueprint": "",
            "council_history": [],
            "model_used": "unknown",
            "error": str(e)
        }


# Export all tools as a list for easy registration with LangGraph agents
ALL_TITAN_TOOLS = [
    evaluate_with_council,
    generate_with_director,
    run_antigravity_loop
]


# Synchronous wrappers for non-async contexts (if needed)
def sync_evaluate_with_council(script_content: str, niche: str = "fitness") -> Dict[str, Any]:
    """Synchronous wrapper for evaluate_with_council"""
    import asyncio
    return asyncio.run(evaluate_with_council(script_content, niche))


def sync_generate_with_director(
    video_context: str,
    niche: str = "fitness",
    max_iterations: int = 3
) -> Dict[str, Any]:
    """Synchronous wrapper for generate_with_director"""
    import asyncio
    return asyncio.run(generate_with_director(video_context, niche, max_iterations))


def sync_run_antigravity_loop(
    video_context: str,
    niche: str = "fitness",
    approval_threshold: float = 85.0
) -> Dict[str, Any]:
    """Synchronous wrapper for run_antigravity_loop"""
    import asyncio
    return asyncio.run(run_antigravity_loop(video_context, niche, approval_threshold))
