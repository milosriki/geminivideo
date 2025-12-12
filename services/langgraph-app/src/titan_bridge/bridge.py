"""
LangGraph-Titan Bridge - Core Integration
==========================================

Core integration logic that connects LangGraph CEO Agent with Titan-Core orchestrator.

This module provides:
1. LangGraph node functions that call Titan services
2. State transformation utilities
3. Routing logic for seamless orchestration

Node Functions:
---------------
- council_evaluation_node: Evaluates content using Titan Council
- director_generation_node: Generates content using Titan Director
- antigravity_loop_node: Runs full Titan Antigravity Loop

Factory Functions:
------------------
- create_council_node: Creates a pre-configured council evaluation node
- create_director_node: Creates a pre-configured director generation node
- create_antigravity_node: Creates a full antigravity loop node
"""

import os
import sys
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.titan_bridge.unified_state import (
    TitanBridgeState,
    TitanCouncilResult,
    TitanDirectorOutput,
    map_ceo_to_titan,
    map_titan_to_ceo
)

# Add titan-core to Python path for imports
TITAN_CORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../titan-core"))
if TITAN_CORE_PATH not in sys.path:
    sys.path.insert(0, TITAN_CORE_PATH)


async def _get_titan_orchestrator():
    """Lazy import of Titan orchestrator"""
    try:
        from ai_council.orchestrator import orchestrator
        return orchestrator
    except ImportError as e:
        print(f"⚠️ Titan orchestrator not available: {e}")
        return None


async def _get_titan_council():
    """Lazy import of Titan council"""
    try:
        from engines.ensemble import council
        return council
    except ImportError as e:
        print(f"⚠️ Titan council not available: {e}")
        return None


# =============================================================================
# CORE NODE FUNCTIONS (for use in LangGraph workflows)
# =============================================================================

async def council_evaluation_node(state: TitanBridgeState) -> Dict[str, Any]:
    """
    LangGraph node that evaluates content using the Titan Council.

    This node:
    1. Extracts content to evaluate from state (titan_context or director output)
    2. Calls Titan Council for multi-model evaluation
    3. Updates state with council results
    4. Sets routing flags based on verdict

    Flow:
        CEO Agent → council_evaluation_node → [APPROVED → Continue | NEEDS_REVISION → Director]

    Args:
        state: TitanBridgeState with content to evaluate

    Returns:
        State updates including:
        - titan_council_results: New evaluation result
        - requires_director_generation: True if revision needed
        - past_steps: Logged action
    """
    print("🏛️ Council Evaluation Node: Analyzing content...")

    council = await _get_titan_council()

    if council is None:
        print("❌ Council not available - skipping evaluation")
        return {
            "past_steps": [("council_evaluation", "ERROR: Council not available")],
            "requires_council_review": False
        }

    # Determine what content to evaluate
    content_to_evaluate = ""
    if state.titan_director_output:
        # Evaluate the latest director output
        output = state.get_latest_director_output()
        content_to_evaluate = output.blueprint
        print(f"📄 Evaluating Director output (Turn {output.turns_taken})...")
    elif state.titan_context:
        # Evaluate the raw context (e.g., user-provided script)
        content_to_evaluate = state.titan_context
        print("📄 Evaluating provided content...")
    else:
        print("⚠️ No content to evaluate")
        return {
            "past_steps": [("council_evaluation", "ERROR: No content to evaluate")],
            "requires_council_review": False
        }

    try:
        # Call Titan Council
        result = await council.evaluate_script(content_to_evaluate, state.titan_niche)

        # Parse result into structured format
        council_result = TitanCouncilResult(
            verdict=result["verdict"],
            final_score=result["final_score"],
            breakdown=result["breakdown"],
            feedback=result["feedback"],
            confidence=result["confidence"],
            timestamp=result["timestamp"],
            errors=result.get("errors")
        )

        print(f"⚖️ VERDICT: {council_result.verdict} (Score: {council_result.final_score}/100)")
        print(f"📊 Breakdown: Gemini={council_result.breakdown.get('gemini_3_pro', 0):.1f}, "
              f"Claude={council_result.breakdown.get('claude_3_5', 0):.1f}, "
              f"GPT={council_result.breakdown.get('gpt_4o', 0):.1f}, "
              f"DeepCTR={council_result.breakdown.get('deep_ctr', 0):.1f}")
        print(f"💡 Feedback: {council_result.feedback}")

        # Build state updates
        updates = {
            "past_steps": [(
                "council_evaluation",
                f"{council_result.verdict} - Score: {council_result.final_score}"
            )]
        }

        # Add council result (triggers operator.add in state)
        state.add_council_result(council_result)

        # Update routing flags based on verdict
        if council_result.verdict == "NEEDS_REVISION":
            updates["requires_director_generation"] = True
            updates["requires_council_review"] = False
            print("🔄 Routing to Director for revision...")
        else:
            updates["requires_director_generation"] = False
            updates["requires_council_review"] = False
            print("✅ Content APPROVED! Continuing CEO workflow...")

        # Map Titan results to CEO-readable format
        ceo_insights = map_titan_to_ceo(result)
        if state.analysis_results:
            updates["analysis_results"] = {
                **state.analysis_results,
                "creative_evaluation": ceo_insights
            }
        else:
            updates["analysis_results"] = {"creative_evaluation": ceo_insights}

        return updates

    except Exception as e:
        print(f"❌ Council evaluation failed: {e}")
        return {
            "past_steps": [("council_evaluation", f"ERROR: {str(e)}")],
            "requires_council_review": False
        }


