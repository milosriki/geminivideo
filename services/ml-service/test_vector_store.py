"""
Vector Store Tests

Agent 39: Vector Database Upgrade
Comprehensive tests for vector store functionality.
"""

import pytest
import asyncio
import os
import sys
from typing import List

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from src.vector_store import VectorStore, SimilarityResult
from src.embedding_pipeline import EmbeddingPipeline
from db.models import Base

# Test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo_test")


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session."""
    session_maker = async_sessionmaker(db_engine, class_=AsyncSession)
    async with session_maker() as session:
        yield session


@pytest.fixture
async def vector_store(db_session):
    """Create vector store instance."""
    return VectorStore(db_session)


@pytest.fixture
async def embedder():
    """Create embedding pipeline instance."""
    return EmbeddingPipeline()


# ============================================================================
# CREATIVE EMBEDDINGS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_creative_embedding(vector_store, embedder):
    """Test storing creative embedding."""
    # Generate embedding
    text = "Stop wasting money on gym memberships"
    text_embedding = await embedder.embed_text(text)

    # Store creative
    creative = await vector_store.store_creative_embedding(
        creative_id="test_blueprint_001",
        creative_type="blueprint",
        text_embedding=text_embedding,
        campaign_id="test_campaign_001",
        hook_text=text,
        hook_type="pain_agitation",
        council_score=8.5,
        predicted_roas=4.2
    )

    assert creative is not None
    assert creative.creative_id == "test_blueprint_001"
    assert creative.creative_type == "blueprint"
    assert creative.hook_text == text
    assert creative.council_score == 8.5


@pytest.mark.asyncio
async def test_find_similar_creatives(vector_store, embedder):
    """Test finding similar creatives."""
    # Store multiple creatives
    texts = [
        "Stop wasting money on gym memberships",
        "Transform your body in 30 days",
        "Get fit without leaving home"
    ]

    for i, text in enumerate(texts):
        embedding = await embedder.embed_text(text)
        await vector_store.store_creative_embedding(
            creative_id=f"test_blueprint_{i:03d}",
            creative_type="blueprint",
            text_embedding=embedding,
            hook_text=text,
            council_score=8.0 + i * 0.1
        )

    # Search for similar
    query = "Save money on fitness"
    query_embedding = await embedder.embed_text(query)

    results = await vector_store.find_similar_creatives(
        embedding=query_embedding,
        embedding_type="text",
        top_k=3
    )

    assert len(results) > 0
    assert results[0].similarity_score > 0
    assert results[0].id.startswith("test_blueprint_")


@pytest.mark.asyncio
async def test_update_creative_performance(vector_store, embedder):
    """Test updating creative performance."""
    # Store creative
    text = "Transform your body"
    embedding = await embedder.embed_text(text)
    await vector_store.store_creative_embedding(
        creative_id="test_perf_001",
        creative_type="blueprint",
        text_embedding=embedding,
        hook_text=text
    )

    # Update performance
    success = await vector_store.update_creative_performance(
        creative_id="test_perf_001",
        actual_roas=4.5,
        impressions=50000,
        conversions=250
    )

    assert success is True


# ============================================================================
# HOOK EMBEDDINGS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_hook_embedding(vector_store, embedder):
    """Test storing hook embedding."""
    text = "Get fit in 15 minutes a day"
    embedding = await embedder.embed_text(text)

    hook = await vector_store.store_hook_embedding(
        hook_id="test_hook_001",
        hook_text=text,
        embedding=embedding,
        hook_type="convenience",
        product_category="fitness_app",
        target_avatar="busy_professionals"
    )

    assert hook is not None
    assert hook.hook_id == "test_hook_001"
    assert hook.hook_text == text
    assert hook.hook_type == "convenience"


@pytest.mark.asyncio
async def test_find_similar_hooks(vector_store, embedder):
    """Test finding similar hooks."""
    # Store hooks
    hooks = [
        ("Get fit quickly", "convenience"),
        ("Save time on workouts", "time_saving"),
        ("Quick fitness results", "convenience")
    ]

    for i, (text, hook_type) in enumerate(hooks):
        embedding = await embedder.embed_text(text)
        await vector_store.store_hook_embedding(
            hook_id=f"test_hook_{i:03d}",
            hook_text=text,
            embedding=embedding,
            hook_type=hook_type,
            product_category="fitness"
        )

        # Add performance
        await vector_store.update_hook_performance(
            hook_id=f"test_hook_{i:03d}",
            avg_roas=4.0 + i * 0.2,
            success_rate=0.85 + i * 0.02
        )

    # Search
    query = "Fast workouts for busy people"
    query_embedding = await embedder.embed_text(query)

    results = await vector_store.find_similar_hooks(
        embedding=query_embedding,
        top_k=3
    )

    assert len(results) > 0
    assert results[0].similarity_score > 0


# ============================================================================
# KNOWLEDGE BASE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_knowledge(vector_store, embedder):
    """Test storing knowledge."""
    content = """The pain-agitation formula works by:
