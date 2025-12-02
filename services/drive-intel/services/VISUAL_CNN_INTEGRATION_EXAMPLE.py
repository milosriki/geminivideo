"""
Visual CNN Integration Examples
Agent 18: How to integrate VisualPatternAnalyzer into existing systems

This file shows practical integration examples with the existing codebase.
"""
import cv2
import numpy as np
from typing import Dict, List, Any
from visual_cnn import VisualPatternAnalyzer, PatternResult, FrameFeatures


# ==================== Example 1: Integration with FeatureExtractorService ====================

def enhance_feature_extractor():
    """
    Example: Enhance existing FeatureExtractorService with visual_cnn

    This shows how to upgrade feature_extractor.py with more advanced CNN analysis
    """
    from feature_extractor import FeatureExtractorService

    class EnhancedFeatureExtractor(FeatureExtractorService):
        """Enhanced version with VisualPatternAnalyzer"""

        def __init__(self):
            super().__init__()
            self.visual_cnn = VisualPatternAnalyzer()

        def extract_advanced_visual_features(
            self,
            video_path: str,
            start_time: float,
            end_time: float
        ) -> Dict[str, Any]:
            """Extract enhanced visual features using CNN"""

            # Get middle frame
            middle_frame = self._extract_frame(video_path, (start_time + end_time) / 2)

            # Extract CNN features
            cnn_features = self.visual_cnn.extract_features(middle_frame)

            # Classify pattern
            pattern_scores = self.visual_cnn.classify_frame(middle_frame)

            # Detect faces
            faces = self.visual_cnn.detect_faces(middle_frame)

            # Analyze composition
            composition = self.visual_cnn.analyze_frame_composition(middle_frame)

            # Extract colors
            colors = self.visual_cnn.extract_dominant_colors(middle_frame)

            return {
                'cnn_embedding': cnn_features.tolist(),
                'embedding_dim': len(cnn_features),
                'pattern_scores': pattern_scores,
                'primary_pattern': max(pattern_scores.items(), key=lambda x: x[1])[0],
                'faces_detected': len(faces),
                'face_bboxes': [f['bbox'] for f in faces],
                'visual_complexity': composition['complexity'],
                'brightness': composition['brightness'],
                'contrast': composition['contrast'],
                'saturation': composition['saturation'],
                'dominant_colors': [color for color, _ in colors[:3]],
                'color_percentages': [pct for _, pct in colors[:3]]
            }


# ==================== Example 2: Video Similarity Search ====================

class VideoSimilarityEngine:
    """
    Example: Build a video similarity search engine

    Use cases:
    - Find similar ad creatives
    - Detect duplicate content
    - Recommend similar videos
    - Content clustering
    """

    def __init__(self):
        self.analyzer = VisualPatternAnalyzer()
        self.video_index = {}  # path -> features

    def index_video(self, video_path: str) -> None:
        """Add video to searchable index"""
        # Sample frames
        frames = self._sample_frames(video_path, n_frames=10)

        # Extract features
        features = self.analyzer.extract_features_batch(frames)

        # Store average feature vector
        avg_features = np.mean(features, axis=0)
        self.video_index[video_path] = avg_features

    def search_similar(self, query_video: str, top_k: int = 5) -> List[tuple]:
        """Find top-k most similar videos"""
        # Extract query features
        frames = self._sample_frames(query_video, n_frames=10)
        features = self.analyzer.extract_features_batch(frames)
        query_features = np.mean(features, axis=0)

        # Calculate similarities
        similarities = []
        for path, db_features in self.video_index.items():
            sim = self._cosine_similarity(query_features, db_features)
            similarities.append((path, sim))

        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    def _sample_frames(self, video_path: str, n_frames: int = 10) -> List[np.ndarray]:
        """Sample frames from video"""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frames = []
        indices = np.linspace(0, total_frames - 1, n_frames, dtype=int)

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        cap.release()
        return frames


# ==================== Example 3: Ad Creative Analyzer ====================

