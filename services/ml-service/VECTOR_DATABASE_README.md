# Vector Database Upgrade - Agent 39

**Status**: ✅ Complete
**Technology**: PostgreSQL + pgvector
**Embedding Models**:
- Text: OpenAI text-embedding-3-large (3072 dimensions)
- Images: CLIP (512 dimensions)

## Overview

Upgraded from in-memory FAISS to persistent PostgreSQL + pgvector for intelligent semantic search and recommendations.

### Why pgvector?

1. **Already have PostgreSQL** - No new infrastructure needed
2. **Persistent storage** - Survives restarts, no data loss
3. **Scalable** - Handles millions of vectors efficiently
4. **ACID compliance** - Transactional consistency with metadata
5. **Simple integration** - SQL-based, works with existing codebase

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vector Store System                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌────────────────────┐             │
│  │  OpenAI API  │      │   CLIP Model       │             │
│  │ text-embed-  │      │  (HuggingFace)     │             │
│  │ 3-large      │      │                    │             │
│  └──────┬───────┘      └────────┬───────────┘             │
│         │                       │                          │
│         └───────┬───────────────┘                          │
│                 │                                           │
│        ┌────────▼──────────┐                               │
│        │ Embedding Pipeline │                              │
│        └────────┬──────────┘                               │
│                 │                                           │
│        ┌────────▼──────────┐                               │
│        │   Vector Store    │                               │
│        │   (pgvector)      │                               │
│        └────────┬──────────┘                               │
│                 │                                           │
│  ┌──────────────┴─────────────────────────┐               │
│  │                                         │               │
│  ▼                 ▼                 ▼     ▼               │
│ Creative       Hook          Knowledge  Product           │
│ Embeddings   Embeddings      Base      Embeddings         │
│ (3072+512d)  (3072d)         (3072d)   (3072d)           │
│                                                            │
│ - Find similar - Find proven - RAG for  - Cold start     │
│   winning       hooks for     context-   recommend-      │
│   creatives     similar       aware      ations          │
│                 products      generation                  │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### 1. Creative Embeddings
Store embeddings for blueprints/videos with performance tracking.

```python
class CreativeEmbedding:
    id: UUID
    creative_id: str  # blueprint_id or video_id
    creative_type: str  # blueprint, video, hook

    # Embeddings
    text_embedding: Vector(3072)  # Hook/script text
    visual_embedding: Vector(512)  # Thumbnail/video frame

    # Context
    campaign_id: str
    hook_text: str
    hook_type: str

    # Performance (for learning)
    council_score: float
    predicted_roas: float
    actual_roas: float
    impressions: int
    conversions: int
```

**Use Case**: Find winning creatives similar to new product

### 2. Hook Embeddings
Store hooks with performance data for recommendations.

```python
class HookEmbedding:
    id: UUID
    hook_id: str
    hook_text: str
    embedding: Vector(3072)

    # Context
    hook_type: str  # pain_agitation, curiosity, etc.
    product_category: str
    target_avatar: str

    # Performance
    avg_ctr: float
    avg_roas: float
    total_impressions: int
    success_rate: float  # % of campaigns where hook worked
```

**Use Case**: Find hooks that worked on similar products

### 3. Knowledge Base Vectors
Store marketing knowledge for RAG-powered generation.

```python
class KnowledgeBaseVector:
    id: UUID
    content_id: str
    content_type: str  # best_practice, case_study, pattern

    title: str
    content: str  # Full knowledge text
    embedding: Vector(3072)

    # Categorization
    category: str  # hook_writing, script_structure, etc.
    tags: List[str]

    # Quality tracking
    confidence_score: float
    usage_count: int
    success_rate: float
```

**Use Case**: Semantic search for best practices to inject into generation

### 4. Product Embeddings
Store products with historical performance for cold start.

```python
class ProductEmbedding:
    id: UUID
    product_id: str
    product_name: str
    embedding: Vector(3072)

    # Product info
    product_description: str
    offer: str
    target_avatar: str

    # Historical performance
    total_campaigns: int
    avg_roas: float
    best_hook_types: List[str]
    best_creative_patterns: List[Dict]
```

**Use Case**: Cold start - find similar products and copy winning patterns

## Installation

### 1. Install pgvector Extension

```bash
# On PostgreSQL server
sudo apt-get install postgresql-15-pgvector

# Or using Docker
docker run -d \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  ankane/pgvector
```

### 2. Install Python Dependencies

```bash
cd /home/user/geminivideo/services/ml-service
pip install -r requirements.txt
```