1. Identifying pain points
2. Agitating the problem
3. Presenting the solution"""

    embedding = await embedder.embed_text(content)

    kb = await vector_store.store_knowledge(
        content_id="test_kb_001",
        content_type="best_practice",
        title="Pain-Agitation Formula",
        content=content,
        embedding=embedding,
        category="hook_writing",
        tags=["pain_agitation", "formula"],
        confidence_score=0.95
    )

    assert kb is not None
    assert kb.content_id == "test_kb_001"
    assert kb.title == "Pain-Agitation Formula"
    assert kb.confidence_score == 0.95


@pytest.mark.asyncio
async def test_search_knowledge(vector_store, embedder):
    """Test searching knowledge."""
    # Store knowledge items
    items = [
        ("Hook Writing Best Practices", "How to write effective hooks for ads"),
        ("Script Structure Guide", "Guide to structuring video scripts"),
        ("Visual Design Principles", "Principles for effective visual design")
    ]

    for i, (title, content) in enumerate(items):
        embedding = await embedder.embed_text(content)
        await vector_store.store_knowledge(
            content_id=f"test_kb_{i:03d}",
            content_type="best_practice",
            title=title,
            content=content,
            embedding=embedding,
            category="marketing",
            confidence_score=0.9
        )

    # Search
    query = "How to create good hooks?"
    query_embedding = await embedder.embed_text(query)

    results = await vector_store.search_knowledge(
        query_embedding=query_embedding,
        top_k=3
    )

    assert len(results) > 0
    assert results[0].similarity_score > 0


@pytest.mark.asyncio
async def test_increment_knowledge_usage(vector_store, embedder):
    """Test incrementing knowledge usage."""
    content = "Test knowledge content"
    embedding = await embedder.embed_text(content)

    await vector_store.store_knowledge(
        content_id="test_usage_001",
        content_type="technique",
        title="Test",
        content=content,
        embedding=embedding
    )

    # Increment usage
    success = await vector_store.increment_knowledge_usage(
        content_id="test_usage_001",
        success=True
    )

    assert success is True


# ============================================================================
# PRODUCT EMBEDDINGS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_product_embedding(vector_store, embedder):
    """Test storing product embedding."""
    description = "AI-powered fitness app for home workouts"
    embedding = await embedder.embed_text(description)

    product = await vector_store.store_product_embedding(
        product_id="test_prod_001",
        product_name="FitHome App",
        embedding=embedding,
        product_description=description,
        offer="50% off",
        target_avatar="busy professionals"
    )

    assert product is not None
    assert product.product_id == "test_prod_001"
    assert product.product_name == "FitHome App"


@pytest.mark.asyncio
async def test_find_similar_products(vector_store, embedder):
    """Test finding similar products."""
    # Store products
    products = [
        ("Fitness App", "Home workout app with AI coach"),
        ("Meal Planner", "Healthy meal planning app"),
        ("Yoga App", "Yoga and meditation app")
    ]

    for i, (name, desc) in enumerate(products):
        embedding = await embedder.embed_text(desc)
        await vector_store.store_product_embedding(
            product_id=f"test_prod_{i:03d}",
            product_name=name,
            embedding=embedding,
            product_description=desc
        )

        # Add performance
        await vector_store.update_product_performance(
            product_id=f"test_prod_{i:03d}",
            campaign_count_delta=10 + i * 5,
            avg_roas=4.0 + i * 0.3
        )

    # Search
    query = "Workout and fitness application"
    query_embedding = await embedder.embed_text(query)

    results = await vector_store.find_similar_products(
        embedding=query_embedding,
        top_k=3,
        min_campaigns=5
    )

    assert len(results) > 0
    assert results[0].similarity_score > 0


# ============================================================================
# UTILITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_stats(vector_store, embedder):
    """Test getting vector store statistics."""
    # Add some data
    text = "Test creative"
    embedding = await embedder.embed_text(text)

    await vector_store.store_creative_embedding(
        creative_id="stats_test_001",
        creative_type="blueprint",
        text_embedding=embedding,
        hook_text=text
    )

    # Get stats
    stats = await vector_store.get_stats()

    assert 'creative_embeddings' in stats
    assert 'total_vectors' in stats
    assert stats['creative_embeddings'] >= 1


@pytest.mark.asyncio
async def test_filters(vector_store, embedder):
    """Test filtering in similarity search."""
    # Store creatives with different scores
    texts = ["Hook A", "Hook B", "Hook C"]
    scores = [7.0, 8.5, 9.0]

    for i, (text, score) in enumerate(zip(texts, scores)):
        embedding = await embedder.embed_text(text)
        await vector_store.store_creative_embedding(
            creative_id=f"filter_test_{i:03d}",
            creative_type="blueprint",
            text_embedding=embedding,
            hook_text=text,
            council_score=score,
            hook_type="pain_agitation" if i % 2 == 0 else "transformation"
        )

    # Search with filters
    query = "Hook"
    query_embedding = await embedder.embed_text(query)

    # Filter by min score
    results = await vector_store.find_similar_creatives(
        embedding=query_embedding,
        embedding_type="text",
        top_k=10,
        filters={"min_council_score": 8.0}
    )

    assert len(results) >= 2  # Should get 8.5 and 9.0
    for result in results:
        assert result.metadata.get('council_score') >= 8.0

    # Filter by hook type
    results = await vector_store.find_similar_creatives(
        embedding=query_embedding,
        embedding_type="text",
        top_k=10,
        filters={"hook_type": "pain_agitation"}
    )

    for result in results:
        assert result.metadata.get('hook_type') == "pain_agitation"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
