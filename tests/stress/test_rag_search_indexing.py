"""
Stress Test: RAG Search and Indexing
Tests RAG system: Winner Index → FAISS Search → GCS Storage → Redis Cache
Covers: Indexing winners, semantic search, pattern extraction, knowledge graph
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any
import httpx
import logging
import uuid

logger = logging.getLogger(__name__)

ML_SERVICE_URL = "http://localhost:8004"
GATEWAY_URL = "http://localhost:8000"


class RAGSearchIndexingTester:
    """Test RAG search and indexing"""
    
    async def test_index_winner(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test indexing a winning ad"""
        start_time = time.time()
        
        try:
            winner_data = {
                "ad_id": ad_id,
                "creative_dna": {
                    "hook_type": random.choice(["testimonial", "transformation", "problem_solution"]),
                    "visual_style": random.choice(["ugc", "professional", "before_after"]),
                    "emotion": random.choice(["desire", "belonging", "fear"]),
                    "hook_text": f"Transform your life in {random.randint(7, 30)} days",
                    "cta_text": "Start Now"
                },
                "performance": {
                    "ctr": random.uniform(0.03, 0.10),
                    "roas": random.uniform(3.0, 8.0),
                    "pipeline_roas": random.uniform(4.0, 10.0),
                    "impressions": random.randint(10000, 100000)
                },
                "metadata": {
                    "platform": "instagram",
                    "campaign_id": f"campaign_{uuid.uuid4()}",
                    "created_at": time.time()
                }
            }
            
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/rag/index-winner",
                json=winner_data,
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "index_winner",
                "success": response.status_code in [200, 201],
                "ad_id": ad_id,
                "indexed": response.json().get("indexed", False) if response.status_code in [200, 201] else False,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "index_winner",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_semantic_search(self, client: httpx.AsyncClient, query: str) -> Dict[str, Any]:
        """Test semantic search in RAG"""
        start_time = time.time()
        
        try:
            search_data = {
                "query": query,
                "top_k": random.randint(3, 10),
                "filters": {
                    "min_roas": random.uniform(2.0, 5.0),
                    "hook_type": random.choice(["testimonial", "transformation", "problem_solution", None])
                }
            }
            
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/rag/search-winners",
                json=search_data,
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                matches = result.get("matches", [])
                return {
                    "operation": "semantic_search",
                    "success": True,
                    "query": query,
                    "matches_count": len(matches),
                    "top_k": search_data["top_k"],
                    "avg_similarity": np.mean([m.get("similarity", 0) for m in matches]) if matches else 0,
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "semantic_search",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "semantic_search",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pattern_extraction(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test pattern extraction from winners"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/pattern-extractor/analyze",
                json={
                    "top_n": random.randint(5, 20),
                    "time_period": random.choice(["last_month", "last_quarter", "last_90_days"]),
                    "analysis_type": "principles"
                },
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "operation": "pattern_extraction",
                    "success": True,
                    "patterns_found": result.get("patterns_count", 0),
                    "principles": result.get("principles", []),
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "pattern_extraction",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "pattern_extraction",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_creative_dna_extraction(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test creative DNA extraction"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/creative-dna/extract",
                json={"ad_id": ad_id},
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "operation": "creative_dna_extraction",
                    "success": True,
                    "dna_score": result.get("dna_score", 0),
                    "dna_components": result.get("components", {}),
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "creative_dna_extraction",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "creative_dna_extraction",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_knowledge_graph_update(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test knowledge graph update"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/knowledge-graph/update",
                json={
                    "patterns": [
                        {
                            "pattern_type": "hook",
                            "pattern": "Transform in X days",
                            "effectiveness": 0.85
                        }
                    ],
                    "source": "rag_indexing"
                },
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "knowledge_graph_update",
                "success": response.status_code in [200, 201],
                "nodes_added": response.json().get("nodes_added", 0) if response.status_code in [200, 201] else 0,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "knowledge_graph_update",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_faiss_search_performance(self, client: httpx.AsyncClient, query_embedding: List[float]) -> Dict[str, Any]:
        """Test FAISS search performance"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/rag/search-winners",
                json={
                    "query_embedding": query_embedding,
                    "top_k": 10
                },
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "operation": "faiss_search",
                    "success": True,
                    "results_count": len(result.get("matches", [])),
                    "search_time_ms": duration,
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "faiss_search",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "faiss_search",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_rag_search_indexing(
    concurrent: int = 30,
    total_operations: int = 300
) -> Dict[str, Any]:
    """Run stress test for RAG search and indexing"""
    
    logger.info(f"Starting RAG search and indexing stress test: {concurrent} concurrent, {total_operations} total")
    
    tester = RAGSearchIndexingTester()
    results = []
    start_time = time.time()
    
    # Generate test queries
    queries = [
        "winning ads with high ROAS",
        "testimonial style hooks that convert",
        "transformation videos with strong emotional appeal",
        "problem solution ads for fitness",
        "before and after videos with high CTR"
    ]
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Index winners
        indexing_tasks = []
        for i in range(total_operations // 3):
            ad_id = f"ad_{uuid.uuid4()}"
            indexing_tasks.append(tester.test_index_winner(client, ad_id))
        
        indexing_results = await asyncio.gather(*indexing_tasks, return_exceptions=True)
        results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in indexing_results])
        
        await asyncio.sleep(2)  # Allow indexing to complete
        
        # Semantic search
        search_tasks = []
        for _ in range(total_operations // 3):
            query = random.choice(queries)
            search_tasks.append(tester.test_semantic_search(client, query))
        
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in search_results])
        
        # Pattern extraction and other operations
        other_tasks = []
        for _ in range(total_operations // 3):
            operation = random.choice([
                tester.test_pattern_extraction(client),
                tester.test_creative_dna_extraction(client, f"ad_{uuid.uuid4()}"),
                tester.test_knowledge_graph_update(client)
            ])
            other_tasks.append(operation)
        
        other_results = await asyncio.gather(*other_tasks, return_exceptions=True)
        results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in other_results])
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Operation-level analysis
    operation_stats = {}
    for result in results:
        operation = result.get("operation", "unknown")
        if operation not in operation_stats:
            operation_stats[operation] = {"total": 0, "successful": 0, "durations": []}
        
        operation_stats[operation]["total"] += 1
        if result.get("success"):
            operation_stats[operation]["successful"] += 1
            if "duration_ms" in result:
                operation_stats[operation]["durations"].append(result["duration_ms"])
    
    operation_analysis = {}
    for operation, stats in operation_stats.items():
        operation_analysis[operation] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_operations": total_operations,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(results) if results else 0,
        "total_duration_seconds": total_duration,
        "operations_per_second": len(results) / total_duration if total_duration > 0 else 0,
        "operation_analysis": operation_analysis
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_rag_search_indexing(concurrent=20, total_operations=100))

