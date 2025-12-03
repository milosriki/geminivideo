"""
Test script for Enhanced CTR Prediction Model
"""
import sys
sys.path.insert(0, '/home/user/geminivideo/services/ml-service')

from src.enhanced_ctr_model import (
    EnhancedCTRPredictor,
    generate_synthetic_training_data
)
import numpy as np


def test_feature_extraction():
    """Test feature extraction from clip data"""
    print("\n=== Testing Feature Extraction ===")

    predictor = EnhancedCTRPredictor()

    # Create sample clip data
    clip_data = {
        'psychology_score': 0.8,
        'psychology_details': {
            'pain_point': 0.7,
            'transformation': 0.8,
            'urgency': 0.6,
            'authority': 0.7,
            'social_proof': 0.6
        },
        'hook_strength': 0.75,
        'hook_details': {
            'has_number': True,
            'has_question': True,
            'motion_spike': 0.8
        },
        'technical_score': 0.85,
        'demographic_match': 0.7,
        'novelty_score': 0.6
    }

    features = predictor.extract_features(clip_data)

    print(f"✓ Extracted {len(features)} features")
    print(f"✓ Expected {len(predictor.feature_names)} features")
    print(f"✓ Feature shape: {features.shape}")
    print(f"✓ Sample features: {features[:10]}")

    assert len(features) == len(predictor.feature_names), "Feature count mismatch!"
    assert features.dtype == np.float32, "Feature dtype should be float32"

    print("✓ Feature extraction test PASSED")
    return True


def test_synthetic_data_generation():
    """Test synthetic training data generation"""
    print("\n=== Testing Synthetic Data Generation ===")

    n_samples = 100
    historical_ads = generate_synthetic_training_data(n_samples=n_samples)

    print(f"✓ Generated {len(historical_ads)} samples")

    # Check structure
    sample = historical_ads[0]
    assert 'clip_data' in sample, "Missing clip_data"
    assert 'actual_ctr' in sample, "Missing actual_ctr"

    # Check CTR range
    ctrs = [ad['actual_ctr'] for ad in historical_ads]
    min_ctr = min(ctrs)
    max_ctr = max(ctrs)
    avg_ctr = np.mean(ctrs)

    print(f"✓ CTR range: [{min_ctr:.4f}, {max_ctr:.4f}]")
    print(f"✓ Average CTR: {avg_ctr:.4f}")

    assert 0.0 <= min_ctr <= 1.0, "CTR out of range"
    assert 0.0 <= max_ctr <= 1.0, "CTR out of range"

    print("✓ Synthetic data generation test PASSED")
    return True


def test_model_training():
    """Test model training"""
    print("\n=== Testing Model Training ===")

    predictor = EnhancedCTRPredictor(model_path='models/test_enhanced_ctr.pkl')

    # Generate training data
    print("Generating training data...")
    historical_ads = generate_synthetic_training_data(n_samples=500)

    # Train model
    print("Training model...")
    metrics = predictor.train(historical_ads, test_size=0.2)

    print(f"\n✓ Training Metrics:")
    print(f"  - Train R²: {metrics['train_r2']:.4f}")
    print(f"  - Test R²: {metrics['test_r2']:.4f}")
    print(f"  - Train Accuracy: {metrics['train_accuracy']:.2%}")
    print(f"  - Test Accuracy: {metrics['test_accuracy']:.2%}")
    print(f"  - Test RMSE: {metrics['test_rmse']:.4f}")
    print(f"  - Test MAE: {metrics['test_mae']:.4f}")
    print(f"  - Features: {metrics['n_features']}")
    print(f"  - Target Achieved: {metrics['target_achieved']}")

    assert metrics['test_r2'] > 0.7, f"R² too low: {metrics['test_r2']}"
    assert metrics['test_accuracy'] > 0.7, f"Accuracy too low: {metrics['test_accuracy']}"

    if metrics['test_r2'] >= 0.88:
        print("\n✓✓✓ TARGET R² > 0.88 ACHIEVED! ✓✓✓")
    else:
        print(f"\n⚠ Target R² > 0.88 not yet achieved (current: {metrics['test_r2']:.4f})")
        print("  Note: May need more training data or hyperparameter tuning")

    print("✓ Model training test PASSED")
    return predictor, metrics


