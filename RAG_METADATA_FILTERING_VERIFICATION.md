# 🔍 RAG METADATA FILTERING VERIFICATION
## Can The System Filter by Hook Style and CTR?

**Question:** "Show me three winning video ads from our database that used a 'testimonial' style hook and had a click-through rate above 2%."

**What It Checks:**
- Can search vector database using metadata filters (hook_style, ctr)
- Can retrieve correct creative assets
- Can combine semantic search with metadata filtering

---

## 🔍 CURRENT IMPLEMENTATION STATUS

### ✅ What Exists

**1. RAG Winner Index (`winner_index.py`)**
```python
# File: services/ml-service/src/winner_index.py

class WinnerIndex:
    """RAG system for winning ad patterns"""
    
    def __init__(self):
        self.faiss_index = None
        self.metadata_store = {}  # Stores metadata per ad_id
        self.redis_client = None
        self.gcs_client = None
    
    def add_winner(
        self,
        ad_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ):
        """Add winning ad to index with metadata"""
        # Store embedding in FAISS
        # Store metadata separately
        self.metadata_store[ad_id] = metadata
```

**2. Creative DNA Extraction (`creative_dna.py`)**
```python
# File: services/ml-service/src/creative_dna.py

def extract_creative_dna(video_path: str, ad_data: Dict) -> Dict:
    """Extract creative DNA including hook style"""
    return {
        'hook_type': detect_hook_type(video_path),  # e.g., 'testimonial'
        'hook_strength': calculate_hook_strength(video_path),
        'ctr': ad_data.get('ctr', 0),
        'roas': ad_data.get('roas', 0),
        # ... other metadata
    }
```

**3. Search Endpoint (Basic)**
```python
# File: services/ml-service/src/main.py

@app.post("/api/ml/rag/search-winners", tags=["RAG"])
async def search_winners(request: WinnerSearchRequest):
    """Search for similar winning ads"""
    # Basic semantic search exists
    # BUT: No metadata filtering yet
```

---

## ⚠️ WHAT'S MISSING: METADATA FILTERING

**Current Limitation:**
- Search is semantic only (vector similarity)
- No metadata filtering (hook_style, ctr thresholds)
- No combination of semantic + metadata filters

---

## 🔧 SOLUTION: ENHANCED RAG WITH METADATA FILTERING

### Step 1: Enhanced Metadata Storage

