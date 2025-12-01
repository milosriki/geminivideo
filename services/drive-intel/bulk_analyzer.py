"""
Google Drive Bulk Analyzer - Analyze all existing ads at once
Scores videos with Council of Titans and generates insights
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

class BulkAdAnalyzer:
    """
    Analyzes multiple video ads from Google Drive in bulk.
    Uses Council of Titans to score each ad and extract winning patterns.
    """

    def __init__(self):
        """Initialize Bulk Analyzer"""
        self.temp_dir = tempfile.mkdtemp(prefix='bulk_analysis_')
        logger.info(f"✅ Bulk Analyzer initialized (temp: {self.temp_dir})")

    async def analyze_drive_folder(
        self,
        folder_id: str,
        max_videos: int = 50,
        niche: str = "fitness"
    ) -> Dict[str, Any]:
        """
        Analyze all video ads in a Google Drive folder.

        Workflow:
        1. Download videos from Google Drive
        2. Analyze each with Council of Titans
        3. Score and rank
        4. Extract patterns from winners
        5. Generate insights

        Args:
            folder_id: Google Drive folder ID containing video ads
            max_videos: Maximum number of videos to analyze (default: 50)
            niche: Business vertical (fitness, e-commerce, education, etc.)

        Returns:
            Dictionary with analysis results and insights
        """
        logger.info(f"🔍 Starting bulk analysis: folder={folder_id}, max={max_videos}")

        try:
            # Step 1: Download videos from Google Drive
            from services.google_drive_service import GoogleDriveService

            drive_service = GoogleDriveService()
            video_files = drive_service.ingest_folder(
                folder_id=folder_id,
                download_path=self.temp_dir,
                max_files=max_videos
            )

            if not video_files:
                return {
                    'success': False,
                    'error': 'No video files found in folder',
                    'videos_analyzed': 0
                }

            logger.info(f"✅ Downloaded {len(video_files)} videos from Google Drive")

            # Step 2: Analyze each video
            analysis_results = []

            for idx, video_info in enumerate(video_files, 1):
                logger.info(f"[{idx}/{len(video_files)}] Analyzing: {video_info['name']}")

                try:
                    result = await self._analyze_single_video(
                        video_path=video_info['local_path'],
                        video_name=video_info['name'],
                        niche=niche
                    )

                    analysis_results.append({
                        **video_info,
                        **result
                    })

                except Exception as e:
                    logger.error(f"Failed to analyze {video_info['name']}: {e}")
                    analysis_results.append({
                        **video_info,
                        'error': str(e),
                        'score': 0
                    })

            # Step 3: Rank by score
            analysis_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # Step 4: Extract patterns from top performers
            patterns = self._extract_patterns_from_results(analysis_results, top_n=10)

            # Step 5: Generate insights
            insights = self._generate_insights(analysis_results, patterns)

            result = {
                'success': True,
                'folder_id': folder_id,
                'videos_analyzed': len(analysis_results),
                'results': analysis_results,
                'patterns': patterns,
                'insights': insights,
                'top_10': analysis_results[:10]
            }

            logger.info(f"✅ Bulk analysis complete: {len(analysis_results)} videos analyzed")

            return result

        except ImportError:
            return {
                'success': False,
                'error': 'Google Drive service not available. Install required packages: '
                         'pip install google-auth google-auth-oauthlib google-api-python-client'
            }
        except Exception as e:
            logger.error(f"Bulk analysis failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'videos_analyzed': 0
            }

    async def _analyze_single_video(
        self,
        video_path: str,
        video_name: str,
        niche: str
    ) -> Dict[str, Any]:
        """
        Analyze a single video with Council of Titans.

        Args:
            video_path: Local path to video file
            video_name: Original video filename
            niche: Business vertical

        Returns:
            Analysis result with score and feedback
        """
        try:
            # Import Council of Titans
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "titan-core"))
            from engines.ensemble import council

            # Analyze video with Deep Video Intelligence first
            try:
                from engines.deep_video_intelligence import DeepVideoIntelligence

                video_intel = DeepVideoIntelligence()
                deep_analysis = video_intel.analyze_video(video_path)

                # Extract script/transcript if available
                transcript = deep_analysis.get('psychological_profile', {}).get('transcript', '')

            except Exception as e:
                logger.warning(f"Deep Video Intelligence failed, using filename only: {e}")
                transcript = video_name
                deep_analysis = {}

            # Evaluate with Council of Titans
            council_result = await council.evaluate_script(
                script_content=transcript or video_name,
                niche=niche
            )

            return {
                'score': council_result.get('final_score', 0),
                'verdict': council_result.get('verdict', 'UNKNOWN'),
                'breakdown': council_result.get('breakdown', {}),
                'feedback': council_result.get('feedback', ''),
                'deep_analysis': deep_analysis,
                'analyzed_at': council_result.get('timestamp')
            }

        except Exception as e:
            logger.error(f"Single video analysis failed: {e}")
            return {
                'score': 0,
                'verdict': 'ERROR',
                'error': str(e)
            }

    def _extract_patterns_from_results(
        self,
        results: List[Dict],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Extract common patterns from top-performing videos.

        Args:
            results: List of analysis results
            top_n: Number of top videos to analyze for patterns

        Returns:
            Dictionary with extracted patterns
        """
        top_videos = [r for r in results if r.get('score', 0) > 70][:top_n]

        if not top_videos:
            return {'patterns': [], 'note': 'No high-scoring videos found'}

        patterns = {
            'avg_score': sum(v.get('score', 0) for v in top_videos) / len(top_videos),
            'common_elements': [],
            'score_distribution': {
                '90-100': len([v for v in results if v.get('score', 0) >= 90]),
                '80-89': len([v for v in results if 80 <= v.get('score', 0) < 90]),
                '70-79': len([v for v in results if 70 <= v.get('score', 0) < 80]),
                '60-69': len([v for v in results if 60 <= v.get('score', 0) < 70]),
                'below_60': len([v for v in results if v.get('score', 0) < 60])
            },
            'model_consensus': {}
        }

        # Analyze model agreement
        for video in top_videos:
            breakdown = video.get('breakdown', {})
            for model, score in breakdown.items():
                if model not in patterns['model_consensus']:
                    patterns['model_consensus'][model] = []
                patterns['model_consensus'][model].append(score)

        # Calculate average scores per model
        for model in patterns['model_consensus']:
            scores = patterns['model_consensus'][model]
            patterns['model_consensus'][model] = sum(scores) / len(scores) if scores else 0

        return patterns

    def _generate_insights(
        self,
        results: List[Dict],
        patterns: Dict
    ) -> List[str]:
        """
        Generate actionable insights from analysis results.

        Args:
            results: All analysis results
            patterns: Extracted patterns from top performers

        Returns:
            List of insight strings
        """
        insights = []

        total_videos = len(results)
        high_scoring = len([r for r in results if r.get('score', 0) >= 80])
        medium_scoring = len([r for r in results if 60 <= r.get('score', 0) < 80])
        low_scoring = len([r for r in results if r.get('score', 0) < 60])

        # Overall performance
        if high_scoring > 0:
            percentage = (high_scoring / total_videos) * 100
            insights.append(f"✅ {high_scoring} videos ({percentage:.1f}%) scored 80+ - These are your winners")

        if low_scoring > total_videos * 0.5:
            insights.append(f"⚠️ {low_scoring} videos scored below 60 - Review hooks and CTA strength")

        # Average score insight
        avg_score = patterns.get('avg_score', 0)
        if avg_score >= 85:
            insights.append(f"🎯 Excellent average score ({avg_score:.1f}) - Your creative quality is strong")
        elif avg_score < 70:
            insights.append(f"📉 Average score ({avg_score:.1f}) needs improvement - Focus on hook strength")

        # Model consensus
        model_consensus = patterns.get('model_consensus', {})
        if model_consensus:
            # Find which model scores highest
            top_model = max(model_consensus.items(), key=lambda x: x[1])
            insights.append(f"🤖 {top_model[0]} rated your ads highest (avg: {top_model[1]:.1f})")

        # Top videos
        if results:
            top_video = results[0]
            insights.append(f"🏆 Top ad: '{top_video.get('name', 'Unknown')}' - Score: {top_video.get('score', 0):.1f}")

        return insights


# Singleton instance
bulk_analyzer = BulkAdAnalyzer()
