# 🔍 How to Trace & Monitor Your LangGraph Agent

## 📊 **Tracing Options**

### **Option 1: LangSmith Studio (Recommended)** ⭐

**Your agent is configured for LangSmith tracing!**

**Access:**
1. **Start your agent:**
   ```bash
   cd services/langgraph-app
   langgraph dev
   ```

2. **Open LangSmith Studio:**
   - URL: https://smith.langchain.com/studio
   - Or use the link shown when you start: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

3. **What you'll see:**
   - ✅ All agent runs
   - ✅ Step-by-step execution
   - ✅ Input/output for each node
   - ✅ Performance metrics
   - ✅ Error traces
   - ✅ Timeline visualization

**Your API Key is already set:**
- ✅ `LANGSMITH_API_KEY` in `.env` (configured with your key)
- ✅ Traces will automatically appear in LangSmith

---

### **Option 2: Local API Docs**

**When agent is running:**
- **API Docs:** http://localhost:2024/docs
- **Health Check:** http://localhost:2024/health

**View API endpoints and test directly in browser**

---

### **Option 3: Command Line Monitoring**

**Watch logs in real-time:**
```bash
cd services/langgraph-app
langgraph dev
# All logs appear in terminal
```

**Test and see traces:**
```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [{
        "role": "user",
        "content": "Test message"
      }]
    }
  }'
```

---

## 🚀 **Start Agent & Enable Tracing**

### **Step 1: Start the Agent**
```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo/services/langgraph-app
langgraph dev
```

**Expected Output:**
```
>    Ready!
>
>    - API: http://localhost:2024
>    - Docs: http://localhost:2024/docs
>    - Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### **Step 2: Open LangSmith Studio**
Click the Studio URL or go to: https://smith.langchain.com/studio

### **Step 3: Make a Request**
Send a request to your agent - traces will appear automatically!

---

## 📈 **What You Can Trace**

### **In LangSmith Studio:**
- ✅ **All Runs:** Every agent execution
- ✅ **Graph Visualization:** See the flow
- ✅ **Node Details:** Input/output for each step
- ✅ **Timing:** How long each step takes
- ✅ **Errors:** Full error stack traces
- ✅ **State Changes:** How state evolves
- ✅ **Context:** Runtime configuration

### **Real-time Monitoring:**
- Live updates as agent runs
- Filter by date, status, or search
- Export traces for analysis

---

## 🔧 **Current Configuration**

**Your `.env` file:**
```env
LANGSMITH_API_KEY=lsv2_...your_key_here...
LANGSMITH_PROJECT=new-agent
```

**This means:**
- ✅ All traces go to LangSmith
- ✅ Project: `new-agent`
- ✅ Automatic tracing enabled

---

## ✅ **Check if Agent is Active**

**Run this command:**
```bash
# Check if port 2024 is in use
lsof -ti:2024 && echo "✅ Agent is RUNNING" || echo "❌ Agent is NOT running"
```

**Or test the API:**
```bash
curl http://localhost:2024/health
```

---

## 🎯 **Quick Start: Activate & Trace**

1. **Start agent:**
   ```bash
   cd services/langgraph-app
   langgraph dev
   ```

2. **Open Studio:**
   - Click the Studio URL from terminal output
   - Or go to: https://smith.langchain.com/studio

3. **Make a test request:**
   ```bash
   curl -X POST http://localhost:2024/runs/stream \
     -H "Content-Type: application/json" \
     -d '{"assistant_id": "agent", "input": {"messages": [{"role": "user", "content": "Hello!"}]}}'
   ```

4. **View trace in Studio:**
   - Refresh LangSmith Studio
   - See your run appear in real-time!

---

## 📊 **After Deployment**

When you deploy to production (`langgraph deploy`):
- ✅ Traces still go to LangSmith
- ✅ Monitor production runs
- ✅ Compare local vs production
- ✅ Debug production issues

---

**Your agent is ready for tracing! Just start it with `langgraph dev`** 🚀

