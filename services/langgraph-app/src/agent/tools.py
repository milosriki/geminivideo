from langchain.tools import tool
from typing import List, Dict, Any, Optional
import json

# --- Try to import the actual 20 Agents ---
try:
    from services.ml_service.src.rag.winner_index_db import WinnerIndexDB
    from services.ml_service.src.rag.embedding_service import EmbeddingService
    from services.ml_service.src.mlops.model_registry import ModelRegistry
    from services.ml_service.src.fatigue_auto_remediation import FatigueAutoRemediation
    from services.ml_service.src.account_scoping import AccountScopedSampler
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    print("⚠️ 20 Agents not found in path. Using mocks.")

# --- RAG Tools (Agents 6 & 9) ---

@tool
async def search_winning_ads(query: str) -> str:
    """Search for winning ad patterns using the RAG system (Agent 6)."""
    if AGENTS_AVAILABLE:
        db = WinnerIndexDB()
        embedding_service = EmbeddingService()
        # Generate embedding for query
        query_vec = await embedding_service.generate_creative_dna_embedding({"query": query})
        # Search
        results = await db.search_winners(query_vec)
        return json.dumps(results)
    else:
        return json.dumps([
            {"ad_id": "mock_1", "metadata": {"hook": "Secret", "roas": 4.5}},
            {"ad_id": "mock_2", "metadata": {"hook": "UGC", "roas": 3.8}}
        ])

# --- MLOps Tools (Agents 10 & 12) ---

@tool
async def check_model_status() -> str:
    """Check the current Champion model status (Agent 10)."""
    if AGENTS_AVAILABLE:
        registry = ModelRegistry()
        champion = await registry.get_champion("BattleHardened")
        return json.dumps(champion or {"status": "no_champion"})
    else:
        return json.dumps({"type": "BattleHardened", "version": "v2.1", "stage": "champion"})

@tool
async def check_ad_fatigue(ad_ids: List[str]) -> str:
    """Check for ad fatigue and recommend remediation (Agent 12)."""
    if AGENTS_AVAILABLE:
        # Mocking the result object for the tool
        remediator = FatigueAutoRemediation()
        results = {}
        for ad_id in ad_ids:
            # In a real scenario, we'd fetch metrics first
            from services.ml_service.src.fatigue_auto_remediation import FatigueResult
            mock_result = FatigueResult(ad_id, "none", 0.0, 0.0)
            decision = await remediator.handle_fatigue(ad_id, mock_result, 100.0)
            results[ad_id] = decision
        return json.dumps(results)
    else:
        return json.dumps({"ad_123": {"action": "none"}, "ad_456": {"action": "pause"}})

# --- Marketing Tools (Agent 14) ---

@tool
async def get_account_config(account_id: str) -> str:
    """Get marketing configuration for a specific account (Agent 14)."""
    if AGENTS_AVAILABLE:
        sampler = AccountScopedSampler(account_id)
        config = await sampler.get_account_config()
        return json.dumps(config)
    else:
        return json.dumps({"kill_roas": 1.5, "scale_roas": 3.0})

# --- CRM Tools (Agent 5 - HubSpot) ---

@tool
async def search_crm_contacts(query: str) -> str:
    """Search HubSpot CRM for contacts (Agent 5)."""
    # This would connect to the actual HubSpot API
    return json.dumps([
        {"id": "1", "name": "John Doe", "status": "lead"},
        {"id": "2", "name": "Jane Smith", "status": "customer"}
    ])

ALL_TOOLS = [
    search_winning_ads,
    check_model_status,
    check_ad_fatigue,
    get_account_config,
    search_crm_contacts
]
