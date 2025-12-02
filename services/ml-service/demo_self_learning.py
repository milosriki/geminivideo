"""
Self-Learning Feedback Loop Demo

Demonstrates all functionality with realistic scenarios.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from self_learning import (
    SelfLearningEngine,
    ModelType,
    DriftType,
    PredictionOutcome,
    DriftReport,
    ModelPerformance
)


class MockDatabaseService:
    """Mock database for testing."""

    def __init__(self):
        self.data = {}

    def query(self, *args, **kwargs):
        return []


def demo_complete_workflow():
    """Demonstrate complete self-learning workflow."""
    print("="*70)
    print("SELF-LEARNING FEEDBACK LOOP DEMO")
    print("="*70)

    # Initialize engine
    print("\n1. Initializing Self-Learning Engine...")
    db = MockDatabaseService()
    model_registry = {
        'roas_predictor': {'version': '1.0'},
        'ctr_predictor': {'version': '1.0'}
    }
    engine = SelfLearningEngine(db, model_registry)
    print("✓ Engine initialized")

    # 2. Register predictions
    print("\n2. Registering predictions...")
    prediction_ids = []
    for i in range(150):
        pred_id = engine.register_prediction(
            model_type=ModelType.ROAS_PREDICTOR,
            predicted_value=2.5 + np.random.normal(0, 0.2),
            features={
                'ad_spend': 1000 + i * 10,
                'audience_size': 50000 + i * 100,
                'ctr': 0.025 + np.random.normal(0, 0.005),
                'engagement_rate': 0.15 + np.random.normal(0, 0.02)
            }
        )
        prediction_ids.append(pred_id)
    print(f"✓ Registered {len(prediction_ids)} predictions")

    # 3. Record outcomes
    print("\n3. Recording prediction outcomes...")
    for i, pred_id in enumerate(prediction_ids):
        # Simulate varying accuracy over time
        if i < 100:
            # Good performance initially
            actual = 2.5 + np.random.normal(0, 0.3)
        else:
            # Degraded performance (concept drift)
            actual = 2.5 + np.random.normal(0, 0.6)

        outcome = engine.record_outcome(pred_id, actual)

        # Backdate some outcomes for drift detection
        if i < 100:
            outcome.timestamp = datetime.now() - timedelta(days=20 - (i // 10))

    print(f"✓ Recorded {len(engine.outcomes)} outcomes")

    # 4. Analyze error distribution
    print("\n4. Analyzing error distribution...")
    error_dist = engine.analyze_error_distribution(
        model_type=ModelType.ROAS_PREDICTOR,
        days_back=30
    )
    print(f"   Sample count: {error_dist['sample_count']}")
    print(f"   Mean absolute error: {error_dist['mean_absolute_error']:.4f}")
    print(f"   Median error: {error_dist['median_error']:.4f}")
    print(f"   Std error: {error_dist['std_error']:.4f}")
    print(f"   Skewness: {error_dist['skewness']:.4f}")
    print(f"   Kurtosis: {error_dist['kurtosis']:.4f}")
    if 'normality_test' in error_dist:
        print(f"   Error distribution normal: {error_dist['normality_test']['is_normal']}")

    # 5. Identify systematic errors
    print("\n5. Identifying systematic errors...")
    systematic_errors = engine.identify_systematic_errors(ModelType.ROAS_PREDICTOR)
    print(f"✓ Found {len(systematic_errors)} systematic error patterns")
    for i, error in enumerate(systematic_errors[:3]):
        print(f"   Pattern {i+1}:")
        print(f"     Feature: {error['feature']}")
        print(f"     Mean error: {error['mean_error']:.4f}")
        print(f"     Bias: {error['bias_direction']}")
        print(f"     P-value: {error['p_value']:.4f}")
        print(f"     Severity: {error['severity']}")

    # 6. Detect feature drift
    print("\n6. Detecting feature drift...")
    feature_drift = engine.identify_feature_drift(
        model_type=ModelType.ROAS_PREDICTOR,
        reference_period_days=30,
        current_period_days=7
    )
    print(f"   Drift type: {feature_drift.drift_type.value}")
    print(f"   Severity: {feature_drift.severity}")
    print(f"   Affected features: {len(feature_drift.affected_features)}")
    if feature_drift.affected_features:
        print(f"   Features: {', '.join(feature_drift.affected_features[:5])}")
    print(f"   Recommendation: {feature_drift.recommendation}")

    # 7. Detect concept drift
    print("\n7. Detecting concept drift (performance degradation)...")
    concept_drift = engine.detect_concept_drift(ModelType.ROAS_PREDICTOR)
    print(f"   Drift type: {concept_drift.drift_type.value}")
    print(f"   Severity: {concept_drift.severity}")
    stats = concept_drift.statistical_tests
    if 'performance_change_pct' in stats:
        print(f"   Performance change: {stats['performance_change_pct']:.2f}%")
        print(f"   Recent MAE: {stats['recent_mae']:.4f}")
        print(f"   Older MAE: {stats['older_mae']:.4f}")
        print(f"   T-test p-value: {stats['t_test']['p_value']:.4f}")
    print(f"   Recommendation: {concept_drift.recommendation}")

    # 8. Detect prediction drift
    print("\n8. Detecting prediction drift...")
    prediction_drift = engine.detect_prediction_drift(ModelType.ROAS_PREDICTOR)
    print(f"   Drift type: {prediction_drift.drift_type.value}")
    print(f"   Severity: {prediction_drift.severity}")
    stats = prediction_drift.statistical_tests
    if 'mean_shift_pct' in stats:
        print(f"   Mean shift: {stats['mean_shift_pct']:.2f}%")
        print(f"   KS statistic: {stats['ks_statistic']:.4f}")
        print(f"   KS p-value: {stats['p_value']:.4f}")
    print(f"   Recommendation: {prediction_drift.recommendation}")

    # 9. Get model performance
    print("\n9. Calculating model performance metrics...")
    performance = engine.get_model_performance(
        model_type=ModelType.ROAS_PREDICTOR,
        days_back=30
    )
    if performance:
        print(f"   Model: {performance.model_type.value}")
        print(f"   MAE: {performance.mae:.4f}")
        print(f"   RMSE: {performance.rmse:.4f}")
        print(f"   R²: {performance.r2:.4f}")
        print(f"   MAPE: {performance.mape:.2f}%")
        print(f"   Sample count: {performance.sample_count}")

    # 10. Check if model should be retrained
    print("\n10. Evaluating retraining necessity...")
    should_retrain, reason = engine.should_retrain(ModelType.ROAS_PREDICTOR)
    print(f"   Should retrain: {should_retrain}")
    print(f"   Reason: {reason}")

    # 11. Get retraining recommendations for all models
    print("\n11. Getting retraining recommendations for all models...")
    recommendations = engine.get_retraining_recommendation()
    for model_name, rec in recommendations.items():
        print(f"   {model_name}:")
        print(f"     Should retrain: {rec['should_retrain']}")
        print(f"     Priority: {rec['priority']}")
        print(f"     Reason: {rec['reason']}")

    # 12. Trigger model retraining
    if should_retrain:
        print("\n12. Triggering model retraining...")
        retrain_result = engine.trigger_model_retrain(
            model_type=ModelType.ROAS_PREDICTOR,
            reason=reason
        )
        print(f"   Retrain ID: {retrain_result['retrain_id']}")
        print(f"   Status: {retrain_result['status']}")
        print(f"   Sample count: {retrain_result['sample_count']}")

    # 13. Set up A/B test
    print("\n13. Setting up A/B test for model versions...")
    ab_test = engine.ab_test_model_versions(
        model_type=ModelType.CTR_PREDICTOR,
        model_a_id="v1.0",
        model_b_id="v1.1",
        traffic_split=0.5,
        duration_days=7
    )
    print(f"   Test ID: {ab_test['test_id']}")
    print(f"   Status: {ab_test['status']}")
    print(f"   Model A: {ab_test['config']['model_a_id']}")
    print(f"   Model B: {ab_test['config']['model_b_id']}")
    print(f"   Traffic split: {ab_test['config']['traffic_split']}")

    # Simulate A/B test outcomes
    test_id = ab_test['test_id']
    engine.ab_tests[test_id]['results']['model_a']['outcomes'] = [
        {'predicted': 0.025, 'actual': 0.025 + np.random.normal(0, 0.005)}
        for _ in range(100)
    ]
    engine.ab_tests[test_id]['results']['model_b']['outcomes'] = [
        {'predicted': 0.025, 'actual': 0.025 + np.random.normal(0, 0.003)}
        for _ in range(100)
    ]

    # 14. Get A/B test results
    print("\n14. Analyzing A/B test results...")
    ab_results = engine.get_ab_test_results(test_id)
    print(f"   Model A:")
    print(f"     Sample count: {ab_results['results']['model_a']['sample_count']}")
    print(f"     MAE: {ab_results['results']['model_a']['mae']:.6f}")
    print(f"     RMSE: {ab_results['results']['model_a']['rmse']:.6f}")
    print(f"   Model B:")
    print(f"     Sample count: {ab_results['results']['model_b']['sample_count']}")
    print(f"     MAE: {ab_results['results']['model_b']['mae']:.6f}")
    print(f"     RMSE: {ab_results['results']['model_b']['rmse']:.6f}")
    if 'comparison' in ab_results['results']:
        comp = ab_results['results']['comparison']
        print(f"   Comparison:")
        print(f"     Winner: {comp['winner']}")
        print(f"     MAE difference: {comp['mae_difference']:.6f}")
        print(f"     Statistically significant: {comp['statistically_significant']}")
        print(f"     P-value: {comp['p_value']:.4f}")

    # 15. Select winning model
    try:
        print("\n15. Selecting winning model...")
        winner = engine.select_winning_model(test_id, min_confidence=0.80)
        if winner:
            print(f"   Winner: {winner}")
            print(f"   ✓ Model promoted to production")
        else:
            print("   No statistically significant winner")
    except ValueError as e:
        print(f"   Could not determine winner: {str(e)}")

    # 16. Update feature weights
    print("\n16. Updating feature weights...")
    performance_data = pd.DataFrame({
        'ad_spend': np.random.randn(100),
        'audience_size': np.random.randn(100),
        'ctr': np.random.randn(100),
        'engagement_rate': np.random.randn(100),
        'actual_value': np.random.randn(100)
    })
    weights = engine.update_feature_weights(
        model_type=ModelType.ROAS_PREDICTOR,
        performance_data=performance_data
    )
    print(f"   Updated weights for {len(weights)} features:")
    for feature, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"     {feature}: {weight:.4f}")

    # 17. Generate comprehensive learning report
    print("\n17. Generating comprehensive learning report...")
    report = engine.generate_learning_report(period_days=7)
    print(f"   Report period: {report['period_days']} days")
    print(f"   Models analyzed: {len(report['models'])}")
    for model_name, model_data in report['models'].items():
        print(f"\n   {model_name}:")
        if model_data['performance']:
            perf = model_data['performance']
            print(f"     MAE: {perf['mae']:.4f}")
            print(f"     MAPE: {perf['mape']:.2f}%")
            print(f"     Sample count: {perf['sample_count']}")
        print(f"     Retraining recommended: {model_data['retraining']['recommended']}")

    # 18. Run daily learning job
    print("\n18. Running daily learning job...")
    daily_results = engine.run_daily_learning_job()
    print(f"   Job: {daily_results['job']}")
    print(f"   Tasks completed: {len(daily_results['tasks'])}")
    for task in daily_results['tasks']:
        print(f"     {task['model_type']}:")
        print(f"       Feature drift: {task['feature_drift_severity']}")
        print(f"       Concept drift: {task['concept_drift_severity']}")

    # 19. Run weekly learning job
    print("\n19. Running weekly learning job...")
    weekly_results = engine.run_weekly_learning_job()
    print(f"   Job: {weekly_results['job']}")
    print(f"   Report generated: ✓")
    print(f"   Retraining recommendations: ✓")
    print(f"   Active A/B tests: {len(weekly_results['active_ab_tests'])}")

    # 20. Check alerts
    print("\n20. Checking system alerts...")
    alerts = engine.check_alerts()
    print(f"   Total alerts: {len(engine.alerts)}")
    print(f"   Recent alerts (24h): {len(alerts)}")
    for alert in alerts[:3]:
        print(f"     {alert['alert_type']} - {alert['model_type']} - {alert['severity']}")

    print("\n" + "="*70)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("✓ Prediction outcome tracking")
    print("✓ Real statistical tests (KS-test, t-test)")
    print("✓ Multi-dimensional drift detection")
    print("✓ Systematic error identification")
    print("✓ Automated retraining triggers")
    print("✓ A/B testing with statistical significance")
    print("✓ Feature importance tracking")
    print("✓ Performance monitoring")
    print("✓ Comprehensive reporting")
    print("✓ Alert system")
    print("✓ Scheduled learning jobs")
    print("="*70)


def demo_drift_detection_scenarios():
    """Demonstrate different drift detection scenarios."""
    print("\n" + "="*70)
    print("DRIFT DETECTION SCENARIOS")
    print("="*70)

    db = MockDatabaseService()
    engine = SelfLearningEngine(db, {})

    # Scenario 1: No drift
    print("\nScenario 1: Stable model (no drift)")
    print("-" * 50)

    for day in range(40):
        timestamp = datetime.now() - timedelta(days=40-day)
        for _ in range(5):
            pred_id = engine.register_prediction(
                model_type=ModelType.CTR_PREDICTOR,
                predicted_value=0.025,
                features={
                    'ad_spend': 1000 + np.random.normal(0, 50),
                    'audience_size': 50000 + np.random.normal(0, 1000)
                }
            )
            outcome = engine.record_outcome(pred_id, 0.025 + np.random.normal(0, 0.002))
            outcome.timestamp = timestamp

    drift = engine.identify_feature_drift(ModelType.CTR_PREDICTOR)
    print(f"Feature drift severity: {drift.severity}")
    print(f"Affected features: {len(drift.affected_features)}")

    concept = engine.detect_concept_drift(ModelType.CTR_PREDICTOR)
    print(f"Concept drift severity: {concept.severity}")
    if 'performance_change_pct' in concept.statistical_tests:
        print(f"Performance change: {concept.statistical_tests['performance_change_pct']:.2f}%")

    # Scenario 2: Feature drift
    print("\nScenario 2: Feature distribution shift")
    print("-" * 50)

    engine2 = SelfLearningEngine(db, {})

    # Old data
    for day in range(30, 7, -1):
        timestamp = datetime.now() - timedelta(days=day)
        for _ in range(5):
            pred_id = engine2.register_prediction(
                model_type=ModelType.ROAS_PREDICTOR,
                predicted_value=2.5,
                features={'ad_spend': 1000 + np.random.normal(0, 100)}
            )
            outcome = engine2.record_outcome(pred_id, 2.5)
            outcome.timestamp = timestamp

    # New data with shifted features
    for day in range(7, 0, -1):
        timestamp = datetime.now() - timedelta(days=day)
        for _ in range(5):
            pred_id = engine2.register_prediction(
                model_type=ModelType.ROAS_PREDICTOR,
                predicted_value=2.5,
                features={'ad_spend': 2500 + np.random.normal(0, 150)}  # Shifted!
            )
            outcome = engine2.record_outcome(pred_id, 2.5)
            outcome.timestamp = timestamp

    drift = engine2.identify_feature_drift(ModelType.ROAS_PREDICTOR)
    print(f"Feature drift severity: {drift.severity}")
    print(f"Affected features: {drift.affected_features}")
    print(f"Recommendation: {drift.recommendation}")

    # Scenario 3: Concept drift
    print("\nScenario 3: Model performance degradation")
    print("-" * 50)

    engine3 = SelfLearningEngine(db, {})

    # Good performance period
    for day in range(30, 7, -1):
        timestamp = datetime.now() - timedelta(days=day)
        for _ in range(5):
            pred_id = engine3.register_prediction(
                model_type=ModelType.ROAS_PREDICTOR,
                predicted_value=2.5,
                features={'ad_spend': 1000}
            )
            actual = 2.5 + np.random.normal(0, 0.1)  # Low error
            outcome = engine3.record_outcome(pred_id, actual)
            outcome.timestamp = timestamp

    # Degraded performance period
    for day in range(7, 0, -1):
        timestamp = datetime.now() - timedelta(days=day)
        for _ in range(5):
            pred_id = engine3.register_prediction(
                model_type=ModelType.ROAS_PREDICTOR,
                predicted_value=2.5,
                features={'ad_spend': 1000}
            )
            actual = 2.5 + np.random.normal(0, 0.8)  # High error!
            outcome = engine3.record_outcome(pred_id, actual)
            outcome.timestamp = timestamp

    concept = engine3.detect_concept_drift(ModelType.ROAS_PREDICTOR)
    print(f"Concept drift severity: {concept.severity}")
    if 'performance_change_pct' in concept.statistical_tests:
        stats = concept.statistical_tests
        print(f"Performance change: {stats['performance_change_pct']:.2f}%")
        print(f"Recent MAE: {stats['recent_mae']:.4f}")
        print(f"Older MAE: {stats['older_mae']:.4f}")
        print(f"T-test p-value: {stats['t_test']['p_value']:.4f}")
    print(f"Recommendation: {concept.recommendation}")

    print("\n" + "="*70)


if __name__ == '__main__':
    # Run main demo
    demo_complete_workflow()

    # Run drift scenarios
    demo_drift_detection_scenarios()
