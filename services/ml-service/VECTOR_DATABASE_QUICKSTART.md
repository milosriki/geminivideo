# Vector Database Quick Start Guide

Get started with the vector database in 5 minutes.

## Prerequisites

- PostgreSQL 11+ with pgvector extension
- OpenAI API key
- Python 3.8+

## Installation (5 steps)

### 1. Install pgvector Extension

**Option A: Docker (Easiest)**
```bash
docker run -d \
  --name pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  ankane/pgvector
```

**Option B: Ubuntu/Debian**
```bash
sudo apt-get install postgresql-15-pgvector
sudo systemctl restart postgresql
```

### 2. Install Python Dependencies

```bash
cd /home/user/geminivideo/services/ml-service
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export OPENAI_API_KEY="sk-proj-..."
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo"
```

### 4. Run Migration

```bash
python migrate_to_pgvector.py
```

Expected output:
```
Connecting to database...
Enabling pgvector extension...
Creating vector database tables...
Creating vector similarity indexes...
Verifying installation...

============================================================
MIGRATION COMPLETED SUCCESSFULLY
============================================================
```

### 5. Run Examples

```bash
python vector_store_examples.py --example full_pipeline
```

## Quick Usage

### Python Script

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.vector_store import VectorStore
from src.embedding_pipeline import EmbeddingPipeline

async def main():
    # Initialize
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo"
    engine = create_async_engine(DATABASE_URL)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # 1. Store a creative
        text = "Stop wasting money on gym memberships you never use"
        embedding = await embedder.embed_text(text)

        await vector_store.store_creative_embedding(
            creative_id="blueprint_001",
            creative_type="blueprint",
            text_embedding=embedding,
            hook_text=text,
            hook_type="pain_agitation",
            council_score=8.5,
            predicted_roas=4.2
        )
        print("✅ Stored creative")

        # 2. Find similar creatives
        query = "Home fitness app for busy professionals"
        query_embedding = await embedder.embed_text(query)

        results = await vector_store.find_similar_creatives(
            embedding=query_embedding,
            embedding_type="text",
            top_k=5
        )

        print(f"\n✅ Found {len(results)} similar creatives:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.id} (similarity: {result.similarity_score:.4f})")
            print(f"     Hook: {result.content}")
            print(f"     Score: {result.metadata.get('council_score')}")

    await engine.dispose()

asyncio.run(main())
```

Save as `test_vector.py` and run:
```bash
python test_vector.py
```

## Common Use Cases

### 1. Find Winning Creatives for New Product

```python
# Your new product
new_product = "AI-powered meal planning app for busy parents"

# Generate embedding
product_embedding = await embedder.embed_text(new_product)

# Find similar winning creatives
similar_creatives = await vector_store.find_similar_creatives(
    embedding=product_embedding,
    embedding_type="text",
    top_k=10,
    filters={"min_council_score": 8.0, "min_roas": 4.0}
)

# Copy their patterns!
for creative in similar_creatives:
    print(f"Winning hook: {creative.content}")
    print(f"ROAS: {creative.metadata['actual_roas']}")
```

### 2. Get Hook Recommendations

```python
# Your product context
product_context = "Quick healthy meals for busy people"

# Generate embedding
context_embedding = await embedder.embed_text(product_context)

# Find proven hooks
proven_hooks = await vector_store.find_similar_hooks(
    embedding=context_embedding,
    top_k=5,
    filters={"min_success_rate": 0.8, "min_roas": 4.0}
)

# Use them as templates
for hook in proven_hooks:
    print(f"Hook: {hook.content}")
    print(f"Success rate: {hook.metadata['success_rate'] * 100}%")
    print(f"Avg ROAS: {hook.metadata['avg_roas']}")
```

### 3. RAG for Context-Aware Generation

```python
# What you need help with
query = "How to write hooks for fitness products targeting busy people?"

# Generate embedding
query_embedding = await embedder.embed_text(query)

# Search knowledge base
relevant_knowledge = await vector_store.search_knowledge(
    query_embedding=query_embedding,
    top_k=5,
    category="hook_writing"
)

# Feed to your AI generator
context = "\n\n".join([kb.content for kb in relevant_knowledge])
prompt = f"""Using this knowledge:
{context}

Generate hooks for: {product_description}
"""
```

### 4. Cold Start for New Product Launch

```python
# Brand new product
new_product = {
    "name": "FitMeal Pro",
    "description": "AI meal planning with grocery delivery integration",
    "target": "Busy professionals who want to eat healthy"
}

# Generate embedding
product_text = f"{new_product['name']}: {new_product['description']}"
product_embedding = await embedder.embed_text(product_text)

