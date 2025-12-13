from typing import Any, Dict, List, Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from src.agent.state import CEOAgentState, Context
from src.agent.tools import ALL_TOOLS
from src.agent.core import llm, get_specialist_llm, PRIMARY_MODEL, FALLBACK_MODEL

# --- LLM Setup ---
# Using GPT-5.1-instant as primary with GPT-4o fallback via base_agent
# The llm instance is imported from core.base_agent with intelligent fallback

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
        SystemMessage(content="You are the CEO of a Fitness Business. Review the current state and plan the next step. Options: 'analyze', 'execute', 'improve'."),
        HumanMessage(content=f"Current Plan: {state.current_plan}\nPast Steps: {state.past_steps}")
    ]
    
    response = await llm.ainvoke(messages)
    plan = response.content
    
    # Simple parsing logic (in production, use structured output)
    next_action = "analyze"
    if "execute" in plan.lower():
        next_action = "execute"
    elif "improve" in plan.lower():
        next_action = "improve"
        
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

# --- Routing Logic ---

def route_task(state: CEOAgentState) -> Literal["analyst", "executor", "self_improver"]:
    return state.active_agent

# --- Graph Construction ---

workflow = StateGraph(CEOAgentState)

workflow.add_node("planner", planning_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("executor", executor_node)
workflow.add_node("self_improver", self_improve_node)

workflow.add_edge("__start__", "planner")

workflow.add_conditional_edges(
    "planner",
    route_task,
    {
        "analyze": "analyst",
        "execute": "executor",
        "improve": "self_improver"
    }
)

workflow.add_edge("analyst", "planner")
workflow.add_edge("executor", "planner")
workflow.add_edge("self_improver", "planner")

# Compile
graph = workflow.compile(name="Fitness CEO Agent")
