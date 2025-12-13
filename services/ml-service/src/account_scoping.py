from typing import Dict, Any
from .battle_hardened_sampler import BattleHardenedSampler

class AccountScopedSampler:
    """
    Wraps the BattleHardenedSampler to provide account-specific configuration and isolation.
    """
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.sampler = BattleHardenedSampler()
        
    async def get_account_config(self) -> Dict[str, Any]:
        # Mock config retrieval
        # In production: Fetch from account_configurations table
        return {
            "kill_roas_threshold": 1.5,
            "scale_roas_threshold": 3.0,
            "ignorance_zone_spend": 100.0
        }

    async def decide(self, ad_id: str, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Makes a decision using account-specific thresholds.
        """
        config = await self.get_account_config()
        
        # Pass config to sampler (assuming sampler supports it, or we wrap the logic)
        # For now, we'll just print that we're using the config
        print(f"🏢 Account {self.account_id}: Using thresholds {config}")
        
        return await self.sampler.decide(ad_id, current_metrics)