class AdCreativeAnalyzer:
    """
    Example: Analyze ad creative patterns for optimization

    Use cases:
    - Identify high-performing visual patterns
    - A/B test creative variations
    - Optimize for engagement
    - Quality control
    """

    def __init__(self):
        self.analyzer = VisualPatternAnalyzer()

    def analyze_ad_creative(self, video_path: str) -> Dict[str, Any]:
        """Comprehensive ad creative analysis"""

        # Full pattern analysis
        pattern_result = self.analyzer.classify_pattern(video_path, sample_rate=1)

        # Scene analysis
        scenes = self.analyzer.detect_scene_types(video_path)

        # Motion analysis
        motion_score = self.analyzer.calculate_motion_score(video_path)
        fast_cuts = self.analyzer.detect_fast_cuts(video_path)

        # Thumbnail selection
        thumbnail, thumb_score = self.analyzer.select_best_thumbnail(video_path)

        # Get sample frame for detailed analysis
        frames = self._get_sample_frames(video_path, n=5)

        # Analyze each frame
        frame_analyses = []
        for frame in frames:
            faces = self.analyzer.detect_faces(frame)
            text_density = self.analyzer.calculate_text_density(frame)
            composition = self.analyzer.analyze_frame_composition(frame)

            frame_analyses.append({
                'faces': len(faces),
                'text_density': text_density,
                'complexity': composition['complexity'],
                'brightness': composition['brightness']
            })

        # Aggregate metrics
        avg_faces = np.mean([f['faces'] for f in frame_analyses])
        avg_text = np.mean([f['text_density'] for f in frame_analyses])
        avg_complexity = np.mean([f['complexity'] for f in frame_analyses])

        return {
            # Pattern information
            'primary_pattern': pattern_result.primary_pattern.value,
            'pattern_confidence': pattern_result.pattern_confidences[
                pattern_result.primary_pattern.value
            ],
            'all_patterns': pattern_result.pattern_confidences,

            # Visual metrics
            'visual_complexity': pattern_result.visual_complexity,
            'motion_score': motion_score,
            'has_fast_cuts': fast_cuts,

            # Content analysis
            'avg_faces_per_frame': float(avg_faces),
            'avg_text_density': float(avg_text),
            'avg_visual_complexity': float(avg_complexity),

            # Scene information
            'scene_count': len(scenes),
            'scene_types': [s['type'] for s in scenes],
            'avg_scene_duration': pattern_result.avg_scene_duration,

            # Colors
            'dominant_colors': pattern_result.dominant_colors,

            # Thumbnail
            'thumbnail_quality': thumb_score,

            # Recommendations
            'recommendations': self._generate_recommendations(
                pattern_result, avg_faces, avg_text, motion_score
            )
        }

    def _generate_recommendations(
        self,
        pattern_result: PatternResult,
        avg_faces: float,
        avg_text: float,
        motion_score: float
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if avg_faces < 0.5:
            recommendations.append("Consider adding more face close-ups for engagement")

        if avg_text < 0.1:
            recommendations.append("Add text overlays to improve message retention")

        if motion_score < 0.2:
            recommendations.append("Increase visual movement to capture attention")

        if pattern_result.scene_count < 3:
            recommendations.append("Add more scene variety to maintain interest")

        if pattern_result.visual_complexity < 0.3:
            recommendations.append("Enhance visual richness with more elements")

        return recommendations

    def _get_sample_frames(self, video_path: str, n: int = 5) -> List[np.ndarray]:
        """Get sample frames"""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frames = []
        indices = np.linspace(0, total_frames - 1, n, dtype=int)

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        cap.release()
        return frames


# ==================== Example 4: Real-time Video Classification ====================

class RealTimeVideoClassifier:
    """
    Example: Real-time video classification

    Use cases:
    - Live stream analysis
    - Real-time content moderation
    - Video upload classification
    """

    def __init__(self):
        self.analyzer = VisualPatternAnalyzer()
        self.frame_buffer = []
        self.buffer_size = 30  # 1 second at 30fps

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process single frame in real-time"""

        # Add to buffer
        self.frame_buffer.append(frame)
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)

        # Classify current frame
        pattern_scores = self.analyzer.classify_frame(frame)

        # Quick analysis
        faces = self.analyzer.detect_faces(frame)
        composition = self.analyzer.analyze_frame_composition(frame)

        return {
            'pattern': max(pattern_scores.items(), key=lambda x: x[1])[0],
            'confidence': max(pattern_scores.values()),
            'faces_detected': len(faces),
            'complexity': composition['complexity'],
            'buffer_size': len(self.frame_buffer)
        }

    def get_sequence_analysis(self) -> Dict[str, Any]:
        """Analyze buffered sequence"""
        if len(self.frame_buffer) < 5:
            return {'status': 'insufficient_frames'}

        # Batch process buffer
        features = self.analyzer.extract_features_batch(self.frame_buffer)

        # Classify all frames
        patterns = []
        for frame in self.frame_buffer:
            scores = self.analyzer.classify_frame(frame)
            patterns.append(max(scores.items(), key=lambda x: x[1])[0])

        # Find dominant pattern
        from collections import Counter
        pattern_counts = Counter(patterns)
        dominant_pattern = pattern_counts.most_common(1)[0][0]

        return {
            'status': 'analyzed',
            'frames_analyzed': len(self.frame_buffer),
            'dominant_pattern': dominant_pattern,
            'pattern_stability': pattern_counts[dominant_pattern] / len(patterns),
            'feature_variance': float(np.var(features))
        }


# ==================== Example 5: Batch Video Processing ====================

def batch_process_videos(video_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Example: Batch process multiple videos efficiently

    Use cases:
    - Process uploaded video library
    - Nightly batch jobs
    - Dataset analysis
    """
    analyzer = VisualPatternAnalyzer()
    results = []

    for video_path in video_paths:
        try:
            # Classify pattern
            pattern_result = analyzer.classify_pattern(video_path, sample_rate=2)

            # Select thumbnail
            thumbnail, thumb_score = analyzer.select_best_thumbnail(video_path)

            # Save thumbnail
            thumbnail_path = video_path.replace('.mp4', '_thumb.jpg')
            cv2.imwrite(thumbnail_path, thumbnail)

            results.append({
                'video_path': video_path,
                'status': 'success',
                'primary_pattern': pattern_result.primary_pattern.value,
                'visual_complexity': pattern_result.visual_complexity,
                'motion_score': pattern_result.motion_score,
                'scene_count': pattern_result.scene_count,
                'face_count': pattern_result.face_count,
                'dominant_colors': pattern_result.dominant_colors,
                'thumbnail_path': thumbnail_path,
                'thumbnail_quality': thumb_score
            })

        except Exception as e:
            results.append({
                'video_path': video_path,
                'status': 'error',
                'error': str(e)
            })

    return results


# ==================== Example 6: Pattern-Based Video Recommendation ====================

class PatternBasedRecommender:
    """
    Example: Recommend videos based on visual pattern similarity

    Use cases:
    - Video recommendations
    - Content discovery
    - Similar content suggestions
    """

    def __init__(self):
        self.analyzer = VisualPatternAnalyzer()
        self.video_patterns = {}  # path -> pattern_result

    def index_videos(self, video_paths: List[str]) -> None:
        """Index videos by their patterns"""
        for video_path in video_paths:
            result = self.analyzer.classify_pattern(video_path, sample_rate=3)
            self.video_patterns[video_path] = result

    def recommend_similar(
        self,
        query_video: str,
        n_recommendations: int = 5
    ) -> List[tuple]:
        """Recommend similar videos"""

        # Get query pattern
        query_result = self.analyzer.classify_pattern(query_video, sample_rate=3)
        query_pattern = query_result.primary_pattern.value

        # Calculate similarity scores
        similarities = []
        for video_path, result in self.video_patterns.items():
            if video_path == query_video:
                continue

            # Pattern similarity
            pattern_sim = query_result.pattern_confidences.get(
                result.primary_pattern.value, 0.0
            )

            # Metric similarity
            complexity_sim = 1.0 - abs(
                query_result.visual_complexity - result.visual_complexity
            )
            motion_sim = 1.0 - abs(
                query_result.motion_score - result.motion_score
            )

            # Combined similarity
            total_sim = (
                pattern_sim * 0.5 +
                complexity_sim * 0.25 +
                motion_sim * 0.25
            )

            similarities.append((video_path, total_sim))

        # Sort and return top N
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:n_recommendations]


