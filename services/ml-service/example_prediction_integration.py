"""
Prediction Logger Integration Example

This example shows how to integrate the prediction logging system
with existing ML models and campaign workflows.

Demonstrates:
1. Logging predictions from ML models
2. Storing prediction IDs with video metadata
3. Scheduled task to fetch actuals
4. Performance monitoring and reporting
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.prediction_logger import PredictionLogger


class VideoMLPipeline:
    """
    Example ML pipeline that integrates prediction logging.

    This simulates the flow from video creation through prediction
    logging and eventual validation.
    """

    def __init__(self):
        self.logger = PredictionLogger()

    async def create_video_with_prediction(
        self,
        video_id: str,
        ad_id: str,
        video_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create video and log ML prediction.

        This represents the flow when a new video is created and
        ML models make predictions about its performance.
        """
        print(f"\n--- Creating Video: {video_id} ---")

        # Step 1: Extract features from video
        features = self._extract_features(video_features)
        print(f"✓ Extracted features: hook={features['hook_type']}, template={features['template_type']}")

        # Step 2: Get ML model predictions
        predictions = self._get_ml_predictions(features)
        print(f"✓ ML Predictions: CTR={predictions['ctr']:.4f}, ROAS={predictions['roas']:.2f}")

        # Step 3: Log prediction for later validation
        prediction_id = await self.logger.log_prediction(
            video_id=video_id,
            ad_id=ad_id,
            predicted_ctr=predictions['ctr'],
            predicted_roas=predictions['roas'],
            predicted_conversion=predictions['conversion'],
            council_score=predictions['confidence'],
            hook_type=features['hook_type'],
            template_type=features['template_type'],
            platform=features['platform'],
            metadata={
                'video_duration': features.get('duration', 0),
                'model_version': 'v2.1',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        print(f"✓ Logged prediction: {prediction_id}")

        # Step 4: Return video metadata with prediction ID
        return {
            'video_id': video_id,
            'ad_id': ad_id,
            'prediction_id': prediction_id,
            'predictions': predictions,
            'features': features
        }

    def _extract_features(self, video_features: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from video."""
        return {
            'hook_type': video_features.get('hook_type', 'problem_solution'),
            'template_type': video_features.get('template_type', 'ugc_style'),
            'platform': video_features.get('platform', 'meta'),
            'duration': video_features.get('duration_seconds', 30),
            'has_cta': video_features.get('has_cta', True)
        }

    def _get_ml_predictions(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Get predictions from ML models.

        In production, this would call your actual ML models
        (EnhancedCTRModel, ROASPredictor, etc.)
        """
        # Simulate ML model predictions based on features
        base_ctr = 0.04

        # Hook type impact
        hook_multipliers = {
            'problem_solution': 1.1,
            'testimonial': 1.0,
            'question': 1.15,
            'statistic': 0.95
        }
        hook_mult = hook_multipliers.get(features['hook_type'], 1.0)

        # Template type impact
        template_multipliers = {
            'ugc_style': 1.2,
            'branded': 0.9,
            'minimal': 1.0
        }
        template_mult = template_multipliers.get(features['template_type'], 1.0)

        # Calculate predictions
        predicted_ctr = base_ctr * hook_mult * template_mult

        return {
            'ctr': predicted_ctr,
            'roas': 2.5 + (predicted_ctr * 10),  # Simplified ROAS model
            'conversion': predicted_ctr * 0.25,   # Simplified conversion model
            'confidence': 0.75 + (hook_mult * 0.1)  # Council confidence
        }


class CampaignPerformanceMonitor:
    """
    Monitor campaign performance and update predictions with actuals.

    This would typically run as a scheduled task (daily cron job).
    """

    def __init__(self):
        self.logger = PredictionLogger()

    async def update_pending_predictions(self, days_old: int = 7):
        """
        Fetch actuals for predictions older than specified days.

        This is the key scheduled task that validates predictions
        against real-world performance.
        """
        print(f"\n--- Updating Pending Predictions (>{days_old} days old) ---")

        # Get pending predictions
        pending = await self.logger.get_pending_predictions(
            days_old=days_old,
            min_council_score=0.0  # Include all predictions
        )

        print(f"Found {len(pending)} predictions needing actuals")

        updated_count = 0
        failed_count = 0

        for pred in pending:
            try:
                # Fetch actual performance from platform
                actuals = await self._fetch_platform_performance(pred['ad_id'], pred['platform'])

                if actuals and actuals['impressions'] >= 100:
                    # Update with actuals
                    result = await self.logger.update_with_actuals(
                        prediction_id=pred['id'],
                        actual_ctr=actuals['ctr'],
                        actual_roas=actuals['roas'],
                        actual_conversion=actuals['conversion'],
                        impressions=actuals['impressions'],
                        clicks=actuals['clicks'],
                        spend=actuals['spend']
                    )

                    print(f"✓ Updated {pred['id'][:8]}... - Accuracy: {result['accuracy']['overall_accuracy']:.1f}%")
                    updated_count += 1
                else:
                    print(f"⊘ Insufficient data for {pred['id'][:8]}... (impressions: {actuals.get('impressions', 0)})")

            except Exception as e:
                print(f"✗ Failed to update {pred['id'][:8]}...: {e}")
                failed_count += 1

        print(f"\nResults: {updated_count} updated, {failed_count} failed, {len(pending) - updated_count - failed_count} skipped")

    async def _fetch_platform_performance(
        self,
        ad_id: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch actual performance from ad platform.

        In production, this would call:
        - Meta Marketing API for Facebook/Instagram
        - TikTok Ads API for TikTok
        - Google Ads API for Google/YouTube
        """
        # Simulate fetching from platform API
        # In production, replace with actual API calls

        await asyncio.sleep(0.1)  # Simulate API call

        # Generate simulated actuals
        # In production, this comes from real platform data
        import random

        impressions = random.randint(5000, 20000)
        clicks = int(impressions * random.uniform(0.035, 0.055))
        spend = random.uniform(100, 300)
        conversions = int(clicks * random.uniform(0.008, 0.015))
        revenue = spend * random.uniform(2.0, 4.0)

        return {
            'impressions': impressions,
            'clicks': clicks,
            'spend': spend,
            'ctr': clicks / impressions if impressions > 0 else 0,
            'roas': revenue / spend if spend > 0 else 0,
            'conversion': conversions / clicks if clicks > 0 else 0
        }


class PerformanceReporter:
    """Generate performance reports from prediction data."""

    def __init__(self):
        self.logger = PredictionLogger()

    async def generate_weekly_report(self):
        """Generate weekly model performance report."""
        print("\n" + "=" * 70)
        print("WEEKLY MODEL PERFORMANCE REPORT")
        print("=" * 70)

        # Overall stats
        stats = await self.logger.get_model_performance_stats(days=7)

        print(f"\n📊 Overall Performance (Last 7 Days)")
        print(f"  Total Predictions: {stats['total_predictions']}")
        print(f"  With Actuals: {stats['predictions_with_actuals']}")

        if stats['predictions_with_actuals'] > 0:
            print(f"\n🎯 Accuracy Metrics")
            print(f"  Average Overall Accuracy: {stats['avg_overall_accuracy']:.2f}%")
            print(f"  Average CTR Error: {stats['avg_ctr_error']:.5f}")
            print(f"  Average ROAS Error: {stats['avg_roas_error']:.2f}")
            print(f"  Median Council Score: {stats['median_council_score']:.2f}")

        # Platform breakdown
        print(f"\n📱 Performance by Platform")
        for platform in ['meta', 'tiktok', 'google']:
            platform_stats = await self.logger.get_model_performance_stats(
                days=7,
                platform=platform
            )

            if platform_stats['predictions_with_actuals'] > 0:
                print(f"  {platform.upper()}:")
                print(f"    Predictions: {platform_stats['predictions_with_actuals']}")
                print(f"    Accuracy: {platform_stats['avg_overall_accuracy']:.2f}%")

        print("\n" + "=" * 70)


async def main_workflow():
    """
    Demonstrate complete workflow from prediction to validation.
    """
    print("="*70)
    print("PREDICTION LOGGING INTEGRATION - Complete Workflow Demo")
    print("="*70)

    # Phase 1: Create videos and log predictions
    print("\n🎬 PHASE 1: Create Videos and Log Predictions")
    print("-" * 70)

    pipeline = VideoMLPipeline()
    created_videos = []

    for i in range(3):
        video_data = await pipeline.create_video_with_prediction(
            video_id=f"demo_video_{i+1}",
            ad_id=f"fb_ad_demo_{i+1}",
            video_features={
                'hook_type': ['problem_solution', 'testimonial', 'question'][i],
                'template_type': ['ugc_style', 'branded', 'ugc_style'][i],
                'platform': 'meta',
                'duration_seconds': 30,
                'has_cta': True
            }
        )
        created_videos.append(video_data)

    # Phase 2: Simulate campaign running
    print("\n⏳ PHASE 2: Campaign Running")
    print("-" * 70)
    print("Simulating 7 days of campaign execution...")
    print("(In production, you wait for actual campaigns to run)")
    await asyncio.sleep(1)  # Simulate time passing

    # Phase 3: Update with actuals
    print("\n📈 PHASE 3: Fetch Actuals and Validate Predictions")
    print("-" * 70)

    monitor = CampaignPerformanceMonitor()
    await monitor.update_pending_predictions(days_old=0)  # Use 0 for demo

    # Phase 4: Generate report
    print("\n📊 PHASE 4: Performance Reporting")
    print("-" * 70)

    reporter = PerformanceReporter()
    await reporter.generate_weekly_report()

    # Phase 5: Show specific video results
    print("\n🎯 PHASE 5: Individual Video Results")
    print("-" * 70)

    logger = PredictionLogger()

    for video in created_videos[:2]:  # Show first 2
        predictions = await logger.get_predictions_by_video(
            video['video_id'],
            include_actuals_only=True
        )

        if predictions:
            pred = predictions[0]
            print(f"\nVideo: {video['video_id']}")
            print(f"  Predicted CTR: {pred['predicted']['ctr']:.4f}")
            if pred['actual']:
                print(f"  Actual CTR: {pred['actual']['ctr']:.4f}")
                print(f"  Accuracy: {pred['metadata'].get('overall_accuracy', 0):.1f}%")

    print("\n" + "="*70)
    print("✅ Complete Workflow Demonstration Finished")
    print("="*70)
    print("\nNext Steps:")
    print("1. Integrate with your actual ML models")
    print("2. Set up scheduled task for actuals fetching")
    print("3. Create dashboards using analytical views")
    print("4. Monitor accuracy trends over time")
    print()


if __name__ == "__main__":
    print("\nPrediction Logger Integration Example")
    print("This demonstrates production integration patterns\n")

    # Run the workflow
    asyncio.run(main_workflow())
