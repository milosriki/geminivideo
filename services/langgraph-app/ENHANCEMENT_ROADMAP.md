# 🎯 LangGraph Agent Enhancement Roadmap

Based on [LangSmith capabilities](https://docs.langchain.com/langsmith/app-development), here's how to enhance your video generation agent:

---

## 🚀 **Phase 1: Basic Video Generation** (Current)

**Status:** ✅ Template ready

**What you have:**
- Basic agent structure
- LangSmith tracing
- Local development setup

**Next:** Customize for video generation

---

## 🎬 **Phase 2: Video Generation Agent**

### **Enhance `src/agent/graph.py`:**

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

class Context(TypedDict):
    """Runtime configuration."""
    platform: str  # "meta", "google", "tiktok"
    duration: int  # Video duration in seconds
    style: str  # Video style

@dataclass
class State:
    """Video generation state."""
    prompt: str
    platform: str = "meta"
    duration: int = 30
    video_url: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None

async def generate_video(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Generate video based on prompt and platform."""
    try:
        # Call your video generation service
        video_url = await call_video_generation_api(
            prompt=state.prompt,
            platform=state.platform,
            duration=state.duration,
            style=runtime.context.get('style', 'default')
        )
        
        return {
            "video_url": video_url,
            "status": "completed",
            "platform": state.platform
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Build the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("generate_video", generate_video)
    .add_edge("__start__", "generate_video")
    .compile(name="Video Generation Agent")
)
```

---

## 👤 **Phase 3: Human-in-the-Loop**

### **Add Review Step:**

```python
@dataclass
class State:
    prompt: str
    video_url: Optional[str] = None
    needs_review: bool = False
    approved: bool = False
    status: str = "pending"

async def request_review(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Request human review of generated video."""
    return {
        "needs_review": True,
        "status": "waiting_for_approval"
    }

async def check_approval(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Check if video was approved."""
    if state.approved:
        return {"status": "approved", "needs_review": False}
    else:
        return {"status": "rejected", "needs_review": False}

# Graph with review
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("generate_video", generate_video)
    .add_node("request_review", request_review)
    .add_node("check_approval", check_approval)
    .add_edge("__start__", "generate_video")
    .add_conditional_edges(
        "generate_video",
        lambda state: "request_review" if state.needs_review else "end"
    )
    .add_edge("request_review", "check_approval")
    .compile(name="Video Generation with Review")
)
```

---

## 📡 **Phase 4: Webhooks & Notifications**

### **Add Webhook Integration:**

```python
import httpx

async def notify_completion(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Send webhook when video is ready."""
    webhook_url = runtime.context.get('webhook_url')
    
    if webhook_url and state.video_url:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={
                "event": "video_generated",
                "video_url": state.video_url,
                "platform": state.platform,
                "status": state.status
            })
    
    return {}

# Add to graph
graph.add_node("notify", notify_completion)
```

---

## ⚡ **Phase 5: Background Jobs & Scheduling**

### **Use Runs API for Background Processing:**

```typescript
// In your Gateway API
import { Client } from "@langchain/langgraph-sdk";

const langgraphClient = new Client({
  apiUrl: process.env.LANGGRAPH_API_URL
});

// Start background video generation
async function generateVideoInBackground(prompt: string, platform: string) {
  const run = await langgraphClient.runs.create(
    null, // No thread (stateless)
    "agent",
    {
      input: {
        prompt,
        platform,
        duration: 30
      }
    }
  );
  
  return run.run_id;
}

// Check status later
async function getVideoStatus(runId: string) {
  const run = await langgraphClient.runs.get(runId);
  return run;
}
```

---

## 🔒 **Phase 6: Concurrency Controls**

### **Limit Concurrent Video Generations:**

```python
from asyncio import Semaphore

# Limit to 3 concurrent generations
video_semaphore = Semaphore(3)

async def generate_video(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    async with video_semaphore:
        # Generate video
        video_url = await call_video_generation_api(...)
        return {"video_url": video_url}
```

---

## 📊 **Phase 7: Advanced Observability**

### **Custom Metrics & Logging:**

```python
import logging

logger = logging.getLogger(__name__)

async def generate_video(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    logger.info(f"Starting video generation: {state.prompt}")
    
    start_time = time.time()
    try:
        video_url = await call_video_generation_api(...)
        duration = time.time() - start_time
        
        logger.info(f"Video generated in {duration}s: {video_url}")
        
        # Custom metrics
        runtime.metrics.record("video_generation_time", duration)
        runtime.metrics.record("video_generation_success", 1)
        
        return {"video_url": video_url, "status": "completed"}
    except Exception as e:
        runtime.metrics.record("video_generation_error", 1)
        logger.error(f"Video generation failed: {e}")
        raise
```

---

## 🎯 **Implementation Priority**

1. **Phase 2** - Basic video generation (Start here)
2. **Phase 4** - Webhooks (Notify Gateway API)
3. **Phase 5** - Background jobs (Better UX)
4. **Phase 3** - Human-in-the-loop (If needed)
5. **Phase 6** - Concurrency (Scale management)
6. **Phase 7** - Advanced observability (Production)

---

## 📚 **Resources**

- **LangSmith Docs:** https://docs.langchain.com/langsmith/app-development
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Your Agent:** `services/langgraph-app/src/agent/graph.py`

---

**Start with Phase 2 to make your agent actually generate videos!** 🚀

