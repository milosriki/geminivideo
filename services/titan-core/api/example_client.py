"""
Example Python client for Titan-Core Master API

This script demonstrates how to:
1. Generate a complete ad campaign
2. Extract top blueprints
3. Render the winning ads
4. Monitor render progress
5. Download completed videos
"""

import requests
import time
import json
from typing import List, Dict, Any


class TitanCoreClient:
    """Python client for Titan-Core Master API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def system_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def evaluate_script(
        self,
        script: str,
        visual_features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Evaluate a script with Council of Titans"""
        payload = {
            "script": script,
            "visual_features": visual_features or {}
        }
        response = self.session.post(
            f"{self.base_url}/council/evaluate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def predict_roas(
        self,
        video_id: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get ROAS prediction from Oracle"""
        payload = {
            "video_id": video_id,
            "features": features
        }
        response = self.session.post(
            f"{self.base_url}/oracle/predict",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def generate_blueprints(
        self,
        product_name: str,
        offer: str,
        target_avatar: str,
        pain_points: List[str],
        desires: List[str],
        num_variations: int = 10,
        platform: str = "reels"
    ) -> Dict[str, Any]:
        """Generate ad blueprints with Director"""
        payload = {
            "product_name": product_name,
            "offer": offer,
            "target_avatar": target_avatar,
            "pain_points": pain_points,
            "desires": desires,
            "num_variations": num_variations,
            "platform": platform
        }
        response = self.session.post(
            f"{self.base_url}/director/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def generate_campaign(
        self,
        product_name: str,
        offer: str,
        target_avatar: str,
        pain_points: List[str],
        desires: List[str],
        num_variations: int = 10,
        approval_threshold: float = 85.0,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete ad campaign (THE MAIN ENDPOINT)

        Returns campaign with top-ranked blueprints
        """
        payload = {
            "product_name": product_name,
            "offer": offer,
            "target_avatar": target_avatar,
            "pain_points": pain_points,
            "desires": desires,
            "num_variations": num_variations,
            "approval_threshold": approval_threshold,
            "platforms": platforms or ["instagram", "tiktok"]
        }
        response = self.session.post(
            f"{self.base_url}/pipeline/generate-campaign",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def start_render(
        self,
        blueprint: Dict[str, Any],
        platform: str = "instagram",
        quality: str = "high",
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """Start a single render job"""
        payload = {
            "blueprint": blueprint,
            "platform": platform,
            "quality": quality,
            "aspect_ratio": aspect_ratio
        }
        response = self.session.post(
            f"{self.base_url}/render/start",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def render_winning(
        self,
        blueprints: List[Dict[str, Any]],
        platform: str = "instagram",
        quality: str = "high",
        aspect_ratio: str = "9:16",
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Render multiple winning blueprints"""
        payload = {
            "blueprints": blueprints,
            "platform": platform,
            "quality": quality,
            "aspect_ratio": aspect_ratio,
            "max_concurrent": max_concurrent
        }
        response = self.session.post(
            f"{self.base_url}/pipeline/render-winning",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_render_status(self, job_id: str) -> Dict[str, Any]:
        """Get render job status"""
        response = self.session.get(f"{self.base_url}/render/{job_id}/status")
        response.raise_for_status()
        return response.json()

    def download_render(self, job_id: str, output_path: str):
        """Download completed render"""
        response = self.session.get(
            f"{self.base_url}/render/{job_id}/download",
            stream=True
        )
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def wait_for_render(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Wait for render to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_render_status(job_id)

            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Render failed: {status.get('error')}")

            print(f"Progress: {status['progress']:.1f}%")
            time.sleep(poll_interval)

        raise TimeoutError(f"Render timed out after {timeout} seconds")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_1_basic_health_check():
    """Example 1: Basic health check"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Health Check")
    print("="*60)

    client = TitanCoreClient()

    # Health check
    health = client.health_check()
    print(f"Health: {health['status']}")

    # System status
    status = client.system_status()
    print(f"Overall Status: {status['overall_status']}")
    print(f"Active Jobs: {status['active_render_jobs']}")

    for component in status['components']:
        icon = "✅" if component['available'] else "❌"
        print(f"{icon} {component['name']}: {component['status']}")


def example_2_evaluate_script():
    """Example 2: Evaluate a script"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Evaluate Script")
    print("="*60)

    client = TitanCoreClient()

    script = """
    Stop scrolling if you want to lose 20lbs in 90 days.
    We help busy professionals transform their bodies without spending hours in the gym.
    Book your free consultation call now.
    """

    result = client.evaluate_script(
        script=script,
        visual_features={
            "has_human_face": True,
            "hook_type": "pattern_interrupt"
        }
    )

    print(f"Final Score: {result['final_score']:.1f}")
    print(f"Approved: {result['approved']}")
    print("\nBreakdown:")
    for model, score in result['breakdown'].items():
        print(f"  {model}: {score:.1f}")


def example_3_generate_blueprints():
    """Example 3: Generate ad blueprints"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Generate Blueprints")
    print("="*60)

    client = TitanCoreClient()

    result = client.generate_blueprints(
        product_name="Elite Fitness Coaching",
        offer="Book your free transformation call",
        target_avatar="Busy professionals 30-45",
        pain_points=["no time for gym", "low energy", "weight gain"],
        desires=["look great", "feel confident", "have energy"],
        num_variations=5
    )

    print(f"Generated {result['count']} blueprints")

    for i, bp in enumerate(result['blueprints'][:3], 1):
        print(f"\n{i}. {bp['title']}")
        print(f"   Hook: {bp['hook_text']}")
        print(f"   CTA: {bp['cta_text']}")


def example_4_complete_campaign():
    """Example 4: Complete campaign generation (THE MAIN WORKFLOW)"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Complete Campaign Generation")
    print("="*60)

    client = TitanCoreClient()

    # Step 1: Generate campaign
    print("\n📝 Step 1: Generating campaign...")
    campaign = client.generate_campaign(
        product_name="Elite Fitness Coaching",
        offer="Book your free transformation call",
        target_avatar="Busy professionals 30-45 who want to get back in shape",
        pain_points=[
            "no time for gym",
            "low energy",
            "gaining weight",
            "feel out of shape"
        ],
        desires=[
            "look great",
            "feel confident",
            "have more energy",
            "be proud of their body"
        ],
        num_variations=10,
        approval_threshold=85.0
    )

    print(f"\n✅ Campaign {campaign['campaign_id']} completed!")
    print(f"   Generated: {campaign['blueprints_generated']}")
    print(f"   Approved: {campaign['blueprints_approved']}")
    print(f"   Rejected: {campaign['blueprints_rejected']}")
    print(f"   Avg Council Score: {campaign['avg_council_score']:.1f}")
    print(f"   Avg Predicted ROAS: {campaign['avg_predicted_roas']:.2f}x")
    print(f"   Duration: {campaign['duration_seconds']:.1f}s")

    # Show top 3 blueprints
    print(f"\n🏆 Top 3 Blueprints:")
    for bp in campaign['top_blueprints'][:3]:
        print(f"\n   Rank {bp['rank']}: {bp['id']}")
        print(f"   Council Score: {bp['council_score']:.1f}")
        print(f"   Predicted ROAS: {bp['predicted_roas']:.2f}x")
        print(f"   Confidence: {bp['confidence']}")

    # Step 2: Render top 3
    print("\n\n🎬 Step 2: Rendering top 3 winners...")
    top_blueprints = [bp['blueprint'] for bp in campaign['top_blueprints'][:3]]

    render_result = client.render_winning(
        blueprints=top_blueprints,
        platform="instagram",
        quality="high",
        aspect_ratio="9:16"
    )

    print(f"✅ Started {render_result['total_jobs']} render jobs")
    print(f"Job IDs: {', '.join(render_result['job_ids'])}")

    # Step 3: Monitor progress
    print("\n\n📊 Step 3: Monitoring render progress...")
    for job_id in render_result['job_ids']:
        print(f"\nJob {job_id}:")
        try:
            status = client.wait_for_render(job_id, timeout=60)
            print(f"  ✅ Completed!")
            print(f"  Output: {status['output_path']}")
        except TimeoutError:
            print(f"  ⏰ Still rendering...")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

    return campaign


def example_5_predict_roas():
    """Example 5: ROAS prediction"""
    print("\n" + "="*60)
    print("EXAMPLE 5: ROAS Prediction")
    print("="*60)

    client = TitanCoreClient()

    prediction = client.predict_roas(
        video_id="test_video_001",
        features={
            "hook_effectiveness": 8.5,
            "has_transformation": True,
            "transformation_believability": 7.0,
            "num_emotional_triggers": 3,
            "cta_strength": 7.5,
            "has_voiceover": True,
            "quality_ratio": 1.5,
            "num_winning_patterns_matched": 2,
            "energy_level": 3,
            "pacing_speed": 3,
            "has_music": True
        }
    )

    print(f"Video ID: {prediction['video_id']}")
    print(f"Final Score: {prediction['final_score']:.1f}/100")
    print(f"\nROAS Prediction:")
    print(f"  Predicted: {prediction['roas_prediction']['predicted_roas']:.2f}x")
    print(f"  Confidence: {prediction['roas_prediction']['confidence_level']}")
    print(f"  Range: {prediction['roas_prediction']['confidence_lower']:.2f}x - {prediction['roas_prediction']['confidence_upper']:.2f}x")
    print(f"\nBreakdown:")
    print(f"  Hook Score: {prediction['hook_score']:.1f}/10")
    print(f"  CTA Score: {prediction['cta_score']:.1f}/10")
    print(f"  Engagement: {prediction['engagement_score']:.1f}/10")
    print(f"  Conversion: {prediction['conversion_score']:.1f}/10")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n🎬 Titan-Core Master API - Example Client")
    print("="*60)

    try:
        # Run examples
        example_1_basic_health_check()
        example_2_evaluate_script()
        example_3_generate_blueprints()
        example_5_predict_roas()

        # The main workflow
        example_4_complete_campaign()

        print("\n\n✅ All examples completed successfully!")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("Make sure the API is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
