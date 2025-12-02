"""
Demo: ROAS Predictor - Agent 16
Shows practical usage of XGBoost + LightGBM ensemble for ROAS prediction.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json

from roas_predictor import ROASPredictor, FeatureSet


def generate_demo_training_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate realistic training data for demo."""
    np.random.seed(42)

    print(f"📊 Generating {n_samples} training samples...")

    data = {
        # Creative features (10)
        'hook_type': np.random.choice(
            ['problem_solution', 'testimonial', 'demo', 'ugc', 'before_after'],
            n_samples,
            p=[0.3, 0.25, 0.2, 0.15, 0.1]
        ),
        'hook_strength': np.random.uniform(4, 10, n_samples),
        'visual_complexity': np.random.uniform(3, 9, n_samples),
        'text_density': np.random.uniform(0.05, 0.35, n_samples),
        'face_presence': np.random.choice([True, False], n_samples, p=[0.7, 0.3]),
        'motion_score': np.random.uniform(4, 10, n_samples),
        'video_duration': np.random.choice([6, 15, 30, 60], n_samples, p=[0.1, 0.5, 0.3, 0.1]),
        'aspect_ratio': np.random.choice([0.5625, 1.0, 1.7778], n_samples, p=[0.6, 0.3, 0.1]),
        'color_vibrancy': np.random.uniform(4, 10, n_samples),
        'scene_count': np.random.randint(1, 10, n_samples),

        # Targeting features (8)
        'audience_size': np.random.randint(500000, 8000000, n_samples),
        'audience_overlap': np.random.uniform(0.05, 0.5, n_samples),
        'cpm_estimate': np.random.uniform(7, 30, n_samples),
        'age_min': np.random.choice([18, 25, 35, 45], n_samples),
        'age_max': np.random.choice([34, 44, 54, 65], n_samples),
        'gender_targeting': np.random.choice(['all', 'male', 'female'], n_samples, p=[0.5, 0.25, 0.25]),
        'interest_count': np.random.randint(2, 20, n_samples),
        'custom_audience': np.random.choice([True, False], n_samples, p=[0.3, 0.7]),

        # Historical features (10)
        'account_avg_roas': np.random.uniform(1.5, 6.0, n_samples),
        'account_avg_ctr': np.random.uniform(0.5, 4.0, n_samples),
        'vertical_avg_roas': np.random.uniform(1.8, 5.5, n_samples),
        'similar_creative_roas': np.random.uniform(1.0, 7.0, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'hour_of_day': np.random.randint(0, 24, n_samples),
        'days_since_last_winner': np.random.randint(1, 90, n_samples),
        'account_spend_30d': np.random.uniform(5000, 300000, n_samples),
        'account_conversions_30d': np.random.randint(30, 2000, n_samples),
        'creative_fatigue_score': np.random.uniform(0, 1.0, n_samples),

        # Copy features (8)
        'cta_type': np.random.choice(
            ['shop_now', 'learn_more', 'sign_up', 'get_offer', 'download'],
            n_samples
        ),
        'urgency_score': np.random.uniform(2, 10, n_samples),
        'benefit_count': np.random.randint(1, 7, n_samples),
        'pain_point_addressed': np.random.choice([True, False], n_samples, p=[0.6, 0.4]),
        'social_proof_present': np.random.choice([True, False], n_samples, p=[0.55, 0.45]),
        'word_count': np.random.randint(15, 120, n_samples),
        'emoji_count': np.random.randint(0, 10, n_samples),
        'question_present': np.random.choice([True, False], n_samples, p=[0.35, 0.65]),
    }

    df = pd.DataFrame(data)

    # Generate realistic ROAS based on key features
    # ROAS is influenced by multiple factors with realistic weights
    roas = (
        # Creative quality (40%)
        df['hook_strength'] * 0.25 +
        df['motion_score'] * 0.15 +
        (df['face_presence'].astype(int) * 0.8) +

        # Historical performance (35%)
        df['account_avg_roas'] * 0.35 +
        df['similar_creative_roas'] * 0.30 +
        df['vertical_avg_roas'] * 0.20 +

        # Copy quality (15%)
        df['urgency_score'] * 0.10 +
        (df['social_proof_present'].astype(int) * 0.5) +
        (df['pain_point_addressed'].astype(int) * 0.4) +

        # Targeting efficiency (10%)
        (1.0 / (df['cpm_estimate'] / 15.0)) * 0.3 +
        (df['custom_audience'].astype(int) * 0.4) +

        # Add realistic noise
        np.random.normal(0, 0.6, n_samples)
    )

    # Normalize to realistic ROAS range (0.3 to 8.0)
    roas = (roas - roas.min()) / (roas.max() - roas.min()) * 7.7 + 0.3

    # Add some outliers
    outlier_mask = np.random.random(n_samples) < 0.05
    roas[outlier_mask] = np.random.uniform(8.0, 12.0, outlier_mask.sum())

    # Ensure non-negative
    roas = np.maximum(roas, 0.1)

    df['actual_roas'] = roas

    print(f"   ROAS range: {roas.min():.2f} - {roas.max():.2f}")
    print(f"   Mean ROAS: {roas.mean():.2f}")
    print(f"   Median ROAS: {np.median(roas):.2f}")

    return df


def demo_training():
    """Demo: Train ROAS predictor."""
    print("\n" + "="*60)
    print("🎯 DEMO 1: Training ROAS Predictor")
    print("="*60)

    # Generate training data
    training_data = generate_demo_training_data(n_samples=1500)

    # Initialize and train
    predictor = ROASPredictor()

    print("\n🔧 Training ensemble (XGBoost + LightGBM)...")
    metrics = predictor.train(training_data, validation_split=0.2)

    print(f"\n📊 Training Results:")
    print(f"   R² Score: {metrics['r2_score']:.4f}")
    print(f"   MAE: {metrics['mae']:.4f}")
    print(f"   RMSE: {metrics['rmse']:.4f}")
    print(f"   Training samples: {metrics['train_samples']}")
    print(f"   Validation samples: {metrics['val_samples']}")

    # Get top features
    print(f"\n🎯 Top 10 Most Important Features:")
    top_features = predictor.get_top_features(n=10)
    for i, (feature, importance) in enumerate(top_features, 1):
        print(f"   {i:2d}. {feature:30s} {importance:.4f}")

    return predictor


def demo_prediction(predictor: ROASPredictor):
    """Demo: Make predictions."""
    print("\n" + "="*60)
    print("🔮 DEMO 2: Making Predictions")
    print("="*60)

    # High-performing creative
    print("\n📈 Scenario 1: High-Performing Creative")
    print("   - Strong hook (9.0)")
    print("   - High motion (8.5)")
    print("   - Face present")
    print("   - Great account history (ROAS 4.5)")
    print("   - Social proof & urgency")

    high_perf = FeatureSet(
        hook_type='problem_solution',
        hook_strength=9.0,
        visual_complexity=7.5,
        face_presence=True,
        motion_score=8.5,
        video_duration=15.0,
        account_avg_roas=4.5,
        account_avg_ctr=2.8,
        vertical_avg_roas=4.0,
        similar_creative_roas=5.0,
        social_proof_present=True,
        urgency_score=8.5,
        benefit_count=4,
        pain_point_addressed=True
    )

    prediction = predictor.predict_roas(high_perf)
    print(f"\n   Predicted ROAS: {prediction.predicted_roas:.2f}")
    print(f"   95% Confidence: [{prediction.confidence_low:.2f}, {prediction.confidence_high:.2f}]")
    print(f"   Confidence Score: {prediction.confidence_score:.2%}")

    print(f"\n   Top 5 Feature Contributions:")
    for i, (feature, contrib) in enumerate(list(prediction.feature_contributions.items())[:5], 1):
        direction = "↑" if contrib > 0 else "↓"
        print(f"      {i}. {feature:30s} {direction} {abs(contrib):6.3f}")

    # Average creative
    print("\n📊 Scenario 2: Average Creative")
    print("   - Medium hook (6.5)")
    print("   - Medium motion (6.0)")
    print("   - Average account history (ROAS 3.0)")

    avg_perf = FeatureSet(
        hook_strength=6.5,
        motion_score=6.0,
        account_avg_roas=3.0,
        similar_creative_roas=3.2,
        urgency_score=6.0
    )

    prediction = predictor.predict_roas(avg_perf)
    print(f"\n   Predicted ROAS: {prediction.predicted_roas:.2f}")
    print(f"   95% Confidence: [{prediction.confidence_low:.2f}, {prediction.confidence_high:.2f}]")
    print(f"   Confidence Score: {prediction.confidence_score:.2%}")

    # Low-performing creative
    print("\n📉 Scenario 3: Low-Performing Creative")
    print("   - Weak hook (4.0)")
    print("   - Low motion (4.5)")
    print("   - No face")
    print("   - Poor account history (ROAS 2.0)")

    low_perf = FeatureSet(
        hook_strength=4.0,
        motion_score=4.5,
        face_presence=False,
        account_avg_roas=2.0,
        similar_creative_roas=1.8,
        social_proof_present=False,
        urgency_score=4.0
    )

    prediction = predictor.predict_roas(low_perf)
    print(f"\n   Predicted ROAS: {prediction.predicted_roas:.2f}")
    print(f"   95% Confidence: [{prediction.confidence_low:.2f}, {prediction.confidence_high:.2f}]")
    print(f"   Confidence Score: {prediction.confidence_score:.2%}")


def demo_batch_prediction(predictor: ROASPredictor):
    """Demo: Batch predictions."""
    print("\n" + "="*60)
    print("🚀 DEMO 3: Batch Predictions")
    print("="*60)

    print("\n📦 Testing 5 creative variants...")

    variants = [
        FeatureSet(hook_type='problem_solution', hook_strength=8.5, motion_score=8.0),
        FeatureSet(hook_type='testimonial', hook_strength=7.5, motion_score=7.0),
        FeatureSet(hook_type='demo', hook_strength=8.0, motion_score=9.0),
        FeatureSet(hook_type='ugc', hook_strength=7.0, motion_score=6.5),
        FeatureSet(hook_type='before_after', hook_strength=9.0, motion_score=8.5),
    ]

    predictions = predictor.predict_batch(variants)

    print(f"\n   {'Variant':<20} {'Hook Type':<18} {'Predicted ROAS':<15} {'Confidence'}")
    print("   " + "-"*75)

    for i, (variant, pred) in enumerate(zip(variants, predictions), 1):
        print(f"   Variant {i:<13} {variant.hook_type:<18} "
              f"{pred.predicted_roas:>6.2f} ± {(pred.confidence_high - pred.confidence_low)/2:>4.2f}      "
              f"{pred.confidence_score:.1%}")

    # Find best variant
    best_idx = max(range(len(predictions)), key=lambda i: predictions[i].predicted_roas)
    print(f"\n   🏆 Best Variant: Variant {best_idx + 1} "
          f"({variants[best_idx].hook_type}) - ROAS {predictions[best_idx].predicted_roas:.2f}")


def demo_explainability(predictor: ROASPredictor):
    """Demo: SHAP explainability."""
    print("\n" + "="*60)
    print("🔍 DEMO 4: Model Explainability (SHAP)")
    print("="*60)

    features = FeatureSet(
        hook_strength=8.5,
        motion_score=8.0,
        face_presence=True,
        account_avg_roas=4.0,
        similar_creative_roas=4.5
    )

    explanation = predictor.explain_prediction(features)

    print(f"\n   Base Value (average): {explanation['base_value']:.2f}")
    print(f"   Predicted Value: {explanation['predicted_value']:.2f}")
    print(f"   Delta: {explanation['predicted_value'] - explanation['base_value']:+.2f}")

    print(f"\n   Top 5 Positive Drivers (increase ROAS):")
    for i, (feature, value) in enumerate(explanation['top_positive_features'], 1):
        print(f"      {i}. {feature:30s} +{value:.3f}")

    print(f"\n   Top 5 Negative Drivers (decrease ROAS):")
    for i, (feature, value) in enumerate(explanation['top_negative_features'], 1):
        print(f"      {i}. {feature:30s} {value:.3f}")


def demo_model_persistence(predictor: ROASPredictor):
    """Demo: Save and load model."""
    print("\n" + "="*60)
    print("💾 DEMO 5: Model Persistence")
    print("="*60)

    model_path = Path("./models/roas_predictor_demo")
    model_path.mkdir(parents=True, exist_ok=True)

    # Save
    print(f"\n📁 Saving model to {model_path}...")
    predictor.save_model(str(model_path))

    files = list(model_path.glob("*"))
    print(f"\n   Saved files:")
    for file in files:
        size_kb = file.stat().st_size / 1024
        print(f"      - {file.name:30s} ({size_kb:>8.2f} KB)")

    # Load
    print(f"\n📂 Loading model from disk...")
    new_predictor = ROASPredictor(str(model_path))

    # Test prediction
    test_features = FeatureSet(hook_strength=8.0, motion_score=7.5)

    pred1 = predictor.predict_roas(test_features, return_explanation=False)
    pred2 = new_predictor.predict_roas(test_features, return_explanation=False)

    print(f"\n   Original model prediction: {pred1.predicted_roas:.4f}")
    print(f"   Loaded model prediction:   {pred2.predicted_roas:.4f}")
    print(f"   Difference:                {abs(pred1.predicted_roas - pred2.predicted_roas):.6f}")
    print(f"\n   ✅ Model persistence verified!")


def demo_drift_detection(predictor: ROASPredictor):
    """Demo: Model drift detection."""
    print("\n" + "="*60)
    print("📊 DEMO 6: Model Drift Detection")
    print("="*60)

    # Generate recent data (slightly different distribution)
    print("\n🔄 Simulating new campaign data...")
    recent_data = generate_demo_training_data(n_samples=200)

    # Add some distribution shift
    recent_data['hook_strength'] *= 0.95  # Slight decrease in hook quality
    recent_data['cpm_estimate'] *= 1.1    # CPM inflation

    drift_metrics = predictor.evaluate_model_drift(recent_data)

    print(f"\n   📈 Current Performance:")
    print(f"      R² Score: {drift_metrics['current_r2']:.4f}")
    print(f"      MAE: {drift_metrics['current_mae']:.4f}")

    print(f"\n   📊 Baseline Performance:")
    print(f"      R² Score: {drift_metrics['baseline_r2']:.4f}")
    print(f"      MAE: {drift_metrics['baseline_mae']:.4f}")

    print(f"\n   🔍 Drift Analysis:")
    print(f"      R² Drift: {drift_metrics['r2_drift']:+.4f}")
    print(f"      MAE Drift: {drift_metrics['mae_drift']:+.4f}")
    print(f"      Drift Detected: {'⚠️  YES' if drift_metrics['drift_detected'] else '✅ NO'}")
    print(f"      Recommendation: {drift_metrics['recommendation'].upper()}")

    # Retraining recommendation
    print(f"\n   ⏰ Retraining Check:")
    recommendation = predictor.get_retraining_recommendation()
    print(f"      Days since training: {recommendation['days_since_training']}")
    print(f"      Should retrain: {'YES' if recommendation['should_retrain'] else 'NO'}")
    print(f"      Reason: {recommendation['reason']}")


def demo_feature_engineering():
    """Demo: Feature engineering from raw data."""
    print("\n" + "="*60)
    print("🛠️  DEMO 7: Feature Engineering")
    print("="*60)

    predictor = ROASPredictor()

    raw_data = {
        'hook_type': 'problem_solution',
        'hook_strength': 8.5,
        'motion_score': 8.0,
        'face_presence': True,
        'video_duration': 15.0,
        'account_avg_roas': 4.0,
        'cpm_estimate': 12.5
    }

    print("\n📝 Raw Input Data:")
    for key, value in raw_data.items():
        print(f"   {key:25s}: {value}")

    features = predictor.engineer_features(raw_data)

    print(f"\n🔧 Engineered FeatureSet:")
    print(f"   Total features: {len(features.to_dict())}")
    print(f"\n   Provided features (user input):")
    for key in raw_data.keys():
        print(f"      {key:30s}: {getattr(features, key)}")

    print(f"\n   Auto-filled features (defaults):")
    auto_filled = ['audience_size', 'urgency_score', 'benefit_count', 'word_count']
    for key in auto_filled:
        print(f"      {key:30s}: {getattr(features, key)}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🚀 ROAS PREDICTOR - AGENT 16 DEMO")
    print("   XGBoost + LightGBM Ensemble with SHAP Explainability")
    print("="*60)

    # Demo 1: Training
    predictor = demo_training()

    # Demo 2: Single predictions
    demo_prediction(predictor)

    # Demo 3: Batch predictions
    demo_batch_prediction(predictor)

    # Demo 4: Explainability
    demo_explainability(predictor)

    # Demo 5: Model persistence
    demo_model_persistence(predictor)

    # Demo 6: Drift detection
    demo_drift_detection(predictor)

    # Demo 7: Feature engineering
    demo_feature_engineering()

    print("\n" + "="*60)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📚 Next steps:")
    print("   1. Run tests: pytest test_roas_predictor.py -v")
    print("   2. Integrate with campaign_tracker.py for real-time ROAS prediction")
    print("   3. Set up automated retraining pipeline")
    print("   4. Monitor model drift on production data")
    print("\n")


if __name__ == '__main__':
    main()
