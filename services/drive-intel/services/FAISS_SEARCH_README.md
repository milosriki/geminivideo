# FAISS Embedding Search Service

Production-grade vector similarity search using FAISS and Sentence Transformers.

## Overview

`faiss_search.py` provides a comprehensive FAISS-powered vector search service with support for multiple index types, GPU acceleration, persistence, and metadata filtering.

## Features

### 1. **Multiple Index Types**
- **Flat**: Exhaustive search (exact results)
- **IVF**: Inverted file index with clustering (fast approximate search)
- **HNSW**: Hierarchical Navigable Small World graphs (optimal for high-dimensional data)

### 2. **Text Embedding**
- Uses `sentence-transformers` library
- Default model: `all-MiniLM-L6-v2` (384 dimensions)
- Batch embedding support
- Automatic model loading

### 3. **GPU Acceleration**
- Optional GPU support for faster search
- Automatic GPU detection
- CPU/GPU index conversion for persistence

### 4. **Search Operations**
- **Vector Search**: Search by embedding vector
- **Text Search**: Search using natural language queries
- **ID-based Search**: Find similar items to existing items
- **Batch Search**: Process multiple queries efficiently
- **Filtered Search**: Apply custom filter functions

### 5. **Index Management**
- Build index from embeddings
- Add single or batch embeddings
- Remove embeddings (soft delete from metadata)
- Update embeddings (remove + add)
- Train IVF indices

### 6. **Persistence**
- Save/load to local disk
- Export to Google Cloud Storage
- Import from GCS
- Metadata preservation

### 7. **Metadata Management**
- Attach metadata to vectors
- Update metadata
- Filter by metadata key-value pairs
- Retrieve metadata by ID

### 8. **Clustering**
- K-means clustering of embeddings
- Find cluster assignments
- Semantic grouping of similar items

### 9. **Statistics**
- Total vector count
- Index dimension
- Training status
- Memory usage estimation

## Usage Examples

### Basic Initialization

```python
from faiss_search import FAISSEmbeddingSearch

# Create with Flat index (exact search)
search = FAISSEmbeddingSearch(
    dimension=384,
    index_type="Flat",
    use_gpu=False
)

# Create with IVF index (approximate search)
search_ivf = FAISSEmbeddingSearch(
    dimension=384,
    index_type="IVF",
    nlist=100,  # Number of clusters
    use_gpu=False
)

# Create with HNSW index (optimal for high-dimensional)
search_hnsw = FAISSEmbeddingSearch(
    dimension=384,
    index_type="HNSW",
    use_gpu=False
)
```

### Building an Index

```python
import numpy as np

# Prepare data
embeddings = np.random.randn(1000, 384).astype(np.float32)
ids = [f"item_{i}" for i in range(1000)]
metadata = [{"category": "A", "score": i} for i in range(1000)]

# Build index
search.build_index(embeddings, ids, metadata)

# Check stats
stats = search.get_stats()
print(f"Indexed {stats.total_vectors} vectors")
print(f"Memory usage: {stats.memory_usage_mb:.2f} MB")
```

### Text-based Search

```python
# Search using natural language
results = search.search_by_text(
    text="What is machine learning?",
    k=10
)

for result in results:
    print(f"ID: {result.id}")
    print(f"Score: {result.score:.4f}")
    print(f"Metadata: {result.metadata}")
```

### Vector Search with Filtering

```python
# Define filter function
def category_filter(id: str, metadata: dict) -> bool:
    return metadata.get("category") == "A"

# Search with filter
query_embedding = np.random.randn(384).astype(np.float32)
results = search.search_similar(
    query_embedding,
    k=10,
    filter_fn=category_filter
)
```

### Find Similar Items

```python
# Find items similar to existing item
similar = search.search_by_id(
    id="item_42",
    k=10,
    exclude_self=True  # Don't include the query item
)
```

### Batch Operations

```python
# Add batch of new embeddings
new_embeddings = np.random.randn(50, 384).astype(np.float32)
new_ids = [f"new_{i}" for i in range(50)]
added_count = search.add_batch(new_embeddings, new_ids)

# Batch search
queries = np.random.randn(5, 384).astype(np.float32)
batch_results = search.batch_search(queries, k=10)
# Returns list of result lists (one per query)
```

### Persistence

```python
# Save to disk
search.save_index("/path/to/index")
# Creates: /path/to/index.index and /path/to/index.meta

# Load from disk
search.load_index("/path/to/index")

# Export to GCS
gcs_uri = search.export_to_gcs(
    bucket_name="my-bucket",
    blob_name="indices/my-index"
)

# Import from GCS
search.import_from_gcs(
    bucket_name="my-bucket",
    blob_name="indices/my-index"
)
```

### Metadata Operations

```python
# Get metadata for ID
metadata = search.get_metadata("item_5")

# Update metadata
search.update_metadata("item_5", {
    "category": "B",
    "updated": True
})

# Filter by metadata
matching_ids = search.filter_by_metadata({
    "category": "A",
    "score": 42
})
```

### Clustering

