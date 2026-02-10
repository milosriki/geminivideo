"""
Data Loader - Fetch training data from PostgreSQL
Enables continuous learning from real Meta performance data
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.feature_engineering import feature_extractor

logger = logging.getLogger(__name__)


class TrainingDataLoader:
    """Load training data from PostgreSQL for XGBoost model"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize data loader
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not set")
        
        # STABILITY FIX: Configure connection pool with proper limits
        self.engine = create_engine(
            self.database_url,
            pool_size=10,  # Maximum number of connections
            max_overflow=20,  # Additional connections beyond pool_size
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            connect_args={
                "connect_timeout": 5,  # 5 second connection timeout
                "application_name": "ml-service-data-loader"
            }
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def fetch_training_data(self, min_impressions: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetch training data from assets table using unified feature extraction
        
        Args:
            min_impressions: Minimum impressions required for an asset to be included
        
        Returns:
            Tuple of (X, y) where X is feature matrix (75+ features) and y is actual CTR values
        """
        logger.info(f"Fetching training data from database (min_impressions={min_impressions})")
        
        session = self.Session()
        
        try:
            # Query to get assets with performance data and clip features
            query = text("""
                SELECT 
                    a.id,
                    pm.impressions,
                    pm.clicks,
                    pm.conversions,
                    pm.roas as actual_roas,
                    a.duration,
                    pm.platform,
                    p.council_score,
                    p.predicted_roas,
                    p.confidence as confidence,
                    cl.features as clip_features,
                    p.hook_type,
                    c.name as product_name,
                    c.target_audience->>'avatar' as target_avatar
                FROM assets a
                JOIN performance_metrics pm ON pm.asset_id = a.id
                JOIN clips cl ON cl.asset_id = a.id
                LEFT JOIN predictions p ON p.clip_id = cl.id
                LEFT JOIN campaigns c ON a.campaign_id = c.id
                WHERE pm.impressions >= :min_impressions
                  AND pm.clicks IS NOT NULL
                  AND pm.impressions > 0
                ORDER BY a.created_at DESC
                LIMIT 10000
            """)
            
            result = session.execute(query, {"min_impressions": min_impressions})
            rows = result.fetchall()
            
            if not rows:
                logger.warning("No training data found in database")
                return None, None
            
            logger.info(f"Fetched {len(rows)} training samples from database")
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(rows, columns=[
                'id', 'impressions', 'clicks', 'conversions', 'actual_roas',
                'duration_seconds', 'platform', 'council_score', 'predicted_roas',
                'confidence', 'clip_features', 'hook_type', 'product_name', 'target_avatar'
            ])
            
            # Calculate actual CTR
            df['actual_ctr'] = df['clicks'] / df['impressions']
            
            # Prepare data for feature extractor
            clips_data_list = []
            
            for _, row in df.iterrows():
                # Start with stored features (from feature extraction time)
                base_features = row['clip_features'] if row['clip_features'] else {}
                
                # Create a copy to avoid modifying original
                clip_data = base_features.copy()
                
                # Merge current metadata overrides ensuring critical fields exist
                clip_data.update({
                    'duration_seconds': float(row['duration_seconds']) if row['duration_seconds'] else 30.0,
                    'platform': row['platform'],
                    'council_score': float(row['council_score']) if row['council_score'] else 0.5,
                    'hook_type': row['hook_type'],
                    # Ensure minimal keys exist if base_features was empty
                    'scene_count': base_features.get('scene_count', 1),
                })
                
                clips_data_list.append(clip_data)
            
            # Use shared feature extractor (Unified Logic)
            # This ensures we get the exact same feature vector as the prediction endpoint
            X = feature_extractor.extract_batch_features(clips_data_list)
            y = df['actual_ctr'].values
            
            logger.info(f"Created unified feature matrix: {X.shape}, target shape: {y.shape}")
            logger.info(f"CTR range: {y.min():.4f} - {y.max():.4f}, mean: {y.mean():.4f}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error fetching training data: {e}")
            raise
        finally:
            session.close()
    
    def get_stats(self) -> dict:
        """Get statistics about available training data"""
        session = self.Session()
        
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN pm.impressions >= 100 THEN 1 END) as videos_with_min_impressions,
                    AVG(pm.impressions) as avg_impressions,
                    AVG(CASE WHEN pm.impressions > 0 THEN pm.clicks::float / pm.impressions END) as avg_ctr
                FROM assets a
                JOIN performance_metrics pm ON pm.asset_id = a.id
                WHERE pm.impressions IS NOT NULL
            """)
            
            result = session.execute(query)
            row = result.fetchone()
            
            return {
                'total_videos': row[0] or 0,
                'videos_with_min_impressions': row[1] or 0,
                'avg_impressions': float(row[2]) if row[2] else 0.0,
                'avg_ctr': float(row[3]) if row[3] else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
        finally:
            session.close()


# Global instance
data_loader = None

def get_data_loader() -> Optional[TrainingDataLoader]:
    """Get or create global data loader instance"""
    global data_loader
    
    if data_loader is None:
        try:
            data_loader = TrainingDataLoader()
        except Exception as e:
            logger.warning(f"Could not initialize TrainingDataLoader: {e}")
            return None
    
    return data_loader
