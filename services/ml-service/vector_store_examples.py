"""
Vector Store Integration Examples

Agent 39: Vector Database Upgrade
Complete examples showing how to use the vector store for:
1. Creative similarity search
2. Hook recommendation
3. Knowledge base RAG
4. Product cold start

Usage:
    python vector_store_examples.py --example <name>

Examples:
    - creative_similarity: Find similar winning creatives
    - hook_recommendation: Find hooks that worked on similar products
    - knowledge_rag: Semantic search for marketing knowledge
    - product_cold_start: Get recommendations for new products
    - full_pipeline: Complete integration example
"""

import asyncio
import logging
import argparse
import sys
import os
from typing import List, Dict, Any

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.connection import get_db_session

from src.vector_store import VectorStore
from src.embedding_pipeline import EmbeddingPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/geminivideo")


# ============================================================================
# EXAMPLE 1: CREATIVE SIMILARITY SEARCH
# ============================================================================

async def example_creative_similarity():
    """
    Example: Find similar winning creatives for a new product.

    Use Case:
    - You have a new product "Ultimate Fitness App"
    - Find successful creatives from similar products
    - Copy their winning patterns automatically
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: CREATIVE SIMILARITY SEARCH")
    logger.info("=" * 60)

    # Initialize
    engine = create_async_engine(DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # Step 1: Store some sample creatives (in real app, this happens during generation)
        logger.info("\n1. Storing sample creative embeddings...")

        sample_creatives = [
            {
                "creative_id": "blueprint_001",
                "hook_text": "Stop wasting money on gym memberships you never use...",
                "campaign_id": "camp_001",
                "hook_type": "pain_agitation",
                "council_score": 8.5,
                "predicted_roas": 4.2,
                "actual_roas": 4.8,
                "impressions": 50000,
                "conversions": 250
            },
            {
                "creative_id": "blueprint_002",
                "hook_text": "Transform your body in just 30 days with professional trainers...",
                "campaign_id": "camp_002",
                "hook_type": "transformation",
                "council_score": 7.8,
                "predicted_roas": 3.5,
                "actual_roas": 3.9,
                "impressions": 45000,
                "conversions": 180
            },
            {
                "creative_id": "blueprint_003",
                "hook_text": "Get fit without leaving your home - professional workout plans...",
                "campaign_id": "camp_003",
                "hook_type": "convenience",
                "council_score": 8.0,
                "predicted_roas": 3.8,
                "actual_roas": 4.1,
                "impressions": 52000,
                "conversions": 220
            }
        ]

        for creative in sample_creatives:
            # Generate embedding
            text_embedding = await embedder.embed_text(creative["hook_text"])

            # Store in vector store
            await vector_store.store_creative_embedding(
                creative_id=creative["creative_id"],
                creative_type="blueprint",
                text_embedding=text_embedding,
                campaign_id=creative["campaign_id"],
                hook_text=creative["hook_text"],
                hook_type=creative["hook_type"],
                council_score=creative["council_score"],
                predicted_roas=creative["predicted_roas"]
            )

            # Update with actual performance
            await vector_store.update_creative_performance(
                creative_id=creative["creative_id"],
                actual_roas=creative["actual_roas"],
                impressions=creative["impressions"],
                conversions=creative["conversions"]
            )

            logger.info(f"  Stored: {creative['creative_id']}")

        # Step 2: Find similar creatives for a new product
        logger.info("\n2. Finding similar creatives for new product...")

        new_product_text = "Home workout app with AI personal trainer and meal plans"
        query_embedding = await embedder.embed_text(new_product_text)

        similar_creatives = await vector_store.find_similar_creatives(
            embedding=query_embedding,
            embedding_type="text",
            top_k=3,
            filters={"min_council_score": 7.0}
        )

        logger.info(f"\nFound {len(similar_creatives)} similar creatives:")
        for i, result in enumerate(similar_creatives, 1):
            logger.info(f"\n  {i}. Creative: {result.id}")
            logger.info(f"     Similarity: {result.similarity_score:.4f}")
            logger.info(f"     Hook: {result.content}")
            logger.info(f"     Hook Type: {result.metadata.get('hook_type')}")
            logger.info(f"     Council Score: {result.metadata.get('council_score')}")
            logger.info(f"     Actual ROAS: {result.metadata.get('actual_roas')}")
            logger.info(f"     Performance: {result.metadata.get('impressions')} impressions, "
                       f"{result.metadata.get('conversions')} conversions")

        logger.info("\nUse Case: Copy the hook style and structure from top result!")

    await engine.dispose()


# ============================================================================
# EXAMPLE 2: HOOK RECOMMENDATION
# ============================================================================

async def example_hook_recommendation():
    """
    Example: Find hooks that performed well on similar products.

    Use Case:
    - You're creating hooks for a new fitness product
    - Find hooks that worked for similar fitness products
    - Get automatic recommendations based on proven success
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: HOOK RECOMMENDATION")
    logger.info("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # Step 1: Store hook embeddings with performance data
        logger.info("\n1. Storing hook embeddings with performance...")

        sample_hooks = [
            {
                "hook_id": "hook_001",
                "hook_text": "Stop wasting money on gym memberships",
                "hook_type": "pain_agitation",
                "product_category": "fitness_app",
                "target_avatar": "busy_professionals",
                "avg_ctr": 3.5,
                "avg_roas": 4.2,
                "success_rate": 0.85
            },
            {
                "hook_id": "hook_002",
                "hook_text": "Get fit in 15 minutes a day",
                "hook_type": "convenience",
                "product_category": "fitness_app",
                "target_avatar": "busy_parents",
                "avg_ctr": 4.1,
                "avg_roas": 4.8,
                "success_rate": 0.92
            },
            {
                "hook_id": "hook_003",
                "hook_text": "Transform your body without equipment",
                "hook_type": "transformation",
                "product_category": "fitness_app",
                "target_avatar": "home_exercisers",
                "avg_ctr": 3.8,
                "avg_roas": 4.5,
                "success_rate": 0.88
            }
        ]

        for hook in sample_hooks:
            # Generate embedding
            embedding = await embedder.embed_text(hook["hook_text"])

            # Store hook
            await vector_store.store_hook_embedding(
                hook_id=hook["hook_id"],
                hook_text=hook["hook_text"],
                embedding=embedding,
                hook_type=hook["hook_type"],
                product_category=hook["product_category"],
                target_avatar=hook["target_avatar"]
            )

            # Update performance
            await vector_store.update_hook_performance(
                hook_id=hook["hook_id"],
                avg_ctr=hook["avg_ctr"],
                avg_roas=hook["avg_roas"],
                success_rate=hook["success_rate"]
            )

            logger.info(f"  Stored: {hook['hook_id']}")

        # Step 2: Find similar hooks for new product
        logger.info("\n2. Finding hooks for new fitness product...")

        new_product = "Quick home workouts for busy professionals"
        query_embedding = await embedder.embed_text(new_product)

        similar_hooks = await vector_store.find_similar_hooks(
            embedding=query_embedding,
            top_k=3,
            filters={"product_category": "fitness_app", "min_success_rate": 0.8}
        )

        logger.info(f"\nFound {len(similar_hooks)} high-performing hooks:")
        for i, result in enumerate(similar_hooks, 1):
            logger.info(f"\n  {i}. Hook: {result.content}")
            logger.info(f"     Similarity: {result.similarity_score:.4f}")
            logger.info(f"     Type: {result.metadata.get('hook_type')}")
            logger.info(f"     Avg CTR: {result.metadata.get('avg_ctr')}%")
            logger.info(f"     Avg ROAS: {result.metadata.get('avg_roas')}")
            logger.info(f"     Success Rate: {result.metadata.get('success_rate') * 100:.1f}%")

        logger.info("\nUse Case: Use these proven hooks as templates for your campaign!")

    await engine.dispose()


# ============================================================================
# EXAMPLE 3: KNOWLEDGE BASE RAG
# ============================================================================

async def example_knowledge_rag():
    """
    Example: Semantic search for marketing knowledge (RAG).

    Use Case:
    - You need best practices for writing hooks
    - Search knowledge base semantically
    - Get context-aware recommendations
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: KNOWLEDGE BASE RAG")
    logger.info("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # Step 1: Store marketing knowledge
        logger.info("\n1. Storing marketing knowledge...")

        knowledge_items = [
            {
                "content_id": "kb_001",
                "content_type": "best_practice",
                "title": "Pain-Agitation Hook Formula",
                "content": """The pain-agitation hook formula is one of the most effective for direct response:
1. Identify a specific pain point your audience experiences
2. Agitate it by describing the consequences
3. Present your solution as the relief
Example: 'Tired of wasting 2 hours at the gym? Your body isn't the problem - your workout plan is.'""",
                "category": "hook_writing",
                "tags": ["pain_agitation", "hook_formula", "direct_response"],
                "confidence_score": 0.95,
                "source": "proven_campaigns"
            },
            {
                "content_id": "kb_002",
                "content_type": "technique",
                "title": "Transformation Hook Pattern",
                "content": """Transformation hooks work by showing the before-after journey:
1. Paint the current state (undesirable)
2. Show the transformation timeline (specific, achievable)
3. Highlight the end result (desirable)
Example: 'From couch potato to 5K runner in 8 weeks - no gym needed.'""",
                "category": "hook_writing",
                "tags": ["transformation", "before_after", "timeline"],
                "confidence_score": 0.92,
                "source": "case_studies"
            },
            {
                "content_id": "kb_003",
                "content_type": "pattern",
                "title": "Convenience Hook for Busy Audiences",
                "content": """When targeting busy audiences, emphasize time-saving and convenience:
1. Acknowledge their time constraints
2. Quantify the time commitment (be specific and low)
3. Show how it fits into their busy life
Example: 'Get fit in just 15 minutes a day - perfect for your lunch break.'""",
                "category": "hook_writing",
                "tags": ["convenience", "time_saving", "busy_audience"],
                "confidence_score": 0.90,
                "source": "learned"
            }
        ]

        for item in knowledge_items:
            # Generate embedding
            embedding = await embedder.embed_text(item["content"])

            # Store knowledge
            await vector_store.store_knowledge(
                content_id=item["content_id"],
                content_type=item["content_type"],
                title=item["title"],
                content=item["content"],
                embedding=embedding,
                category=item["category"],
                tags=item["tags"],
                confidence_score=item["confidence_score"],
                source=item["source"]
            )

            logger.info(f"  Stored: {item['title']}")

        # Step 2: Search for relevant knowledge
        logger.info("\n2. Searching for hook writing techniques...")

        query = "How to write hooks for fitness products targeting busy people?"
        query_embedding = await embedder.embed_text(query)

        relevant_knowledge = await vector_store.search_knowledge(
            query_embedding=query_embedding,
            top_k=3,
            category="hook_writing",
            min_confidence=0.85
        )

        logger.info(f"\nFound {len(relevant_knowledge)} relevant knowledge items:")
        for i, result in enumerate(relevant_knowledge, 1):
            logger.info(f"\n  {i}. {result.metadata.get('title')}")
            logger.info(f"     Relevance: {result.similarity_score:.4f}")
            logger.info(f"     Type: {result.metadata.get('content_type')}")
            logger.info(f"     Confidence: {result.metadata.get('confidence_score')}")
            logger.info(f"     Content: {result.content[:200]}...")

        logger.info("\nUse Case: Feed this knowledge to your AI hook generator for context-aware generation!")

    await engine.dispose()


