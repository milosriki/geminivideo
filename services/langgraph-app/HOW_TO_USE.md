# 🚀 How to Use Your LangGraph Agent

## 📍 Quick Start

Your agent is now running and connected to LangSmith Studio! Here's how to use it:

---

## 🎯 Method 1: Using LangSmith Studio (Easiest) ⭐

### Step 1: Configure Assistant (if not done)

1. In LangSmith Studio, go to the **Assistants** sidebar
2. Click on your assistant (e.g., "NEW ASISTANT LANG C... v2")
3. Set:
   - **Assistant ID:** `agent`
   - **My Configurable Param:** `video-generation` (or any value you want)
   - **Recursion limit:** `25`
4. Click **"Save"**

### Step 2: Test Your Agent

1. In the **Input** section at the bottom:
   - **Changeme field:** Enter any text (e.g., `"Hello, test input"`)
2. Click **"Submit"** button
3. Watch the execution in real-time:
   - See the graph execute (`_start_` → `call_model` → `_end_`)
   - View the output in the right panel
   - Check traces and state changes

### Step 3: View Results

- **Output:** You'll see: `"output from call_model. Configured with {your_param_value}"`
- **Traces:** Click on nodes to see input/output for each step
- **State:** See how the state changes through execution

---

## 🔧 Method 2: Using API Calls (Programmatic)

### Test with curl

```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "changeme": "Hello from API!"
    },
    "config": {
      "configurable": {
        "my_configurable_param": "api-test"
      }
    }
  }'
```

### Test with Python

```python
from langgraph_sdk import get_client

# Connect to your local server
client = get_client(url="http://localhost:2024")

# Run the agent
async for chunk in client.runs.stream(
    None,  # Threadless run
    "agent",  # Assistant ID
    input={
        "changeme": "Hello from Python!"
    },
    config={
        "configurable": {
            "my_configurable_param": "python-test"
        }
    }
):
    print(chunk.data)
```

### Test with TypeScript/JavaScript

```typescript
import axios from 'axios';

const langgraphClient = axios.create({
  baseURL: 'http://localhost:2024',
});

const response = await langgraphClient.post('/runs/stream', {
  assistant_id: 'agent',
  input: {
    changeme: 'Hello from TypeScript!'
  },
  config: {
    configurable: {
      my_configurable_param: 'typescript-test'
    }
  }
});

console.log(response.data);
```

---

## 📊 Understanding Your Agent

### Current Behavior

Your agent currently:
1. **Receives input** via the `changeme` field
2. **Processes it** through the `call_model` function
3. **Returns output** with your configurable parameter

**Example Input:**
```json
{
  "changeme": "test input"
}
```

**Example Output:**
```json
{
  "changeme": "output from call_model. Configured with video-generation"
}
```

### Graph Structure

```
_start_ → call_model → _end_
```

- **`_start_`**: Entry point
- **`call_model`**: Your processing function
- **`_end_`**: Exit point

---

## 🎨 Customizing Your Agent

### 1. Change the Configurable Parameter

In LangSmith Studio:
- Edit the assistant configuration
- Change **"My Configurable Param"** to any value
- This affects the output message

### 2. Modify the Input Field

In `src/agent/graph.py`, change the `State` class:

```python
@dataclass
class State:
    changeme: str = "example"
    # Add more fields:
    # user_message: str = ""
    # video_prompt: str = ""
```

### 3. Add More Nodes

Edit `src/agent/graph.py`:

```python
graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_node(another_function)  # Add more nodes
    .add_edge("__start__", "call_model")
    .add_edge("call_model", "another_function")  # Connect nodes
    .add_edge("another_function", "__end__")
    .compile(name="New Graph")
)
```

---

## 🔍 Debugging & Monitoring

### In LangSmith Studio

1. **View Traces:**
   - Click on any node in the graph
   - See input/output for that step
   - Check execution time

2. **View State:**
   - See how state changes between nodes
   - Inspect values at each step

3. **View Logs:**
   - Check the terminal where `langgraph dev` is running
   - See all execution logs

### Check Server Health

```bash
curl http://localhost:2024/health
```

### View API Docs

Open in browser: http://localhost:2024/docs

---

## 🚀 Next Steps

### For Video Generation Project

1. **Add LLM Integration:**
   ```python
   from langchain_openai import ChatOpenAI
   
   llm = ChatOpenAI(model="gpt-4")
   ```

2. **Add Video Generation Logic:**
   - Connect to your video generation service
   - Process video prompts
   - Return video URLs

3. **Add Memory/State Management:**
   - Store conversation history
   - Track video generation requests
   - Manage user sessions

4. **Add Error Handling:**
   - Try/except blocks
   - Validation
   - Retry logic

---

## 📝 Example Use Cases

### 1. Simple Echo Agent (Current)
- Input: `{"changeme": "hello"}`
- Output: `{"changeme": "output from call_model. Configured with video-generation"}`

### 2. Video Prompt Processing (Future)
- Input: `{"video_prompt": "Create a fitness video"}`
- Output: `{"video_url": "https://...", "status": "completed"}`

### 3. Multi-Step Workflow (Future)
- Step 1: Generate script
- Step 2: Generate video
- Step 3: Upload to platform
- Step 4: Return results

---

## 🆘 Troubleshooting

### "Connection failed"
- Make sure `langgraph dev` is running
- Check server is on port 2024: `curl http://localhost:2024/health`

### "Assistant not found"
- Make sure Assistant ID is `agent` (matches `langgraph.json`)

### "No output"
- Check the input format matches your `State` class
- Verify the graph is compiled correctly

### "API key missing"
- Make sure `.env` file has `LANGSMITH_API_KEY`
- Restart the server after adding the key

---

## 📚 Resources

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **LangSmith Studio:** https://smith.langchain.com/studio
- **Your Agent Code:** `services/langgraph-app/src/agent/graph.py`
- **Configuration:** `services/langgraph-app/langgraph.json`

---

## ✅ Quick Test Checklist

- [ ] Server running (`langgraph dev`)
- [ ] Connected to LangSmith Studio
- [ ] Assistant configured (ID: `agent`)
- [ ] Tested with input in Studio
- [ ] Viewed output and traces
- [ ] Tested with API call (optional)

**You're ready to build!** 🎉

