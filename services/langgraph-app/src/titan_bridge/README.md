# Titan Bridge Module

**Version**: 1.0.0
**Status**: Production Ready

---

## What is Titan Bridge?

The **Titan Bridge** is a unified orchestration layer that seamlessly connects:

- **LangGraph CEO Agent** (Strategic Business Intelligence)
- **Titan-Core Orchestrator** (Multi-Model Creative Evaluation)

This enables the CEO Agent to leverage world-class creative evaluation for ad scripts, video concepts, and marketing content through a multi-model AI council.

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from src.titan_bridge.titan_tools import evaluate_with_council

# Evaluate creative content
result = await evaluate_with_council(
    script_content="Your ad script here...",
    niche="fitness"
)

print(f"Score: {result['final_score']}/100")
```

---

## Module Structure

```
titan_bridge/
├── __init__.py              # Package exports and version
├── unified_state.py         # Extended state management
├── titan_tools.py           # LangGraph-compatible tools
├── bridge.py                # Core integration nodes
├── README.md                # This file
└── QUICK_START.md           # Quick start guide
```

---

## Key Components

### 1. Unified State (`unified_state.py`)

**Classes**:
- `TitanCouncilResult`: Structured council evaluation results
- `TitanDirectorOutput`: Director generation outputs
- `TitanBridgeState`: Extended state combining CEO + Titan contexts

**Mapping Functions**:
- `map_ceo_to_titan()`: CEO business intelligence → Titan context
- `map_titan_to_ceo()`: Titan evaluation → CEO insights

### 2. LangGraph Tools (`titan_tools.py`)

**Available Tools**:
- `evaluate_with_council(script, niche)`: Multi-model evaluation
- `generate_with_director(context, niche, iterations)`: Creative generation
- `run_antigravity_loop(context, niche, threshold)`: Full pipeline

**Usage**:
```python
from src.titan_bridge.titan_tools import ALL_TITAN_TOOLS

# Register with agent
agent = create_react_agent(llm, ALL_TITAN_TOOLS)
```

### 3. Bridge Nodes (`bridge.py`)

**Node Functions**:
- `council_evaluation_node(state)`: Evaluate content with council
- `director_generation_node(state)`: Generate content with director
- `antigravity_loop_node(state)`: Run full loop

**Factory Functions**:
```python
from src.titan_bridge import create_council_node

workflow.add_node("council", create_council_node())
```

---

## Integration with CEO Agent

The CEO Agent (`/services/langgraph-app/src/agent/graph.py`) now has:

1. **New Node**: `creative_review_node`
   - Routes creative content to Titan Council
   - Returns evaluation scores and feedback

2. **Enhanced Routing**:
   - CEO can choose `creative_review` action
   - Automatic integration with planning decisions

3. **Updated Planning**:
   - CEO aware of creative review capability
   - Incorporates Titan feedback into strategy

---

## Council Architecture

The Titan Council evaluates content using 4 AI models:

| Model | Weight | Focus Area |
|-------|--------|------------|
| **Gemini 3 Pro** | 40% | Creative reasoning, hook strength |
| **Claude 3.5 Sonnet** | 30% | Psychology, emotional triggers |
| **GPT-4o** | 20% | Logic, structure, coherence |
| **DeepCTR** | 10% | Data-driven CTR predictions |

**Final Score**: Weighted average (0-100)
**Verdict**: APPROVED if score ≥ threshold (85.0 default)

---

## Usage Examples

### Example 1: Simple Evaluation

```python
from src.titan_bridge.titan_tools import evaluate_with_council

result = await evaluate_with_council(
    "Hook: Transform your body in 30 days!",
    "fitness"
)

if result["verdict"] == "APPROVED":
    print("Ready for production!")
```

### Example 2: Generate + Evaluate

```python
from src.titan_bridge.titan_tools import run_antigravity_loop

result = await run_antigravity_loop(
    video_context="30-day fitness challenge",
    niche="fitness",
    approval_threshold=85.0
)

print(result["blueprint"])  # Approved script
```

### Example 3: CEO Integration

```python
from src.agent.graph import graph, CEOAgentState

state = CEOAgentState(
    current_plan=["Evaluate ad creative"],
    analysis_results={"creative_content": "Your script..."}
)

result = await graph.ainvoke(state)
# CEO automatically routes to creative_review if needed
```

---

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Optional
ML_SERVICE_URL=http://ml-service:8000
COUNCIL_APPROVAL_THRESHOLD=85.0
```

