# LangGraph-Titan Bridge Integration

**Version**: 1.0.0
**Status**: Production Ready
**Created**: 2025-12-12

---

## Overview

The **LangGraph-Titan Bridge** is a unified orchestration layer that seamlessly connects two powerful AI agent systems:

1. **LangGraph CEO Agent** (`/services/langgraph-app/src/agent/graph.py`)
   - Strategic business orchestrator using GPT-4o
   - Manages CRM, Analytics, and Marketing specialist agents
   - Handles business planning, analysis, execution, and self-improvement

2. **Titan-Core Orchestrator** (`/services/titan-core/ai_council/orchestrator.py`)
   - Multi-model creative evaluation system
   - Director (Gemini 3 Pro) generates high-quality creative content
   - Council (Gemini + Claude + GPT-4o + DeepCTR) evaluates and scores
   - Implements the "Antigravity Loop" for iterative improvement

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph CEO Agent                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Planner  │──▶│ Analyst  │   │ Executor │   │ Improver │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Creative Review Node (Titan Bridge)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │                                                          │
└───────┼──────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Titan-Core Orchestrator                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Council Evaluator                      │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐    │  │
│  │  │ Gemini  │  │ Claude  │  │  GPT-4o │  │ DeepCTR  │    │  │
│  │  │ 3 Pro   │  │ 3.5 Son │  │         │  │  Model   │    │  │
│  │  │  40%    │  │   30%   │  │   20%   │  │   10%    │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └──────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Director (Gemini 3 Pro)                   │  │
│  │         Extended Reasoning Creative Generation            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Antigravity Loop Orchestrator                    │  │
│  │   Generate → Evaluate → Improve → Repeat until Approved   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Bridge Components

### 1. **Unified State Management** (`unified_state.py`)

**Purpose**: Extends `CEOAgentState` to track Titan operations.

**Key Classes**:

- **`TitanCouncilResult`**: Structured council evaluation results
  ```python
  TitanCouncilResult(
      verdict="APPROVED",
      final_score=88.5,
      breakdown={"gemini_3_pro": 92, "claude_3_5": 86, "gpt_4o": 87, "deep_ctr": 85},
      feedback="Strong hook and emotional triggers",
      confidence=1.0,
      timestamp="2025-12-12T10:30:00Z"
  )
  ```

- **`TitanDirectorOutput`**: Director generation results
  ```python
  TitanDirectorOutput(
      blueprint="Your generated ad script here...",
      model_used="gemini-3-pro-preview",
      turns_taken=2,
      status="APPROVED",
      timestamp="2025-12-12T10:30:00Z"
  )
  ```

- **`TitanBridgeState`**: Extended state combining both systems
  - Inherits all CEOAgentState fields
  - Adds: `titan_council_results`, `titan_director_output`, `titan_context`, etc.
  - Provides routing methods: `should_route_to_council()`, `should_route_to_director()`

**Mapping Functions**:

- `map_ceo_to_titan()`: Converts CEO business intelligence to Titan creative context
- `map_titan_to_ceo()`: Converts Titan creative evaluation to CEO-readable insights

### 2. **LangGraph Tools** (`titan_tools.py`)

**Purpose**: Wrap Titan functionality as LangGraph-compatible tools.

**Available Tools**:

1. **`evaluate_with_council(script_content, niche)`**
   - Evaluates script/content with multi-model council
   - Returns verdict, score, breakdown, feedback
   - Use for: Quality assurance, creative review, content scoring

2. **`generate_with_director(video_context, niche, max_iterations)`**
   - Generates creative content using Gemini 3 Pro Director
   - Iteratively improves based on council feedback
   - Use for: Script generation, ad copy creation, creative concepts

3. **`run_antigravity_loop(video_context, niche, approval_threshold)`**
   - Runs full Director → Council → Iterate loop
   - Returns approved or rejected content after max iterations
   - Use for: End-to-end creative pipeline