# ==================== Usage Example ====================

if __name__ == "__main__":
    """
    Example usage of all integration patterns
    """

    # Example 1: Enhanced feature extraction
    print("Example 1: Enhanced Feature Extraction")
    print("-" * 50)
    # extractor = enhance_feature_extractor()
    # features = extractor.extract_advanced_visual_features('video.mp4', 0, 5)
    print("✓ Enhanced feature extractor ready\n")

    # Example 2: Video similarity search
    print("Example 2: Video Similarity Search")
    print("-" * 50)
    # search_engine = VideoSimilarityEngine()
    # search_engine.index_video('video1.mp4')
    # results = search_engine.search_similar('query.mp4', top_k=5)
    print("✓ Similarity search engine ready\n")

    # Example 3: Ad creative analysis
    print("Example 3: Ad Creative Analysis")
    print("-" * 50)
    # ad_analyzer = AdCreativeAnalyzer()
    # analysis = ad_analyzer.analyze_ad_creative('ad.mp4')
    print("✓ Ad creative analyzer ready\n")

    # Example 4: Real-time classification
    print("Example 4: Real-time Classification")
    print("-" * 50)
    # classifier = RealTimeVideoClassifier()
    # result = classifier.process_frame(frame)
    print("✓ Real-time classifier ready\n")

    # Example 5: Batch processing
    print("Example 5: Batch Processing")
    print("-" * 50)
    # results = batch_process_videos(['v1.mp4', 'v2.mp4'])
    print("✓ Batch processor ready\n")

    # Example 6: Pattern-based recommendations
    print("Example 6: Pattern-Based Recommendations")
    print("-" * 50)
    # recommender = PatternBasedRecommender()
    # recommender.index_videos(['v1.mp4', 'v2.mp4'])
    # recommendations = recommender.recommend_similar('query.mp4')
    print("✓ Recommender system ready\n")

    print("=" * 50)
    print("All integration examples ready!")
    print("Uncomment code blocks to run with actual videos")
