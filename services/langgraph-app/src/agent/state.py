from typing import TypedDict, List, Annotated, Dict, Any, Optional
import operator
from dataclasses import dataclass, field

@dataclass
class CEOAgentState:
    """State for the Fitness CEO Agent."""
    messages: Annotated[List[Any], operator.add] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)
    past_steps: Annotated[List[tuple], operator.add] = field(default_factory=list)
    business_metrics: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    active_agent: str = "planner"
    performance_log: List[Dict[str, Any]] = field(default_factory=list)
    improvement_proposals: List[str] = field(default_factory=list)
    
class Context(TypedDict, total=False):
    """Configuration context."""
    account_id: str