### Niche-Specific Thresholds

```python
NICHE_THRESHOLDS = {
    "fitness": 85.0,
    "e-commerce": 82.0,
    "education": 88.0,
    "finance": 90.0,
    "entertainment": 80.0
}
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/test_titan_bridge.py

# Integration tests
pytest tests/integration/

# Run examples
python -m examples.titan_bridge_examples example1
```

### Manual Testing

```python
# Test council
from src.titan_bridge.titan_tools import evaluate_with_council
result = await evaluate_with_council("Test script", "fitness")
print(result)

# Test director
from src.titan_bridge.titan_tools import generate_with_director
result = await generate_with_director("Test context", "fitness")
print(result)
```

---

## Performance

### Latency
- Council evaluation: ~3-5 seconds
- Director generation: ~5-10 seconds per iteration
- Full loop: ~15-30 seconds (3 iterations max)

### Cost (per operation)
- Council evaluation: $0.02 - $0.05
- Director generation: $0.01 - $0.02 per iteration
- Full loop: $0.05 - $0.15

### Throughput
- Concurrent evaluations: 10-20/second
- Sequential pipeline: 2-4 operations/second

---

## Error Handling

### Graceful Degradation

1. **Model Failure**: Uses neutral score (70.0), reduces confidence
2. **Service Unavailable**: Returns error status, continues workflow
3. **Rate Limits**: Implements backoff, queues requests

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Council not available | Import failed | Check dependencies |
| No content to evaluate | Missing context | Set titan_context |
| Max iterations reached | Loop exhausted | Increase max_iterations |

---

## Advanced Usage

### Custom Workflows

```python
from langgraph.graph import StateGraph
from src.titan_bridge import TitanBridgeState, create_council_node

# Create custom workflow
workflow = StateGraph(TitanBridgeState)
workflow.add_node("council", create_council_node())
# Add more nodes...

graph = workflow.compile()
```

### Batch Operations

```python
# Evaluate multiple scripts in parallel
scripts = ["Script 1", "Script 2", "Script 3"]
tasks = [evaluate_with_council(s, "fitness") for s in scripts]
results = await asyncio.gather(*tasks)
```

### Custom Routing

```python
from src.titan_bridge.bridge import get_titan_routing_decision

def my_router(state):
    decision = get_titan_routing_decision(state)
    # Add custom logic
    return decision
```

---

## Documentation

- **Full Guide**: `/services/langgraph-app/TITAN_BRIDGE_INTEGRATION.md`
- **Quick Start**: `QUICK_START.md`
- **Examples**: `/services/langgraph-app/examples/titan_bridge_examples.py`
- **API Reference**: See docstrings in source files

---

## Troubleshooting

### "Import Error: titan-core not found"

```bash
cd /home/user/geminivideo/services/titan-core
pip install -r requirements.txt
```

### "Missing API keys"

```bash
export GEMINI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key
```

### "No content to evaluate"

```python
state.titan_context = "Your content here"
# or
state.analysis_results["creative_content"] = "Your content"
```

---

## Contributing

### Adding New Tools

1. Create function in `titan_tools.py` with `@tool` decorator
2. Add to `ALL_TITAN_TOOLS` list
3. Update documentation

### Adding New Nodes

1. Create node function in `bridge.py`
2. Create factory function
3. Export in `__init__.py`

### Extending State

1. Add fields to `TitanBridgeState` in `unified_state.py`
2. Add helper methods
3. Update mapping functions

---

## Roadmap

### Current (v1.0.0)
- ✅ Unified state management
- ✅ LangGraph tool wrappers
- ✅ CEO Agent integration
- ✅ Multi-model evaluation

### Planned (v1.1.0)
- ⏳ Visual content evaluation
- ⏳ Streaming results
- ⏳ Advanced routing strategies
- ⏳ A/B testing support

### Future (v2.0.0)
- 🔮 Distributed evaluation
- 🔮 Fine-tuned niche models
- 🔮 Automated threshold tuning
- 🔮 Hot-swappable council members

---

## License

Proprietary - GeminiVideo Platform

---

## Support

- **Documentation**: See full guide in `TITAN_BRIDGE_INTEGRATION.md`
- **Examples**: Run `python -m examples.titan_bridge_examples`
- **Tests**: Run `pytest tests/`

---

**Built with ❤️ for the GeminiVideo Platform**