```python
# File: services/ml-service/src/winner_index.py

import faiss
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class WinnerMetadata:
    """Structured metadata for winning ads"""
    ad_id: str
    hook_type: str  # 'testimonial', 'problem-solution', 'transformation', etc.
    hook_strength: float
    ctr: float
    roas: float
    pipeline_roas: float
    creative_dna: Dict[str, Any]
    video_url: str
    thumbnail_url: str
    campaign_id: str
    created_at: str
    indexed_at: str

class EnhancedWinnerIndex:
    """RAG system with metadata filtering support"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.metadata_store: Dict[str, WinnerMetadata] = {}
        self.ad_ids: List[str] = []  # Maps FAISS index to ad_id
        
    def add_winner(
        self,
        ad_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ):
        """
        Add winning ad with embedding and metadata.
        
        Args:
            ad_id: Unique ad identifier
            embedding: Vector embedding (768-dim)
            metadata: Structured metadata including hook_type, ctr, etc.
        """
        # Store embedding in FAISS
        embedding = np.array(embedding).reshape(1, -1).astype('float32')
        self.faiss_index.add(embedding)
        
        # Store metadata
        winner_metadata = WinnerMetadata(
            ad_id=ad_id,
            hook_type=metadata.get('hook_type', 'unknown'),
            hook_strength=metadata.get('hook_strength', 0.0),
            ctr=metadata.get('ctr', 0.0),
            roas=metadata.get('roas', 0.0),
            pipeline_roas=metadata.get('pipeline_roas', 0.0),
            creative_dna=metadata.get('creative_dna', {}),
            video_url=metadata.get('video_url', ''),
            thumbnail_url=metadata.get('thumbnail_url', ''),
            campaign_id=metadata.get('campaign_id', ''),
            created_at=metadata.get('created_at', ''),
            indexed_at=datetime.utcnow().isoformat()
        )
        
        self.metadata_store[ad_id] = winner_metadata
        self.ad_ids.append(ad_id)
        
        logger.info(f"Added winner {ad_id} to index: hook_type={winner_metadata.hook_type}, ctr={winner_metadata.ctr:.2%}")
    
    def search_with_filters(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with metadata filters.
        
        Args:
            query_embedding: Query vector (768-dim)
            top_k: Number of results to return
            filters: Metadata filters
                - hook_type: str or List[str] (e.g., 'testimonial' or ['testimonial', 'transformation'])
                - ctr_min: float (minimum CTR threshold)
                - roas_min: float (minimum ROAS threshold)
                - pipeline_roas_min: float (minimum pipeline ROAS)
        
        Returns:
            List of matching winners with similarity scores
        """
        if filters is None:
            filters = {}
        
        # Step 1: Semantic search (get more candidates than needed)
        query_embedding = np.array(query_embedding).reshape(1, -1).astype('float32')
        search_k = min(top_k * 10, len(self.ad_ids))  # Get 10x candidates for filtering
        
        distances, indices = self.faiss_index.search(query_embedding, search_k)
        
        # Step 2: Apply metadata filters
        filtered_results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.ad_ids):
                continue
            
            ad_id = self.ad_ids[idx]
            metadata = self.metadata_store.get(ad_id)
            
            if not metadata:
                continue
            
            # Apply filters
            if not self._matches_filters(metadata, filters):
                continue
            
            # Calculate similarity score (1 - normalized distance)
            similarity = 1.0 / (1.0 + distance)
            
            filtered_results.append({
                'ad_id': ad_id,
                'similarity': float(similarity),
                'distance': float(distance),
                'metadata': {
                    'hook_type': metadata.hook_type,
                    'hook_strength': metadata.hook_strength,
                    'ctr': metadata.ctr,
                    'roas': metadata.roas,
                    'pipeline_roas': metadata.pipeline_roas,
                    'video_url': metadata.video_url,
                    'thumbnail_url': metadata.thumbnail_url,
                    'campaign_id': metadata.campaign_id,
                    'creative_dna': metadata.creative_dna
                }
            })
            
            # Stop when we have enough results
            if len(filtered_results) >= top_k:
                break
        
        return filtered_results
    
    def _matches_filters(self, metadata: WinnerMetadata, filters: Dict[str, Any]) -> bool:
        """Check if metadata matches all filters"""
        
        # Hook type filter
        if 'hook_type' in filters:
            filter_hook = filters['hook_type']
            if isinstance(filter_hook, str):
                if metadata.hook_type.lower() != filter_hook.lower():
                    return False
            elif isinstance(filter_hook, list):
                if metadata.hook_type.lower() not in [h.lower() for h in filter_hook]:
                    return False
        
        # CTR filter
        if 'ctr_min' in filters:
            if metadata.ctr < filters['ctr_min']:
                return False
        
        if 'ctr_max' in filters:
            if metadata.ctr > filters['ctr_max']:
                return False
        
        # ROAS filter
        if 'roas_min' in filters:
            if metadata.roas < filters['roas_min']:
                return False
        
        # Pipeline ROAS filter
        if 'pipeline_roas_min' in filters:
            if metadata.pipeline_roas < filters['pipeline_roas_min']:
                return False
        
        # Campaign filter
        if 'campaign_id' in filters:
            if metadata.campaign_id != filters['campaign_id']:
                return False
        
        return True
    
    def search_by_metadata_only(
        self,
        filters: Dict[str, Any],
        top_k: int = 10,
        sort_by: str = 'ctr'
    ) -> List[Dict[str, Any]]:
        """
        Search by metadata only (no semantic search).
        Useful for pure filtering queries.
        """
        matches = []
        
        for ad_id, metadata in self.metadata_store.items():
            if self._matches_filters(metadata, filters):
                matches.append({
                    'ad_id': ad_id,
                    'metadata': {
                        'hook_type': metadata.hook_type,
                        'hook_strength': metadata.hook_strength,
                        'ctr': metadata.ctr,
                        'roas': metadata.roas,
                        'pipeline_roas': metadata.pipeline_roas,
                        'video_url': metadata.video_url,
                        'thumbnail_url': metadata.thumbnail_url,
                        'campaign_id': metadata.campaign_id,
                        'creative_dna': metadata.creative_dna
                    }
                })
        
        # Sort by specified metric
        if sort_by == 'ctr':
            matches.sort(key=lambda x: x['metadata']['ctr'], reverse=True)
        elif sort_by == 'roas':
            matches.sort(key=lambda x: x['metadata']['roas'], reverse=True)
        elif sort_by == 'pipeline_roas':
            matches.sort(key=lambda x: x['metadata']['pipeline_roas'], reverse=True)
        
        return matches[:top_k]
```

---

### Step 2: Enhanced API Endpoint

