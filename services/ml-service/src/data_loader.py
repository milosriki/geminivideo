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
        Fetch training data from videos table
        
        Args:
            min_impressions: Minimum impressions required for a video to be included
        
        Returns:
            Tuple of (X, y) where X is feature matrix and y is actual CTR values
        """
        logger.info(f"Fetching training data from database (min_impressions={min_impressions})")
        
        session = self.Session()
        
        try:
            # Query to get videos with performance data
            query = text("""
                SELECT 
                    v.id,
                    v.impressions,
                    v.clicks,
                    v.conversions,
                    v.actual_roas,
                    v.duration_seconds,
                    v.platform,
                    b.council_score,
                    b.predicted_roas,
                    b.confidence,
                    b.hook_text,
                    b.hook_type,
                    c.product_name,
                    c.target_avatar
                FROM videos v
                JOIN blueprints b ON v.blueprint_id = b.id
                JOIN campaigns c ON v.campaign_id = c.id
                WHERE v.impressions >= :min_impressions
                  AND v.clicks IS NOT NULL
                  AND v.impressions > 0
                ORDER BY v.created_at DESC
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
                'confidence', 'hook_text', 'hook_type', 'product_name', 'target_avatar'
            ])
            
            # Calculate actual CTR
            df['actual_ctr'] = df['clicks'] / df['impressions']
            
            # Feature engineering (simplified for now)
            # In a real system, we'd use the full feature_engineering.py
            features = []
            
            for _, row in df.iterrows():
                feature_vec = [
                    row['council_score'] or 0.5,
                    row['predicted_roas'] or 0.0,
                    row['confidence'] or 0.5,
                    row['duration_seconds'] or 30.0,
                    1.0 if row['platform'] == 'reels' else 0.0,
                    1.0 if row['platform'] == 'feed' else 0.0,
                    1.0 if row['platform'] == 'stories' else 0.0,
                    len(row['hook_text']) if row['hook_text'] else 0,
                    1.0 if row['hook_type'] == 'question' else 0.0,
                    1.0 if row['hook_type'] == 'statement' else 0.0,
                    # Add 30 more features to match expected 40 features
                    # For now, use zeros as placeholders
                    *[0.0] * 30
                ]
                features.append(feature_vec)
            
            X = np.array(features)
            y = df['actual_ctr'].values
            
            logger.info(f"Created feature matrix: {X.shape}, target shape: {y.shape}")
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
                    COUNT(CASE WHEN impressions >= 100 THEN 1 END) as videos_with_min_impressions,
                    AVG(impressions) as avg_impressions,
                    AVG(CASE WHEN impressions > 0 THEN clicks::float / impressions END) as avg_ctr
                FROM videos
                WHERE impressions IS NOT NULL
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
