# 🔗 Connect LangSmith Studio to Your Local Agent

Based on the [LangSmith Studio Quickstart](https://docs.langchain.com/langsmith/quick-start-studio#local-development-server), here's how to connect Studio to your running agent:

---

## 🚀 **Step-by-Step Connection**

### **Step 1: Start Your Local Agent Server**

```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo/services/langgraph-app
langgraph dev
```

**Expected Output:**
```
>    Ready!
>
>    - API: http://localhost:2024
>
>    - Docs: http://localhost:2024/docs
>
>    - LangSmith Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

**Keep this terminal running!** The server must stay active.

---

### **Step 2: Connect Studio**

You have **3 ways** to connect:

#### **Option A: Direct URL (Easiest)** ⭐

**Just click the Studio URL from the terminal output:**
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

This automatically connects Studio to your local server!

---

#### **Option B: Via LangSmith UI**

1. **Go to:** https://smith.langchain.com
2. **Navigate to:** **Deployments** in the left sidebar
3. **Click:** **Studio** button (or "Connect to local server")
4. **Enter Base URL:** `http://127.0.0.1:2024`
5. **Click:** **Connect**

---

#### **Option C: Manual Connection**

1. **Go to:** https://smith.langchain.com/studio
2. **Click:** "Connect to local server" button
3. **In the modal:**
   - **Base URL:** `http://127.0.0.1:2024` (or `http://localhost:2024`)
   - **Custom Headers:** (Optional - leave empty for now)
4. **Click:** **Connect**

---

## 🔧 **Connection Settings**

### **Base URL Options:**

- `http://127.0.0.1:2024` ✅ (Recommended)
- `http://localhost:2024` ✅ (Also works)

**Both point to the same local server!**

### **Custom Headers (Optional):**

If you need authentication or custom headers:
- Click **"+ Custom Header"**
- Enter header name (e.g., `Authorization`)
- Enter header value (e.g., `Bearer your-token`)
- Headers are stored locally in your browser

---

## 🌐 **Safari Browser Issue**

**If using Safari:**

Safari blocks `localhost` connections. Use the `--tunnel` flag:

```bash
langgraph dev --tunnel
```

This creates a secure tunnel (via Cloudflare) so Safari can connect.

---

## ✅ **Verify Connection**

Once connected, you should see:

1. **Graph Visualization:**
   - Your agent's graph structure
   - Nodes: `__start__`, `call_model`, `__end__`
   - Arrows showing flow

2. **Studio Interface:**
   - Left sidebar with Studio tools
   - Graph editor in center
   - Properties panel on right

3. **Test It:**
   - Send a test message
   - See it execute in real-time
   - View traces and state changes

---

## 🔍 **What You Can Do in Studio**

### **1. Visualize Your Agent**
- See the graph structure
- Understand the flow
- Identify nodes and edges

### **2. Test & Debug**
- Send test inputs
- Step through execution
- View state at each step
- See errors and logs

### **3. Edit & Iterate**
- Modify prompts
- Adjust configuration
- Test changes immediately
- Hot reload (changes apply automatically)

### **4. Monitor Traces**
- See all agent runs
- View execution timeline
- Debug issues
- Analyze performance

---

## 🐛 **Troubleshooting**

### **"Cannot connect to server"**

**Check:**
1. ✅ Is `langgraph dev` running?
2. ✅ Is the server on port 2024?
3. ✅ Try `http://127.0.0.1:2024` instead of `localhost`
4. ✅ Check firewall settings

### **"Connection refused"**

**Solution:**
```bash
# Make sure server is running
cd services/langgraph-app
langgraph dev

# Verify it's listening
curl http://localhost:2024/health
```

### **Safari Issues**

**Solution:**
```bash
langgraph dev --tunnel
```

---

## 📊 **Disable Tracing (Optional)**

If you don't want data sent to LangSmith:

**Edit `.env` file:**
```env
LANGSMITH_TRACING=false
```

**Note:** With tracing disabled, Studio still works locally, but no data leaves your machine.

---

## 🎯 **Quick Start Commands**

```bash
# 1. Start agent
cd services/langgraph-app
langgraph dev

# 2. Open Studio (click the URL from terminal, or):
# https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

# 3. Test connection
curl http://localhost:2024/health
```

---

## 🔗 **Useful Links**

- **Studio:** https://smith.langchain.com/studio
- **Docs:** https://docs.langchain.com/langsmith/quick-start-studio#local-development-server
- **Your Agent:** `services/langgraph-app/`

---

## ✅ **Summary**

1. **Start:** `langgraph dev` (in `services/langgraph-app/`)
2. **Connect:** Click the Studio URL from terminal output
3. **Or:** Go to https://smith.langchain.com/studio and enter `http://127.0.0.1:2024`
4. **Use:** Visualize, test, debug, and iterate on your agent!

**Your agent is ready to connect to Studio!** 🚀

