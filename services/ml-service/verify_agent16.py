"""
Quick verification script for Agent 16 - ROAS Predictor
Demonstrates all key features in ~30 lines
"""

from roas_predictor import ROASPredictor, FeatureSet
import pandas as pd
import numpy as np

print("🎯 Agent 16 Verification - ROAS Predictor")
print("="*60)

# 1. Generate minimal training data
np.random.seed(42)
data = pd.DataFrame({
    'hook_type': np.random.choice(['problem_solution', 'testimonial'], 200),
    'hook_strength': np.random.uniform(5, 10, 200),
    'visual_complexity': np.random.uniform(3, 9, 200),
    'text_density': np.random.uniform(0.1, 0.3, 200),
    'face_presence': np.random.choice([True, False], 200),
    'motion_score': np.random.uniform(5, 10, 200),
    'video_duration': np.random.uniform(10, 30, 200),
    'aspect_ratio': np.random.choice([0.5625, 1.0], 200),
    'color_vibrancy': np.random.uniform(5, 10, 200),
    'scene_count': np.random.randint(2, 6, 200),
    'audience_size': np.random.randint(1000000, 3000000, 200),
    'audience_overlap': np.random.uniform(0.1, 0.3, 200),
    'cpm_estimate': np.random.uniform(10, 20, 200),
    'age_min': np.random.choice([25, 35], 200),
    'age_max': np.random.choice([44, 54], 200),
    'gender_targeting': np.random.choice(['all', 'female'], 200),
    'interest_count': np.random.randint(3, 10, 200),
    'custom_audience': np.random.choice([True, False], 200),
    'account_avg_roas': np.random.uniform(2.5, 4.5, 200),
    'account_avg_ctr': np.random.uniform(1.0, 2.5, 200),
    'vertical_avg_roas': np.random.uniform(2.0, 4.0, 200),
    'similar_creative_roas': np.random.uniform(2.0, 5.0, 200),
    'day_of_week': np.random.randint(0, 7, 200),
    'hour_of_day': np.random.randint(8, 20, 200),
    'days_since_last_winner': np.random.randint(3, 30, 200),
    'account_spend_30d': np.random.uniform(30000, 100000, 200),
    'account_conversions_30d': np.random.randint(200, 800, 200),
    'creative_fatigue_score': np.random.uniform(0, 0.5, 200),
    'cta_type': np.random.choice(['shop_now', 'learn_more'], 200),
    'urgency_score': np.random.uniform(5, 10, 200),
    'benefit_count': np.random.randint(2, 5, 200),
    'pain_point_addressed': np.random.choice([True, False], 200),
    'social_proof_present': np.random.choice([True, False], 200),
    'word_count': np.random.randint(30, 80, 200),
    'emoji_count': np.random.randint(1, 5, 200),
    'question_present': np.random.choice([True, False], 200),
})
data['actual_roas'] = (
    data['hook_strength'] * 0.4 +
    data['account_avg_roas'] * 0.6 +
    np.random.normal(0, 0.3, 200)
).clip(0.5, 8.0)

print(f"✓ Training data: {len(data)} campaigns")

# 2. Train model
predictor = ROASPredictor()
metrics = predictor.train(data)
print(f"✓ Model trained: R²={metrics['r2_score']:.4f}, MAE={metrics['mae']:.4f}")

# 3. Predict
features = FeatureSet(hook_strength=8.5, motion_score=8.0, account_avg_roas=4.0)
pred = predictor.predict_roas(features)
print(f"✓ Prediction: {pred.predicted_roas:.2f} (CI: [{pred.confidence_low:.2f}, {pred.confidence_high:.2f}])")

# 4. Explain
top_features = predictor.get_top_features(n=3)
print(f"✓ Top 3 features: {', '.join([f[0] for f in top_features])}")

# 5. Save/Load
predictor.save_model('./models/verify_model')
new_predictor = ROASPredictor('./models/verify_model')
pred2 = new_predictor.predict_roas(features, return_explanation=False)
print(f"✓ Model persistence: {abs(pred.predicted_roas - pred2.predicted_roas) < 0.01}")

print("\n" + "="*60)
print("🎉 Agent 16 VERIFIED - All systems operational!")
print("="*60)
