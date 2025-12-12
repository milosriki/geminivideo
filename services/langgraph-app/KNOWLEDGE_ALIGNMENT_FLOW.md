# 🧠 Knowledge, Alignment & Flow - Complete Guide

## 📊 Current Agent System

### **11 Total Agents**

#### **5 Core Super Agents** (Enhanced Thinking)
1. **DataIntelligenceAgent** 🗄️
   - Database Management
   - Analytics
   - Performance Monitoring
   - Query Optimization

2. **CreativeIntelligenceAgent** 🎨
   - Content Generation
   - Video Analysis
   - Creative Strategy
   - Psychological Triggers

3. **BusinessIntelligenceAgent** 💼
   - Campaign Optimization
   - Budget Management
   - ROI Analysis
   - A/B Testing

4. **MLIntelligenceAgent** 🤖
   - Predictions (CTR, ROAS)
   - Model Optimization
   - Pattern Recognition
   - Continuous Learning

5. **SystemIntelligenceAgent** ⚙️
   - API Integrations
   - Security
   - Error Recovery
   - System Optimization

#### **6 Expert Agents** (Specialized)
6. **MetaAdsExpertAgent** 📱
   - Meta Ads API expertise
   - Campaign management
   - Ad optimization

7. **OpenSourceLearnerAgent** 📚
   - Learning from open source
   - Code analysis
   - Best practices

8. **PsychologyExpertAgent** 🧠
   - Psychological triggers
   - Consumer behavior
   - Persuasion techniques

9. **MoneyBusinessExpertAgent** 💰
   - Business strategy
   - Financial analysis
   - Revenue optimization

10. **VideoScraperAgent** 🎬
    - Video content scraping
    - Content analysis
    - Trend detection

11. **SelfHealingAgent** 🔧
    - System self-repair
    - Error recovery
    - Auto-optimization

---

## 🧠 Knowledge System Setup

### **1. Auto-Discovery System**

**Location:** `src/agent/learning/auto_discover.py`

**What it does:**
- Automatically discovers ALL database tables (no hardcoding!)
- Discovers ALL database functions
- Finds recent data patterns
- Discovers table relationships
- Saves to `agent_memory` table

**How it works:**
```python
# Runs automatically or on demand
knowledge = await auto_discovery.discover_app_structure()

# Returns:
{
    "tables": [...],           # All tables discovered
    "functions": [...],         # All functions discovered
    "recent_patterns": {...},   # Data patterns
    "relationships": [...]      # Table relationships
}
```

**When it runs:**
- Hourly (background learner)
- Before agent execution (if cache expired)
- On demand (when requested)

---

### **2. Learning Middleware**

**Location:** `src/agent/learning/learning_middleware.py`

**What it does:**
- Loads app knowledge BEFORE every agent execution
- Learns from every interaction AFTER execution
- Extracts patterns automatically
- Updates agent memory continuously

**Flow:**
```
BEFORE Execution:
1. Load cached app structure OR discover fresh
2. Add knowledge to agent context
3. Add semantic search results (if available)

AFTER Execution:
1. Save interaction to agent_memory
2. Extract patterns from result
3. Update agent-specific memory
4. Learn from success/failure
```

**Integration:**
- Automatically integrated in `graph.py`
- Runs transparently for all agents
- No manual intervention needed

---

### **3. Semantic Search**

**Location:** `src/agent/learning/semantic_search.py`

**What it does:**
- Searches past learning semantically
- Finds relevant context for questions
- Uses vector embeddings (when available)
- Falls back to text search

**How it works:**
```python
# Search past learning
memories = await semantic_search.search_memories("campaign optimization", limit=5)

# Get relevant context
context = await semantic_search.get_relevant_context("How to optimize campaigns?")
```

**Storage:**
- All interactions saved to `agent_memory` table
- Vector embeddings stored (when OpenAI available)
- Semantic search function in database

---

### **4. Background Learner**

**Location:** `src/agent/learning/background_learner.py`

**What it does:**
- Runs continuously (hourly by default)
- Rediscover app structure automatically
- Learns from recent changes
- Extracts patterns

**Flow:**
```
Every Hour:
1. Rediscover all tables/functions
2. Find recent changes (last 24 hours)
3. Extract patterns from changes
4. Save to agent_memory
5. Update knowledge base
```

---

## 🔄 Complete Flow

### **Flow 1: User Request → Agent Execution**

```
1. User Request
   ↓
2. Graph Entry (graph.py)
   ↓
3. Learning Middleware (BEFORE)
   ├─→ Load app knowledge
   ├─→ Semantic search for context
   └─→ Add to agent context
   ↓
4. Determine Agent Tasks
   ├─→ Route to appropriate super agent
   ├─→ Or route to expert agent
   └─→ Set dependencies
   ↓
5. Agent Orchestration
   ├─→ Execute agents (sequential/parallel/pipeline)
   ├─→ Each agent:
   │   ├─→ Think (3-4 steps)
   │   ├─→ Execute with reasoning
   │   └─→ Return result + thinking
   ↓
6. Learning Middleware (AFTER)
   ├─→ Save interaction
   ├─→ Extract patterns
   └─→ Update memory
   ↓
7. Return Result
   └─→ With thinking, reasoning, and data
```

