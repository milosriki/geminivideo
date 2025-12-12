# Titan Bridge Quick Start Guide

Get started with the LangGraph-Titan Bridge in 5 minutes.

---

## Installation

### 1. Install Dependencies

```bash
# LangGraph dependencies
cd /home/user/geminivideo/services/langgraph-app
pip install -r requirements.txt

# Titan-Core dependencies
cd /home/user/geminivideo/services/titan-core
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Create .env file
cat > /home/user/geminivideo/.env << EOF
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
ML_SERVICE_URL=http://localhost:8000
EOF

# Load environment
source /home/user/geminivideo/.env
```

---

## Basic Usage

### Option 1: Use as LangGraph Tools

```python
from src.titan_bridge.titan_tools import evaluate_with_council

# Evaluate creative content
result = await evaluate_with_council(
    script_content="Hook: Transform your body in 30 days!",
    niche="fitness"
)

print(f"Verdict: {result['verdict']}")
print(f"Score: {result['final_score']}/100")
```

### Option 2: Add to Existing CEO Agent

The CEO Agent already has the bridge integrated! Just run it:

```python
from src.agent.graph import graph
from src.agent.state import CEOAgentState

state = CEOAgentState(
    current_plan=["Review creative content"],
    analysis_results={
        "creative_content": "Your ad script here..."
    }
)

result = await graph.ainvoke(state)
```

### Option 3: Use Titan Bridge State Directly

```python
from src.titan_bridge import TitanBridgeState, create_council_node
from langgraph.graph import StateGraph

# Create workflow
workflow = StateGraph(TitanBridgeState)
workflow.add_node("council", create_council_node())
workflow.add_edge("__start__", "council")

# Run
graph = workflow.compile()
state = TitanBridgeState(
    titan_context="Generate viral fitness ad",
    titan_niche="fitness"
)
result = await graph.ainvoke(state)
```

---

## Common Patterns

### Pattern 1: Evaluate Existing Content

```python
from src.titan_bridge.titan_tools import evaluate_with_council

async def evaluate_my_script():
    script = """
    Hook: Tired of boring workouts?
    Body: Our AI-powered fitness app adapts to YOUR body...
    CTA: Download now and get 30 days free!
    """

    result = await evaluate_with_council(script, "fitness")

    if result["final_score"] >= 85:
        print("Ready to publish!")
    else:
        print(f"Needs work: {result['feedback']}")
```

### Pattern 2: Generate + Evaluate Loop

```python
from src.titan_bridge.titan_tools import run_antigravity_loop

async def create_approved_ad():
    result = await run_antigravity_loop(
        video_context="30-day body transformation challenge",
        niche="fitness",
        approval_threshold=85.0
    )

    if result["status"] == "APPROVED":
        return result["blueprint"]
    else:
        raise Exception("Could not generate approved content")
```

### Pattern 3: Custom CEO Workflow

```python
from src.agent.graph import workflow
from src.titan_bridge import create_council_node

# Add custom node that calls Titan
async def my_creative_node(state):
    # Your custom logic here
    # Then delegate to Titan
    from src.titan_bridge.bridge import council_evaluation_node
    return await council_evaluation_node(state)

# Add to workflow
workflow.add_node("my_creative_review", my_creative_node)
```

---

## Testing

### Test Council Connection

```python
import asyncio
from src.titan_bridge.titan_tools import evaluate_with_council

async def test_council():
    result = await evaluate_with_council(
        "Test script: Buy now!",
        "fitness"
    )
    print("Council is working!" if result["final_score"] > 0 else "Error!")

asyncio.run(test_council())
```

### Test Director Connection

```python
import asyncio
from src.titan_bridge.titan_tools import generate_with_director

async def test_director():
    result = await generate_with_director(
        "Test: Create a fitness ad",
        "fitness",
        max_iterations=1
    )
    print("Director is working!" if result["blueprint"] else "Error!")

asyncio.run(test_director())
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.titan_bridge")
logger.setLevel(logging.DEBUG)
```

### Check State

```python
from src.titan_bridge import TitanBridgeState

state = TitanBridgeState()
print(f"Should route to council? {state.should_route_to_council()}")
print(f"Should route to director? {state.should_route_to_director()}")
print(f"Titan summary: {state.get_titan_summary()}")
```

---

## Next Steps

1. Read the full documentation: `TITAN_BRIDGE_INTEGRATION.md`
2. Explore example workflows: `examples/titan_bridge_examples.py`
3. Run integration tests: `pytest tests/integration/`
4. Customize for your use case

---

## Need Help?

- Check the troubleshooting section in main docs
- Review error codes and solutions
- Run tests to verify setup

**Happy Building!** 🚀