```python
# Cluster embeddings
clusters = search.cluster_embeddings(n_clusters=10)

# Returns: {cluster_id: [list of IDs]}
for cluster_id, items in clusters.items():
    print(f"Cluster {cluster_id}: {len(items)} items")
```

### Embedding Generation

```python
# Single text embedding
embedding = search.embed_text("This is a test sentence")

# Batch text embedding
texts = [
    "First sentence",
    "Second sentence",
    "Third sentence"
]
embeddings = search.embed_texts(texts)
# Returns: numpy array of shape (3, 384)
```

## Data Classes

### SearchResult

```python
@dataclass
class SearchResult:
    id: str              # External ID
    score: float         # Similarity score (higher = more similar)
    metadata: Dict[str, Any]  # Associated metadata
```

### IndexStats

```python
@dataclass
class IndexStats:
    total_vectors: int      # Number of indexed vectors
    dimension: int          # Embedding dimension
    index_type: str         # Index type (Flat, IVF, HNSW)
    is_trained: bool        # Whether index is trained (IVF only)
    memory_usage_mb: float  # Estimated memory usage
```

## Performance Considerations

### Index Type Selection

| Index Type | Speed | Accuracy | Training Required | Best For |
|-----------|-------|----------|-------------------|----------|
| Flat | Slow | 100% | No | <10K vectors, exact results needed |
| IVF | Fast | ~95% | Yes | 10K-10M vectors, good speed/accuracy trade-off |
| HNSW | Very Fast | ~99% | No | High-dimensional data, best query performance |

### Memory Usage

- **Flat**: `4 bytes × dimension × n_vectors`
- **IVF**: Similar to Flat + cluster overhead
- **HNSW**: ~2-3× Flat due to graph structure

### GPU Acceleration

```python
# Enable GPU
search = FAISSEmbeddingSearch(
    dimension=384,
    index_type="IVF",
    use_gpu=True  # Requires CUDA and faiss-gpu
)
```

Benefits:
- 10-50× faster search for large indices
- Parallel batch processing
- Automatic CPU/GPU conversion for persistence

## Error Handling

All methods include comprehensive error handling:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Errors are logged and exceptions raised or empty results returned
try:
    results = search.search_by_text("query", k=10)
except Exception as e:
    print(f"Search failed: {e}")
```

## Integration with Drive-Intel

```python
from faiss_search import FAISSEmbeddingSearch
from feature_extractor import FeatureExtractor

# Initialize
search = FAISSEmbeddingSearch(dimension=384, index_type="HNSW")
extractor = FeatureExtractor()

# Extract and index video clip embeddings
clips = extractor.extract_features(video_path)

embeddings = []
ids = []
metadata = []

for clip in clips:
    if clip.features.embedding:
        embeddings.append(clip.features.embedding)
        ids.append(clip.id)
        metadata.append({
            "asset_id": clip.asset_id,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "scene_type": clip.scene_type
        })

# Build index
search.build_index(
    np.array(embeddings),
    ids,
    metadata
)

# Search for similar clips
results = search.search_by_text(
    "outdoor mountain scenery",
    k=10
)

# Filter by asset
def asset_filter(id, metadata):
    return metadata.get("asset_id") == "asset_123"

results = search.search_by_text(
    "sunset scene",
    k=5,
    filter_fn=asset_filter
)
```

## Dependencies

Required packages (already in requirements.txt):
- `faiss-cpu==1.9.0.post1` (or `faiss-gpu` for GPU support)
- `sentence-transformers==3.3.1`
- `numpy==1.26.4`

Optional for GCS:
- `google-cloud-storage` (add to requirements.txt if using GCS features)

## Testing

Run the test suite:

```bash
cd services/drive-intel/services
python test_faiss_search.py
```

## Production Deployment

### Recommendations

1. **Index Type**: Use HNSW for production (best performance)
2. **GPU**: Enable if available for >100K vectors
3. **Persistence**: Save indices regularly, export to GCS for backup
4. **Monitoring**: Track index stats and search latency
5. **Scaling**: For >10M vectors, consider distributed FAISS or specialized vector databases

### Example Production Setup

```python
# Production configuration
search = FAISSEmbeddingSearch(
    dimension=384,
    index_type="HNSW",
    use_gpu=True  # If available
)

# Regular persistence
import schedule

def save_index():
    search.save_index("/data/indices/production_index")
    search.export_to_gcs("my-bucket", "indices/production_index")

# Save every hour
schedule.every().hour.do(save_index)
```

## Limitations

1. **FAISS Deletion**: True deletion not supported - removed items stay in index but are excluded via metadata
2. **Index Updates**: Require rebuild for optimal performance after many updates
3. **Memory**: Entire index must fit in RAM (or GPU memory)
4. **Cluster State**: `find_cluster()` requires persistent cluster assignments (simplified implementation)

## Future Enhancements

- [ ] Distributed FAISS for multi-node scaling
- [ ] Online index updates with minimal rebuild
- [ ] Automatic index type selection based on data size
- [ ] Advanced filtering with range queries
- [ ] Real-time cluster assignment persistence
- [ ] Integration with vector database alternatives (Pinecone, Milvus, Weaviate)

## License

Part of the GeminiVideo Drive-Intel service.
