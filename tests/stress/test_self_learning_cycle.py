"""
Stress Test: Complete Self-Learning Cycle (7 Loops)
Tests all 7 self-learning loops working together
Covers: Actuals Fetcher → Accuracy Tracker → Auto-Retrain → Compound Learning → 
        Auto-Promote → Cross-Learning → RAG Indexing
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

GATEWAY_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8004"


class SelfLearningCycleTester:
    """Test complete self-learning cycle orchestration"""
    
    async def test_loop_1_actuals_fetcher(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 1: Fetch actual performance from Meta"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/actuals/fetch",
                json={"account_id": account_id, "time_range": "last_30_days"},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "actuals_fetcher",
                    "success": True,
                    "actuals_count": result.get("actuals_count", 0),
                    "linked_predictions": result.get("linked_predictions", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "actuals_fetcher",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "actuals_fetcher",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_2_accuracy_tracker(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 2: Calculate prediction accuracy"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/accuracy/calculate",
                json={"account_id": account_id},
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "accuracy_tracker",
                    "success": True,
                    "accuracy": result.get("accuracy", 0),
                    "rmse": result.get("rmse", 0),
                    "mae": result.get("mae", 0),
                    "r_squared": result.get("r_squared", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "accuracy_tracker",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "accuracy_tracker",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_3_auto_retrain(self, client: httpx.AsyncClient, account_id: str, accuracy: float) -> Dict[str, Any]:
        """Loop 3: Auto-retrain if accuracy < threshold"""
        start_time = time.time()
        
        try:
            if accuracy >= 0.80:
                return {
                    "loop": "auto_retrain",
                    "success": True,
                    "triggered": False,
                    "reason": "Accuracy above threshold",
                    "duration_ms": (time.time() - start_time) * 1000
                }
            
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/train/ctr",
                json={
                    "account_id": account_id,
                    "trigger": "auto_retrain",
                    "min_accuracy": 0.80
                },
                timeout=300.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "auto_retrain",
                    "success": True,
                    "triggered": True,
                    "new_model_version": result.get("model_version"),
                    "champion_score": result.get("champion_score", 0),
                    "challenger_score": result.get("challenger_score", 0),
                    "promoted": result.get("promoted", False),
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "auto_retrain",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "auto_retrain",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_4_compound_learning(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 4: Extract patterns from winners"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/compound-learn/extract",
                json={"account_id": account_id, "time_range": "last_30_days"},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "compound_learning",
                    "success": True,
                    "new_patterns": result.get("new_patterns", 0),
                    "new_knowledge_nodes": result.get("new_knowledge_nodes", 0),
                    "patterns": result.get("patterns", []),
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "compound_learning",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "compound_learning",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_5_auto_promote(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 5: Auto-promote winning ads"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/auto-promote/check",
                json={"account_id": account_id},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "auto_promote",
                    "success": True,
                    "total_checked": result.get("total_checked", 0),
                    "promoted_count": result.get("promoted_count", 0),
                    "budget_increases": result.get("budget_increases", 0),
                    "new_variations": result.get("new_variations", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "auto_promote",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "auto_promote",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_6_cross_learning(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 6: Cross-account pattern sharing"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/cross-learn/share",
                json={"account_id": account_id, "anonymize": True},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "cross_learning",
                    "success": True,
                    "patterns_shared": result.get("patterns_shared", 0),
                    "global_patterns_received": result.get("global_patterns_received", 0),
                    "status": "active",
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "cross_learning",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "cross_learning",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_loop_7_rag_indexing(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Loop 7: Auto-index winners to RAG"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/rag/index-winners",
                json={"account_id": account_id, "auto_index": True},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "loop": "rag_indexing",
                    "success": True,
                    "indexed_count": result.get("indexed_count", 0),
                    "status": "auto_indexed_in_feedback_loop",
                    "duration_ms": duration
                }
            else:
                return {
                    "loop": "rag_indexing",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "loop": "rag_indexing",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_complete_cycle(self, client: httpx.AsyncClient, account_id: str) -> Dict[str, Any]:
        """Test complete self-learning cycle"""
        cycle_start = time.time()
        loops = []
        
        # Loop 1: Actuals Fetcher
        loop1 = await self.test_loop_1_actuals_fetcher(client, account_id)
        loops.append(loop1)
        await asyncio.sleep(1)
        
        # Loop 2: Accuracy Tracker
        loop2 = await self.test_loop_2_accuracy_tracker(client, account_id)
        loops.append(loop2)
        accuracy = loop2.get("accuracy", 0.85) if loop2.get("success") else 0.85
        await asyncio.sleep(1)
        
        # Loop 3: Auto-Retrain
        loop3 = await self.test_loop_3_auto_retrain(client, account_id, accuracy)
        loops.append(loop3)
        await asyncio.sleep(2)
        
        # Loop 4: Compound Learning
        loop4 = await self.test_loop_4_compound_learning(client, account_id)
        loops.append(loop4)
        await asyncio.sleep(1)
        
        # Loop 5: Auto-Promote
        loop5 = await self.test_loop_5_auto_promote(client, account_id)
        loops.append(loop5)
        await asyncio.sleep(1)
        
        # Loop 6: Cross-Learning
        loop6 = await self.test_loop_6_cross_learning(client, account_id)
        loops.append(loop6)
        await asyncio.sleep(1)
        
        # Loop 7: RAG Indexing
        loop7 = await self.test_loop_7_rag_indexing(client, account_id)
        loops.append(loop7)
        
        total_duration = (time.time() - cycle_start) * 1000
        
        successful_loops = sum(1 for l in loops if l.get("success"))
        
        return {
            "success": successful_loops >= 5,  # Allow some loops to fail
            "loops": loops,
            "total_loops": len(loops),
            "successful_loops": successful_loops,
            "total_duration_ms": total_duration,
            "account_id": account_id
        }


async def stress_test_self_learning_cycle(
    concurrent: int = 5,
    total_cycles: int = 20
) -> Dict[str, Any]:
    """Run stress test for complete self-learning cycle"""
    
    logger.info(f"Starting self-learning cycle stress test: {concurrent} concurrent, {total_cycles} total")
    
    # Generate test account IDs
    account_ids = [f"test-account-{uuid.uuid4()}" for _ in range(total_cycles)]
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_cycles, batch_size):
            batch_account_ids = account_ids[i:i + batch_size]
            
            async def run_cycle(account_id):
                tester = SelfLearningCycleTester()
                return await tester.test_complete_cycle(client, account_id)
            
            batch_results = await asyncio.gather(
                *[run_cycle(account_id) for account_id in batch_account_ids],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "loops": []
                    })
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_cycles + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Loop-level analysis
    loop_stats = {}
    for result in results:
        for loop in result.get("loops", []):
            loop_name = loop.get("loop", "unknown")
            if loop_name not in loop_stats:
                loop_stats[loop_name] = {"total": 0, "successful": 0, "durations": []}
            
            loop_stats[loop_name]["total"] += 1
            if loop.get("success"):
                loop_stats[loop_name]["successful"] += 1
                if "duration_ms" in loop:
                    loop_stats[loop_name]["durations"].append(loop["duration_ms"])
    
    loop_analysis = {}
    for loop_name, stats in loop_stats.items():
        loop_analysis[loop_name] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_cycles": total_cycles,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_cycles if total_cycles > 0 else 0,
        "total_duration_seconds": total_duration,
        "cycles_per_second": total_cycles / total_duration if total_duration > 0 else 0,
        "loop_analysis": loop_analysis,
        "avg_cycle_duration_ms": np.mean([r.get("total_duration_ms", 0) for r in successful]) if successful else 0,
        "p95_cycle_duration_ms": np.percentile([r.get("total_duration_ms", 0) for r in successful], 95) if successful else 0
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_self_learning_cycle(concurrent=3, total_cycles=10))

