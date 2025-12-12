"""Super Agent 7: Open Source Learner - Learns from websites about topics."""

from typing import Any, Dict, List, Optional
import logging
import requests
from datetime import datetime
from urllib.parse import quote

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class OpenSourceLearnerAgent(SuperAgent):
    """Learns from open source websites about video ads, marketing, psychology topics."""

    def __init__(self, **kwargs):
        super().__init__(
            name="OpenSourceLearnerAgent",
            description=(
                "Open source learner. Scrapes and learns from websites about video ads, "
                "marketing, psychology, business strategy, and related topics. Builds "
                "knowledge base from open source content."
            ),
            domains=[
                "Web Scraping",
                "Content Learning",
                "Knowledge Base Building",
                "Topic Research",
                "Open Source Intelligence",
            ],
            thinking_steps=4,
            **kwargs,
        )
        self.client = supabase_client.client

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute open source learning operations."""
        operation = input_data.get("operation", "learn_from_web")

        if operation == "learn_from_web":
            return await self._learn_from_web(input_data, thinking)
        elif operation == "learn_about_topic":
            return await self._learn_about_topic(input_data, thinking)
        elif operation == "scrape_article":
            return await self._scrape_article(input_data, thinking)
        elif operation == "build_knowledge_base":
            return await self._build_knowledge_base(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _learn_from_web(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn from web sources about video ads and marketing."""
        try:
            topics = input_data.get("topics", [
                "video ad optimization",
                "Facebook ads best practices",
                "video marketing psychology",
                "conversion optimization",
                "ad creative strategies",
            ])

            learned_content = []

            for topic in topics:
                # Use web search (in production, use proper web scraping)
                # For now, save topic for learning
                content = {
                    "topic": topic,
                    "learned_at": datetime.now().isoformat(),
                    "source": "web_search",
                    "content": f"Knowledge about {topic}",
                }

                learned_content.append(content)

                # Save to memory
                if self.client:
                    self.client.table("agent_memory").insert({
                        "key": f"web_learning_{quote(topic)}",
                        "value": content,
                        "type": "web_learning",
                        "metadata": {
                            "topic": topic,
                            "source": "open_source",
                        },
                    }).execute()

            logger.info(f"✅ Learned about {len(topics)} topics from web")

            return {
                "topics_learned": len(topics),
                "learned_content": learned_content,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Web learning error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _learn_about_topic(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn about a specific topic from open source."""
        topic = input_data.get("topic", "video ads")

        # Key sources for video ads knowledge
        sources = [
            "YouTube Creator Academy",
            "Facebook Business Help Center",
            "Marketing blogs",
            "Psychology research papers",
            "Business strategy resources",
        ]

        knowledge = {
            "topic": topic,
            "sources": sources,
            "key_insights": [
                f"Best practices for {topic}",
                f"Common mistakes in {topic}",
                f"Advanced strategies for {topic}",
            ],
            "learned_at": datetime.now().isoformat(),
        }

        # Save to memory
        if self.client:
            self.client.table("agent_memory").insert({
                "key": f"topic_learning_{quote(topic)}",
                "value": knowledge,
                "type": "topic_learning",
            }).execute()

        return {
            "topic": topic,
            "knowledge": knowledge,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _scrape_article(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scrape article content from URL."""
        url = input_data.get("url")

        if not url:
            return {"error": "URL required"}

        try:
            # In production, use proper web scraping (BeautifulSoup, etc.)
            # For now, save URL for processing
            article_data = {
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "content": "Article content would be scraped here",
            }

            if self.client:
                self.client.table("agent_memory").insert({
                    "key": f"scraped_article_{quote(url)}",
                    "value": article_data,
                    "type": "scraped_article",
                }).execute()

            return {
                "url": url,
                "article_data": article_data,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Article scraping error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _build_knowledge_base(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build knowledge base from all learned content."""
        try:
            if self.client:
                # Get all web learning
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .in_("type", ["web_learning", "topic_learning", "scraped_article"])
                    .order("created_at", desc=True)
                    .limit(500)
                    .execute()
                )

                all_learning = result.data or []

                # Build knowledge base
                knowledge_base = {
                    "total_items": len(all_learning),
                    "topics": list(set(item.get("value", {}).get("topic", "") for item in all_learning if item.get("value", {}).get("topic"))),
                    "sources": list(set(item.get("metadata", {}).get("source", "") for item in all_learning if item.get("metadata", {}).get("source"))),
                    "built_at": datetime.now().isoformat(),
                }

                # Save knowledge base
                self.client.table("agent_memory").insert({
                    "key": "open_source_knowledge_base",
                    "value": knowledge_base,
                    "type": "knowledge_base",
                }).execute()

                return {
                    "knowledge_base": knowledge_base,
                    "items_count": len(all_learning),
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Knowledge base building error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

