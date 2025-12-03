"""
Vertex AI Service Demo
Shows how to use the real Vertex AI integration for video analysis, image generation, and more.
"""

import os
from vertex_ai import VertexAIService, VideoAnalysis

def main():
    """Demo various Vertex AI capabilities."""

    # Initialize service
    print("🚀 Initializing Vertex AI Service...")
    service = VertexAIService(
        project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location="us-central1"
    )

    # ========================================================================
    # 1. VIDEO ANALYSIS
    # ========================================================================
    print("\n" + "="*60)
    print("1. VIDEO ANALYSIS")
    print("="*60)

    # Analyze a video from GCS
    video_uri = "gs://your-bucket/sample-ad.mp4"
    print(f"\n📹 Analyzing video: {video_uri}")

    analysis = service.analyze_video(video_uri)

    print(f"\n📊 Results:")
    print(f"  Summary: {analysis.summary}")
    print(f"  Scenes: {len(analysis.scenes)}")
    print(f"  Objects: {', '.join(analysis.objects_detected[:5])}")
    print(f"  Sentiment: {analysis.sentiment}")
    print(f"  Hook Quality: {analysis.hook_quality}/100")
    print(f"  Engagement Score: {analysis.engagement_score}/100")
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"  {i}. {rec}")

    # ========================================================================
    # 2. AD COPY GENERATION
    # ========================================================================
    print("\n" + "="*60)
    print("2. AD COPY GENERATION")
    print("="*60)

    product_info = """
    Smart Fitness Watch with:
    - 24/7 heart rate monitoring
    - 50+ workout modes
    - 7-day battery life
    - Waterproof design
    - Sleep tracking
    Price: $199
    """

    print("\n✍️ Generating ad copy variants...")
    variants = service.generate_ad_copy(
        product_info=product_info,
        style="urgent",
        num_variants=3
    )

    for i, variant in enumerate(variants, 1):
        print(f"\n📝 Variant {i}:")
        print(f"  {variant}")

    # ========================================================================
    # 3. HOOK IMPROVEMENT
    # ========================================================================
    print("\n" + "="*60)
    print("3. HOOK IMPROVEMENT")
    print("="*60)

    current_hook = "Check out this new fitness watch!"
    target_emotion = "urgency"

    print(f"\n🎣 Current hook: {current_hook}")
    print(f"🎯 Target emotion: {target_emotion}")
    print("\n🔄 Improved hooks:")

    improved_hooks = service.improve_hook(current_hook, target_emotion)
    for i, hook in enumerate(improved_hooks, 1):
        print(f"  {i}. {hook}")

    # ========================================================================
    # 4. COMPETITOR ANALYSIS
    # ========================================================================
    print("\n" + "="*60)
    print("4. COMPETITOR ANALYSIS")
    print("="*60)

    competitor_video = "gs://your-bucket/competitor-ad.mp4"
    print(f"\n🔍 Analyzing competitor: {competitor_video}")

    insights = service.analyze_competitor_ad(competitor_video)
    print(f"\n📊 Competitor Insights:")
    print(f"  Hook Quality: {insights.get('hook_quality')}/100")
    print(f"  Engagement: {insights.get('engagement_score')}/100")
    print(f"\n💡 Key Learnings:")
    for rec in insights.get('recommendations', [])[:3]:
        print(f"  - {rec}")

    # ========================================================================
    # 5. IMAGE GENERATION
    # ========================================================================
    print("\n" + "="*60)
    print("5. IMAGE GENERATION")
    print("="*60)

    image_prompt = "A sleek fitness watch on a runner's wrist, sunset background, professional product photography"
    print(f"\n🎨 Generating images: {image_prompt}")

    images = service.generate_image(
        prompt=image_prompt,
        aspect_ratio="1:1",
        num_images=2
    )

    print(f"\n✅ Generated {len(images)} images")
    for i, img_bytes in enumerate(images):
        output_path = f"generated_image_{i+1}.jpg"
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"  Saved: {output_path} ({len(img_bytes)} bytes)")

    # ========================================================================
    # 6. TEXT EMBEDDINGS
    # ========================================================================
    print("\n" + "="*60)
    print("6. TEXT EMBEDDINGS")
    print("="*60)

    texts = [
        "High-performance fitness watch",
        "Premium smartwatch for athletes",
        "Luxury timepiece for executives",
        "Budget-friendly activity tracker"
    ]

    print("\n📊 Generating embeddings for similarity search...")
    embeddings = service.embed_texts(texts)

    print(f"\n✅ Generated embeddings: {embeddings.shape}")

    # Calculate similarity between first two
    import numpy as np
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    print(f"\n🔗 Similarity between '{texts[0]}' and '{texts[1]}':")
    print(f"  {similarity:.3f}")

    # ========================================================================
    # 7. STORYBOARD GENERATION
    # ========================================================================
    print("\n" + "="*60)
    print("7. STORYBOARD GENERATION")
    print("="*60)

    print("\n🎬 Generating video ad storyboard...")
    storyboard = service.generate_storyboard(
        product_description=product_info,
        style="energetic"
    )

    print(f"\n✅ Generated {len(storyboard)} scenes:")
    for scene in storyboard:
        print(f"\n  ⏱️ {scene.get('timestamp', 'N/A')}")
        print(f"  📝 {scene.get('description', 'N/A')}")
        print(f"  🎯 Purpose: {scene.get('purpose', 'N/A')}")

    # ========================================================================
    # 8. CHAT SESSION
    # ========================================================================
    print("\n" + "="*60)
    print("8. CHAT SESSION")
    print("="*60)

    print("\n💬 Starting chat session...")
    chat = service.start_chat(
        system_instruction="You are an expert marketing consultant specializing in video ads."
    )

    messages = [
        "What makes a good hook for a fitness product ad?",
        "How long should the video be?",
        "What's the best aspect ratio for Instagram Reels?"
    ]

    for msg in messages:
        print(f"\n👤 User: {msg}")
        response = service.chat(chat, msg)
        print(f"🤖 Assistant: {response[:200]}...")

    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print("="*60)


if __name__ == "__main__":
    # Make sure GOOGLE_CLOUD_PROJECT is set
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("   Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        exit(1)

    main()
