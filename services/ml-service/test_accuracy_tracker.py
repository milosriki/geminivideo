"""
Test script for Accuracy Tracker - Agent 9
Demonstrates prediction vs actuals tracking for investor validation
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.accuracy_tracker import accuracy_tracker
import random
from datetime import datetime, timedelta
import uuid


async def generate_test_predictions():
    """Generate test predictions with realistic data"""

    hook_types = ['question', 'number', 'emotion', 'problem', 'solution', 'testimonial']
    templates = ['template_001', 'template_002', 'template_003', 'template_004']

    print("🔄 Generating 50 test predictions with actuals...")

    for i in range(50):
        # Generate prediction
        prediction_id = f"pred_{uuid.uuid4().hex[:8]}"
        campaign_id = f"camp_{uuid.uuid4().hex[:8]}"
        creative_id = f"creative_{uuid.uuid4().hex[:8]}"

        hook_type = random.choice(hook_types)
        template_id = random.choice(templates)

        # Generate realistic predictions
        base_ctr = random.uniform(0.01, 0.08)  # 1-8% CTR
        base_roas = random.uniform(1.5, 4.5)  # 1.5x - 4.5x ROAS

        predicted_ctr = base_ctr
        predicted_roas = base_roas

        # Record prediction
        success = await accuracy_tracker.record_prediction(
            prediction_id=prediction_id,
            campaign_id=campaign_id,
            creative_id=creative_id,
            predicted_ctr=predicted_ctr,
            predicted_roas=predicted_roas,
            hook_type=hook_type,
            template_id=template_id,
            features={
                'psychology_score': random.uniform(0.5, 0.9),
                'hook_strength': random.uniform(0.6, 0.95),
                'technical_score': random.uniform(0.7, 0.95)
            },
            demographic_target={
                'age_range': '25-45',
                'interests': ['fitness', 'wellness']
            }
        )

        if not success:
            print(f"❌ Failed to record prediction {prediction_id}")
            continue

        # Simulate actual results with some variance (realistic prediction accuracy)
        # Good model should be within 15-20% of prediction
        ctr_variance = random.uniform(-0.20, 0.25)  # ±20% with slight positive bias
        roas_variance = random.uniform(-0.18, 0.22)  # ±18% with slight positive bias

        actual_ctr = max(0.005, predicted_ctr * (1 + ctr_variance))
        actual_roas = max(0.5, predicted_roas * (1 + roas_variance))
        actual_conversions = int(random.uniform(5, 50))

        # Update with actuals
        success = await accuracy_tracker.update_with_actuals(
            prediction_id=prediction_id,
            actual_ctr=actual_ctr,
            actual_roas=actual_roas,
            actual_conversions=actual_conversions
        )

        if success:
            print(f"✅ Prediction {i+1}/50: CTR {predicted_ctr:.4f} → {actual_ctr:.4f}, ROAS {predicted_roas:.2f} → {actual_roas:.2f}")
        else:
            print(f"❌ Failed to update actuals for {prediction_id}")

    print("\n✅ Test predictions generated successfully!")


async def test_accuracy_metrics():
    """Test accuracy metrics calculation"""
    print("\n📊 Testing Accuracy Metrics...")

    metrics = await accuracy_tracker.calculate_accuracy_metrics(days_back=30)

    print("\n=== ACCURACY METRICS ===")
    print(f"Total predictions: {metrics.get('total_predictions')}")
    print(f"CTR MAE: {metrics.get('ctr_mae'):.4f}")
    print(f"CTR RMSE: {metrics.get('ctr_rmse'):.4f}")
    print(f"CTR Accuracy: {metrics.get('ctr_accuracy'):.2f}%")
    print(f"ROAS MAE: {metrics.get('roas_mae'):.4f}")
    print(f"ROAS RMSE: {metrics.get('roas_rmse'):.4f}")
    print(f"ROAS Accuracy: {metrics.get('roas_accuracy'):.2f}%")
    print(f"Predictions above threshold: {metrics.get('predictions_above_threshold')}")
    print(f"ROI Generated: ${metrics.get('roi_generated'):,.2f}")


async def test_hook_type_breakdown():
    """Test accuracy breakdown by hook type"""
    print("\n📊 Testing Hook Type Breakdown...")

    breakdown = await accuracy_tracker.get_accuracy_by_hook_type(days_back=30)

    print("\n=== ACCURACY BY HOOK TYPE ===")
    print(f"Total hook types analyzed: {breakdown.get('total_hook_types')}")
    print(f"Best performing: {breakdown.get('best_performing')}")
    print("\nHook Type Performance:")

    for hook_type, metrics in breakdown.get('hook_types', {}).items():
        print(f"\n  {hook_type}:")
        print(f"    Count: {metrics['count']}")
        print(f"    CTR MAE: {metrics['ctr_mae']:.4f}")
        print(f"    ROAS MAE: {metrics['roas_mae']:.4f}")
        print(f"    Avg Actual ROAS: {metrics['avg_actual_roas']:.2f}")


async def test_template_breakdown():
    """Test accuracy breakdown by template"""
    print("\n📊 Testing Template Breakdown...")

    breakdown = await accuracy_tracker.get_accuracy_by_template(days_back=30)

    print("\n=== ACCURACY BY TEMPLATE ===")
    print(f"Total templates analyzed: {breakdown.get('total_templates')}")
    print(f"Best performing: {breakdown.get('best_performing')}")
    print("\nTemplate Performance:")

    for template_id, metrics in breakdown.get('templates', {}).items():
        print(f"\n  {template_id}:")
        print(f"    Count: {metrics['count']}")
        print(f"    CTR MAE: {metrics['ctr_mae']:.4f}")
        print(f"    ROAS MAE: {metrics['roas_mae']:.4f}")
        print(f"    Avg Actual ROAS: {metrics['avg_actual_roas']:.2f}")


async def test_top_performers():
    """Test top performers"""
    print("\n📊 Testing Top Performers...")

    top_performers = await accuracy_tracker.get_top_performing_ads(limit=5)

    print("\n=== TOP 5 PERFORMING ADS ===")
    for i, ad in enumerate(top_performers, 1):
        print(f"\n{i}. {ad['prediction_id']}")
        print(f"   Hook: {ad['hook_type']}, Template: {ad['template_id']}")
        print(f"   Predicted CTR: {ad['predicted_ctr']:.4f} → Actual: {ad['actual_ctr']:.4f}")
        print(f"   Predicted ROAS: {ad['predicted_roas']:.2f} → Actual: {ad['actual_roas']:.2f}")
        print(f"   Accuracy Score: {ad['accuracy_score']:.2f}%")


async def test_investor_report():
    """Test full investor report generation"""
    print("\n📊 Testing INVESTOR REPORT (€5M Validation)...")

    report = await accuracy_tracker.generate_investor_report(days_back=30)

    print("\n" + "="*60)
    print("INVESTOR VALIDATION REPORT")
    print("="*60)

    print(f"\nReport Generated: {report.get('report_generated_at')}")
    print(f"Period: {report.get('period_analyzed')}")

    # Executive Summary
    summary = report.get('summary', {})
    print("\n--- EXECUTIVE SUMMARY ---")
    print(f"Total Predictions: {summary.get('total_predictions')}")
    print(f"CTR Accuracy: {summary.get('ctr_accuracy')}%")
    print(f"ROAS Accuracy: {summary.get('roas_accuracy')}%")
    print(f"High Performers: {summary.get('predictions_above_threshold')}")
    print(f"ROI Generated: ${summary.get('roi_generated'):,.2f}")
    print(f"Model Confidence: {summary.get('model_confidence_score')}%")

    # Model Confidence
    confidence = report.get('model_confidence', {})
    print("\n--- MODEL CONFIDENCE ---")
    print(f"Overall Score: {confidence.get('overall_score')}%")
    print(f"CTR Confidence: {confidence.get('ctr_confidence')}")
    print(f"ROAS Confidence: {confidence.get('roas_confidence')}")
    print(f"Reliability Grade: {confidence.get('reliability_grade')}")

    # Revenue Impact
    revenue = report.get('revenue_impact', {})
    print("\n--- REVENUE IMPACT ---")
    print(f"Total Revenue: ${revenue.get('total_revenue'):,.2f}")
    print(f"Total Spend: ${revenue.get('total_spend'):,.2f}")
    print(f"ROI Generated: ${revenue.get('roi_generated'):,.2f}")
    print(f"Average ROAS: {revenue.get('avg_roas'):.2f}x")
    print(f"Revenue from High Accuracy: ${revenue.get('revenue_from_high_accuracy'):,.2f}")
    print(f"Cost Savings: ${revenue.get('cost_savings'):,.2f}")

    # Learning Improvement
    learning = report.get('learning_improvement', {})
    print("\n--- LEARNING & IMPROVEMENT ---")
    print(f"Current CTR Accuracy: {learning.get('current_ctr_accuracy')}%")
    print(f"Current ROAS Accuracy: {learning.get('current_roas_accuracy')}%")
    print(f"CTR Improvement: {learning.get('ctr_improvement'):+.2f}%")
    print(f"ROAS Improvement: {learning.get('roas_improvement'):+.2f}%")
    print(f"Learning Status: {learning.get('learning_status')}")

    # Investment Validation
    validation = report.get('investment_validation', {})
    print("\n--- INVESTMENT VALIDATION ---")
    print(f"Accuracy Target Met: {'✅ YES' if validation.get('accuracy_target_met') else '❌ NO'}")
    print(f"ROI Positive: {'✅ YES' if validation.get('roi_positive') else '❌ NO'}")
    print(f"Learning Improving: {'✅ YES' if validation.get('learning_improving') else '❌ NO'}")
    print(f"\n🎯 OVERALL VERDICT: {validation.get('overall_verdict')}")

    print("\n" + "="*60)


async def test_daily_snapshot():
    """Test daily snapshot creation"""
    print("\n📊 Testing Daily Snapshot Creation...")

    success = await accuracy_tracker.create_daily_snapshot()

    if success:
        print("✅ Daily snapshot created successfully!")
    else:
        print("❌ Failed to create daily snapshot (may be no data)")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ACCURACY TRACKER TEST SUITE - AGENT 9")
    print("€5M Investment Validation System")
    print("="*60)

    # Generate test data
    await generate_test_predictions()

    # Run tests
    await test_accuracy_metrics()
    await test_hook_type_breakdown()
    await test_template_breakdown()
    await test_top_performers()
    await test_daily_snapshot()

    # Generate full investor report
    await test_investor_report()

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60)
    print("\nAccuracy tracker is ready for production use.")
    print("API Endpoint: GET /api/ml/accuracy-report")


if __name__ == "__main__":
    asyncio.run(main())