### **Flow 2: Knowledge Discovery**

```
Background Learner (Hourly):
   ↓
1. Discover Tables
   ├─→ Query information_schema
   ├─→ Get all public tables
   └─→ Count rows
   ↓
2. Discover Functions
   ├─→ Query pg_proc
   ├─→ Get all SQL functions
   └─→ List function names
   ↓
3. Discover Patterns
   ├─→ Sample recent data
   ├─→ Extract patterns
   └─→ Identify trends
   ↓
4. Save to Memory
   ├─→ Save to agent_memory table
   ├─→ Update cache
   └─→ Ready for agents
```

### **Flow 3: Agent Thinking Process**

```
Agent Receives Request:
   ↓
1. Thinking Step 1: Problem Analysis
   ├─→ Analyze problem deeply
   ├─→ Identify key aspects
   └─→ Consider perspectives
   ↓
2. Thinking Step 2: Approach Evaluation
   ├─→ Evaluate approaches
   ├─→ Consider trade-offs
   └─→ Identify dependencies
   ↓
3. Thinking Step 3: Reasoning
   ├─→ Reason through implications
   ├─→ Validate assumptions
   └─→ Think logically
   ↓
4. Thinking Step 4: Synthesis
   ├─→ Synthesize solution
   ├─→ Make decisions
   └─→ Plan action
   ↓
5. Execute with Reasoning
   ├─→ Use thinking to guide execution
   ├─→ Apply domain expertise
   └─→ Return result + thinking
```

---

## 🎯 Agent Alignment

### **How Agents Are Aligned**

#### **1. Knowledge Alignment**
- **Shared Knowledge Base:** All agents use same `agent_memory` table
- **Auto-Discovery:** All agents benefit from discovered structure
- **Semantic Search:** All agents can search past learning
- **Unified Learning:** Learning applies across all agents

#### **2. Execution Alignment**
- **Consistent Interface:** All agents implement `_execute_with_reasoning()`
- **Thinking Framework:** All super agents use same thinking process
- **Error Handling:** All agents use same error handling from BaseAgent
- **Learning Integration:** All agents learn automatically via middleware

#### **3. Data Alignment**
- **Shared Context:** App knowledge loaded for all agents
- **Consistent State:** State passed between agents consistently
- **Dependency Management:** Proper dependency chains
- **Result Format:** Consistent result structure

#### **4. Domain Alignment**
- **Super Agents:** Handle related domains together
- **Expert Agents:** Handle specialized domains
- **Clear Boundaries:** Each agent has clear responsibilities
- **No Overlap:** Minimal overlap between agents

---

## 📋 Operation Routing

### **How Operations Route to Agents**

```python
Operation → Agent Mapping:

"analyze_campaign" → 
  data_intelligence → business_intelligence → ml_intelligence

"generate_content" → 
  creative_intelligence → system_intelligence

"optimize_budget" → 
  data_intelligence → business_intelligence → ml_intelligence

"full_pipeline" → 
  creative_intelligence → ml_intelligence → business_intelligence

Keyword-based routing:
- "data", "database", "query" → data_intelligence
- "content", "video", "creative" → creative_intelligence
- "campaign", "budget", "roi" → business_intelligence
- "predict", "ml", "model" → ml_intelligence
- "api", "security", "error" → system_intelligence
- "meta", "ads" → meta_ads_expert
- "psychology", "trigger" → psychology_expert
- etc.
```

---

## 🔄 Complete Example Flow

### **Example: "Analyze Campaign"**

```
1. User Request:
   {
     "operation": "analyze_campaign",
     "campaign_id": "camp_123"
   }
   ↓
2. Learning Middleware (BEFORE):
   - Load app structure (58 tables, 21 functions)
   - Search past campaign analyses
   - Add context: "Similar campaigns had CTR 0.045"
   ↓
3. Route to Agents:
   - Task 1: data_intelligence (query database)
   - Task 2: business_intelligence (optimize) [depends on Task 1]
   - Task 3: ml_intelligence (predict) [depends on Task 2]
   ↓
4. DataIntelligenceAgent Executes:
   - Think Step 1: "What data do I need?"
   - Think Step 2: "How to query efficiently?"
   - Think Step 3: "What patterns to look for?"
   - Think Step 4: "Synthesize query strategy"
   - Execute: Query campaigns table
   - Return: Campaign data + thinking
   ↓
5. BusinessIntelligenceAgent Executes:
   - Receives: Campaign data from Task 1
   - Think Step 1-4: Strategic optimization thinking
   - Execute: Analyze and optimize
   - Return: Optimizations + thinking
   ↓
6. MLIntelligenceAgent Executes:
   - Receives: Optimizations from Task 2
   - Think Step 1-4: Prediction thinking
   - Execute: Predict ROAS
   - Return: Predictions + thinking
   ↓
7. Learning Middleware (AFTER):
   - Save all 3 interactions
   - Extract patterns: "Campaign optimization → ROAS prediction"
   - Update memory: "camp_123 analysis pattern"
   ↓
8. Return Result:
   {
     "agent_results": {
       "data_intelligence": {...},
       "business_intelligence": {...},
       "ml_intelligence": {...}
     },
     "thinking": {...},
     "reasoning": {...}
   }
```