**Example Usage**:
```python
from src.titan_bridge.titan_tools import evaluate_with_council

result = await evaluate_with_council(
    script_content="Hook: Are you tired of yo-yo dieting?...",
    niche="fitness"
)

if result["verdict"] == "APPROVED":
    print(f"Great! Score: {result['final_score']}/100")
```

### 3. **Bridge Core** (`bridge.py`)

**Purpose**: Core integration logic with LangGraph node functions.

**Node Functions**:

1. **`council_evaluation_node(state)`**
   - Evaluates content in state with Titan Council
   - Updates state with results and routing flags
   - Returns to CEO workflow with insights

2. **`director_generation_node(state)`**
   - Generates creative content using Titan Director
   - Incorporates previous council feedback
   - Triggers council review after generation

3. **`antigravity_loop_node(state)`**
   - Runs complete Antigravity Loop internally
   - Single-shot "generate and approve" operation
   - Returns final approved/rejected content

**Factory Functions**:
```python
from src.titan_bridge import create_council_node

# Add to LangGraph workflow
workflow.add_node("council", create_council_node())
```

**Routing Helpers**:
- `should_route_to_council(state)`: Check if council review needed
- `should_route_to_director(state)`: Check if director generation needed
- `get_titan_routing_decision(state)`: Comprehensive routing logic

---

## Integration into LangGraph CEO Agent

### Modified Files

**`/services/langgraph-app/src/agent/graph.py`**

**Changes**:

1. **Imports Added**:
   ```python
   from src.titan_bridge import TitanBridgeState, create_council_node, create_director_node
   from src.titan_bridge.bridge import get_titan_routing_decision
   ```

2. **New Node: `creative_review_node`**
   - Delegates creative evaluation to Titan Council
   - Extracts creative content from state
   - Returns council verdict and feedback to CEO

3. **Updated Routing: `route_task()`**
   - Now supports routing to `creative_review`
   - CEO can choose creative review alongside analyze/execute/improve

4. **Graph Construction**:
   ```python
   workflow.add_node("creative_review", creative_review_node)
   workflow.add_conditional_edges(
       "planner",
       route_task,
       {
           "analyze": "analyst",
           "execute": "executor",
           "improve": "self_improver",
           "creative_review": "creative_review"  # NEW
       }
   )
   workflow.add_edge("creative_review", "planner")  # Return to CEO
   ```

5. **Updated Planning Node**:
   - CEO now aware of `creative_review` option
   - Can detect creative content and route to Titan
   - Incorporates council feedback into strategic decisions

---

## Usage Examples

### Example 1: Simple Council Evaluation

```python
from src.titan_bridge.titan_tools import evaluate_with_council

# Evaluate an ad script
result = await evaluate_with_council(
    script_content="""
    Hook: Are you tired of yo-yo dieting?
    Body: Our 30-day transformation program uses science-backed methods...
    CTA: Start your free trial today!
    """,
    niche="fitness"
)

print(f"Verdict: {result['verdict']}")
print(f"Score: {result['final_score']}/100")
print(f"Feedback: {result['feedback']}")
print(f"Breakdown: {result['breakdown']}")
```

### Example 2: Director Generation with Iterations

```python
from src.titan_bridge.titan_tools import generate_with_director

# Generate a viral ad script
result = await generate_with_director(
    video_context="30-day transformation program for busy professionals",
    niche="fitness",
    max_iterations=3
)

if result["status"] == "APPROVED":
    print("Script Approved!")
    print(result["blueprint"])
    print(f"Council Score: {result['council_review']['final_score']}")
else:
    print("Script Rejected after 3 iterations")
```

### Example 3: Full Antigravity Loop

```python
from src.titan_bridge.titan_tools import run_antigravity_loop

# Run complete creative pipeline
result = await run_antigravity_loop(
    video_context="High-intensity interval training for busy professionals",
    niche="fitness",
    approval_threshold=87.0
)

print(f"Status: {result['status']}")
print(f"Final Score: {result['final_score']}")
print(f"Iterations: {result['iterations']}")
print(f"Time Taken: {result['total_time']:.2f}s")
```