async def director_generation_node(state: TitanBridgeState) -> Dict[str, Any]:
    """
    LangGraph node that generates content using the Titan Director.

    This node:
    1. Uses titan_context as creative brief
    2. Calls Titan Director (Gemini 3 Pro) for content generation
    3. Updates state with director output
    4. Triggers council review if content generated

    Flow:
        CEO Agent → director_generation_node → Council Evaluation → [Iterate or Approve]

    Args:
        state: TitanBridgeState with titan_context set

    Returns:
        State updates including:
        - titan_director_output: Generated content
        - requires_council_review: True to trigger evaluation
        - titan_iterations: Incremented counter
        - past_steps: Logged action
    """
    print("🎬 Director Generation Node: Creating content...")

    orchestrator = await _get_titan_orchestrator()

    if orchestrator is None:
        print("❌ Orchestrator not available - skipping generation")
        return {
            "past_steps": [("director_generation", "ERROR: Orchestrator not available")],
            "requires_director_generation": False
        }

    if not state.titan_context:
        print("⚠️ No context provided for generation")
        return {
            "past_steps": [("director_generation", "ERROR: No context provided")],
            "requires_director_generation": False
        }

    try:
        # Add feedback from previous council evaluation if available
        prompt = state.titan_context
        latest_council = state.get_latest_council_result()
        if latest_council and latest_council.verdict == "NEEDS_REVISION":
            prompt = f"{prompt}\n\nPREVIOUS FEEDBACK: {latest_council.feedback}"
            print(f"📝 Including council feedback in generation prompt")

        print(f"🎥 Generating with Director (Iteration {state.titan_iterations + 1}/{state.max_titan_iterations})...")

        # Call Titan Director via Orchestrator
        result = await orchestrator.run(prompt, state.titan_niche)

        # Parse result into structured format
        director_output = TitanDirectorOutput(
            blueprint=result["blueprint"],
            model_used=result["model_used"],
            turns_taken=result["turns_taken"],
            status=result["status"],
            timestamp=result.get("timestamp", ""),
            agent_thoughts=result.get("agent_thoughts", [])
        )

        print(f"📜 Director generated content: {director_output.blueprint[:100]}...")
        print(f"🔄 Took {director_output.turns_taken} turns, Status: {director_output.status}")

        # Build state updates
        updates = {
            "past_steps": [(
                "director_generation",
                f"Generated content - Status: {director_output.status}"
            )]
        }

        # Add director output (triggers state updates)
        state.add_director_output(director_output)

        # Routing: always trigger council review after generation
        updates["requires_council_review"] = True
        updates["requires_director_generation"] = False

        print("🏛️ Routing to Council for evaluation...")

        return updates

    except Exception as e:
        print(f"❌ Director generation failed: {e}")
        return {
            "past_steps": [("director_generation", f"ERROR: {str(e)}")],
            "requires_director_generation": False
        }