```python
# File: services/ml-service/src/main.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class WinnerSearchRequest(BaseModel):
    """Request for searching winners"""
    query: Optional[str] = None  # Natural language query (for semantic search)
    query_embedding: Optional[List[float]] = None  # Pre-computed embedding
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None  # Metadata filters
    search_mode: str = "hybrid"  # "semantic", "metadata", or "hybrid"

class WinnerSearchResponse(BaseModel):
    """Response with filtered winners"""
    query: Optional[str]
    filters: Optional[Dict[str, Any]]
    total_in_memory: int
    results_found: int
    winners: List[Dict[str, Any]]
    search_mode: str

@app.post("/api/ml/rag/search-winners", tags=["RAG"])
async def search_winners(request: WinnerSearchRequest):
    """
    Search for winning ads with metadata filtering.
    
    Examples:
    1. Semantic + Metadata:
       {
         "query": "testimonial style ad",
         "filters": {"hook_type": "testimonial", "ctr_min": 0.02},
         "top_k": 3
       }
    
    2. Metadata only:
       {
         "filters": {"hook_type": "testimonial", "ctr_min": 0.02},
         "top_k": 3,
         "search_mode": "metadata"
       }
    
    3. Semantic only:
       {
         "query": "testimonial style ad",
         "top_k": 3,
         "search_mode": "semantic"
       }
    """
    try:
        winner_index = get_winner_index()
        
        # Determine search mode
        has_semantic = request.query or request.query_embedding
        has_metadata = request.filters and len(request.filters) > 0
        
        if request.search_mode == "metadata" or (not has_semantic and has_metadata):
            # Metadata-only search
            results = winner_index.search_by_metadata_only(
                filters=request.filters or {},
                top_k=request.top_k,
                sort_by=request.filters.get('sort_by', 'ctr') if request.filters else 'ctr'
            )
            search_mode = "metadata"
        
        elif request.search_mode == "semantic" or (has_semantic and not has_metadata):
            # Semantic-only search
            if request.query_embedding:
                query_embedding = np.array(request.query_embedding)
            else:
                # Generate embedding from query text
                query_embedding = await generate_embedding(request.query)
            
            results = winner_index.search_with_filters(
                query_embedding=query_embedding,
                top_k=request.top_k,
                filters={}  # No filters
            )
            search_mode = "semantic"
        
        else:
            # Hybrid: semantic + metadata filtering
            if request.query_embedding:
                query_embedding = np.array(request.query_embedding)
            else:
                query_embedding = await generate_embedding(request.query)
            
            results = winner_index.search_with_filters(
                query_embedding=query_embedding,
                top_k=request.top_k,
                filters=request.filters or {}
            )
            search_mode = "hybrid"
        
        return WinnerSearchResponse(
            query=request.query,
            filters=request.filters,
            total_in_memory=len(winner_index.metadata_store),
            results_found=len(results),
            winners=results,
            search_mode=search_mode
        )
        
    except Exception as e:
        logger.error(f"Error searching winners: {e}", exc_info=True)
        raise HTTPException(500, str(e))

async def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding from text using sentence transformer"""
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text)
    return embedding
```

---

### Step 3: Hook Type Detection

```python
# File: services/ml-service/src/creative_dna.py

def detect_hook_type(video_path: str, transcript: Optional[str] = None) -> str:
    """
    Detect hook style from video.
    
    Returns:
        'testimonial', 'problem-solution', 'transformation', 
        'question', 'statistic', 'story', 'demo', 'comparison'
    """
    # Method 1: Analyze transcript (if available)
    if transcript:
        hook_type = detect_hook_from_text(transcript)
        if hook_type:
            return hook_type
    
    # Method 2: Analyze video frames (first 3 seconds)
    frames = extract_frames(video_path, start_time=0, duration=3)
    hook_type = detect_hook_from_visuals(frames)
    
    return hook_type or 'unknown'

def detect_hook_from_text(text: str) -> Optional[str]:
    """Detect hook type from transcript text"""
    text_lower = text.lower()
    
    # Testimonial patterns
    testimonial_patterns = [
        r"i (used to|was|am)",
        r"my (story|experience)",
        r"before (i|we)",
        r"customer (says|said|testimonial)",
        r"client (says|said|testimonial)"
    ]
    if any(re.search(pattern, text_lower) for pattern in testimonial_patterns):
        return 'testimonial'
    
    # Problem-solution patterns
    problem_patterns = [
        r"(struggling|problem|issue|challenge)",
        r"(solution|fix|solve|answer)"
    ]
    if any(re.search(pattern, text_lower) for pattern in problem_patterns):
        return 'problem-solution'
    
    # Question patterns
    if text.strip().endswith('?'):
        return 'question'
    
    # Statistic patterns
    if re.search(r'\d+%|\d+ out of \d+', text_lower):
        return 'statistic'
    
    return None

def detect_hook_from_visuals(frames: List[np.ndarray]) -> Optional[str]:
    """Detect hook type from video frames"""
    # Use computer vision to detect:
    # - Person speaking (testimonial)
    # - Before/after comparison (transformation)
    # - Product demo (demo)
    # - Text overlay with question (question)
    
    # Simplified: Use face detection
    if detect_face_in_frames(frames):
        return 'testimonial'  # Likely testimonial if person visible
    
    return None
```

