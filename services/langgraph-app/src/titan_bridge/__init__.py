"""
LangGraph-Titan Bridge
======================

Unified bridge between LangGraph CEO Agent and Titan-Core's Council/Oracle/Director.

This module enables seamless orchestration between:
- LangGraph CEO Agent (GPT-4o based strategic planning)
- Titan-Core Orchestrator (Multi-model creative evaluation)

Components:
-----------
- bridge.py: Core integration logic and LangGraph nodes
- unified_state.py: Extended state management combining both systems
- titan_tools.py: LangGraph-compatible tools wrapping Titan functions

Usage:
------
    from src.titan_bridge import create_council_node, TitanBridgeState
    from src.titan_bridge.titan_tools import evaluate_with_council

    # Add to your LangGraph workflow
    workflow.add_node("council_evaluation", create_council_node())
"""

from src.titan_bridge.unified_state import TitanBridgeState
from src.titan_bridge.bridge import create_council_node, create_director_node
from src.titan_bridge.titan_tools import (
    evaluate_with_council,
    generate_with_director,
    run_antigravity_loop
)

__all__ = [
    "TitanBridgeState",
    "create_council_node",
    "create_director_node",
    "evaluate_with_council",
    "generate_with_director",
    "run_antigravity_loop"
]

__version__ = "1.0.0"
