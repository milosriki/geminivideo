"""
Ingestion service for processing video files
"""
import os
import uuid
from typing import List, Dict, Any
from pathlib import Path
from models.asset import Asset, Clip, ClipFeatures
from models.persistence import PersistenceLayer


class IngestService:
    """
    Service for ingesting video files and processing them
    """
    
    def __init__(self, persistence: PersistenceLayer):
        self.persistence = persistence
    
    async def ingest_folder(
        self,
        folder_path: str,
        scene_detector,
        feature_extractor,
        search_service
    ) -> Dict[str, Any]:
        """
        Ingest all video files from a folder
        
        Args:
            folder_path: Path to folder containing videos
            scene_detector: Scene detection service
            feature_extractor: Feature extraction service
            search_service: Search service for indexing
            
        Returns:
            Dict with ingestion results
        """
        # Validate and sanitize folder path
        folder_path = os.path.abspath(folder_path)
        
        # Security: Ensure path is within allowed directories
        # In production, configure ALLOWED_PATHS environment variable
        allowed_paths = os.getenv('ALLOWED_INGEST_PATHS', '/data/inputs').split(':')
        if not any(folder_path.startswith(os.path.abspath(allowed)) for allowed in allowed_paths):
            raise ValueError(f"Folder path not in allowed directories: {folder_path}")
        
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder not found: {folder_path}")
        
        # Find video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        video_files = []
        
        for file_path in Path(folder_path).rglob('*'):
            if file_path.suffix.lower() in video_extensions:
                video_files.append(str(file_path))
        
        if not video_files:
            return {
                "status": "error",
                "message": "No video files found in folder",
                "folder_path": folder_path
            }
        
        ingested_assets = []
        
        for video_path in video_files:
            try:
                asset = await self._ingest_video(
                    video_path,
                    scene_detector,
                    feature_extractor
                )
                
                # Add clips to search index
                if asset.clips:
                    search_service.add_clips(asset.clips)
                    # Calculate novelty scores
                    search_service.calculate_novelty_scores(asset.clips)
                
                # Save asset
                self.persistence.save_asset(asset)
                ingested_assets.append(asset.id)
                
            except Exception as e:
                print(f"Error ingesting {video_path}: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"Ingested {len(ingested_assets)} video(s)",
            "folder_path": folder_path,
            "total_videos": len(video_files),
            "successful": len(ingested_assets),
            "asset_ids": ingested_assets
        }
    
    async def _ingest_video(
        self,
        video_path: str,
        scene_detector,
        feature_extractor
    ) -> Asset:
        """
        Ingest a single video file
        
        Args:
            video_path: Path to video file
            scene_detector: Scene detection service
            feature_extractor: Feature extraction service
            
        Returns:
            Asset object with all clips and features
        """
        # Get video info
        video_info = scene_detector.get_video_info(video_path)
        
        # Create asset
        asset = Asset(
            id=str(uuid.uuid4()),
            filename=os.path.basename(video_path),
            filepath=video_path,
            duration=video_info['duration'],
            resolution=video_info['resolution'],
            fps=video_info['fps'],
            file_size=video_info['file_size']
        )
        
        # Detect scenes
        scenes = scene_detector.detect_scenes(video_path)
        
        # Process each scene
        clips = []
        for idx, (start_time, end_time) in enumerate(scenes):
            duration = end_time - start_time
            
            # Skip very short scenes
            if duration < 1.0:
                continue
            
            # Extract features
            features = feature_extractor.extract_features(
                video_path,
                start_time,
                end_time
            )
            
            # Create clip
            clip = Clip(
                id=str(uuid.uuid4()),
                asset_id=asset.id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                features=features
            )
            
            clips.append(clip)
        
        asset.clips = clips
        
        return asset