---

### Step 4: Usage Example

```python
# Example: Query for testimonial ads with CTR > 2%

# Request
POST /api/ml/rag/search-winners
{
  "query": "testimonial style ad",
  "filters": {
    "hook_type": "testimonial",
    "ctr_min": 0.02
  },
  "top_k": 3,
  "search_mode": "hybrid"
}

# Response
{
  "query": "testimonial style ad",
  "filters": {
    "hook_type": "testimonial",
    "ctr_min": 0.02
  },
  "total_in_memory": 150,
  "results_found": 3,
  "search_mode": "hybrid",
  "winners": [
    {
      "ad_id": "ad_123",
      "similarity": 0.87,
      "metadata": {
        "hook_type": "testimonial",
        "hook_strength": 0.92,
        "ctr": 0.034,
        "roas": 4.5,
        "pipeline_roas": 0.0,
        "video_url": "https://storage.googleapis.com/.../ad_123.mp4",
        "thumbnail_url": "https://storage.googleapis.com/.../ad_123.jpg",
        "campaign_id": "campaign_456",
        "creative_dna": {
          "hook_length_seconds": 3.2,
          "caption_style": "bold",
          "cta_type": "learn_more"
        }
      }
    },
    {
      "ad_id": "ad_789",
      "similarity": 0.82,
      "metadata": {
        "hook_type": "testimonial",
        "hook_strength": 0.88,
        "ctr": 0.028,
        "roas": 3.8,
        "pipeline_roas": 0.0,
        "video_url": "https://storage.googleapis.com/.../ad_789.mp4",
        "thumbnail_url": "https://storage.googleapis.com/.../ad_789.jpg",
        "campaign_id": "campaign_456",
        "creative_dna": {
          "hook_length_seconds": 2.8,
          "caption_style": "subtle",
          "cta_type": "sign_up"
        }
      }
    },
    {
      "ad_id": "ad_456",
      "similarity": 0.79,
      "metadata": {
        "hook_type": "testimonial",
        "hook_strength": 0.85,
        "ctr": 0.025,
        "roas": 4.2,
        "pipeline_roas": 0.0,
        "video_url": "https://storage.googleapis.com/.../ad_456.mp4",
        "thumbnail_url": "https://storage.googleapis.com/.../ad_456.jpg",
        "campaign_id": "campaign_789",
        "creative_dna": {
          "hook_length_seconds": 3.5,
          "caption_style": "bold",
          "cta_type": "learn_more"
        }
      }
    }
  ]
}
```

---

## 🧪 TESTING

### Test 1: Metadata-Only Search
```bash
curl -X POST http://localhost:8003/api/ml/rag/search-winners \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "hook_type": "testimonial",
      "ctr_min": 0.02
    },
    "top_k": 3,
    "search_mode": "metadata"
  }'
```

### Test 2: Hybrid Search
```bash
curl -X POST http://localhost:8003/api/ml/rag/search-winners \
  -H "Content-Type: application/json" \
  -d '{
    "query": "testimonial style ad",
    "filters": {
      "hook_type": "testimonial",
      "ctr_min": 0.02
    },
    "top_k": 3,
    "search_mode": "hybrid"
  }'
```

### Test 3: Multiple Filters
```bash
curl -X POST http://localhost:8003/api/ml/rag/search-winners \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "hook_type": ["testimonial", "transformation"],
      "ctr_min": 0.02,
      "roas_min": 3.0
    },
    "top_k": 5,
    "search_mode": "metadata"
  }'
```

---

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Enhance WinnerIndex with metadata filtering
- [ ] Add WinnerMetadata dataclass
- [ ] Implement search_with_filters method
- [ ] Implement search_by_metadata_only method
- [ ] Update API endpoint to accept filters
- [ ] Add hook type detection to Creative DNA
- [ ] Store hook_type in metadata when indexing
- [ ] Test metadata-only search
- [ ] Test hybrid search (semantic + metadata)
- [ ] Verify creative assets (video_url, thumbnail_url) are returned

---

## 📊 SUMMARY

**Question:** "Show me three winning video ads from our database that used a 'testimonial' style hook and had a click-through rate above 2%."

**Current Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**What Exists:**
- ✅ RAG Winner Index (basic semantic search)
- ✅ Creative DNA extraction
- ✅ Metadata storage structure

**What's Missing:**
- ⚠️ Metadata filtering (hook_type, ctr_min)
- ⚠️ Hook type detection
- ⚠️ Combined semantic + metadata search
- ⚠️ Creative asset URLs in response

**Estimated Time to Complete:** 4-6 hours

**This enhancement will enable the exact query you described!**