# ============================================================================
# EXAMPLE 4: PRODUCT COLD START
# ============================================================================

async def example_product_cold_start():
    """
    Example: Get recommendations for brand new products.

    Use Case:
    - Launching a completely new product
    - No historical campaign data
    - Find similar products and copy their winning patterns
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: PRODUCT COLD START")
    logger.info("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # Step 1: Store product embeddings with historical data
        logger.info("\n1. Storing product embeddings...")

        sample_products = [
            {
                "product_id": "prod_001",
                "product_name": "FitHome - Home Workout App",
                "description": "AI-powered home workout app with personalized plans",
                "offer": "7-day free trial, then $29/month",
                "target_avatar": "Busy professionals 25-40",
                "total_campaigns": 15,
                "avg_roas": 4.2,
                "best_hook_types": ["pain_agitation", "convenience", "transformation"],
                "best_patterns": ["time_scarcity", "no_equipment", "quick_results"]
            },
            {
                "product_id": "prod_002",
                "product_name": "QuickFit - 15 Minute Workouts",
                "description": "Short, effective workouts for busy people",
                "offer": "50% off first month",
                "target_avatar": "Busy parents 30-45",
                "total_campaigns": 22,
                "avg_roas": 4.8,
                "best_hook_types": ["convenience", "time_saving"],
                "best_patterns": ["busy_lifestyle", "minimal_time", "family_friendly"]
            },
            {
                "product_id": "prod_003",
                "product_name": "FlexGym - Virtual Gym Classes",
                "description": "Live virtual fitness classes from home",
                "offer": "Free 14-day trial",
                "target_avatar": "Fitness enthusiasts 20-35",
                "total_campaigns": 18,
                "avg_roas": 3.9,
                "best_hook_types": ["transformation", "community"],
                "best_patterns": ["live_classes", "community", "variety"]
            }
        ]

        for product in sample_products:
            # Generate embedding from product description
            embedding = await embedder.embed_text(
                f"{product['product_name']}: {product['description']}"
            )

            # Store product
            await vector_store.store_product_embedding(
                product_id=product["product_id"],
                product_name=product["product_name"],
                embedding=embedding,
                product_description=product["description"],
                offer=product["offer"],
                target_avatar=product["target_avatar"]
            )

            # Update with historical performance
            await vector_store.update_product_performance(
                product_id=product["product_id"],
                campaign_count_delta=product["total_campaigns"],
                avg_roas=product["avg_roas"],
                best_hook_types=product["best_hook_types"],
                best_creative_patterns=product["best_patterns"]
            )

            logger.info(f"  Stored: {product['product_name']}")

        # Step 2: Find similar products for new launch
        logger.info("\n2. Finding similar products for NEW product...")

        new_product = "WorkoutPro - Smart home fitness with AI coaching and nutrition tracking"
        new_product_embedding = await embedder.embed_text(new_product)

        similar_products = await vector_store.find_similar_products(
            embedding=new_product_embedding,
            top_k=3,
            min_campaigns=10  # Only proven products
        )

        logger.info(f"\nFound {len(similar_products)} similar proven products:")
        for i, result in enumerate(similar_products, 1):
            logger.info(f"\n  {i}. Product: {result.metadata.get('product_name')}")
            logger.info(f"     Similarity: {result.similarity_score:.4f}")
            logger.info(f"     Campaigns: {result.metadata.get('total_campaigns')}")
            logger.info(f"     Avg ROAS: {result.metadata.get('avg_roas')}")
            logger.info(f"     Best Hook Types: {', '.join(result.metadata.get('best_hook_types', []))}")
            logger.info(f"     Best Patterns: {', '.join(result.metadata.get('best_creative_patterns', []))}")

        logger.info("\nUse Case: Use these patterns as starting point for your new product launch!")

    await engine.dispose()


# ============================================================================
# EXAMPLE 5: FULL PIPELINE
# ============================================================================

async def example_full_pipeline():
    """
    Example: Complete integration showing the full workflow.

    Demonstrates:
    1. New campaign starts
    2. Find similar products (cold start)
    3. Get hook recommendations
    4. Get knowledge for generation
    5. Store generated creatives
    6. Track performance
    7. Learn and improve
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 5: FULL PIPELINE INTEGRATION")
    logger.info("=" * 60)

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession)

    async with session_maker() as session:
        vector_store = VectorStore(session)
        embedder = EmbeddingPipeline()

        # PHASE 1: NEW CAMPAIGN STARTS
        logger.info("\n[PHASE 1] New campaign for: 'MealPrepPro - Healthy meal planning app'")

        new_product = {
            "name": "MealPrepPro",
            "description": "AI-powered meal planning and prep app for busy people",
            "offer": "50% off first 3 months",
            "target": "Busy professionals who want to eat healthy"
        }

        # PHASE 2: COLD START - FIND SIMILAR PRODUCTS
        logger.info("\n[PHASE 2] Finding similar products for recommendations...")

        product_text = f"{new_product['name']}: {new_product['description']}"
        product_embedding = await embedder.embed_text(product_text)

        similar_products = await vector_store.find_similar_products(
            embedding=product_embedding,
            top_k=2,
            min_campaigns=5
        )

        logger.info(f"Found {len(similar_products)} similar products")
        recommended_hook_types = []
        for prod in similar_products:
            hook_types = prod.metadata.get('best_hook_types', [])
            recommended_hook_types.extend(hook_types)
        recommended_hook_types = list(set(recommended_hook_types))[:3]
        logger.info(f"Recommended hook types: {', '.join(recommended_hook_types)}")

        # PHASE 3: GET HOOK RECOMMENDATIONS
        logger.info("\n[PHASE 3] Getting hook recommendations...")

        hook_query = f"healthy meal planning for {new_product['target']}"
        hook_embedding = await embedder.embed_text(hook_query)

        similar_hooks = await vector_store.find_similar_hooks(
            embedding=hook_embedding,
            top_k=2,
            filters={"min_success_rate": 0.8}
        )

        logger.info(f"Found {len(similar_hooks)} high-performing hooks")
        for hook in similar_hooks:
            logger.info(f"  - {hook.content} (ROAS: {hook.metadata.get('avg_roas')})")

        # PHASE 4: GET KNOWLEDGE FOR GENERATION
        logger.info("\n[PHASE 4] Getting marketing knowledge...")

        knowledge_query = "How to write hooks about healthy eating and convenience"
        knowledge_embedding = await embedder.embed_text(knowledge_query)

        relevant_knowledge = await vector_store.search_knowledge(
            query_embedding=knowledge_embedding,
            top_k=2,
            min_confidence=0.85
        )

        logger.info(f"Found {len(relevant_knowledge)} relevant knowledge items")
        for kb in relevant_knowledge:
            logger.info(f"  - {kb.metadata.get('title')}")

        # PHASE 5: GENERATE & STORE CREATIVES
        logger.info("\n[PHASE 5] Generating and storing creatives...")

        generated_hook = "Stop wasting hours meal planning - get AI-powered healthy meals in minutes"
        hook_embedding = await embedder.embed_text(generated_hook)

        await vector_store.store_creative_embedding(
            creative_id="mealprep_blueprint_001",
            creative_type="blueprint",
            text_embedding=hook_embedding,
            campaign_id="mealprep_camp_001",
            hook_text=generated_hook,
            hook_type="pain_agitation",
            council_score=8.2,
            predicted_roas=4.0
        )

        logger.info("Stored creative: mealprep_blueprint_001")

        # PHASE 6: TRACK PERFORMANCE (simulated)
        logger.info("\n[PHASE 6] Campaign runs... tracking performance...")
        await asyncio.sleep(0.5)  # Simulate time passing

        await vector_store.update_creative_performance(
            creative_id="mealprep_blueprint_001",
            actual_roas=4.5,
            impressions=30000,
            conversions=150
        )

        logger.info("Performance tracked: ROAS 4.5, 30k impressions, 150 conversions")

        # PHASE 7: LEARN & IMPROVE
        logger.info("\n[PHASE 7] Learning from performance...")

        # Store hook for future recommendations
        await vector_store.store_hook_embedding(
            hook_id="mealprep_hook_001",
            hook_text=generated_hook,
            embedding=hook_embedding,
            hook_type="pain_agitation",
            product_category="meal_planning",
            target_avatar="busy_professionals"
        )

        await vector_store.update_hook_performance(
            hook_id="mealprep_hook_001",
            avg_roas=4.5,
            avg_ctr=3.2,
            success_rate=0.9
        )

        logger.info("Hook stored for future recommendations!")

        # PHASE 8: STATS
        logger.info("\n[PHASE 8] Vector store statistics...")
        stats = await vector_store.get_stats()
        logger.info(f"Total vectors in database: {stats.get('total_vectors')}")
        logger.info(f"  - Creative embeddings: {stats.get('creative_embeddings')}")
        logger.info(f"  - Hook embeddings: {stats.get('hook_embeddings')}")
        logger.info(f"  - Knowledge vectors: {stats.get('knowledge_vectors')}")
        logger.info(f"  - Product embeddings: {stats.get('product_embeddings')}")

        logger.info("\n" + "=" * 60)
        logger.info("FULL PIPELINE COMPLETE!")
        logger.info("=" * 60)

    await engine.dispose()


# ============================================================================
# CLI
# ============================================================================

async def run_example(example_name: str):
    """Run specified example."""
    examples = {
        "creative_similarity": example_creative_similarity,
        "hook_recommendation": example_hook_recommendation,
        "knowledge_rag": example_knowledge_rag,
        "product_cold_start": example_product_cold_start,
        "full_pipeline": example_full_pipeline
    }

    if example_name not in examples:
        logger.error(f"Unknown example: {example_name}")
        logger.info(f"Available examples: {', '.join(examples.keys())}")
        return

    await examples[example_name]()


def main():
    parser = argparse.ArgumentParser(description="Vector Store Integration Examples")
    parser.add_argument(
        '--example',
        type=str,
        default='full_pipeline',
        choices=['creative_similarity', 'hook_recommendation', 'knowledge_rag', 'product_cold_start', 'full_pipeline', 'all'],
        help='Example to run'
    )

    args = parser.parse_args()

    try:
        if args.example == 'all':
            # Run all examples
            examples = ['creative_similarity', 'hook_recommendation', 'knowledge_rag', 'product_cold_start', 'full_pipeline']
            for ex in examples:
                asyncio.run(run_example(ex))
                print("\n\n")
        else:
            asyncio.run(run_example(args.example))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