New dependencies:
- `pgvector==0.2.4` - PostgreSQL vector support
- `asyncpg==0.29.0` - Async PostgreSQL driver
- `openai==1.54.0` - Text embeddings
- `transformers==4.36.0` - CLIP model
- `torch==2.1.0` - PyTorch for CLIP
- `sentence-transformers==2.2.2` - Embedding utilities

### 3. Run Migration

```bash
cd /home/user/geminivideo/services/ml-service

# Basic migration (creates tables and indexes)
python migrate_to_pgvector.py --database-url postgresql+asyncpg://user:pass@host:5432/dbname

# With FAISS data migration (if you have existing FAISS index)
python migrate_to_pgvector.py \
  --database-url postgresql+asyncpg://... \
  --migrate-faiss \
  --faiss-index /path/to/faiss_index
```

### 4. Set Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo"
```

## Usage

### Quick Start

```python
from src.vector_store import VectorStore
from src.embedding_pipeline import EmbeddingPipeline
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Initialize
engine = create_async_engine(DATABASE_URL)
embedder = EmbeddingPipeline(openai_api_key="sk-...")

async with AsyncSession(engine) as session:
    vector_store = VectorStore(session)

    # Store creative embedding
    text_embedding = await embedder.embed_text("Stop wasting money on gym memberships...")

    await vector_store.store_creative_embedding(
        creative_id="blueprint_001",
        creative_type="blueprint",
        text_embedding=text_embedding,
        hook_text="Stop wasting money on gym memberships...",
        hook_type="pain_agitation",
        council_score=8.5,
        predicted_roas=4.2
    )

    # Find similar creatives
    query = "Home fitness app for busy people"
    query_embedding = await embedder.embed_text(query)

    similar = await vector_store.find_similar_creatives(
        embedding=query_embedding,
        embedding_type="text",
        top_k=10,
        filters={"min_council_score": 8.0}
    )

    for result in similar:
        print(f"Creative: {result.id}")
        print(f"Similarity: {result.similarity_score:.4f}")
        print(f"ROAS: {result.metadata.get('actual_roas')}")
```

### Integration with Blueprint Generation

```python
async def generate_blueprints_with_intelligence(campaign_id: str, product_info: dict):
    """Generate blueprints using vector intelligence."""

    # 1. Find similar products (cold start)
    product_text = f"{product_info['name']}: {product_info['description']}"
    product_embedding = await embedder.embed_text(product_text)

    similar_products = await vector_store.find_similar_products(
        embedding=product_embedding,
        top_k=5,
        min_campaigns=10  # Only proven products
    )

    # Extract winning patterns
    recommended_hook_types = []
    for product in similar_products:
        recommended_hook_types.extend(product.metadata['best_hook_types'])

    # 2. Find proven hooks
    hook_query = f"{product_info['target_avatar']} {product_info['pain_points'][0]}"
    hook_embedding = await embedder.embed_text(hook_query)

    proven_hooks = await vector_store.find_similar_hooks(
        embedding=hook_embedding,
        top_k=10,
        filters={"min_success_rate": 0.8}
    )

    # 3. Get marketing knowledge (RAG)
    knowledge_query = f"How to write {recommended_hook_types[0]} hooks for {product_info['category']}"
    knowledge_embedding = await embedder.embed_text(knowledge_query)

    relevant_knowledge = await vector_store.search_knowledge(
        query_embedding=knowledge_embedding,
        top_k=5,
        category="hook_writing"
    )

    # 4. Generate blueprints with context
    context = {
        "similar_products": similar_products,
        "proven_hooks": proven_hooks,
        "knowledge": relevant_knowledge
    }

    blueprints = await ai_generate_blueprints(product_info, context)

    # 5. Store embeddings for future learning
    for blueprint in blueprints:
        embedding = await embedder.embed_text(blueprint['hook_text'])

        await vector_store.store_creative_embedding(
            creative_id=blueprint['id'],
            creative_type="blueprint",
            text_embedding=embedding,
            campaign_id=campaign_id,
            hook_text=blueprint['hook_text'],
            hook_type=blueprint['hook_type'],
            council_score=blueprint['council_score'],
            predicted_roas=blueprint['predicted_roas']
        )

    return blueprints