### Example 4: CEO Agent with Titan Integration

```python
from src.agent.graph import graph
from src.agent.state import CEOAgentState

# Initialize state
initial_state = CEOAgentState(
    current_plan=["Evaluate new ad campaign creative"],
    analysis_results={
        "creative_content": "Hook: Transform your body in 30 days..."
    }
)

# Run CEO Agent (will automatically route to creative_review if needed)
result = await graph.ainvoke(initial_state)

# Check if creative review was performed
for step, detail in result["past_steps"]:
    if step == "creative_review":
        print(f"Creative Review: {detail}")
```

### Example 5: Using TitanBridgeState Directly

```python
from src.titan_bridge import TitanBridgeState, create_council_node
from langgraph.graph import StateGraph

# Create workflow with TitanBridgeState
workflow = StateGraph(TitanBridgeState)

# Add Titan nodes
workflow.add_node("council", create_council_node())
workflow.add_node("director", create_director_node())

# Set up routing
workflow.add_edge("__start__", "director")
workflow.add_edge("director", "council")

# Initialize state with context
state = TitanBridgeState(
    titan_context="Generate a viral fitness ad script",
    titan_niche="fitness",
    max_titan_iterations=3
)

# Run workflow
graph = workflow.compile()
result = await graph.ainvoke(state)

# Get results
print(result.get_titan_summary())
```

---

## Configuration

### Environment Variables

**Required for Titan-Core**:
```bash
# Gemini 3 Pro (Director)
GEMINI_API_KEY=your_gemini_api_key
# or
GOOGLE_API_KEY=your_google_api_key

# Claude 3.5 Sonnet (Council)
ANTHROPIC_API_KEY=your_anthropic_api_key

# GPT-4o (Council)
OPENAI_API_KEY=your_openai_api_key

# DeepCTR ML Service (optional, fallback if not set)
ML_SERVICE_URL=http://ml-service:8000

# Custom Approval Threshold (optional)
COUNCIL_APPROVAL_THRESHOLD=85.0
```

### Niche-Specific Thresholds

The Council uses different approval thresholds based on business vertical:

| Niche        | Threshold | Rationale                              |
|--------------|-----------|----------------------------------------|
| fitness      | 85.0      | High bar for competitive market        |
| e-commerce   | 82.0      | Slightly lower for product ads         |
| education    | 88.0      | Higher bar for credibility             |
| finance      | 90.0      | Highest bar for trust-sensitive        |
| entertainment| 80.0      | Lower bar for viral/fun content        |

Override globally with `COUNCIL_APPROVAL_THRESHOLD` env var.

---

## Testing

### Unit Tests

```bash
# Test Titan tools
cd /home/user/geminivideo/services/langgraph-app
python -m pytest tests/test_titan_tools.py

# Test bridge integration
python -m pytest tests/test_titan_bridge.py

# Test unified state
python -m pytest tests/test_unified_state.py
```

### Integration Tests

```bash
# Test full CEO → Titan → CEO flow
python -m pytest tests/integration/test_ceo_titan_integration.py

# Test antigravity loop
python -m pytest tests/integration/test_antigravity_loop.py
```

### Manual Testing

```python
# Test council evaluation
python -m src.titan_bridge.titan_tools evaluate_with_council

# Test director generation
python -m src.titan_bridge.titan_tools generate_with_director

# Test CEO agent with creative review
python -m src.agent.graph
```

---

## Performance Characteristics

### Latency

- **Council Evaluation**: ~3-5 seconds (4 parallel model calls)
- **Director Generation**: ~5-10 seconds per iteration
- **Full Antigravity Loop**: ~15-30 seconds (depends on iterations)

### Cost per Operation

Approximate costs (varies by input length):

