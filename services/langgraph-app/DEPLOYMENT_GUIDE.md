# 🚀 LangGraph Agent Deployment Guide

## 📍 **Where Is Your Agent?**

**Location:** `services/langgraph-app/`

**Agent File:** `src/agent/graph.py`

**Configuration:** `langgraph.json`

---

## 🤖 **What Your Agent Does**

Your current agent is a **template/starter agent** that:

1. **Receives input** via the `State` class
2. **Processes it** through the `call_model` function
3. **Returns output** with a configurable parameter

**Current Behavior:**
- Takes input: `{"changeme": "example"}`
- Returns: `"output from call_model. Configured with {my_configurable_param}"`

**This is a starter template** - you can customize it for your video generation workflow!

---

## 🚀 **Deployment Options**

### **Option 1: Run Locally (Development/Testing)**

**Start the agent server:**
```bash
cd services/langgraph-app
langgraph dev
```

**Expected Output:**
```
>    Ready!
>
>    - API: [http://localhost:2024](http://localhost:2024/)
>
>    - Docs: http://localhost:2024/docs
>
>    - Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

**Test it:**
```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [{
        "role": "user",
        "content": "Hello!"
      }]
    }
  }'
```

---

### **Option 2: Deploy to LangSmith Cloud (Production)** ⭐ RECOMMENDED

**Prerequisites:**
- ✅ LangSmith API key (you have this!)
- ✅ LangGraph CLI installed

**Deploy Steps:**

1. **Login to LangSmith:**
```bash
langgraph login
```

2. **Deploy your agent:**
```bash
cd services/langgraph-app
langgraph deploy
```

**This will:**
- Upload your agent to LangSmith Cloud
- Create a deployment
- Give you a production API endpoint
- Enable monitoring and tracing

**After deployment, you'll get:**
- Production API URL
- Deployment ID
- Access to LangSmith Studio for monitoring

---

### **Option 3: Deploy to Your Own Infrastructure**

You can also deploy LangGraph Server to:
- **Docker:** Run as a container
- **Cloud Run / AWS Lambda:** Serverless
- **Kubernetes:** For scale

See: https://langchain-ai.github.io/langgraph/concepts/langgraph_server/

---

## 📝 **Quick Start: Deploy Now**

### **Step 1: Test Locally First**
```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo/services/langgraph-app
langgraph dev
```

### **Step 2: Deploy to Cloud**
```bash
langgraph login  # If not already logged in
langgraph deploy
```

---

## 🔧 **Customize Your Agent for Video Generation**

To make your agent useful for video generation, modify `src/agent/graph.py`:

**Example: Video Generation Agent**
```python
@dataclass
class State:
    """Input state for video generation."""
    prompt: str
    platform: str = "meta"
    duration: int = 30

async def generate_video(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Generate video based on prompt."""
    # Your video generation logic here
    return {
        "video_url": "https://...",
        "status": "completed",
        "platform": state.platform
    }
```

---

## 📊 **Monitor Your Agent**

Once deployed, monitor at:
- **LangSmith Studio:** https://smith.langchain.com/studio
- **API Docs:** Your deployment URL + `/docs`
- **Traces:** View all agent runs in LangSmith

---

## ✅ **Current Status**

- ✅ Agent code: `src/agent/graph.py`
- ✅ Configuration: `langgraph.json`
- ✅ Environment: `.env` with LangSmith API key
- ✅ Dependencies: Installed
- ⏳ **Ready to deploy!**

---

## 🎯 **Next Steps**

1. **Test locally:** `langgraph dev`
2. **Deploy to cloud:** `langgraph deploy`
3. **Integrate with your API:** Use the deployment URL in your gateway API
4. **Customize:** Modify the agent for your video workflow

---

**Your agent is ready to deploy!** 🚀

