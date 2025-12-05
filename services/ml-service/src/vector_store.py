"""
Vector Store - pgvector-powered semantic search for creatives, hooks, and knowledge.

Agent 39: Upgrade Vector Database
Replaces in-memory FAISS with persistent PostgreSQL + pgvector.

Features:
- Creative similarity search (find winning creatives similar to new products)
- Hook similarity search (find hooks that worked on similar products)
- Knowledge base RAG (semantic search for marketing best practices)
- Product similarity (cold start recommendations)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import (
    CreativeEmbedding,
    HookEmbedding,
    KnowledgeBaseVector,
    ProductEmbedding
)

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result from similarity search."""
    id: str
    similarity_score: float
    metadata: Dict[str, Any]
    content: Optional[str] = None


class VectorStore:
    """
    Intelligent vector store for semantic search and recommendations.

    Uses PostgreSQL + pgvector for persistent, scalable vector search.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize vector store.

        Args:
            db_session: Async database session
        """
        self.db_session = db_session

    # ========================================================================
    # CREATIVE EMBEDDINGS
    # ========================================================================

    async def store_creative_embedding(
        self,
        creative_id: str,
        creative_type: str,
        text_embedding: Optional[List[float]] = None,
        visual_embedding: Optional[List[float]] = None,
        campaign_id: Optional[str] = None,
        hook_text: Optional[str] = None,
        hook_type: Optional[str] = None,
        council_score: Optional[float] = None,
        predicted_roas: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreativeEmbedding:
        """
        Store creative embedding for similarity search.

        Args:
            creative_id: Unique creative identifier (blueprint_id or video_id)
            creative_type: Type of creative (blueprint, video, hook)
            text_embedding: Text embedding vector (3072 dims for text-embedding-3-large)
            visual_embedding: Visual embedding vector (512 dims for CLIP)
            campaign_id: Associated campaign ID
            hook_text: Hook text content
            hook_type: Type of hook
            council_score: AI council approval score
            predicted_roas: Predicted ROAS
            metadata: Additional metadata

        Returns:
            CreativeEmbedding record
        """
        try:
            # Check if already exists
            result = await self.db_session.execute(
                select(CreativeEmbedding).where(CreativeEmbedding.creative_id == creative_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                if text_embedding:
                    existing.text_embedding = text_embedding
                if visual_embedding:
                    existing.visual_embedding = visual_embedding
                if campaign_id:
                    existing.campaign_id = campaign_id
                if hook_text:
                    existing.hook_text = hook_text
                if hook_type:
                    existing.hook_type = hook_type
                if council_score is not None:
                    existing.council_score = council_score
                if predicted_roas is not None:
                    existing.predicted_roas = predicted_roas
                if metadata:
                    existing.metadata = metadata

                await self.db_session.commit()
                await self.db_session.refresh(existing)
                logger.info(f"Updated creative embedding: {creative_id}")
                return existing
            else:
                # Insert new
                creative_emb = CreativeEmbedding(
                    creative_id=creative_id,
                    creative_type=creative_type,
                    text_embedding=text_embedding,
                    visual_embedding=visual_embedding,
                    campaign_id=campaign_id,
                    hook_text=hook_text,
                    hook_type=hook_type,
                    council_score=council_score,
                    predicted_roas=predicted_roas,
                    metadata=metadata or {}
                )
                self.db_session.add(creative_emb)
                await self.db_session.commit()
                await self.db_session.refresh(creative_emb)
                logger.info(f"Stored creative embedding: {creative_id}")
                return creative_emb

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to store creative embedding: {e}")
            raise

    async def find_similar_creatives(
        self,
        embedding: List[float],
        embedding_type: str = "text",  # "text" or "visual"
        top_k: int = 10,
        min_score: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SimilarityResult]:
        """
        Find similar performing creatives.

        This is POWERFUL for:
        - Finding winning creatives similar to new product
        - Copying successful patterns automatically
        - Cold start recommendations

        Args:
            embedding: Query embedding vector
            embedding_type: Type of embedding ("text" or "visual")
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            filters: Optional filters (campaign_id, hook_type, min_council_score, etc.)

        Returns:
            List of similar creatives with similarity scores
        """
        try:
            # Build query based on embedding type
            if embedding_type == "text":
                embedding_col = CreativeEmbedding.text_embedding
            else:
                embedding_col = CreativeEmbedding.visual_embedding

            # Use cosine similarity (1 - cosine distance)
            similarity = 1 - embedding_col.cosine_distance(embedding)

            query = select(
                CreativeEmbedding,
                similarity.label('similarity')
            ).where(
                embedding_col.isnot(None)
            )

            # Apply filters
            if filters:
                if 'campaign_id' in filters:
                    query = query.where(CreativeEmbedding.campaign_id == filters['campaign_id'])
                if 'hook_type' in filters:
                    query = query.where(CreativeEmbedding.hook_type == filters['hook_type'])
                if 'min_council_score' in filters:
                    query = query.where(CreativeEmbedding.council_score >= filters['min_council_score'])
                if 'creative_type' in filters:
                    query = query.where(CreativeEmbedding.creative_type == filters['creative_type'])

            # Filter by minimum similarity score
            if min_score:
                query = query.having(similarity >= min_score)

            # Order by similarity and limit
            query = query.order_by(similarity.desc()).limit(top_k)

            result = await self.db_session.execute(query)
            rows = result.all()

            results = []
            for creative, score in rows:
                results.append(SimilarityResult(
                    id=creative.creative_id,
                    similarity_score=float(score),
                    metadata={
                        'creative_type': creative.creative_type,
                        'campaign_id': creative.campaign_id,
                        'hook_text': creative.hook_text,
                        'hook_type': creative.hook_type,
                        'council_score': creative.council_score,
                        'predicted_roas': creative.predicted_roas,
                        'actual_roas': creative.actual_roas,
                        'impressions': creative.impressions,
                        'conversions': creative.conversions,
                        **creative.metadata
                    },
                    content=creative.hook_text
                ))

            logger.info(f"Found {len(results)} similar creatives")
            return results

        except Exception as e:
            logger.error(f"Failed to find similar creatives: {e}")
            return []

    async def update_creative_performance(
        self,
        creative_id: str,
        actual_roas: Optional[float] = None,
        impressions: Optional[int] = None,
        conversions: Optional[int] = None
    ) -> bool:
        """
        Update creative performance metrics.

        This enables learning from winners - successful creatives get
        higher weight in similarity search.

        Args:
            creative_id: Creative identifier
            actual_roas: Actual ROAS from campaign
            impressions: Total impressions
            conversions: Total conversions

        Returns:
            Success status
        """
        try:
            result = await self.db_session.execute(
                select(CreativeEmbedding).where(CreativeEmbedding.creative_id == creative_id)
            )
            creative = result.scalar_one_or_none()

            if not creative:
                logger.warning(f"Creative not found: {creative_id}")
                return False

            if actual_roas is not None:
                creative.actual_roas = actual_roas
            if impressions is not None:
                creative.impressions = impressions
            if conversions is not None:
                creative.conversions = conversions

            await self.db_session.commit()
            logger.info(f"Updated creative performance: {creative_id}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update creative performance: {e}")
            return False

    # ========================================================================
    # HOOK EMBEDDINGS
    # ========================================================================

    async def store_hook_embedding(
        self,
        hook_id: str,
        hook_text: str,
        embedding: List[float],
        hook_type: Optional[str] = None,
        product_category: Optional[str] = None,
        target_avatar: Optional[str] = None,
        pain_points: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HookEmbedding:
        """
        Store hook embedding.

        Args:
            hook_id: Unique hook identifier
            hook_text: Hook text content
            embedding: Hook embedding vector (3072 dims)
            hook_type: Type of hook
            product_category: Product category
            target_avatar: Target audience
            pain_points: List of pain points
            metadata: Additional metadata

        Returns:
            HookEmbedding record
        """
        try:
            result = await self.db_session.execute(
                select(HookEmbedding).where(HookEmbedding.hook_id == hook_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.hook_text = hook_text
                existing.embedding = embedding
                if hook_type:
                    existing.hook_type = hook_type
                if product_category:
                    existing.product_category = product_category
                if target_avatar:
                    existing.target_avatar = target_avatar
                if pain_points:
                    existing.pain_points = pain_points
                if metadata:
                    existing.metadata = metadata

                await self.db_session.commit()
                await self.db_session.refresh(existing)
                return existing
            else:
                hook_emb = HookEmbedding(
                    hook_id=hook_id,
                    hook_text=hook_text,
                    embedding=embedding,
                    hook_type=hook_type,
                    product_category=product_category,
                    target_avatar=target_avatar,
                    pain_points=pain_points or [],
                    metadata=metadata or {}
                )
                self.db_session.add(hook_emb)
                await self.db_session.commit()
                await self.db_session.refresh(hook_emb)
                logger.info(f"Stored hook embedding: {hook_id}")
                return hook_emb

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to store hook embedding: {e}")
            raise

    async def find_similar_hooks(
        self,
        hook_text: str = None,
        embedding: List[float] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SimilarityResult]:
        """
        Find hooks that performed well on similar products.

        This enables AUTOMATIC hook recommendation based on what worked
        for similar products/audiences.

        Args:
            hook_text: Hook text (will be embedded if embedding not provided)
            embedding: Pre-computed embedding vector
            top_k: Number of results
            filters: Optional filters (hook_type, product_category, min_success_rate)

        Returns:
            List of similar hooks with performance data
        """
        if embedding is None and hook_text is None:
            raise ValueError("Must provide either hook_text or embedding")

        # If we only have text, we need to embed it
        # For now, require embedding to be passed in
        if embedding is None:
            raise ValueError("Embedding must be provided (embed hook_text first)")

        try:
            similarity = 1 - HookEmbedding.embedding.cosine_distance(embedding)

            query = select(
                HookEmbedding,
                similarity.label('similarity')
            )

            # Apply filters
            if filters:
                if 'hook_type' in filters:
                    query = query.where(HookEmbedding.hook_type == filters['hook_type'])
                if 'product_category' in filters:
                    query = query.where(HookEmbedding.product_category == filters['product_category'])
                if 'min_success_rate' in filters:
                    query = query.where(HookEmbedding.success_rate >= filters['min_success_rate'])
                if 'min_roas' in filters:
                    query = query.where(HookEmbedding.avg_roas >= filters['min_roas'])

            query = query.order_by(similarity.desc()).limit(top_k)

            result = await self.db_session.execute(query)
            rows = result.all()

            results = []
            for hook, score in rows:
                results.append(SimilarityResult(
                    id=hook.hook_id,
                    similarity_score=float(score),
                    metadata={
                        'hook_type': hook.hook_type,
                        'product_category': hook.product_category,
                        'target_avatar': hook.target_avatar,
                        'avg_ctr': hook.avg_ctr,
                        'avg_roas': hook.avg_roas,
                        'total_impressions': hook.total_impressions,
                        'total_conversions': hook.total_conversions,
                        'success_rate': hook.success_rate,
                        **hook.metadata
                    },
                    content=hook.hook_text
                ))

            logger.info(f"Found {len(results)} similar hooks")
            return results

        except Exception as e:
            logger.error(f"Failed to find similar hooks: {e}")
            return []

    async def update_hook_performance(
        self,
        hook_id: str,
        avg_ctr: Optional[float] = None,
        avg_roas: Optional[float] = None,
        impressions_delta: Optional[int] = None,
        conversions_delta: Optional[int] = None,
        success_rate: Optional[float] = None
    ) -> bool:
        """
        Update hook performance metrics.

        Args:
            hook_id: Hook identifier
            avg_ctr: Average CTR
            avg_roas: Average ROAS
            impressions_delta: Additional impressions to add
            conversions_delta: Additional conversions to add
            success_rate: Success rate (0-1)

        Returns:
            Success status
        """
        try:
            result = await self.db_session.execute(
                select(HookEmbedding).where(HookEmbedding.hook_id == hook_id)
            )
            hook = result.scalar_one_or_none()

            if not hook:
                logger.warning(f"Hook not found: {hook_id}")
                return False

            if avg_ctr is not None:
                hook.avg_ctr = avg_ctr
            if avg_roas is not None:
                hook.avg_roas = avg_roas
            if impressions_delta is not None:
                hook.total_impressions = (hook.total_impressions or 0) + impressions_delta
            if conversions_delta is not None:
                hook.total_conversions = (hook.total_conversions or 0) + conversions_delta
            if success_rate is not None:
                hook.success_rate = success_rate

            await self.db_session.commit()
            logger.info(f"Updated hook performance: {hook_id}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update hook performance: {e}")
            return False

    # ========================================================================
    # KNOWLEDGE BASE (RAG)
    # ========================================================================

    async def store_knowledge(
        self,
        content_id: str,
        content_type: str,
        title: str,
        content: str,
        embedding: List[float],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        confidence_score: Optional[float] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBaseVector:
        """
        Store marketing knowledge for RAG-powered generation.

        Args:
            content_id: Unique content identifier
            content_type: Type (best_practice, case_study, pattern, technique)
            title: Title of knowledge
            content: Full content text
            embedding: Content embedding vector (3072 dims)
            category: Category (hook_writing, script_structure, etc.)
            tags: List of tags
            summary: Short summary
            confidence_score: Confidence in this knowledge (0-1)
            source: Source of knowledge
            source_url: Source URL
            metadata: Additional metadata

        Returns:
            KnowledgeBaseVector record
        """
        try:
            result = await self.db_session.execute(
                select(KnowledgeBaseVector).where(KnowledgeBaseVector.content_id == content_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.title = title
                existing.content = content
                existing.embedding = embedding
                if content_type:
                    existing.content_type = content_type
                if category:
                    existing.category = category
                if tags:
                    existing.tags = tags
                if summary:
                    existing.summary = summary
                if confidence_score is not None:
                    existing.confidence_score = confidence_score
                if source:
                    existing.source = source
                if source_url:
                    existing.source_url = source_url
                if metadata:
                    existing.metadata = metadata

                await self.db_session.commit()
                await self.db_session.refresh(existing)
                return existing
            else:
                knowledge = KnowledgeBaseVector(
                    content_id=content_id,
                    content_type=content_type,
                    title=title,
                    content=content,
                    embedding=embedding,
                    category=category,
                    tags=tags or [],
                    summary=summary,
                    confidence_score=confidence_score,
                    source=source,
                    source_url=source_url,
                    metadata=metadata or {}
                )
                self.db_session.add(knowledge)
                await self.db_session.commit()
                await self.db_session.refresh(knowledge)
                logger.info(f"Stored knowledge: {content_id}")
                return knowledge

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to store knowledge: {e}")
            raise

    async def search_knowledge(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        category: Optional[str] = None,
        content_type: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[SimilarityResult]:
        """
        Semantic search for marketing knowledge (RAG).

        This enables CONTEXT-AWARE generation by finding relevant
        best practices and patterns.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            category: Filter by category
            content_type: Filter by content type
            min_confidence: Minimum confidence score

        Returns:
            List of relevant knowledge with similarity scores
        """
        try:
            similarity = 1 - KnowledgeBaseVector.embedding.cosine_distance(query_embedding)

            query = select(
                KnowledgeBaseVector,
                similarity.label('similarity')
            )

            # Apply filters
            if category:
                query = query.where(KnowledgeBaseVector.category == category)
            if content_type:
                query = query.where(KnowledgeBaseVector.content_type == content_type)
            if min_confidence:
                query = query.where(KnowledgeBaseVector.confidence_score >= min_confidence)

            query = query.order_by(similarity.desc()).limit(top_k)

            result = await self.db_session.execute(query)
            rows = result.all()

            results = []
            for kb, score in rows:
                results.append(SimilarityResult(
                    id=kb.content_id,
                    similarity_score=float(score),
                    metadata={
                        'title': kb.title,
                        'content_type': kb.content_type,
                        'category': kb.category,
                        'tags': kb.tags,
                        'summary': kb.summary,
                        'confidence_score': kb.confidence_score,
                        'usage_count': kb.usage_count,
                        'success_rate': kb.success_rate,
                        'source': kb.source,
                        'source_url': kb.source_url,
                        **kb.metadata
                    },
                    content=kb.content
                ))

            logger.info(f"Found {len(results)} relevant knowledge items")
            return results

        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []

    async def increment_knowledge_usage(
        self,
        content_id: str,
        success: bool = True
    ) -> bool:
        """
        Track knowledge usage and success rate.

        Args:
            content_id: Knowledge identifier
            success: Whether usage was successful

        Returns:
            Success status
        """
        try:
            result = await self.db_session.execute(
                select(KnowledgeBaseVector).where(KnowledgeBaseVector.content_id == content_id)
            )
            kb = result.scalar_one_or_none()

            if not kb:
                return False

            kb.usage_count = (kb.usage_count or 0) + 1

            # Update success rate with exponential moving average
            if kb.success_rate is None:
                kb.success_rate = 1.0 if success else 0.0
            else:
                alpha = 0.1  # Smoothing factor
                kb.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * kb.success_rate

            await self.db_session.commit()
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to increment knowledge usage: {e}")
            return False

    # ========================================================================
    # PRODUCT EMBEDDINGS
    # ========================================================================

    async def store_product_embedding(
        self,
        product_id: str,
        product_name: str,
        embedding: List[float],
        product_description: Optional[str] = None,
        offer: Optional[str] = None,
        target_avatar: Optional[str] = None,
        pain_points: Optional[List[str]] = None,
        desires: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProductEmbedding:
        """
        Store product embedding.

        Args:
            product_id: Unique product identifier
            product_name: Product name
            embedding: Product embedding vector (3072 dims)
            product_description: Product description
            offer: Product offer
            target_avatar: Target audience
            pain_points: List of pain points
            desires: List of desires
            metadata: Additional metadata

        Returns:
            ProductEmbedding record
        """
        try:
            result = await self.db_session.execute(
                select(ProductEmbedding).where(ProductEmbedding.product_id == product_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.product_name = product_name
                existing.embedding = embedding
                if product_description:
                    existing.product_description = product_description
                if offer:
                    existing.offer = offer
                if target_avatar:
                    existing.target_avatar = target_avatar
                if pain_points:
                    existing.pain_points = pain_points
                if desires:
                    existing.desires = desires
                if metadata:
                    existing.metadata = metadata

                await self.db_session.commit()
                await self.db_session.refresh(existing)
                return existing
            else:
                product_emb = ProductEmbedding(
                    product_id=product_id,
                    product_name=product_name,
                    embedding=embedding,
                    product_description=product_description,
                    offer=offer,
                    target_avatar=target_avatar,
                    pain_points=pain_points or [],
                    desires=desires or [],
                    metadata=metadata or {}
                )
                self.db_session.add(product_emb)
                await self.db_session.commit()
                await self.db_session.refresh(product_emb)
                logger.info(f"Stored product embedding: {product_id}")
                return product_emb

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to store product embedding: {e}")
            raise

    async def find_similar_products(
        self,
        embedding: List[float],
        top_k: int = 10,
        min_campaigns: Optional[int] = None
    ) -> List[SimilarityResult]:
        """
        Find similar products for cold start recommendations.

        When launching a NEW product, find similar products with
        successful campaigns and copy their winning patterns.

        Args:
            embedding: Product embedding vector
            top_k: Number of results
            min_campaigns: Minimum number of campaigns (filter for proven products)

        Returns:
            List of similar products with historical performance
        """
        try:
            similarity = 1 - ProductEmbedding.embedding.cosine_distance(embedding)

            query = select(
                ProductEmbedding,
                similarity.label('similarity')
            )

            # Filter by minimum campaigns
            if min_campaigns:
                query = query.where(ProductEmbedding.total_campaigns >= min_campaigns)

            query = query.order_by(similarity.desc()).limit(top_k)

            result = await self.db_session.execute(query)
            rows = result.all()

            results = []
            for product, score in rows:
                results.append(SimilarityResult(
                    id=product.product_id,
                    similarity_score=float(score),
                    metadata={
                        'product_name': product.product_name,
                        'offer': product.offer,
                        'target_avatar': product.target_avatar,
                        'total_campaigns': product.total_campaigns,
                        'avg_roas': product.avg_roas,
                        'best_hook_types': product.best_hook_types,
                        'best_creative_patterns': product.best_creative_patterns,
                        **product.metadata
                    },
                    content=product.product_description
                ))

            logger.info(f"Found {len(results)} similar products")
            return results

        except Exception as e:
            logger.error(f"Failed to find similar products: {e}")
            return []

    async def update_product_performance(
        self,
        product_id: str,
        campaign_count_delta: int = 1,
        avg_roas: Optional[float] = None,
        best_hook_types: Optional[List[str]] = None,
        best_creative_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update product performance and learnings.

        Args:
            product_id: Product identifier
            campaign_count_delta: Number of campaigns to add
            avg_roas: New average ROAS
            best_hook_types: List of successful hook types
            best_creative_patterns: List of successful creative patterns

        Returns:
            Success status
        """
        try:
            result = await self.db_session.execute(
                select(ProductEmbedding).where(ProductEmbedding.product_id == product_id)
            )
            product = result.scalar_one_or_none()

            if not product:
                return False

            product.total_campaigns = (product.total_campaigns or 0) + campaign_count_delta

            if avg_roas is not None:
                # Update with exponential moving average
                if product.avg_roas is None:
                    product.avg_roas = avg_roas
                else:
                    alpha = 0.2
                    product.avg_roas = alpha * avg_roas + (1 - alpha) * product.avg_roas

            if best_hook_types:
                product.best_hook_types = best_hook_types
            if best_creative_patterns:
                product.best_creative_patterns = best_creative_patterns

            await self.db_session.commit()
            logger.info(f"Updated product performance: {product_id}")
            return True

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update product performance: {e}")
            return False

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Dict with counts and statistics
        """
        try:
            # Count records in each table
            creative_count = await self.db_session.execute(
                select(func.count()).select_from(CreativeEmbedding)
            )
            hook_count = await self.db_session.execute(
                select(func.count()).select_from(HookEmbedding)
            )
            knowledge_count = await self.db_session.execute(
                select(func.count()).select_from(KnowledgeBaseVector)
            )
            product_count = await self.db_session.execute(
                select(func.count()).select_from(ProductEmbedding)
            )

            return {
                'creative_embeddings': creative_count.scalar(),
                'hook_embeddings': hook_count.scalar(),
                'knowledge_vectors': knowledge_count.scalar(),
                'product_embeddings': product_count.scalar(),
                'total_vectors': (
                    creative_count.scalar() +
                    hook_count.scalar() +
                    knowledge_count.scalar() +
                    product_count.scalar()
                )
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
