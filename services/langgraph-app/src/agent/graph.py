"""LangGraph multi-agent system with 5 super agents with enhanced thinking.

This is a production-grade agentic AI system with:
- 5 super agents with enhanced thinking capabilities
- LangChain integration
- Comprehensive error handling
- Learning and memory
- Supabase persistence
- Full observability
- Unlimited learning system
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from agent.core.orchestrator import AgentOrchestrator, AgentTask, OrchestrationStrategy
from agent.learning.learning_middleware import learning_middleware
from agent.learning.semantic_search import semantic_search
from agent.execution.execution_tools import EXECUTION_TOOLS
from agent.super_agents import (
    BusinessIntelligenceAgent,
    CreativeIntelligenceAgent,
    DataIntelligenceAgent,
    MLIntelligenceAgent,
    SystemIntelligenceAgent,
    MetaAdsExpertAgent,
    OpenSourceLearnerAgent,
    PsychologyExpertAgent,
    MoneyBusinessExpertAgent,
    VideoScraperAgent,
    SelfHealingAgent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Context(TypedDict, total=False):
    """Context parameters for the agent system.

    Set these when creating assistants OR when invoking the graph.
    """

    user_id: Optional[str]
    campaign_id: Optional[str]
    operation: Optional[str]
    strategy: Optional[str]  # orchestration strategy


@dataclass
class State:
    """Input state for the agent system.

    Defines the structure of incoming data and agent results.
    """

    input_data: Dict[str, Any]
    agent_results: Dict[str, Any] = None
    errors: list = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.agent_results is None:
            self.agent_results = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


# Initialize 11 super agents + expert agents with enhanced thinking
def _initialize_agents() -> Dict[str, Any]:
    """Initialize 11 super agents + expert agents with enhanced thinking capabilities."""
    agents = {
        # Core 5 super agents
        "data_intelligence": DataIntelligenceAgent(),
        "creative_intelligence": CreativeIntelligenceAgent(),
        "business_intelligence": BusinessIntelligenceAgent(),
        "ml_intelligence": MLIntelligenceAgent(),
        "system_intelligence": SystemIntelligenceAgent(),
        # Expert agents
        "meta_ads_expert": MetaAdsExpertAgent(),
        "open_source_learner": OpenSourceLearnerAgent(),
        "psychology_expert": PsychologyExpertAgent(),
        "money_business_expert": MoneyBusinessExpertAgent(),
        "video_scraper": VideoScraperAgent(),
        "self_healing": SelfHealingAgent(),
    }
    logger.info(f"Initialized {len(agents)} super agents + expert agents with enhanced thinking")
    return agents


# Global agent registry
_AGENTS = _initialize_agents()
_ORCHESTRATOR = AgentOrchestrator(
    strategy=OrchestrationStrategy.ADAPTIVE,
    max_concurrent=10,
)

# Register all agents with orchestrator
for name, agent in _AGENTS.items():
    _ORCHESTRATOR.register_agent(agent)


async def orchestrate_agents(
    state: State, runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Orchestrate multiple agents based on input."""
    try:
        input_data = state.input_data
        context = runtime.context or {}
        
        # LEARNING MIDDLEWARE: Load app knowledge before execution
        state_dict = {
            "input_data": input_data,
            "agent_results": state.agent_results or {},
            "errors": state.errors or [],
            "metadata": state.metadata or {},
        }
        state_dict = await learning_middleware.before_agent_execution(state_dict)
        
        # Add semantic search context if available
        if input_data.get("auto_discover", True):
            question = str(input_data.get("operation", ""))
            relevant_context = await semantic_search.get_relevant_context(question)
            if relevant_context:
                state_dict["semantic_context"] = relevant_context
        
        operation = input_data.get("operation", "analyze_campaign")
        strategy_name = context.get("strategy", "adaptive")
        
        # Map strategy string to enum
        strategy_map = {
            "sequential": OrchestrationStrategy.SEQUENTIAL,
            "parallel": OrchestrationStrategy.PARALLEL,
            "pipeline": OrchestrationStrategy.PIPELINE,
            "adaptive": OrchestrationStrategy.ADAPTIVE,
        }
        strategy = strategy_map.get(strategy_name, OrchestrationStrategy.ADAPTIVE)

        # Determine which agents to run based on operation
        tasks = _determine_agent_tasks(operation, input_data, context)

        # Orchestrate agents
        result = await _ORCHESTRATOR.orchestrate(tasks, strategy=strategy)

        # LEARNING MIDDLEWARE: Learn from execution
        for agent_name, agent_result in result.results.items():
            await learning_middleware.after_agent_execution(
                state_dict,
                agent_name,
                agent_result.data if agent_result.success else agent_result.error,
                agent_result.execution_time,
            )

        return {
            "agent_results": result.results,
            "execution_order": result.execution_order,
            "total_time": result.total_time,
            "errors": result.errors,
            "success": result.success,
            "metadata": {
                "strategy": strategy.value,
                "agents_executed": len(result.results),
                "app_knowledge_loaded": "app_knowledge" in state_dict,
            },
        }

    except Exception as e:
        logger.error(f"Orchestration error: {e}", exc_info=True)
        return {
            "agent_results": {},
            "errors": [str(e)],
            "success": False,
        }


