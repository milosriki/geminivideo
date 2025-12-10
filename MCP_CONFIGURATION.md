# 🔗 MCP Server Configuration

## ✅ **Current MCP Servers**

Your `.cursor/mcp.json` is configured with:

### **1. Supabase MCP** ✅
- **Server:** `supabase`
- **URL:** `https://mcp.supabase.com/mcp?project_ref=akhirugwpozlxfvtqmvj&features=account%2Cdocs%2Cdatabase%2Cdebugging%2Cstorage%2Cbranching%2Cfunctions%2Cdevelopment`
- **Features:** Full Supabase integration
- **Status:** ✅ Connected

### **2. LangChain Docs MCP** ✅
- **Server:** `docs-langchain`
- **URL:** `https://docs.langchain.com/mcp`
- **Purpose:** Access LangChain documentation
- **Status:** ✅ Added

---

## 📚 **What You Can Do with LangChain Docs MCP**

### **Access LangChain Documentation:**
- Search LangChain docs
- Get code examples
- Find API references
- Access tutorials and guides

### **Use Cases:**
- Ask questions about LangGraph
- Get code snippets
- Understand concepts
- Find best practices

---

## 🔧 **Configuration File**

**Location:** `.cursor/mcp.json`

**Full Configuration:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp?project_ref=akhirugwpozlxfvtqmvj&features=account%2Cdocs%2Cdatabase%2Cdebugging%2Cstorage%2Cbranching%2Cfunctions%2Cdevelopment"
    },
    "docs-langchain": {
      "url": "https://docs.langchain.com/mcp"
    }
  }
}
```

---

## 🚀 **How to Use**

### **In Cursor:**
1. The MCP servers are automatically available
2. Ask questions about LangChain/LangGraph
3. Get documentation references
4. Access code examples

### **Example Queries:**
- "How do I add human-in-the-loop to my LangGraph agent?"
- "Show me LangGraph streaming examples"
- "What are LangGraph StateGraph best practices?"

---

## 🔄 **Restart Required**

After updating MCP configuration:

1. **Restart Cursor** (recommended)
   - Close and reopen Cursor
   - MCP servers will reconnect automatically

2. **Or wait** - Connection may refresh automatically

---

## ✅ **Verification**

To verify MCP servers are connected:

1. **Check Cursor status** - MCP servers should show as connected
2. **Test queries** - Ask about LangChain/LangGraph
3. **Check responses** - Should include documentation references

---

## 📝 **Additional MCP Servers**

You can add more MCP servers:

```json
{
  "mcpServers": {
    "supabase": { ... },
    "docs-langchain": { ... },
    "another-server": {
      "url": "https://example.com/mcp"
    }
  }
}
```

---

## 🔗 **Resources**

- **LangChain Docs:** https://docs.langchain.com
- **MCP Protocol:** https://modelcontextprotocol.io
- **Your Config:** `.cursor/mcp.json`

---

**Your MCP configuration is updated! Restart Cursor to activate the LangChain docs server.** 🚀

