"""Semantic search for agent memory - finds past learning."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Semantic search over agent memory."""

    def __init__(self):
        self.client = supabase_client.client

    async def search_memories(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search agent memories semantically."""
        if not self.client:
            return []

        try:
            # Get query embedding (would use OpenAI embeddings in production)
            # For now, use text search as fallback
            query_embedding = await self._get_embedding(query)

            if query_embedding:
                # Use semantic search function
                result = self.client.rpc(
                    "semantic_search_memories",
                    {
                        "query_embedding": query_embedding,
                        "limit_count": limit,
                    },
                ).execute()

                if result.data:
                    return result.data

            # Fallback: text search
            return await self._text_search(query, limit)

        except Exception as e:
            logger.warning(f"Semantic search failed, using text search: {e}")
            return await self._text_search(query, limit)

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text (would use OpenAI in production)."""
        # In production, use:
        # from langchain_openai import OpenAIEmbeddings
        # embeddings = OpenAIEmbeddings()
        # return await embeddings.aembed_query(text)

        # For now, return None to use text search
        return None

    async def _text_search(
        self, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback text search."""
        if not self.client:
            return []

        try:
            # Search in query and response fields
            result = (
                self.client.table("agent_memory")
                .select("*")
                .or_(f"query.ilike.%{query}%,response.ilike.%{query}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            if result.data:
                return [
                    {
                        "id": item.get("id"),
                        "query": item.get("query"),
                        "response": item.get("response"),
                        "similarity": 0.8,  # Placeholder
                    }
                    for item in result.data
                ]

        except Exception as e:
            logger.debug(f"Text search failed: {e}")

        return []

    async def get_relevant_context(
        self, question: str, limit: int = 5
    ) -> str:
        """Get relevant context from past learning."""
        memories = await self.search_memories(question, limit)

        if not memories:
            return "No relevant past learning found."

        context_parts = []
        for memory in memories:
            context_parts.append(
                f"Q: {memory.get('query', '')}\nA: {memory.get('response', '')[:200]}"
            )

        return "\n\n".join(context_parts)


# Global instance
semantic_search = SemanticSearch()