def _determine_agent_tasks(
    operation: str, input_data: Dict[str, Any], context: Dict[str, Any]
) -> list[AgentTask]:
    """Determine which super agents to run based on operation.
    
    Optimized for ad problem solving with best agent combinations.
    """
    tasks = []

    # Ad-specific workflows (optimized for ad problems)
    if operation == "create_winning_ad":
        from agent.workflows.ad_workflows import create_winning_ad_workflow
        return create_winning_ad_workflow(input_data)
    
    elif operation == "optimize_underperforming_ad":
        from agent.workflows.ad_workflows import optimize_underperforming_ad_workflow
        return optimize_underperforming_ad_workflow(input_data)
    
    elif operation == "maximize_roas":
        from agent.workflows.ad_workflows import maximize_roas_workflow
        return maximize_roas_workflow(input_data)
    
    elif operation == "fix_low_ctr":
        from agent.workflows.ad_workflows import fix_low_ctr_workflow
        return fix_low_ctr_workflow(input_data)

    elif operation == "analyze_campaign":
        # Campaign analysis - uses multiple super agents with thinking
        tasks.extend([
            AgentTask(
                agent=_AGENTS["data_intelligence"],
                input_data={
                    "operation": "query_database",
                    "problem": f"Analyze campaign {input_data.get('campaign_id')}",
                    "query": "SELECT * FROM campaigns WHERE id = ?",
                },
                priority=1,
            ),
            AgentTask(
                agent=_AGENTS["business_intelligence"],
                input_data={
                    "operation": "optimize_campaign",
                    "problem": f"Optimize campaign {input_data.get('campaign_id')}",
                    "campaign_id": input_data.get("campaign_id"),
                },
                dependencies=["data_intelligence"],
                priority=2,
            ),
            AgentTask(
                agent=_AGENTS["ml_intelligence"],
                input_data={
                    "operation": "predict_performance",
                    "problem": "Predict ROAS for campaign",
                    "ad_data": input_data.get("ad_data", {}),
                },
                dependencies=["business_intelligence"],
                priority=3,
            ),
        ])

    elif operation == "generate_content":
        # Content generation - creative intelligence with thinking
        tasks.extend([
            AgentTask(
                agent=_AGENTS["creative_intelligence"],
                input_data={
                    "operation": "generate_content",
                    "problem": "Generate high-converting ad content",
                    "campaign_data": input_data.get("campaign_data", {}),
                },
                priority=1,
            ),
            AgentTask(
                agent=_AGENTS["system_intelligence"],
                input_data={
                    "operation": "check_security",
                    "problem": "Validate generated content",
                    "content": input_data.get("content", {}),
                },
                dependencies=["creative_intelligence"],
                priority=2,
            ),
        ])

    elif operation == "optimize_budget":
        # Budget optimization - business + ML intelligence
        tasks.extend([
            AgentTask(
                agent=_AGENTS["data_intelligence"],
                input_data={
                    "operation": "monitor_metrics",
                    "problem": "Monitor current performance metrics",
                    "metrics": input_data.get("metrics", {}),
                },
                priority=1,
            ),
            AgentTask(
                agent=_AGENTS["business_intelligence"],
                input_data={
                    "operation": "manage_budget",
                    "problem": "Optimize budget allocation",
                    "ad_states": input_data.get("ad_states", []),
                },
                dependencies=["data_intelligence"],
                priority=2,
            ),
            AgentTask(
                agent=_AGENTS["ml_intelligence"],
                input_data={
                    "operation": "predict_performance",
                    "problem": "Predict performance with new budget",
                    "ad_data": input_data.get("ad_data", {}),
                },
                dependencies=["business_intelligence"],
                priority=3,
            ),
        ])

    elif operation == "full_pipeline":
        # Full pipeline - all super agents with thinking
        tasks.extend([
            AgentTask(
                agent=_AGENTS["creative_intelligence"],
                input_data={
                    "operation": "analyze_video",
                    "problem": "Analyze video content",
                    "video_url": input_data.get("video_url"),
                },
                priority=1,
            ),
            AgentTask(
                agent=_AGENTS["creative_intelligence"],
                input_data={
                    "operation": "generate_content",
                    "problem": "Generate ad script from video",
                    "campaign_data": input_data.get("campaign_data", {}),
                },
                dependencies=["creative_intelligence"],  # Depends on previous video analysis task
                priority=2,
            ),
            AgentTask(
                agent=_AGENTS["ml_intelligence"],
                input_data={
                    "operation": "predict_performance",
                    "problem": "Predict CTR for generated content",
                    "ad_data": input_data.get("ad_data", {}),
                },
                dependencies=["creative_intelligence"],  # Depends on content generation
                priority=3,
            ),
            AgentTask(
                agent=_AGENTS["business_intelligence"],
                input_data={
                    "operation": "optimize_campaign",
                    "problem": "Optimize campaign based on predictions",
                    "campaign_id": input_data.get("campaign_id"),
                },
                dependencies=["ml_intelligence"],  # Depends on ML predictions
                priority=4,
            ),
        ])

    elif operation == "learn_from_meta" or "meta" in operation.lower():
        # Meta Ads learning
        tasks.append(AgentTask(
            agent=_AGENTS["meta_ads_expert"],
            input_data={"operation": "learn_from_meta", **input_data},
            priority=1,
        ))
    elif operation == "scrape_videos" or "scrape" in operation.lower():
        # Video scraping
        tasks.append(AgentTask(
            agent=_AGENTS["video_scraper"],
            input_data={"operation": "scrape_videos", **input_data},
            priority=1,
        ))
    elif operation == "learn_from_web" or "open_source" in operation.lower():
        # Open source learning
        tasks.append(AgentTask(
            agent=_AGENTS["open_source_learner"],
            input_data={"operation": "learn_from_web", **input_data},
            priority=1,
        ))
    elif "psychology" in operation.lower() or "trigger" in operation.lower():
        # Psychology expert
        tasks.append(AgentTask(
            agent=_AGENTS["psychology_expert"],
            input_data={"operation": "analyze_psychology", **input_data},
            priority=1,
        ))
    elif "roi" in operation.lower() or "money" in operation.lower() or "revenue" in operation.lower():
        # Money/Business expert
        tasks.append(AgentTask(
            agent=_AGENTS["money_business_expert"],
            input_data={"operation": "optimize_roi", **input_data},
            priority=1,
        ))
    elif operation == "health_check" or "self_heal" in operation.lower():
        # Self-healing
        tasks.append(AgentTask(
            agent=_AGENTS["self_healing"],
            input_data={"operation": "health_check", **input_data},
            priority=1,
        ))
    else:
        # Default: use appropriate super agent based on operation type
        # Optimized routing for ad problems with best agent combinations
        operation_lower = operation.lower()
        
        # Ad-specific routing (combine agents for better ad problem solving)
        if any(keyword in operation_lower for keyword in ["ad", "ctr", "creative", "hook", "conversion"]):
            # Ad problems: Creative + Psychology (MOST IMPORTANT for ads - 60-70% impact)
            tasks.append(AgentTask(
                agent=_AGENTS["creative_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
            # Always pair with psychology for ad problems
            tasks.append(AgentTask(
                agent=_AGENTS["psychology_expert"],
                input_data={"operation": "apply_triggers", "problem": str(input_data)},
                dependencies=["creative_intelligence"],
                priority=1
            ))
        
        elif any(keyword in operation_lower for keyword in ["roas", "roi", "revenue", "budget", "optimize", "campaign"]):
            # Business problems: Business + ML + Money (for maximum ROAS)
            tasks.append(AgentTask(
                agent=_AGENTS["business_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
            tasks.append(AgentTask(
                agent=_AGENTS["ml_intelligence"],
                input_data={"operation": "predict_performance", "problem": str(input_data)},
                dependencies=["business_intelligence"],
                priority=2
            ))
            if any(keyword in operation_lower for keyword in ["roi", "revenue", "money"]):
                tasks.append(AgentTask(
                    agent=_AGENTS["money_business_expert"],
                    input_data={"operation": "optimize_revenue", "problem": str(input_data)},
                    dependencies=["ml_intelligence"],
                    priority=3
                ))
        
        elif any(keyword in operation_lower for keyword in ["predict", "ml", "model", "pattern"]):
            tasks.append(AgentTask(
                agent=_AGENTS["ml_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
        
        elif any(keyword in operation_lower for keyword in ["data", "database", "query", "analytics", "monitor"]):
            tasks.append(AgentTask(
                agent=_AGENTS["data_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
        
        elif any(keyword in operation_lower for keyword in ["content", "video", "generate", "script"]):
            tasks.append(AgentTask(
                agent=_AGENTS["creative_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
        
        elif any(keyword in operation_lower for keyword in ["meta", "facebook", "ads", "api"]):
            # Meta Ads: Expert + System (platform mastery)
            tasks.append(AgentTask(
                agent=_AGENTS["meta_ads_expert"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))
            tasks.append(AgentTask(
                agent=_AGENTS["system_intelligence"],
                input_data={"operation": "integrate_api", "problem": str(input_data)},
                dependencies=["meta_ads_expert"],
                priority=2
            ))
        
        else:
            tasks.append(AgentTask(
                agent=_AGENTS["system_intelligence"],
                input_data={"operation": operation, "problem": str(input_data)},
                priority=1
            ))

    return tasks


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Main entry point - orchestrates all agents."""
    logger.info(f"Processing request: {state.input_data.get('operation', 'unknown')}")
    
    result = await orchestrate_agents(state, runtime)

    return {
        "changeme": "Multi-agent system executed",
        "results": result,
    }


# Define the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("orchestrate", orchestrate_agents)
    .add_node("call_model", call_model)
    .add_edge("__start__", "orchestrate")
    .add_edge("orchestrate", "call_model")
    .compile(name="11 Super Agents + Expert Agents with Enhanced Thinking")
)
