# 🚀 LangGraph Quick Start

## ✅ Installation Complete!

LangGraph CLI is installed and the app template has been created.

---

## 📋 Next Steps

### **1. Get LangSmith API Key**

Go to: **https://smith.langchain.com/settings**
- Sign up (free)
- Create a new API key
- Copy the key (starts with `lsv2_pt_...`)

### **2. Create `.env` File**

```bash
cd services/langgraph-app
cp .env.example .env
```

Then edit `.env` and add your API key:
```bash
LANGSMITH_API_KEY=lsv2_pt_your_key_here
```

### **3. Launch the Server**

```bash
langgraph dev
```

The server will start at:
- **API:** http://localhost:2024
- **Docs:** http://localhost:2024/docs
- **Studio UI:** https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

---

## 🔗 Integration with Your Project

### **From Gateway API (TypeScript):**

```typescript
import axios from 'axios';

const langgraphClient = axios.create({
  baseURL: process.env.LANGGRAPH_URL || 'http://localhost:2024',
});

// Call LangGraph agent
const response = await langgraphClient.post('/runs/stream', {
  assistant_id: 'agent',
  input: {
    messages: [{
      role: 'human',
      content: 'Your question here'
    }]
  },
  stream_mode: 'messages-tuple'
});
```

### **From Python Services:**

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

async for chunk in client.runs.stream(
    None,  # Threadless run
    "agent",
    input={
        "messages": [{
            "role": "human",
            "content": "Your question here",
        }],
    },
):
    print(chunk.data)
```

---

## 📁 Project Structure

```
services/langgraph-app/
├── .env.example          # Environment template
├── langgraph.json        # LangGraph configuration
├── pyproject.toml        # Python dependencies
├── README.md             # Documentation
└── src/                  # Your agent code
    └── agent.py          # Main agent implementation
```

---

## 🎯 Use Cases for Your Project

1. **AI Council Integration** - Use LangGraph for advanced decision-making workflows
2. **Video Processing Workflows** - Orchestrate complex video editing pipelines
3. **ML Service Integration** - Enhance ML workflows with LangGraph agents
4. **Multi-Agent Orchestration** - Coordinate multiple AI agents

---

## 📚 Resources

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **LangSmith Studio:** https://smith.langchain.com/studio
- **API Reference:** https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref/

---

**Ready to start! Just add your LangSmith API key and run `langgraph dev`** 🚀

