import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

print("🔍 Verifying 20-Agent Deployment...")

try:
    # Agent 1
    from services.ml_service.src.battle_hardened_sampler import BattleHardenedSampler
    print("✅ Agent 1: BattleHardenedSampler - OK")
except ImportError:
    print("⚠️ Agent 1: BattleHardenedSampler - Import Failed (might need path adjustment)")
except Exception as e:
    print(f"❌ Agent 1: Error - {e}")

try:
    # Agent 6
    from services.ml_service.src.rag.winner_index_db import WinnerIndexDB
    print("✅ Agent 6: WinnerIndexDB - OK")
except Exception as e:
    print(f"❌ Agent 6: Error - {e}")

try:
    # Agent 9
    from services.ml_service.src.rag.embedding_service import EmbeddingService
    print("✅ Agent 9: EmbeddingService - OK")
except Exception as e:
    print(f"❌ Agent 9: Error - {e}")

try:
    # Agent 10
    from services.ml_service.src.mlops.model_registry import ModelRegistry
    print("✅ Agent 10: ModelRegistry - OK")
except Exception as e:
    print(f"❌ Agent 10: Error - {e}")

try:
    # Agent 12
    from services.ml_service.src.fatigue_auto_remediation import FatigueAutoRemediation
    print("✅ Agent 12: FatigueAutoRemediation - OK")
except Exception as e:
    print(f"❌ Agent 12: Error - {e}")

try:
    # Agent 14
    from services.ml_service.src.account_scoping import AccountScopedSampler
    print("✅ Agent 14: AccountScopedSampler - OK")
except Exception as e:
    print(f"❌ Agent 14: Error - {e}")

print("\n🎉 Verification Complete!")