def test_prediction():
    """Test single prediction"""
    print("\n=== Testing Prediction ===")

    # Use trained model from previous test
    predictor = EnhancedCTRPredictor(model_path='models/test_enhanced_ctr.pkl')

    if not predictor.is_trained:
        print("Training model first...")
        historical_ads = generate_synthetic_training_data(n_samples=500)
        predictor.train(historical_ads)

    # Create test clip data
    clip_data = {
        'psychology_score': 0.85,
        'psychology_details': {
            'pain_point': 0.8,
            'transformation': 0.85,
            'urgency': 0.7,
            'authority': 0.75,
            'social_proof': 0.7
        },
        'hook_strength': 0.8,
        'hook_first_3_seconds': 0.85,
        'hook_details': {
            'has_number': True,
            'has_question': True,
            'motion_spike': 0.85,
            'pattern_interrupt': 0.8,
            'curiosity_gap': 0.75
        },
        'technical_score': 0.9,
        'demographic_match': 0.8,
        'novelty_score': 0.7
    }

    # Predict
    result = predictor.predict(clip_data)

    print(f"\n✓ Prediction Results:")
    print(f"  - Predicted CTR: {result['predicted_ctr']:.4f} ({result['predicted_ctr']*100:.2f}%)")
    print(f"  - Predicted Band: {result['predicted_band']}")
    print(f"  - Confidence: {result['confidence']:.2f}")

    assert 'predicted_ctr' in result, "Missing predicted_ctr"
    assert 'predicted_band' in result, "Missing predicted_band"
    assert 'confidence' in result, "Missing confidence"
    assert 0.0 <= result['predicted_ctr'] <= 1.0, "CTR out of range"

    print("✓ Prediction test PASSED")
    return result


def test_batch_prediction():
    """Test batch prediction"""
    print("\n=== Testing Batch Prediction ===")

    predictor = EnhancedCTRPredictor(model_path='models/test_enhanced_ctr.pkl')

    if not predictor.is_trained:
        print("Training model first...")
        historical_ads = generate_synthetic_training_data(n_samples=500)
        predictor.train(historical_ads)

    # Create multiple test clips
    clips = []
    for i in range(5):
        clips.append({
            'psychology_score': 0.5 + i * 0.1,
            'hook_strength': 0.6 + i * 0.05,
            'technical_score': 0.7 + i * 0.05,
            'demographic_match': 0.6 + i * 0.08,
            'novelty_score': 0.5 + i * 0.08
        })

    # Batch predict
    results = predictor.predict_batch(clips)

    print(f"\n✓ Batch Prediction Results ({len(results)} clips):")
    for i, result in enumerate(results):
        print(f"  Clip {i+1}: CTR={result['predicted_ctr']:.4f}, Band={result['predicted_band']}")

    assert len(results) == len(clips), "Result count mismatch"

    print("✓ Batch prediction test PASSED")
    return results


def test_feature_importance():
    """Test feature importance extraction"""
    print("\n=== Testing Feature Importance ===")

    predictor = EnhancedCTRPredictor(model_path='models/test_enhanced_ctr.pkl')

    if not predictor.is_trained:
        print("Training model first...")
        historical_ads = generate_synthetic_training_data(n_samples=500)
        predictor.train(historical_ads)

    # Get feature importance
    importance = predictor.get_feature_importance()

    print(f"\n✓ Feature Importance (Top 10):")
    for i, (feature, score) in enumerate(list(importance.items())[:10]):
        print(f"  {i+1}. {feature}: {score:.4f}")

    assert len(importance) == len(predictor.feature_names), "Importance count mismatch"

    print("✓ Feature importance test PASSED")
    return importance


def test_save_load():
    """Test model save and load"""
    print("\n=== Testing Save/Load ===")

    # Create and train a model
    predictor1 = EnhancedCTRPredictor(model_path='models/test_save_load.pkl')
    historical_ads = generate_synthetic_training_data(n_samples=200)
    metrics1 = predictor1.train(historical_ads)

    # Save
    predictor1.save()
    print("✓ Model saved")

    # Load in new instance
    predictor2 = EnhancedCTRPredictor(model_path='models/test_save_load.pkl')
    predictor2.load()
    print("✓ Model loaded")

    # Verify metrics match
    assert predictor2.is_trained, "Loaded model should be trained"
    assert predictor2.training_metrics == metrics1, "Metrics mismatch"

    print("✓ Save/Load test PASSED")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced CTR Prediction Model - Test Suite")
    print("=" * 60)

    try:
        # Run tests
        test_feature_extraction()
        test_synthetic_data_generation()
        predictor, metrics = test_model_training()
        test_prediction()
        test_batch_prediction()
        test_feature_importance()
        test_save_load()

        print("\n" + "=" * 60)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 60)
        print("\nModel Summary:")
        print(f"  - Features: {len(predictor.feature_names)}")
        print(f"  - Test R²: {metrics['test_r2']:.4f}")
        print(f"  - Test Accuracy: {metrics['test_accuracy']:.2%}")
        print(f"  - Target R² > 0.88: {'✓ ACHIEVED' if metrics['target_achieved'] else '✗ Not Yet'}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
