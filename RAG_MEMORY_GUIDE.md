# RAG Winner Memory System - User Guide

## 🧠 What is RAG Memory?

RAG (Retrieval Augmented Generation) Winner Memory is a **persistent learning system** that remembers EVERY winning ad you've ever run and lets you search for similar winners.

### **How It Works**
```
Ad Performance → Feedback Loop → Auto-Index Winners → Persistent Memory → Search Similar Ads
```

---

## 🔄 Automatic Memory (Zero Human Effort)

### **When an ad hits 3%+ CTR:**
1. ✅ **Automatically** saved to FAISS vector index
2. ✅ **Automatically** stored in GCS (permanent)
3. ✅ **Automatically** cached in Redis (fast lookup)
4. ✅ **Automatically** becomes searchable

**You don't do anything.** The system learns automatically.

---

## 💾 Memory Backends (Triple Redundancy)

| Backend | Purpose | Persistence | Speed |
|---------|---------|-------------|-------|
| **FAISS** | Vector similarity search | Temporary (RAM) | ⚡ Instant |
| **GCS** | Permanent storage | Forever | 🐢 2-5s |
| **Redis** | Fast lookups | 30 days | ⚡⚡ <10ms |

**On startup**: Loads all winners from GCS → FAISS (warm cache)
**On new winner**: Saves to all 3 backends
**On search**: FAISS finds similar, Redis caches results

---

## 📡 API Endpoints

### 1. **Search Similar Winners** (Most Powerful)
```bash
POST /api/ml/rag/search-winners

# Example: Find ads like "fitness transformation"
curl -X POST https://ml-service.geminivideo.run/api/ml/rag/search-winners \
  -H "Content-Type: application/json" \
  -d '{
    "query": "fitness transformation before after",
    "top_k": 5,
    "min_ctr": 0.03,
    "min_similarity": 0.7
  }'

# Response:
{
  "query": "fitness transformation before after",
  "total_in_memory": 1247,  # Total winners stored
  "results_found": 5,
  "winners": [
    {
      "data": {
        "ad_id": "ad_123",
        "hook": "Lost 30 Pounds in 90 Days",
        "ctr": 0.048,
        "roas": 4.2
      },
      "similarity": 0.92  # 92% similar to your query
    },
    ...
  ],
  "memory_backend": "GCS + Redis"
}
```

### 2. **Manual Index Winner** (Optional)
```bash
POST /api/ml/rag/index-winner

# Manually add a winner (normally auto-indexed)
curl -X POST https://ml-service.geminivideo.run/api/ml/rag/index-winner \
  -H "Content-Type: application/json" \
  -d '{
    "ad_id": "ad_456",
    "ad_data": {
      "hook": "Transform Your Body",
      "body": "12-week program",
      "cta": "Start Free Trial"
    },
    "ctr": 0.045,
    "roas": 3.5,
    "conversions": 127,
    "spend": 500.0
  }'

# Response:
{
  "status": "indexed",  # or "skipped" if CTR < 3%
  "ad_id": "ad_456",
  "total_in_memory": 1248,
  "memory_backend": "GCS + Redis"
}
```

### 3. **Memory Stats**
```bash
GET /api/ml/rag/memory-stats

# Get memory status
curl https://ml-service.geminivideo.run/api/ml/rag/memory-stats

# Response:
{
  "total_winners_in_memory": 1247,
  "faiss_index_size": 1247,
  "dimension": 384,  # Embedding dimension
  "namespace": "production_winners",
  "storage_backend": "GCS",
  "redis_cache": {
    "connected": true,
    "used_memory_mb": 45.2,
    "total_keys": 3741
  },
  "embedding_model": "all-MiniLM-L6-v2",
  "memory_status": "persistent"
}
```

### 4. **Get Specific Winner**
```bash
GET /api/ml/rag/winner/{ad_id}

# Fast lookup from Redis cache
curl https://ml-service.geminivideo.run/api/ml/rag/winner/ad_123

# Response:
{
  "ad_id": "ad_123",
  "ad_data": { ... },
  "ctr": 0.048,
  "roas": 4.2,
  "indexed_at": "2025-12-06T20:30:00Z",
  "source": "Redis"  # or "FAISS"
}
```

### 5. **Clear Cache** (Redis only)
```bash
DELETE /api/ml/rag/clear-cache

# Clears Redis cache, FAISS/GCS persist
curl -X DELETE https://ml-service.geminivideo.run/api/ml/rag/clear-cache

# Response:
{
  "status": "cache_cleared",
  "keys_deleted": 523,
  "note": "FAISS index persists in GCS"
}
```

---

## 🎯 Use Cases

### **1. "Find More Ads Like This Winner"**
```javascript
// You have a 5% CTR ad, want more like it
const response = await fetch('/api/ml/rag/search-winners', {
  method: 'POST',
  body: JSON.stringify({
    query: "keto diet meal plan weight loss",
    top_k: 10,
    min_ctr: 0.04  // Only show ads with 4%+ CTR
  })
});

// Returns: 10 similar winning ads with proven performance
```

### **2. "What Hooks Work for My Niche?"**
```javascript
// Search for winning hooks in your niche
const response = await fetch('/api/ml/rag/search-winners', {
  method: 'POST',
  body: JSON.stringify({
    query: "real estate agent lead generation",
    top_k: 20,
    min_similarity: 0.6  // 60%+ similar
  })
});

// Returns: 20 winning hooks you can remix
```

