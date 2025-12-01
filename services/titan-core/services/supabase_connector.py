"""
Supabase Connector - Persistence layer for analysis results
Stores video analysis, scores, and insights in Supabase PostgreSQL
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseConnector:
    """
    Connects to Supabase for persisting analysis results.
    Falls back gracefully if Supabase is not configured.
    """

    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        self.client = None
        self.enabled = False

        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.enabled = True
                logger.info("✅ Supabase connector initialized")
            except ImportError:
                logger.warning(
                    "Supabase Python client not installed. "
                    "Install with: pip install supabase"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
        else:
            logger.warning(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables to enable persistence."
            )

    def save_analysis(
        self,
        video_path: str,
        analysis_result: Dict[str, Any]
    ) -> bool:
        """
        Save video analysis results to Supabase.

        Args:
            video_path: Path to the analyzed video
            analysis_result: Analysis results dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Supabase not enabled, skipping save")
            return False

        try:
            # Prepare data for insertion
            data = {
                'video_path': video_path,
                'analysis_result': analysis_result,
                'visual_score': analysis_result.get('visual_score') or analysis_result.get('deep_ad_score', 0),
                'technical_metrics': analysis_result.get('technical_metrics', {}),
                'semantic_analysis': analysis_result.get('semantic_analysis', {}),
                'psychological_profile': analysis_result.get('psychological_profile', {}),
                'analyzed_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }

            # Insert into video_analysis table
            response = self.client.table('video_analysis').insert(data).execute()

            if response.data:
                logger.info(f"✅ Saved analysis for {video_path} to Supabase")
                return True
            else:
                logger.warning(f"No data returned from Supabase insert for {video_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to save analysis to Supabase: {e}")
            return False

    def get_analysis(
        self,
        video_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis results for a video.

        Args:
            video_path: Path to the video

        Returns:
            Analysis results dictionary or None
        """
        if not self.enabled:
            return None

        try:
            response = self.client.table('video_analysis')\
                .select('*')\
                .eq('video_path', video_path)\
                .order('analyzed_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0].get('analysis_result')
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve analysis from Supabase: {e}")
            return None

    def save_campaign_insights(
        self,
        campaign_id: str,
        insights: Dict[str, Any]
    ) -> bool:
        """
        Save Meta campaign insights.

        Args:
            campaign_id: Meta Campaign ID
            insights: Campaign insights dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            data = {
                'campaign_id': campaign_id,
                'insights': insights,
                'avg_ctr': insights.get('ctr_analysis', {}).get('avg_ctr', 0),
                'avg_roas': insights.get('roas_analysis', {}).get('avg_roas', 0),
                'top_performers_count': len(insights.get('top_performers', [])),
                'fetched_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('campaign_insights').insert(data).execute()

            if response.data:
                logger.info(f"✅ Saved campaign insights for {campaign_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to save campaign insights: {e}")
            return False

    def get_top_performing_ads(
        self,
        limit: int = 10,
        min_score: float = 80.0
    ) -> list:
        """
        Get top-performing ads from database.

        Args:
            limit: Maximum number of ads to return
            min_score: Minimum visual score threshold

        Returns:
            List of top-performing ad analysis results
        """
        if not self.enabled:
            return []

        try:
            response = self.client.table('video_analysis')\
                .select('*')\
                .gte('visual_score', min_score)\
                .order('visual_score', desc=True)\
                .limit(limit)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Failed to retrieve top performing ads: {e}")
            return []

    def create_tables_if_not_exist(self) -> bool:
        """
        Create necessary tables in Supabase if they don't exist.
        Note: This requires SUPABASE_SERVICE_ROLE_KEY with admin permissions.

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Supabase not enabled, cannot create tables")
            return False

        logger.info("ℹ️ Table creation should be done via Supabase Dashboard or migrations")
        logger.info("Required tables:")
        logger.info("  - video_analysis (video_path, analysis_result, visual_score, ...)")
        logger.info("  - campaign_insights (campaign_id, insights, avg_ctr, avg_roas, ...)")
        logger.info("Visit https://supabase.com/dashboard to create these tables")

        return False


# Singleton instance
supabase_connector = SupabaseConnector()
