# 🤖 20-Agent Multi-Agent System

## Overview

This is a **production-grade multi-agent system** with 20 specialized AI agents, built with LangGraph and LangChain. Each agent is an expert in its domain, with unlimited learning capabilities and elastic knowledge.

## 🎯 Key Features

- **20 Specialized Agents** - Each agent is a top-level expert in its field
- **LangChain Integration** - Full LangChain support with LLM orchestration
- **Agentic AI** - True agentic patterns with autonomy and learning
- **Comprehensive Error Handling** - Retry logic, error recovery, and resilience
- **Learning & Memory** - Agents learn from every experience
- **Supabase Integration** - Persistent storage for agent memories and executions
- **Full Observability** - Monitoring, metrics, and health checks
- **Multiple Orchestration Strategies** - Sequential, parallel, pipeline, adaptive

## 📋 The 20 Agents

### Core Operations (Agents 1-5)
1. **DatabaseAgent** - Database operations, migrations, optimization
2. **VideoAnalysisAgent** - Video content analysis, scene detection, emotion extraction
3. **MLPredictionAgent** - CTR prediction, ROAS forecasting, ML models
4. **ContentGenerationAgent** - Ad scripts, hooks, creative content
5. **CampaignOptimizationAgent** - Campaign performance optimization

### Analysis & Management (Agents 6-10)
6. **CreativeAnalysisAgent** - Creative performance analysis
7. **BudgetManagementAgent** - Intelligent budget allocation
8. **PerformanceMonitoringAgent** - System and ad performance monitoring
9. **ABTestingAgent** - A/B testing and statistical analysis
10. **AttributionAgent** - Multi-touch attribution and conversion tracking

### Intelligence & Quality (Agents 11-15)
11. **RAGKnowledgeAgent** - Knowledge base management and retrieval
12. **QualityAssuranceAgent** - Quality validation and compliance
13. **IntegrationAgent** - External API integrations (Meta, Google, TikTok)
14. **LearningAgent** - Continuous learning from all experiences
15. **OrchestrationAgent** - Multi-agent workflow coordination

### Infrastructure (Agents 16-20)
16. **ErrorRecoveryAgent** - Error detection and recovery
17. **SecurityAgent** - Security validation and compliance
18. **ScalingAgent** - Performance optimization and scaling
19. **ReportingAgent** - Reports, dashboards, and insights
20. **InnovationAgent** - Research, experimentation, and improvement

## 🚀 Quick Start

### Installation

```bash
cd services/langgraph-app
pip install -e .
```

### Environment Setup

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

### Basic Usage

```python
from agent import graph

# Run a campaign analysis
result = await graph.graph.ainvoke({
    "input_data": {
        "operation": "analyze_campaign",
        "campaign_id": "camp_123",
        "ad_data": {"hook": "test hook"},
    }
})

print(result)
```

### Available Operations

- `analyze_campaign` - Full campaign analysis workflow
- `generate_content` - Content generation with QA
- `optimize_budget` - Budget optimization workflow
- `full_pipeline` - End-to-end video to ad pipeline

## 🏗️ Architecture

### Agent Base Class

All agents inherit from `BaseAgent` which provides:
- LangChain LLM integration
- Error handling with retries
- Learning and memory
- Status tracking
- Performance metrics

### Orchestration

The `AgentOrchestrator` coordinates agents with:
- **Sequential** - One after another
- **Parallel** - All at once (with concurrency limits)
- **Pipeline** - Based on dependencies (topological sort)
- **Adaptive** - Dynamic based on results

### Learning System

Agents learn from:
- Successful executions
- Errors and failures
- Performance patterns
- Best practices

All learnings are stored in Supabase for persistence.

## 📊 Monitoring

### Health Status

```python
from agent.monitoring.observability import observability_manager

health = observability_manager.get_health_status()
print(health)
```

### Agent Metrics

```python
metrics = observability_manager.get_metrics("DatabaseAgent")
print(metrics)
```

## 🧪 Testing

### Run Tests

```bash
pytest tests/
```

### Test Coverage

- Unit tests for individual agents
- Integration tests for workflows
- Error handling tests
- Performance tests

## 🔧 Configuration

### Agent Configuration

Each agent can be configured:

```python
agent = DatabaseAgent(
    max_retries=5,
    retry_delay=2.0,
    enable_learning=True,
)
```

### Orchestration Strategy

```python
from agent.core.orchestrator import OrchestrationStrategy

result = await orchestrator.orchestrate(
    tasks,
    strategy=OrchestrationStrategy.PARALLEL,
)
```

## 📈 Best Practices

### 1. Use Appropriate Operations

Choose the right operation for your use case:
- `analyze_campaign` for campaign analysis
- `generate_content` for content creation
- `optimize_budget` for budget management
- `full_pipeline` for end-to-end workflows

### 2. Error Handling

All agents have built-in error handling, but you should:
- Check `result.success` before using results
- Handle `result.errors` appropriately
- Use retry logic for transient failures

### 3. Learning

Enable learning for agents that benefit:
```python
agent = DatabaseAgent(enable_learning=True)
```

### 4. Monitoring

Monitor agent performance:
```python
metrics = observability_manager.get_metrics()
```

## 🔐 Security

- All agents validate inputs
- SecurityAgent checks for vulnerabilities
- Supabase RLS policies enforced
- API keys stored securely

## 🚀 Deployment

### LangGraph Cloud

```bash
langgraph deploy
```

### Local Development

```bash
langgraph dev
```

## 📚 Documentation

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [Agent Architecture](./docs/ARCHITECTURE.md)
- [API Reference](./docs/API.md)

## 🤝 Contributing

1. Follow the agent patterns in `BaseAgent`
2. Add comprehensive tests
3. Update documentation
4. Ensure error handling

## 📝 License

MIT

---

**Built with ❤️ using LangGraph and LangChain**