### **3. "Automatic Learning (Zero Effort)"**
```javascript
// Just send feedback, RAG auto-indexes winners
await fetch('/api/ml/feedback', {
  method: 'POST',
  body: JSON.stringify({
    ad_id: "new_ad_789",
    variant_id: "new_ad_789",
    impressions: 10000,
    clicks: 350,  // 3.5% CTR
    conversions: 25,
    spend: 100,
    revenue: 500
  })
});

// ✅ Automatically indexed to RAG memory (CTR > 3%)
// ✅ Now searchable forever
// ✅ Will appear in future similarity searches
```

---

## 📊 Memory Growth Over Time

```
Week 1:   50 winners   (learning phase)
Week 2:   150 winners  (pattern detection begins)
Month 1:  500 winners  (useful insights)
Month 3:  1500 winners (powerful recommendations)
Month 6:  3000+ winners (enterprise-grade knowledge)
```

**The more you run, the smarter it gets.**

---

## 🔥 Advanced Features

### **Embedding-Based Search**
- Uses `all-MiniLM-L6-v2` (384-dimension embeddings)
- Semantic similarity (understands meaning, not just keywords)
- Example: "lose weight fast" matches "quick fat loss" (85% similar)

### **Auto-Deduplication**
- Won't index the same ad twice (Redis check)
- Saves storage and keeps results clean

### **Context-Aware**
- Searches understand niche/industry
- "fitness transformation" won't return "home improvement" ads

### **Production-Grade**
- GCS backup = never lose data
- Redis cache = <10ms lookups
- FAISS index = instant similarity search

---

## 🚨 What Happens If...

**Q: Server restarts?**
A: ✅ All winners reload from GCS on startup (5-10 seconds)

**Q: GCS fails?**
A: ✅ Falls back to local disk storage

**Q: Redis fails?**
A: ✅ Still works, just slower (no cache)

**Q: I delete a winner?**
A: ❌ Not currently supported (append-only for data integrity)

---

## 📈 ROI Example

### **Without RAG Memory:**
- Brainstorm 10 new hook ideas (2 hours)
- Test all 10 ($500 budget)
- 1-2 work (10-20% success rate)

### **With RAG Memory:**
- Search 1,000 winning hooks (10 seconds)
- Pick top 5 most similar to your best performer
- Test those 5 ($250 budget)
- 3-4 work (60-80% success rate)

**Result:** 3x success rate, 50% lower cost, 99.9% faster

---

## 🎓 Best Practices

### **1. Let It Auto-Index**
Don't manually index. Let the feedback loop do it automatically when CTR > 3%.

### **2. Use Specific Queries**
- ❌ Bad: "good ad"
- ✅ Good: "fitness transformation before/after testimonial"

### **3. Adjust Thresholds**
```javascript
// Conservative (only best winners)
{ min_ctr: 0.05, min_similarity: 0.85 }

// Balanced (default)
{ min_ctr: 0.03, min_similarity: 0.70 }

// Exploratory (more results)
{ min_ctr: 0.025, min_similarity: 0.60 }
```

### **4. Monitor Memory Growth**
```bash
# Check weekly
curl /api/ml/rag/memory-stats

# Should grow 50-200 winners/month
# If not growing = need more traffic or lower thresholds
```

---

## 🔌 Integration Examples

### **Frontend: Search Component**
```typescript
import { useState } from 'react';

function WinnerSearch() {
  const [query, setQuery] = useState('');
  const [winners, setWinners] = useState([]);

  const search = async () => {
    const res = await fetch('/api/ml/rag/search-winners', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 10 })
    });
    const data = await res.json();
    setWinners(data.winners);
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search winning ads..."
      />
      <button onClick={search}>Search Memory</button>

      {winners.map(w => (
        <div key={w.data.ad_id}>
          <h3>{w.data.hook}</h3>
          <p>CTR: {(w.ctr * 100).toFixed(2)}% | Similarity: {(w.similarity * 100).toFixed(0)}%</p>
        </div>
      ))}
    </div>
  );
}
```

### **Backend: Auto-Recommend**
```python
# When creating new campaign, recommend similar winners
async def create_campaign(concept: str):
    # Search RAG memory
    res = await httpx.post("/api/ml/rag/search-winners", json={
        "query": concept,
        "top_k": 5,
        "min_ctr": 0.04
    })
    winners = res.json()['winners']

    # Use winning hooks as inspiration
    recommended_hooks = [w['data']['hook'] for w in winners[:3]]

    return {
        "concept": concept,
        "recommended_hooks": recommended_hooks,
        "based_on": f"{len(winners)} similar winners"
    }
```

---

## ✅ Verification

```bash
# 1. Check if RAG is running
curl /api/ml/rag/memory-stats

# 2. Manually index a test winner
curl -X POST /api/ml/rag/index-winner \
  -H "Content-Type: application/json" \
  -d '{
    "ad_id": "test_winner_1",
    "ad_data": {"hook": "Test Hook", "body": "Test body"},
    "ctr": 0.05
  }'

# 3. Search for it
curl -X POST /api/ml/rag/search-winners \
  -H "Content-Type: application/json" \
  -d '{"query": "test hook", "top_k": 5}'

# Should return: test_winner_1 with high similarity
```

---

## 🎉 Summary

**RAG Memory = Your Ad Intelligence Database**

- ✅ Automatic (learns from every winner)
- ✅ Persistent (GCS + Redis + FAISS)
- ✅ Fast (<10ms lookups)
- ✅ Smart (semantic similarity)
- ✅ Growing (gets better over time)

**Every winning ad becomes institutional knowledge.**

Start running ads → System learns → Search for similar winners → Launch more winners → Repeat.

The flywheel effect. 🚀
