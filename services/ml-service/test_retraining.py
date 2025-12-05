#!/usr/bin/env python3
"""
Test ML Model Retraining Loop - Agent 10
Quick verification that retraining infrastructure works
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_retraining_components():
    """Test all retraining components"""
    print("="*60)
    print("Testing ML Model Retraining Loop (Agent 10)")
    print("="*60)

    # Test 1: Import components
    print("\n1. Testing imports...")
    try:
        from src.ctr_model import ctr_predictor
        from src.accuracy_tracker import accuracy_tracker
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Check accuracy tracker
    print("\n2. Testing AccuracyTracker...")
    try:
        if accuracy_tracker.db_enabled:
            metrics = await accuracy_tracker.calculate_accuracy_metrics(days_back=7)
            print(f"✅ AccuracyTracker working")
            print(f"   - Total predictions: {metrics.get('total_predictions', 0)}")
            print(f"   - CTR MAE: {metrics.get('ctr_mae', 0):.4f}")
        else:
            print("⚠️  Database not available - tracker will use mock data")
    except Exception as e:
        print(f"❌ AccuracyTracker test failed: {e}")

    # Test 3: Check CTRPredictor has accuracy_tracker
    print("\n3. Testing CTRPredictor integration...")
    try:
        if ctr_predictor.accuracy_tracker:
            print("✅ CTRPredictor has AccuracyTracker")
        else:
            print("⚠️  CTRPredictor missing AccuracyTracker")
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

    # Test 4: Test check_and_retrain method
    print("\n4. Testing check_and_retrain method...")
    try:
        result = await ctr_predictor.check_and_retrain()
        print(f"✅ check_and_retrain executed")
        print(f"   - Status: {result.get('status', 'unknown')}")

        if result['status'] == 'no_retrain_needed':
            print(f"   - Current MAE: {result.get('current_accuracy', {}).get('ctr_mae', 0):.4f}")
            print(f"   - Threshold: {result.get('threshold', 0):.2f}")
        elif result['status'] == 'retrained':
            print(f"   - Samples used: {result.get('samples', 0)}")
            print(f"   - New R²: {result.get('metrics', {}).get('test_r2', 0):.4f}")
        elif result['status'] == 'insufficient_data':
            print(f"   - Data count: {result.get('count', 0)}")
        elif result['status'] == 'error':
            print(f"   - Error: {result.get('error', 'unknown')}")

    except Exception as e:
        print(f"❌ check_and_retrain test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Check cron script exists
    print("\n5. Testing cron script...")
    cron_path = os.path.join(os.path.dirname(__file__), 'cron_retrain.sh')
    if os.path.exists(cron_path):
        if os.access(cron_path, os.X_OK):
            print(f"✅ Cron script exists and is executable")
        else:
            print(f"⚠️  Cron script exists but is not executable")
            print(f"   Run: chmod +x {cron_path}")
    else:
        print(f"❌ Cron script not found")

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Set up DATABASE_URL environment variable")
    print("2. Ensure prediction_records table has data")
    print("3. Schedule cron job: crontab -e")
    print("4. Monitor retraining: tail -f /var/log/ml-retrain.log")
    print("\nDocumentation: services/ml-service/RETRAINING_LOOP.md")

    return True


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(test_retraining_components())
    sys.exit(0 if success else 1)
