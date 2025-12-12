from typing import Any, Dict, List, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from src.agent.state import CEOAgentState, Context
from src.agent.tools import ALL_TOOLS

# Titan Bridge Integration
from src.titan_bridge import TitanBridgeState, create_council_node, create_director_node
from src.titan_bridge.bridge import get_titan_routing_decision

# --- LLM Setup ---
# Using GPT-4o as the "CEO Brain"
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- Specialist Agents (Sub-Graphs) ---

def create_specialist(name: str, prompt: str, tools: List[Any]):
    """Creates a specialized ReAct agent."""
    return create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=prompt
    )

# 1. CRM Expert
crm_agent = create_specialist(
    "crm_expert",
    "You are a CRM Expert. Analyze client data and sales patterns.",
    [t for t in ALL_TOOLS if "crm" in t.name]
)

# 2. Analytics Expert (RAG + MLOps)
analytics_agent = create_specialist(
    "analytics_expert",
    "You are an Analytics Expert. Use RAG to find winning patterns and check model status.",
    [t for t in ALL_TOOLS if "winning" in t.name or "model" in t.name]
)

# 3. Marketing Expert (Ads + Fatigue)
marketing_agent = create_specialist(
    "marketing_expert",
    "You are a Marketing Expert. Manage ad fatigue and account configuration.",
    [t for t in ALL_TOOLS if "fatigue" in t.name or "account" in t.name]
)

# --- CEO Nodes ---

async def planning_node(state: CEOAgentState):
    """The CEO plans the next strategic move."""
    print("🧠 CEO Planning...")

    messages = [
        SystemMessage(content="""You are the CEO of a Fitness Business. Review the current state and plan the next step.

Options:
- 'analyze': Get CRM/Analytics insights
- 'execute': Run marketing campaigns
- 'improve': Propose new tools/capabilities
- 'creative_review': Evaluate creative content with Titan Council (NEW)

When you see creative content (ad scripts, video concepts) or need creative quality assessment, choose 'creative_review' to leverage multi-model AI evaluation."""),
        HumanMessage(content=f"Current Plan: {state.current_plan}\nPast Steps: {state.past_steps}\n\nAnalysis Results: {state.analysis_results}")
    ]

    response = await llm.ainvoke(messages)
    plan = response.content

    # Simple parsing logic (in production, use structured output)
    next_action = "analyze"
    if "execute" in plan.lower():
        next_action = "execute"
    elif "improve" in plan.lower():
        next_action = "improve"
    elif "creative" in plan.lower() or "review" in plan.lower():
        next_action = "creative_review"

    return {"current_plan": [plan], "active_agent": next_action}

async def analyst_node(state: CEOAgentState):
    """Delegates to Analytics & CRM experts."""
    print("🔍 CEO Analyzing...")
    
    # Call Analytics Expert
    analytics_result = await analytics_agent.ainvoke({"messages": [HumanMessage(content="Analyze current winning patterns.")]})
    
    # Call CRM Expert
    crm_result = await crm_agent.ainvoke({"messages": [HumanMessage(content="Check for hot leads.")]})
    
    combined_insights = {
        "analytics": analytics_result["messages"][-1].content,
        "crm": crm_result["messages"][-1].content
    }
    
    return {
        "analysis_results": combined_insights,
        "past_steps": [("analysis", "completed")]
    }

async def executor_node(state: CEOAgentState):
    """Delegates to Marketing Expert to execute actions."""
    print("⚡ CEO Executing...")
    
    # Call Marketing Expert
    marketing_result = await marketing_agent.ainvoke({"messages": [HumanMessage(content="Check ad fatigue and recommend actions.")]})
    
    return {
        "past_steps": [("execution", marketing_result["messages"][-1].content)]
    }

async def self_improve_node(state: CEOAgentState):
    """Reflects on performance and proposes tool improvements."""
    print("🚀 CEO Self-Improving...")

    proposal = "Proposal: Create a new tool for 'Viral Hook Generation' based on RAG data."

    return {
        "improvement_proposals": [proposal],
        "past_steps": [("improvement", proposal)]
    }

async def creative_review_node(state: CEOAgentState):
    """
    TITAN BRIDGE: Delegates creative review to the Titan Council.

    When the CEO needs to evaluate creative content (ad scripts, video concepts),
    this node routes to the Titan Council for multi-model evaluation.

    Flow:
        CEO detects creative content → creative_review_node → Titan Council →
        Returns with score + feedback → CEO makes strategic decision
    """
    print("🎨 CEO: Requesting Creative Review from Titan Council...")

    # Convert CEOAgentState to TitanBridgeState if needed
    # For now, we'll use the council directly for a simple evaluation

    # Check if there's creative content to review in the current state
    creative_content = None

    # Try to extract creative content from analysis_results
    if hasattr(state, 'analysis_results') and state.analysis_results:
        creative_content = state.analysis_results.get('creative_content', None)

    # If no creative content, create a test scenario
    if not creative_content:
        creative_content = "Sample ad script: Transform your body in 30 days with our proven system."

    # Import and use the Titan Council
    try:
        from src.titan_bridge.titan_tools import evaluate_with_council

        print(f"📝 Evaluating content: {creative_content[:100]}...")
        result = await evaluate_with_council(creative_content, niche="fitness")

        print(f"⚖️ Council Verdict: {result['verdict']} (Score: {result['final_score']}/100)")

        # Map results back to CEO state
        creative_insights = {
            "council_verdict": result['verdict'],
            "council_score": result['final_score'],
            "council_feedback": result['feedback'],
            "council_breakdown": result['breakdown']
        }

        return {
            "analysis_results": {**state.analysis_results, "creative_review": creative_insights},
            "past_steps": [("creative_review", f"Council: {result['verdict']} ({result['final_score']}/100)")]
        }
    except Exception as e:
        print(f"⚠️ Creative review unavailable: {e}")
        return {
            "past_steps": [("creative_review", f"ERROR: {str(e)}")]
        }

# --- Routing Logic ---

def route_task(state: CEOAgentState) -> Literal["analyst", "executor", "self_improver", "creative_review"]:
    """
    Enhanced routing with Titan Bridge support.

    Routes to:
    - analyst: For CRM/Analytics insights
    - executor: For marketing execution
    - self_improver: For tool evolution
    - creative_review: For Titan Council evaluation (NEW)
    """
    # Check if creative review is needed
    # In a real scenario, the CEO planning node would set active_agent = "creative_review"
    # when it detects the need for creative evaluation

    return state.active_agent

# --- Graph Construction ---

workflow = StateGraph(CEOAgentState)

workflow.add_node("planner", planning_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("executor", executor_node)
workflow.add_node("self_improver", self_improve_node)
workflow.add_node("creative_review", creative_review_node)  # NEW: Titan Bridge

workflow.add_edge("__start__", "planner")

workflow.add_conditional_edges(
    "planner",
    route_task,
    {
        "analyze": "analyst",
        "execute": "executor",
        "improve": "self_improver",
        "creative_review": "creative_review"  # NEW: Route to Titan
    }
)

workflow.add_edge("analyst", "planner")
workflow.add_edge("executor", "planner")
workflow.add_edge("self_improver", "planner")
workflow.add_edge("creative_review", "planner")  # NEW: Return to CEO after review

# Compile
graph = workflow.compile(name="Fitness CEO Agent")