# Find similar products
similar_products = await vector_store.find_similar_products(
    embedding=product_embedding,
    top_k=5,
    min_campaigns=10  # Only products with proven track record
)

# Get recommendations
print("Based on similar products, recommend:")
for product in similar_products:
    print(f"\n- {product.metadata['product_name']}")
    print(f"  Avg ROAS: {product.metadata['avg_roas']}")
    print(f"  Best hook types: {', '.join(product.metadata['best_hook_types'])}")
    print(f"  Winning patterns: {', '.join(product.metadata['best_creative_patterns'])}")
```

## Integration with Blueprint Generation

```python
async def generate_blueprints_with_intelligence(campaign_id, product_info):
    """Generate blueprints using vector intelligence."""

    # 1. Cold start - find similar products
    product_embedding = await embedder.embed_text(product_info['description'])
    similar_products = await vector_store.find_similar_products(
        embedding=product_embedding,
        top_k=3
    )

    # 2. Get proven hooks
    hook_embedding = await embedder.embed_text(product_info['pain_points'][0])
    proven_hooks = await vector_store.find_similar_hooks(
        embedding=hook_embedding,
        top_k=5,
        filters={"min_success_rate": 0.8}
    )

    # 3. Get marketing knowledge
    knowledge_embedding = await embedder.embed_text("hook writing best practices")
    knowledge = await vector_store.search_knowledge(
        query_embedding=knowledge_embedding,
        category="hook_writing"
    )

    # 4. Generate with rich context
    context = {
        "similar_products": similar_products,
        "proven_hooks": proven_hooks,
        "knowledge": knowledge
    }
    blueprints = await your_ai_generator(product_info, context)

    # 5. Store for future learning
    for bp in blueprints:
        embedding = await embedder.embed_text(bp['hook_text'])
        await vector_store.store_creative_embedding(
            creative_id=bp['id'],
            text_embedding=embedding,
            hook_text=bp['hook_text'],
            council_score=bp['council_score']
        )

    return blueprints
```

## Troubleshooting

### Error: "pgvector extension not found"

```bash
# Check if extension is available
psql -d geminivideo -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"

# Enable extension (as superuser)
psql -d geminivideo -c "CREATE EXTENSION vector;"
```

### Error: "OpenAI API key not set"

```bash
export OPENAI_API_KEY="sk-proj-..."
```

### Error: "Cannot connect to database"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d geminivideo -c "SELECT 1;"
```

### Slow queries

```sql
-- Check if indexes exist
SELECT * FROM pg_indexes WHERE indexname LIKE 'idx_%embedding%';

-- Rebuild index
REINDEX INDEX idx_creative_text_embedding;
```

## Next Steps

1. **Read full documentation**: `VECTOR_DATABASE_README.md`
2. **Run all examples**: `python vector_store_examples.py --example all`
3. **Run tests**: `pytest test_vector_store.py -v`
4. **Integrate with your services**: See integration examples in README

## Quick Reference

### Vector Store Methods

```python
# Creative embeddings
await vector_store.store_creative_embedding(...)
await vector_store.find_similar_creatives(...)
await vector_store.update_creative_performance(...)

# Hook embeddings
await vector_store.store_hook_embedding(...)
await vector_store.find_similar_hooks(...)
await vector_store.update_hook_performance(...)

# Knowledge base
await vector_store.store_knowledge(...)
await vector_store.search_knowledge(...)
await vector_store.increment_knowledge_usage(...)

# Product embeddings
await vector_store.store_product_embedding(...)
await vector_store.find_similar_products(...)
await vector_store.update_product_performance(...)

# Utilities
await vector_store.get_stats()
```

### Embedding Pipeline Methods

```python
embedder = EmbeddingPipeline(openai_api_key="sk-...")

# Text embeddings
embedding = await embedder.embed_text(text)
embeddings = await embedder.embed_texts([text1, text2, ...])

# Image embeddings
embedding = embedder.embed_image(image_path)
embeddings = embedder.embed_images([path1, path2, ...])

# Hybrid
result = await embedder.embed_creative(text=..., image_path=...)
```

## Getting Help

- **Examples**: `python vector_store_examples.py --example <name>`
- **Tests**: `pytest test_vector_store.py::test_<name> -v`
- **Documentation**: `VECTOR_DATABASE_README.md`
- **Implementation**: `AGENT39_IMPLEMENTATION_SUMMARY.md`

## Success Checklist

- [ ] pgvector extension installed
- [ ] Migration completed successfully
- [ ] Environment variables set
- [ ] Examples run without errors
- [ ] Can store and retrieve embeddings
- [ ] Similarity search returns results
- [ ] Ready to integrate with services

**You're ready to use intelligent vector search!** 🚀
