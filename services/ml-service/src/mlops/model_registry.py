from typing import Dict, Optional
import time

class ModelRegistry:
    """
    Manages the lifecycle of ML models (Champion/Challenger framework).
    """
    
    def __init__(self):
        self.registry = {} # Mock registry: model_id -> metadata

    async def register_model(
        self,
        model_type: str,
        version: str,
        stage: str,  # 'champion', 'challenger', 'archived'
        metrics: Dict[str, float]
    ) -> str:
        """
        Registers a new model version.
        """
        model_id = f"{model_type}_v{version}"
        print(f"📦 Registering model: {model_id} ({stage})")
        
        self.registry[model_id] = {
            "type": model_type,
            "version": version,
            "stage": stage,
            "metrics": metrics,
            "created_at": time.time()
        }
        return model_id

    async def promote_challenger(self, model_id: str) -> None:
        """
        Promotes a challenger model to champion.
        """
        if model_id not in self.registry:
            raise ValueError(f"Model {model_id} not found")
            
        # Demote current champion
        model_type = self.registry[model_id]["type"]
        for mid, data in self.registry.items():
            if data["type"] == model_type and data["stage"] == "champion":
                data["stage"] = "archived"
                print(f"📉 Demoted {mid} to archived")
        
        # Promote new champion
        self.registry[model_id]["stage"] = "champion"
        print(f"🏆 Promoted {model_id} to champion")

    async def get_champion(self, model_type: str) -> Optional[Dict]:
        for data in self.registry.values():
            if data["type"] == model_type and data["stage"] == "champion":
                return data
        return None
