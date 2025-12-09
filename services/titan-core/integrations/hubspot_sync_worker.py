import logging
import time
from typing import List, Dict, Any
import requests
import os

logger = logging.getLogger(__name__)

class HubSpotSyncWorker:
    """
    Worker to batch sync deals from HubSpot CRM.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUBSPOT_ACCESS_TOKEN")
        self.base_url = "https://api.hubapi.com/crm/v3/objects/deals"
        
    def fetch_recent_deals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch recently modified deals.
        """
        if not self.api_key:
            logger.warning("HubSpot API key not found. Skipping sync.")
            return []
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "limit": limit,
            "properties": ["dealname", "amount", "dealstage", "hs_analytics_source_data_1"],
            "sort": "-hs_lastmodifieddate"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Error fetching HubSpot deals: {e}")
            return []

    def sync_to_ml_service(self, ml_service_url: str):
        """
        Fetch deals and push to ML service for ingestion.
        """
        deals = self.fetch_recent_deals()
        if not deals:
            return
            
        # Transform deals to ad performance format
        ad_performances = {}
        for deal in deals:
            props = deal.get("properties", {})
            # Extract ad_id from UTM or custom property
            # This is a simplified logic for the worker
            utm_content = props.get("hs_analytics_source_data_1", "")
            if "utm_content=" in utm_content:
                try:
                    ad_id = utm_content.split("utm_content=")[1].split("&")[0]
                    amount = float(props.get("amount") or 0)
                    if ad_id:
                        ad_performances[ad_id] = ad_performances.get(ad_id, 0) + amount
                except:
                    pass
        
        if ad_performances:
            try:
                requests.post(
                    f"{ml_service_url}/api/ml/ingest-crm-data",
                    json={"ad_performances": ad_performances},
                    timeout=5
                )
                logger.info(f"Synced {len(ad_performances)} ad records to ML service")
            except Exception as e:
                logger.error(f"Error pushing to ML service: {e}")

if __name__ == "__main__":
    # Simple standalone execution
    logging.basicConfig(level=logging.INFO)
    worker = HubSpotSyncWorker()
    worker.sync_to_ml_service("http://localhost:8003")
