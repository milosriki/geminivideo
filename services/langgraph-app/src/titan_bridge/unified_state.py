"""
Unified State Management
=========================

Extends CEOAgentState to include Titan-Core context, enabling seamless
state synchronization between LangGraph CEO Agent and Titan Council.

The TitanBridgeState tracks:
- Council evaluation scores and feedback
- Director-generated creative content
- Antigravity loop iterations and outcomes
- Cross-system communication metadata
"""

from typing import Any, Dict, List, Annotated, Optional
import operator
from dataclasses import dataclass, field
from datetime import datetime

from src.agent.state import CEOAgentState


@dataclass
class TitanCouncilResult:
    """
    Structured result from Titan Council evaluation.
    Maps directly to the output of CouncilEvaluator.evaluate_script()
    """
    verdict: str  # "APPROVED" | "NEEDS_REVISION"
    final_score: float  # 0-100
    breakdown: Dict[str, float]  # Individual model scores
    feedback: str  # Actionable feedback
    confidence: float  # 0-1
    timestamp: str
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for state storage"""
        return {
            "verdict": self.verdict,
            "final_score": self.final_score,
            "breakdown": self.breakdown,
            "feedback": self.feedback,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "errors": self.errors
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TitanCouncilResult":
        """Create from dictionary"""
        return cls(
            verdict=data["verdict"],
            final_score=data["final_score"],
            breakdown=data["breakdown"],
            feedback=data["feedback"],
            confidence=data["confidence"],
            timestamp=data["timestamp"],
            errors=data.get("errors")
        )


@dataclass
class TitanDirectorOutput:
    """
    Output from Titan Director (Gemini 3 Pro).
    Tracks creative generation from the Antigravity Loop.
    """
    blueprint: str  # Generated script/content
    model_used: str  # "gemini-3-pro-preview"
    turns_taken: int  # Number of iterations
    status: str  # "APPROVED" | "REJECTED"
    timestamp: str
    agent_thoughts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for state storage"""
        return {
            "blueprint": self.blueprint,
            "model_used": self.model_used,
            "turns_taken": self.turns_taken,
            "status": self.status,
            "timestamp": self.timestamp,
            "agent_thoughts": self.agent_thoughts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TitanDirectorOutput":
        """Create from dictionary"""
        return cls(
            blueprint=data["blueprint"],
            model_used=data["model_used"],
            turns_taken=data["turns_taken"],
            status=data["status"],
            timestamp=data["timestamp"],
            agent_thoughts=data.get("agent_thoughts", [])
        )


@dataclass
class TitanBridgeState(CEOAgentState):
    """
    Extended state that combines LangGraph CEO Agent and Titan-Core contexts.

    Inherits from CEOAgentState:
    - messages: Communication history
    - current_plan: Strategic plans
    - past_steps: Execution history
    - business_metrics: Performance data
    - analysis_results: CRM/Analytics insights
    - active_agent: Current routing state
    - performance_log: Historical performance
    - improvement_proposals: Self-evolution suggestions

    Adds Titan-specific fields:
    - titan_council_results: Council evaluation history
    - titan_director_output: Director generation output
    - titan_context: Creative context for Titan operations
    - titan_niche: Business vertical (fitness, e-commerce, etc.)
    - titan_iterations: Antigravity loop iteration count
    - requires_council_review: Flag to trigger council evaluation
    """

    # Titan Council Integration
    titan_council_results: Annotated[List[Dict[str, Any]], operator.add] = field(default_factory=list)

    # Titan Director Integration
    titan_director_output: Optional[Dict[str, Any]] = None

    # Creative Context
    titan_context: str = ""  # Video context, campaign brief, etc.
    titan_niche: str = "fitness"  # Default niche

    # Loop Management
    titan_iterations: int = 0
    max_titan_iterations: int = 3

    # Routing Flags
    requires_council_review: bool = False
    requires_director_generation: bool = False

    # Cross-System Metadata
    last_titan_call: Optional[str] = None
    titan_approval_threshold: float = 85.0

    def add_council_result(self, result: TitanCouncilResult):
        """
        Add a council evaluation result to the state history.
        Automatically updates routing flags based on verdict.
        """
        result_dict = result.to_dict()
        self.titan_council_results = [result_dict]  # Triggers operator.add
        self.last_titan_call = datetime.utcnow().isoformat()

        # Update routing flags
        if result.verdict == "NEEDS_REVISION":
            self.requires_director_generation = True
        else:
            self.requires_director_generation = False
            self.requires_council_review = False

    def add_director_output(self, output: TitanDirectorOutput):
        """
        Add director generation output to the state.
        Automatically triggers council review if approved.
        """
        self.titan_director_output = output.to_dict()
        self.titan_iterations += 1
        self.last_titan_call = datetime.utcnow().isoformat()

        # Update routing flags
        if output.status == "APPROVED":
            self.requires_council_review = False
            self.requires_director_generation = False
        elif self.titan_iterations < self.max_titan_iterations:
            self.requires_council_review = True
        else:
            # Max iterations reached, stop loop
            self.requires_council_review = False
            self.requires_director_generation = False

    def get_latest_council_result(self) -> Optional[TitanCouncilResult]:
        """Get the most recent council evaluation result"""
        if not self.titan_council_results:
            return None
        return TitanCouncilResult.from_dict(self.titan_council_results[-1])

    def get_latest_director_output(self) -> Optional[TitanDirectorOutput]:
        """Get the most recent director output"""
        if not self.titan_director_output:
            return None
        return TitanDirectorOutput.from_dict(self.titan_director_output)

    def should_route_to_council(self) -> bool:
        """
        Determine if the current state should route to council evaluation.
        Considers:
        - requires_council_review flag
        - Presence of director output to evaluate
        - Iteration limits
        """
        return (
            self.requires_council_review
            and self.titan_iterations < self.max_titan_iterations
            and (self.titan_director_output is not None or self.titan_context)
        )

    def should_route_to_director(self) -> bool:
        """
        Determine if the current state should route to director generation.
        Considers:
        - requires_director_generation flag
        - Iteration limits
        - Presence of context
        """
        return (
            self.requires_director_generation
            and self.titan_iterations < self.max_titan_iterations
            and bool(self.titan_context)
        )

    def get_titan_summary(self) -> str:
        """
        Generate a human-readable summary of Titan operations.
        Useful for CEO agent decision-making.
        """
        if not self.titan_council_results and not self.titan_director_output:
            return "No Titan operations performed yet."

        summary_parts = [f"Titan Status (Niche: {self.titan_niche}, Iterations: {self.titan_iterations})"]

        # Council summary
        if self.titan_council_results:
            latest = self.get_latest_council_result()
            summary_parts.append(
                f"Council: {latest.verdict} (Score: {latest.final_score}/100, "
                f"Confidence: {latest.confidence:.0%})"
            )
            summary_parts.append(f"Feedback: {latest.feedback}")

        # Director summary
        if self.titan_director_output:
            output = self.get_latest_director_output()
            summary_parts.append(
                f"Director: {output.status} after {output.turns_taken} turns "
                f"(Model: {output.model_used})"
            )

        return " | ".join(summary_parts)


def map_ceo_to_titan(ceo_state: CEOAgentState) -> Dict[str, Any]:
    """
    Map CEOAgentState to Titan-compatible context.
    Extracts relevant business intelligence for creative generation.
    """
    return {
        "business_metrics": ceo_state.business_metrics,
        "analysis_results": ceo_state.analysis_results,
        "past_performance": ceo_state.performance_log,
        "improvement_suggestions": ceo_state.improvement_proposals
    }


def map_titan_to_ceo(titan_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Titan Council results to CEO-readable insights.
    Converts creative evaluation into strategic business intelligence.
    """
    return {
        "creative_quality_score": titan_result.get("final_score", 0),
        "creative_feedback": titan_result.get("feedback", ""),
        "creative_confidence": titan_result.get("confidence", 0),
        "creative_verdict": titan_result.get("verdict", "UNKNOWN")
    }