```

### Learning from Performance

```python
async def update_creative_performance_and_learn(creative_id: str, performance_data: dict):
    """Update performance and propagate learnings."""

    # Update creative performance
    await vector_store.update_creative_performance(
        creative_id=creative_id,
        actual_roas=performance_data['roas'],
        impressions=performance_data['impressions'],
        conversions=performance_data['conversions']
    )

    # If successful, store hook for future recommendations
    if performance_data['roas'] > 4.0:
        creative = await get_creative(creative_id)
        hook_embedding = await embedder.embed_text(creative['hook_text'])

        await vector_store.store_hook_embedding(
            hook_id=f"hook_{creative_id}",
            hook_text=creative['hook_text'],
            embedding=hook_embedding,
            hook_type=creative['hook_type'],
            product_category=creative['product_category']
        )

        await vector_store.update_hook_performance(
            hook_id=f"hook_{creative_id}",
            avg_roas=performance_data['roas'],
            avg_ctr=performance_data['ctr'],
            success_rate=1.0  # This campaign was successful
        )
```

## Examples

Run comprehensive examples:

```bash
cd /home/user/geminivideo/services/ml-service

# Run all examples
python vector_store_examples.py --example all

# Run specific example
python vector_store_examples.py --example creative_similarity
python vector_store_examples.py --example hook_recommendation
python vector_store_examples.py --example knowledge_rag
python vector_store_examples.py --example product_cold_start
python vector_store_examples.py --example full_pipeline
```

## Testing

Run comprehensive tests:

```bash
cd /home/user/geminivideo/services/ml-service

# Set test database
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo_test"

# Run tests
pytest test_vector_store.py -v -s

# Run specific test
pytest test_vector_store.py::test_find_similar_creatives -v
```

## Performance

### Index Types

pgvector supports multiple index types:

1. **IVFFlat** (default in our schema)
   - Fast approximate nearest neighbor search
   - Good for 100K+ vectors
   - Configurable accuracy/speed tradeoff

2. **HNSW** (optional, faster queries)
   - Hierarchical Navigable Small World graph
   - Better query performance
   - Higher memory usage

### Optimization Tips

1. **Batch insertions**: Insert embeddings in batches of 100-1000
2. **Index tuning**: Adjust `lists` parameter based on dataset size
3. **Query optimization**: Use filters to reduce search space
4. **Connection pooling**: Configure appropriate pool size

### Expected Performance

- **Query latency**: 10-50ms for top-10 similarity search
- **Throughput**: 1000+ queries/second (with proper indexing)
- **Storage**: ~12KB per vector (3072 dims) + metadata

## API Reference

### VectorStore Class

#### Creative Embeddings

```python
await vector_store.store_creative_embedding(
    creative_id: str,
    creative_type: str,
    text_embedding: List[float] = None,
    visual_embedding: List[float] = None,
    campaign_id: str = None,
    hook_text: str = None,
    hook_type: str = None,
    council_score: float = None,
    predicted_roas: float = None,
    metadata: dict = None
) -> CreativeEmbedding

await vector_store.find_similar_creatives(
    embedding: List[float],
    embedding_type: str = "text",  # or "visual"
    top_k: int = 10,
    min_score: float = None,
    filters: dict = None
) -> List[SimilarityResult]

await vector_store.update_creative_performance(
    creative_id: str,
    actual_roas: float = None,
    impressions: int = None,
    conversions: int = None
) -> bool
```

#### Hook Embeddings

```python
await vector_store.store_hook_embedding(
    hook_id: str,
    hook_text: str,
    embedding: List[float],
    hook_type: str = None,
    product_category: str = None,
    target_avatar: str = None,
    pain_points: List[str] = None,
    metadata: dict = None
) -> HookEmbedding

await vector_store.find_similar_hooks(
    embedding: List[float],
    top_k: int = 5,
    filters: dict = None
) -> List[SimilarityResult]

await vector_store.update_hook_performance(
    hook_id: str,
    avg_ctr: float = None,
    avg_roas: float = None,
    impressions_delta: int = None,
    conversions_delta: int = None,
    success_rate: float = None
) -> bool
```

#### Knowledge Base

```python
await vector_store.store_knowledge(
    content_id: str,
    content_type: str,
    title: str,
    content: str,
    embedding: List[float],
    category: str = None,
    tags: List[str] = None,
    summary: str = None,
    confidence_score: float = None,
    source: str = None,
    source_url: str = None,
    metadata: dict = None
) -> KnowledgeBaseVector

await vector_store.search_knowledge(
    query_embedding: List[float],
    top_k: int = 5,
    category: str = None,
    content_type: str = None,
    min_confidence: float = None
) -> List[SimilarityResult]