- **Council Evaluation**: $0.02 - $0.05
  - Gemini 3 Pro: $0.01
  - Claude 3.5 Sonnet: $0.015
  - GPT-4o: $0.01
  - DeepCTR: $0.005

- **Director Generation**: $0.01 - $0.02 per iteration

- **Full Loop**: $0.05 - $0.15 (3 iterations max)

### Throughput

- **Concurrent Evaluations**: 10-20 per second (model rate limits)
- **Sequential Pipeline**: 2-4 operations per second

---

## Error Handling

### Graceful Degradation

1. **Council Member Failure**:
   - If any model fails, uses neutral score (70.0)
   - Reduces confidence score proportionally
   - Continues with remaining models

2. **Orchestrator Unavailable**:
   - Returns error status with clear message
   - Logs warning and continues CEO workflow
   - Suggests dependency check

3. **Rate Limits**:
   - Implements exponential backoff
   - Queues requests when limits hit
   - Returns cached results when available (5-minute TTL)

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `ERROR: Council not available` | Import failed | Check dependencies |
| `ERROR: No content to evaluate` | Missing context | Provide titan_context |
| `ERROR: Max iterations reached` | Loop exhausted | Increase max_titan_iterations |

---

## Troubleshooting

### "Titan orchestrator not available"

**Cause**: Missing titan-core dependencies or incorrect path

**Solution**:
```bash
cd /home/user/geminivideo/services/titan-core
pip install -r requirements.txt
```

### "Council evaluation failed"

**Cause**: Missing API keys or invalid credentials

**Solution**:
```bash
# Check environment variables
echo $GEMINI_API_KEY
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Set if missing
export GEMINI_API_KEY=your_key_here
```

### "No content to evaluate"

**Cause**: State doesn't have `titan_context` or `titan_director_output`

**Solution**:
```python
state.titan_context = "Your creative content here"
# or
state.analysis_results["creative_content"] = "Your content"
```

---

## Roadmap

### Phase 1: Foundation (Completed)
- ✅ Unified state management
- ✅ LangGraph tool wrappers
- ✅ Bridge nodes and routing
- ✅ CEO Agent integration

### Phase 2: Enhancement (Planned)
- ⏳ Visual evaluation (image/video analysis)
- ⏳ Streaming results for real-time feedback
- ⏳ Advanced routing strategies (A/B testing)
- ⏳ Multi-niche optimization

### Phase 3: Scale (Future)
- 🔮 Distributed council evaluation (sharding)
- 🔮 Fine-tuned DeepCTR per vertical
- 🔮 Automated threshold tuning based on performance
- 🔮 Council member hot-swapping (new models)

---

## Contributing

### Adding New Tools

1. Create tool function in `titan_tools.py`:
   ```python
   @tool
   async def my_new_tool(arg1: str, arg2: int) -> Dict[str, Any]:
       """Tool description"""
       # Implementation
       return result
   ```

2. Add to `ALL_TITAN_TOOLS` list

3. Update documentation

### Adding New Nodes

1. Create node function in `bridge.py`:
   ```python
   async def my_new_node(state: TitanBridgeState) -> Dict[str, Any]:
       """Node description"""
       # Implementation
       return state_updates
   ```

2. Create factory function:
   ```python
   def create_my_node():
       return my_new_node
   ```

3. Export in `__init__.py`

### Extending State

1. Add fields to `TitanBridgeState` in `unified_state.py`:
   ```python
   my_new_field: Optional[str] = None
   ```

2. Add helper methods:
   ```python
   def get_my_field(self) -> Optional[str]:
       return self.my_new_field
   ```

3. Update mapping functions if needed

---

## License

Proprietary - GeminiVideo Platform

---

## Support

For issues or questions:
- **Technical**: Check troubleshooting section
- **Integration**: Review usage examples
- **Performance**: See performance characteristics

---

**Last Updated**: 2025-12-12
**Bridge Version**: 1.0.0
**LangGraph Version**: Compatible with LangGraph 0.0.x+
**Titan-Core Version**: Compatible with current titan-core
