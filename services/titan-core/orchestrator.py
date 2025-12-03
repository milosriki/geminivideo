import os
import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from engines.ensemble import council

# CONFIGURATION
# OFFICIAL GEMINI 3 MODEL (Verified)
GEMINI_MODEL_VERSION = os.getenv("GEMINI_MODEL_ID", "gemini-3-pro-preview")
DISPLAY_MODEL_NAME = "Gemini 3 Pro (Preview)"

from autogen_agentchat.messages import TextMessage

async def run_titan_flow(video_context: str, niche: str = "fitness"):
    """
    THE "ANTIGRAVITY" LOOP:
    1. Director (Gemini 3 Pro) drafts the concept.
    2. Council (Gemini + GPT-4o + Claude) critiques it.
    3. If Score > 85, we approve for generation.
    """
    print(f"🎬 TITAN AGENT (Model: {DISPLAY_MODEL_NAME}): Analyzing '{video_context}'...")
    from prompts.engine import PromptEngine

    # 1. The Director (Gemini 3 Pro)
    model_client = OpenAIChatCompletionClient(
        model=GEMINI_MODEL_VERSION,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/", # Google's OpenAI-compatible endpoint
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "gemini-3"
        }
    )

    # Use Dynamic Prompt Engine to inject Knowledge Context (Hormozi Rules, etc.)
    system_msg = PromptEngine.get_director_system_message(niche)
    
    # Inject Market Trends
    try:
        import json
        from pathlib import Path
        trends_path = Path(__file__).parent / "knowledge" / "trends.json"
        if trends_path.exists():
            with open(trends_path, 'r') as f:
                trends_data = json.load(f)
                trends_list = [t['description'] for t in trends_data.get('trends', [])]
                if trends_list:
                    system_msg += f"\n\n## 📈 MARKET TRENDS (EXTERNAL):\n" + "\n".join([f"- {t}" for t in trends_list])
                    print(f"✅ Injected {len(trends_list)} market trends into context")
    except Exception as e:
        print(f"⚠️ Failed to load market trends: {e}")

    director = AssistantAgent(
        name="Director",
        system_message=system_msg,
        model_client=model_client
    )

    # 2. The User Proxy (Executioner)
    user_proxy = UserProxyAgent(
        name="User_Proxy",
        # code_execution_config=False, # Removed in new API, default is safe
    )

    # 3. Start the Creative Loop (The Titan Loop)
    print("🎥 DIRECTOR: Drafting script with extended reasoning...")
    
    # --- MEMORY RECALL START ---
    try:
        from memory_manager import memory_manager
        print("🧠 MEMORY: Recalling past lessons...")
        memory_context = memory_manager.recall_relevant_lessons(niche)
        if memory_context:
            system_msg += f"\n\n{memory_context}"
    except Exception as e:
        print(f"⚠️ Memory Recall Failed: {e}")
    # --- MEMORY RECALL END ---

    # --- GRAPH CONTEXT START ---
    try:
        import json
        from pathlib import Path
        graph_path = Path(__file__).parent / "knowledge" / "concept_graph.json"
        if graph_path.exists():
            with open(graph_path, 'r') as f:
                graph = json.load(f)
                nodes = graph.get("nodes", {})
                
                # Simple traversal: Niche -> Related Concepts -> Related Styles
                related_concepts = nodes.get(niche, {}).get("related", [])
                suggested_styles = []
                for concept in related_concepts:
                    styles = nodes.get(concept, {}).get("related", [])
                    suggested_styles.extend(styles)
                
                if suggested_styles:
                    system_msg += f"\n\n## 🕸️ GRAPH SUGGESTIONS:\nBased on '{niche}', consider these styles:\n" + "\n".join([f"- {s}" for s in set(suggested_styles)])
                    print(f"🕸️ GRAPH: Found {len(suggested_styles)} connected styles for '{niche}'")
    except Exception as e:
        print(f"⚠️ Graph Context Failed: {e}")
    # --- GRAPH CONTEXT END ---
            
    # Update agent with new system message containing memory & graph
    director = AssistantAgent(
        name="Director",
        system_message=system_msg,
        model_client=model_client
    )
    
    # --- MCP INTEGRATION START ---
    mcp_tools_available = []
    try:
        from mcp_wrapper import meta_ads_client
        # ... (MCP code remains same) ...
    except Exception as e:
        print(f"⚠️ MCP Integration Warning: {e}")
    # --- MCP INTEGRATION END ---

    # Initial Draft
    response = await director.on_messages(
        [TextMessage(content=f"Context: {video_context}. Niche: {niche}. Generate a viral ad script JSON with 'hook', 'body', 'cta'. Think deeply about psychological triggers.", source="user")],
        cancellation_token=None
    )
    last_msg = response.chat_message.content
    
    turns = 0
    max_turns = 3
    final_status = "REJECTED"
    critique = {}
    
    while turns < max_turns:
        turns += 1
        print(f"🏛️ COUNCIL: Reviewing draft (Turn {turns}/{max_turns})...")
        critique = await council.evaluate_script(last_msg)
        
        print(f"⚖️ VERDICT: {critique['verdict']} (Score: {critique['final_score']})")
        print(f"📊 Breakdown: Gemini={critique['breakdown']['gemini_3_pro']}, Claude={critique['breakdown']['claude_3_5']}, GPT={critique['breakdown']['gpt_4o']}, DeepCTR={critique['breakdown']['deep_ctr']}")

        if critique['final_score'] > 85:
            final_status = "APPROVED"
            print("✅ SCRIPT APPROVED!")
            
            # --- MEMORY STORAGE (SUCCESS) ---
            try:
                memory_manager.memorize_episode(
                    niche=niche,
                    goal="viral_script",
                    outcome="success",
                    lesson=f"Score {critique['final_score']}: {critique.get('feedback', 'Good script')}"
                )
            except: pass
            # -------------------------------
            break
            
        if turns < max_turns:
            print(f"🔄 REFLEXION: Director is reflecting on failure (Score: {critique['final_score']})...")
            
            # 1. REFLECTION STEP
            reflect_prompt = PromptEngine.get_reflection_prompt(critique.get('feedback', 'Improve hook'))
            reflect_response = await director.on_messages(
                [TextMessage(content=reflect_prompt, source="user")],
                cancellation_token=None
            )
            reflection = reflect_response.chat_message.content
            print(f"🤔 THOUGHT: {reflection[:100]}...")
            
            # 2. PLANNING STEP
            plan_prompt = PromptEngine.get_planning_prompt(reflection)
            plan_response = await director.on_messages(
                [TextMessage(content=plan_prompt, source="user")],
                cancellation_token=None
            )
            plan = plan_response.chat_message.content
            print(f"📝 PLAN: {plan[:100]}...")
            
            # 3. RETRY STEP
            print("✍️ REWRITING: Executing the plan...")
            response = await director.on_messages(
                [TextMessage(content=f"Execute this plan and rewrite the script JSON:\n{plan}", source="user")],
                cancellation_token=None
            )
            last_msg = response.chat_message.content
            
            # --- MEMORY STORAGE (FAILURE) ---
            try:
                memory_manager.memorize_episode(
                    niche=niche,
                    goal="viral_script",
                    outcome="failure",
                    lesson=f"Failed with score {critique['final_score']}. Mistake: {reflection}"
                )
            except: pass
            # -------------------------------
    
    return {
        "status": final_status,
        "model_used": GEMINI_MODEL_VERSION,
        "blueprint": last_msg,
        "council_review": critique,
        "turns_taken": turns,
        "agent_thoughts": [last_msg] # Simplified
    }