await vector_store.increment_knowledge_usage(
    content_id: str,
    success: bool = True
) -> bool
```

#### Product Embeddings

```python
await vector_store.store_product_embedding(
    product_id: str,
    product_name: str,
    embedding: List[float],
    product_description: str = None,
    offer: str = None,
    target_avatar: str = None,
    pain_points: List[str] = None,
    desires: List[str] = None,
    metadata: dict = None
) -> ProductEmbedding

await vector_store.find_similar_products(
    embedding: List[float],
    top_k: int = 10,
    min_campaigns: int = None
) -> List[SimilarityResult]

await vector_store.update_product_performance(
    product_id: str,
    campaign_count_delta: int = 1,
    avg_roas: float = None,
    best_hook_types: List[str] = None,
    best_creative_patterns: List[dict] = None
) -> bool
```

### EmbeddingPipeline Class

```python
embedder = EmbeddingPipeline(
    openai_api_key: str = None,
    clip_model_name: str = "openai/clip-vit-base-patch32"
)

# Text embeddings
embedding = await embedder.embed_text(text: str) -> List[float]
embeddings = await embedder.embed_texts(texts: List[str]) -> List[List[float]]

# Image embeddings
embedding = embedder.embed_image(image_path: str) -> List[float]
embeddings = embedder.embed_images(image_paths: List[str]) -> List[List[float]]

# Hybrid
result = await embedder.embed_creative(
    text: str = None,
    image_path: str = None
) -> dict  # {'text_embedding': [...], 'visual_embedding': [...]}
```

## Monitoring

### Vector Store Statistics

```python
stats = await vector_store.get_stats()
# {
#   'creative_embeddings': 1250,
#   'hook_embeddings': 450,
#   'knowledge_vectors': 120,
#   'product_embeddings': 85,
#   'total_vectors': 1905
# }
```

### Database Queries

```sql
-- Check index status
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename LIKE '%embedding%';

-- Check vector counts
SELECT
    (SELECT COUNT(*) FROM creative_embeddings) as creatives,
    (SELECT COUNT(*) FROM hook_embeddings) as hooks,
    (SELECT COUNT(*) FROM knowledge_base_vectors) as knowledge,
    (SELECT COUNT(*) FROM product_embeddings) as products;

-- Check performance
SELECT
    hook_id,
    avg_roas,
    success_rate,
    total_impressions
FROM hook_embeddings
WHERE success_rate > 0.8
ORDER BY avg_roas DESC
LIMIT 10;
```

## Migration from FAISS

If you have existing FAISS embeddings:

```bash
python migrate_to_pgvector.py \
  --database-url postgresql+asyncpg://... \
  --migrate-faiss \
  --faiss-index /path/to/faiss_index \
  --creative-type blueprint
```

This will:
1. Load FAISS index and metadata
2. Extract all embeddings
3. Store in pgvector with metadata
4. Preserve ID mappings

## Troubleshooting

### pgvector Extension Not Found

```sql
-- Check if pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Enable extension (requires superuser)
CREATE EXTENSION vector;
```

### Slow Queries

```sql
-- Check if indexes exist
SELECT * FROM pg_indexes WHERE indexname LIKE 'idx_%embedding%';

-- Rebuild index if needed
REINDEX INDEX idx_creative_text_embedding;
```

### Out of Memory

Reduce batch size or adjust PostgreSQL memory settings:

```sql
-- Check current settings
SHOW shared_buffers;
SHOW work_mem;

-- Increase if needed (in postgresql.conf)
shared_buffers = 256MB
work_mem = 64MB
```

## Future Enhancements

1. **Multi-modal search**: Combine text + visual similarity
2. **Hybrid search**: Combine vector + keyword search
3. **Automatic reindexing**: Rebuild indexes as data grows
4. **A/B testing**: Compare different embedding models
5. **Compression**: Use product quantization for larger datasets

## Related Files

- `/home/user/geminivideo/services/ml-service/src/vector_store.py` - Main vector store implementation
- `/home/user/geminivideo/services/ml-service/src/embedding_pipeline.py` - Embedding generation
- `/home/user/geminivideo/shared/db/models.py` - Database models
- `/home/user/geminivideo/services/ml-service/migrate_to_pgvector.py` - Migration script
- `/home/user/geminivideo/services/ml-service/vector_store_examples.py` - Usage examples
- `/home/user/geminivideo/services/ml-service/test_vector_store.py` - Test suite

## Support

For issues or questions:
1. Check logs: `tail -f /var/log/ml-service.log`
2. Run tests: `pytest test_vector_store.py -v`
3. Verify installation: `python migrate_to_pgvector.py --database-url ...`