async def antigravity_loop_node(state: TitanBridgeState) -> Dict[str, Any]:
    """
    LangGraph node that runs the full Titan Antigravity Loop.

    This is a convenience node that runs the complete Director → Council → Iterate
    cycle internally, without requiring manual routing between nodes.

    Use this when you want a single-shot "generate and approve" operation.
    Use separate council_evaluation_node and director_generation_node when you
    want CEO Agent to orchestrate the loop with additional logic between steps.

    Flow:
        CEO Agent → antigravity_loop_node → [Complete, returns approved/rejected content]

    Args:
        state: TitanBridgeState with titan_context set

    Returns:
        State updates including:
        - titan_director_output: Final content (approved or rejected)
        - titan_council_results: All council evaluations from the loop
        - titan_iterations: Total iterations performed
        - past_steps: Logged action
    """
    print("🌀 Antigravity Loop Node: Running full Titan loop...")

    orchestrator = await _get_titan_orchestrator()

    if orchestrator is None:
        print("❌ Orchestrator not available - skipping loop")
        return {
            "past_steps": [("antigravity_loop", "ERROR: Orchestrator not available")]
        }

    if not state.titan_context:
        print("⚠️ No context provided for loop")
        return {
            "past_steps": [("antigravity_loop", "ERROR: No context provided")]
        }

    try:
        print(f"🎬 Running Antigravity Loop (Max iterations: {state.max_titan_iterations})...")

        # Run the full loop
        result = await orchestrator.run(state.titan_context, state.titan_niche)

        # Parse director output
        director_output = TitanDirectorOutput(
            blueprint=result["blueprint"],
            model_used=result["model_used"],
            turns_taken=result["turns_taken"],
            status=result["status"],
            timestamp=result.get("timestamp", ""),
            agent_thoughts=result.get("agent_thoughts", [])
        )

        # Parse council result
        council_result = TitanCouncilResult(
            verdict=result["council_review"]["verdict"],
            final_score=result["council_review"]["final_score"],
            breakdown=result["council_review"]["breakdown"],
            feedback=result["council_review"]["feedback"],
            confidence=result["council_review"]["confidence"],
            timestamp=result["council_review"]["timestamp"],
            errors=result["council_review"].get("errors")
        )

        print(f"🏁 Loop Complete: {director_output.status} after {director_output.turns_taken} turns")
        print(f"⚖️ Final Verdict: {council_result.verdict} (Score: {council_result.final_score}/100)")

        # Update state
        state.add_director_output(director_output)
        state.add_council_result(council_result)

        # Build state updates
        updates = {
            "titan_iterations": director_output.turns_taken,
            "past_steps": [(
                "antigravity_loop",
                f"{director_output.status} - Final Score: {council_result.final_score}"
            )]
        }

        # Map results to CEO-readable format
        ceo_insights = map_titan_to_ceo(result["council_review"])
        if state.analysis_results:
            updates["analysis_results"] = {
                **state.analysis_results,
                "creative_evaluation": ceo_insights
            }
        else:
            updates["analysis_results"] = {"creative_evaluation": ceo_insights}

        return updates

    except Exception as e:
        print(f"❌ Antigravity loop failed: {e}")
        return {
            "past_steps": [("antigravity_loop", f"ERROR: {str(e)}")]
        }


# =============================================================================
# FACTORY FUNCTIONS (convenience wrappers for node creation)
# =============================================================================

def create_council_node():
    """
    Factory function to create a pre-configured council evaluation node.

    Returns:
        Async function compatible with LangGraph workflow.add_node()

    Example:
        workflow.add_node("council_evaluation", create_council_node())
    """
    return council_evaluation_node


def create_director_node():
    """
    Factory function to create a pre-configured director generation node.

    Returns:
        Async function compatible with LangGraph workflow.add_node()

    Example:
        workflow.add_node("director_generation", create_director_node())
    """
    return director_generation_node


def create_antigravity_node():
    """
    Factory function to create a pre-configured antigravity loop node.

    Returns:
        Async function compatible with LangGraph workflow.add_node()

    Example:
        workflow.add_node("antigravity_loop", create_antigravity_node())
    """
    return antigravity_loop_node


# =============================================================================
# ROUTING HELPERS (for conditional edges in LangGraph)
# =============================================================================

def should_route_to_council(state: TitanBridgeState) -> bool:
    """
    Routing logic: Should we evaluate with council?

    Returns True if:
    - requires_council_review flag is set
    - We haven't exceeded max iterations
    - There's content to evaluate
    """
    return state.should_route_to_council()


def should_route_to_director(state: TitanBridgeState) -> bool:
    """
    Routing logic: Should we generate with director?

    Returns True if:
    - requires_director_generation flag is set
    - We haven't exceeded max iterations
    - There's context to work with
    """
    return state.should_route_to_director()


def get_titan_routing_decision(state: TitanBridgeState) -> str:
    """
    Comprehensive routing decision for Titan operations.

    Returns:
        - "council": Route to council evaluation
        - "director": Route to director generation
        - "continue": Return to CEO agent main flow
        - "end": Terminate (max iterations or error)
    """
    # Check iteration limits
    if state.titan_iterations >= state.max_titan_iterations:
        print(f"🛑 Max iterations ({state.max_titan_iterations}) reached")
        return "end"

    # Check routing flags
    if state.should_route_to_council():
        return "council"

    if state.should_route_to_director():
        return "director"

    # Check if we have approved content
    latest_council = state.get_latest_council_result()
    if latest_council and latest_council.verdict == "APPROVED":
        print("✅ Content approved - continuing CEO workflow")
        return "continue"

    # Default: continue CEO workflow
    return "continue"