---

## 🗄️ Knowledge Storage

### **Database Tables**

#### **1. agent_memory**
```sql
- id: UUID
- key: TEXT (e.g., "app_structure", "agent_patterns_*")
- value: JSONB (knowledge data)
- type: TEXT (structure_discovery, interaction, agent_patterns, daily_discovery)
- thread_id: TEXT
- agent_name: TEXT
- query: TEXT
- response: TEXT
- embeddings: VECTOR(1536) -- For semantic search
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ
```

**Stores:**
- App structure (tables, functions)
- Agent interactions
- Learned patterns
- Daily discoveries

#### **2. human_approval_queue**
```sql
- id: UUID
- tool_name: TEXT
- parameters: JSONB
- risk_level: TEXT
- status: TEXT (pending, approved, rejected)
- requested_by: TEXT
- approved_by: TEXT
- created_at: TIMESTAMPTZ
```

**Stores:**
- Dangerous action approvals
- Human review queue

#### **3. agent_execution_log**
```sql
- id: UUID
- agent_name: TEXT
- operation: TEXT
- input_data: JSONB
- result: JSONB
- execution_time: FLOAT
- success: BOOLEAN
- error: TEXT
- created_at: TIMESTAMPTZ
```

**Stores:**
- All agent executions
- Performance metrics
- Error logs

---

## 🔧 Alignment Mechanisms

### **1. Knowledge Alignment**

**How:**
- All agents read from same `agent_memory` table
- Auto-discovery updates knowledge for all
- Semantic search available to all
- Unified learning applies to all

**Result:**
- Consistent knowledge across agents
- No knowledge silos
- Shared learning

### **2. Execution Alignment**

**How:**
- All super agents inherit from `SuperAgent`
- All implement `_execute_with_reasoning()`
- All use same thinking framework
- All use same error handling

**Result:**
- Consistent execution pattern
- Predictable behavior
- Easy to maintain

### **3. Data Alignment**

**How:**
- State passed consistently
- Context shared between agents
- Dependencies properly managed
- Results in consistent format

**Result:**
- Smooth agent handoffs
- No data loss
- Clear data flow

### **4. Domain Alignment**

**How:**
- Clear domain boundaries
- Super agents for related domains
- Expert agents for specialized domains
- No overlapping responsibilities

**Result:**
- Clear ownership
- No confusion
- Efficient routing

---

## 📊 Knowledge Flow Diagram

```
┌─────────────────────────────────────┐
│   Background Learner (Hourly)       │
│   - Discovers tables/functions      │
│   - Finds patterns                  │
│   - Saves to agent_memory           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   agent_memory Table                │
│   - App structure                   │
│   - Interactions                    │
│   - Patterns                        │
│   - Embeddings (for search)         │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Learning Middleware               │
│   BEFORE: Load knowledge            │
│   AFTER: Save learning              │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Agent Execution                   │
│   - Think (3-4 steps)               │
│   - Execute with reasoning          │
│   - Use knowledge from context      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Semantic Search                   │
│   - Find relevant past learning      │
│   - Add to context                  │
└─────────────────────────────────────┘
```

---

## 🎯 Key Points

### **Knowledge Setup:**
1. ✅ **Auto-Discovery** - Discovers everything automatically
2. ✅ **Learning Middleware** - Loads/saves knowledge automatically
3. ✅ **Semantic Search** - Finds relevant past learning
4. ✅ **Background Learning** - Continuous discovery

### **Alignment:**
1. ✅ **Shared Knowledge** - All agents use same knowledge base
2. ✅ **Consistent Interface** - All agents follow same pattern
3. ✅ **Unified Learning** - Learning applies to all
4. ✅ **Clear Domains** - Each agent has clear responsibilities

### **Flow:**
1. ✅ **Request → Learning → Routing → Execution → Learning → Result**
2. ✅ **Knowledge flows: Discovery → Storage → Loading → Use → Learning**
3. ✅ **Agents aligned through shared knowledge and consistent patterns**

---

## ✅ Summary

**Knowledge System:**
- Auto-discovers entire app structure
- Stores in `agent_memory` table
- Loads before execution
- Learns after execution
- Searches semantically

**Alignment:**
- All agents use same knowledge
- All follow same patterns
- All learn together
- Clear domain boundaries

**Flow:**
- User request → Learning → Agent execution → Learning → Result
- Knowledge: Discovery → Storage → Loading → Use → Learning
- Agents: Think → Execute → Learn

**Status: ✅ Fully Aligned and Production Ready**

