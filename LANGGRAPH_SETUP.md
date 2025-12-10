# 🚀 LangGraph Setup Guide

## 📋 Prerequisites

1. **LangSmith API Key** - Get from: https://smith.langchain.com/settings
2. **Node.js** (for Node server) or **Python 3.11+** (for Python server)

---

## 🎯 Installation Options

### **Option 1: Node.js Server (Recommended for this project)**

Since you have a TypeScript/Node.js gateway-api, this integrates well:

```bash
# Install LangGraph CLI globally
npm install -g @langchain/langgraph-cli

# Or use npx (no global install needed)
npx @langchain/langgraph-cli
```

### **Option 2: Python Server**

If you prefer Python (you have Python services):

```bash
# Python >= 3.11 is required
pip install -U "langgraph-cli[inmem]"
```

---

## 📦 Setup Steps

### **Step 1: Create LangGraph App**

**Node.js:**
```bash
npx @langchain/langgraph-cli new services/langgraph-app --template new-langgraph-project-js
```

**Python:**
```bash
langgraph new services/langgraph-app --template new-langgraph-project-python
```

### **Step 2: Install Dependencies**

**Node.js:**
```bash
cd services/langgraph-app
yarn install
```

**Python:**
```bash
cd services/langgraph-app
pip install -e .
```

### **Step 3: Configure Environment**

Create `.env` file in `services/langgraph-app/`:

```bash
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

### **Step 4: Launch Server**

**Node.js:**
```bash
npx @langchain/langgraph-cli dev
```

**Python:**
```bash
langgraph dev
```

Server will start at: `http://localhost:2024`

---

## 🔗 Integration with Your Project

### **Option A: Standalone Service**

Keep LangGraph as a separate service and call it from gateway-api:

```typescript
// In gateway-api/src/index.ts
import axios from 'axios';

const langgraphClient = axios.create({
  baseURL: process.env.LANGGRAPH_URL || 'http://localhost:2024',
});
```

### **Option B: Embedded in Gateway API**

Integrate LangGraph directly into your gateway-api service.

---

## 📝 Next Steps

1. Get LangSmith API key from: https://smith.langchain.com/settings
2. Choose Node.js or Python server
3. Run the setup commands above
4. Test the API

---

**Ready to start? Let me know which option you prefer (Node.js or Python)!** 🚀

