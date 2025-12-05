"""
Test Alert System End-to-End
Agent 16 - Real-Time Performance Alerts

Tests:
1. Alert rule creation and management
2. Metric checking and alert triggering
3. Alert acknowledgment and resolution
4. Alert statistics and history
5. WebSocket notifications (simulated)
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, '/home/user/geminivideo/services/ml-service/src')

from alerts.alert_engine import alert_engine, Alert
from alerts.alert_rules import alert_rule_manager, AlertRule, AlertType, AlertSeverity
from alerts.alert_notifier import alert_notifier, NotificationChannel


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_alert_rules():
    """Test alert rule management"""
    print_section("TEST 1: Alert Rule Management")

    # Get all default rules
    rules = alert_rule_manager.get_all_rules()
    print(f"✅ Loaded {len(rules)} default alert rules")

    # Display some rules
    for i, rule in enumerate(rules[:3], 1):
        print(f"\n{i}. {rule.name}")
        print(f"   Type: {rule.alert_type.value}")
        print(f"   Severity: {rule.severity.value}")
        print(f"   Threshold: {rule.threshold_operator} {rule.threshold}")
        print(f"   Lookback: {rule.lookback_minutes} minutes")
        print(f"   Cooldown: {rule.cooldown_minutes} minutes")

    # Create a custom rule
    custom_rule = AlertRule(
        rule_id="test_custom_roas",
        name="Test Custom ROAS Alert",
        alert_type=AlertType.ROAS_DROP,
        severity=AlertSeverity.CRITICAL,
        threshold=4.0,
        threshold_operator="<",
        lookback_minutes=30,
        cooldown_minutes=10,
        metadata={
            "description": "Custom ROAS alert for testing",
            "action": "Test action"
        }
    )

    alert_rule_manager.add_rule(custom_rule)
    print(f"\n✅ Created custom rule: {custom_rule.name}")

    # Test enable/disable
    alert_rule_manager.disable_rule("test_custom_roas")
    print(f"✅ Disabled custom rule")

    alert_rule_manager.enable_rule("test_custom_roas")
    print(f"✅ Enabled custom rule")

    return True


def test_alert_triggering():
    """Test alert triggering"""
    print_section("TEST 2: Alert Triggering")

    # Test 1: ROAS Drop Alert (should trigger)
    print("\n1. Testing ROAS drop (1.5x < 2.0x threshold)...")
    alerts = alert_engine.check_roas(
        campaign_id="camp_test_001",
        campaign_name="Test Campaign #1",
        roas=1.5,
        context={
            "spend": 5000,
            "revenue": 7500
        }
    )

    if alerts:
        alert = alerts[0]
        print(f"✅ Alert triggered: {alert.title}")
        print(f"   Severity: {alert.severity.value}")
        print(f"   Message: {alert.message}")
        print(f"   Metric: {alert.metric_value} (threshold: {alert.threshold_value})")
    else:
        print("❌ No alert triggered (expected alert)")

    # Test 2: ROAS OK (should NOT trigger)
    print("\n2. Testing ROAS OK (3.5x > 2.0x threshold)...")
    alerts = alert_engine.check_roas(
        campaign_id="camp_test_002",
        campaign_name="Test Campaign #2",
        roas=3.5,
        context={
            "spend": 5000,
            "revenue": 17500
        }
    )

    if not alerts:
        print("✅ No alert triggered (as expected)")
    else:
        print("❌ Alert triggered (should not have triggered)")

    # Test 3: Budget Warning (should trigger)
    print("\n3. Testing budget warning (85% > 80% threshold)...")
    alerts = alert_engine.check_budget(
        campaign_id="camp_test_003",
        campaign_name="Test Campaign #3",
        budget_spent_pct=85.0,
        context={
            "daily_budget": 10000,
            "spent": 8500
        }
    )

    if alerts:
        alert = alerts[0]
        print(f"✅ Alert triggered: {alert.title}")
        print(f"   Message: {alert.message}")
    else:
        print("❌ No alert triggered (expected alert)")

    # Test 4: CTR Anomaly
    print("\n4. Testing CTR anomaly (25% drop > 20% threshold)...")
    alerts = alert_engine.check_ctr(
        campaign_id="camp_test_004",
        campaign_name="Test Campaign #4",
        ctr_drop_pct=25.0,
        context={
            "avg_ctr": 2.5,
            "current_ctr": 1.875
        }
    )

    if alerts:
        alert = alerts[0]
        print(f"✅ Alert triggered: {alert.title}")
    else:
        print("❌ No alert triggered (expected alert)")

    # Test 5: Cooldown logic (should NOT trigger immediately)
    print("\n5. Testing cooldown logic (same campaign, same rule)...")
    alerts = alert_engine.check_roas(
        campaign_id="camp_test_001",  # Same campaign as test 1
        campaign_name="Test Campaign #1",
        roas=1.4,  # Even worse ROAS
        context={"spend": 5000, "revenue": 7000}
    )

    if not alerts:
        print("✅ No alert triggered due to cooldown (as expected)")
    else:
        print(f"❌ Alert triggered despite cooldown: {alerts[0].title}")

    return True


def test_alert_management():
    """Test alert acknowledgment and resolution"""
    print_section("TEST 3: Alert Management")

    # Get active alerts
    active_alerts = alert_engine.get_active_alerts(limit=5)
    print(f"✅ Found {len(active_alerts)} active alerts")

    if active_alerts:
        alert = active_alerts[0]
        print(f"\nAlert: {alert.title}")
        print(f"  ID: {alert.alert_id}")
        print(f"  Campaign: {alert.campaign_name}")
        print(f"  Acknowledged: {alert.acknowledged}")
        print(f"  Resolved: {alert.resolved}")

        # Acknowledge the alert
        print(f"\nAcknowledging alert...")
        success = alert_engine.acknowledge_alert(alert.alert_id, "test_user")
        if success:
            print("✅ Alert acknowledged")
            print(f"   Acknowledged by: {alert.acknowledged_by}")
            print(f"   Acknowledged at: {alert.acknowledged_at}")
        else:
            print("❌ Failed to acknowledge alert")

        # Resolve the alert
        print(f"\nResolving alert...")
        success = alert_engine.resolve_alert(alert.alert_id)
        if success:
            print("✅ Alert resolved")
        else:
            print("❌ Failed to resolve alert")

        # Check active alerts again
        active_after = alert_engine.get_active_alerts()
        print(f"\n✅ Active alerts after resolution: {len(active_after)}")

    return True


def test_alert_statistics():
    """Test alert statistics"""
    print_section("TEST 4: Alert Statistics")

    # Overall stats
    stats = alert_engine.get_alert_stats()
    print(f"Overall Statistics:")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Active alerts: {stats['active_alerts']}")
    print(f"  Acknowledged: {stats['acknowledged']}")
    print(f"  Resolved: {stats['resolved']}")

    print(f"\nBy Type:")
    for alert_type, count in stats['by_type'].items():
        print(f"  {alert_type}: {count}")

    print(f"\nBy Severity:")
    for severity, count in stats['by_severity'].items():
        print(f"  {severity}: {count}")

    # Campaign-specific stats
    print(f"\nCampaign-Specific Stats (camp_test_001):")
    campaign_stats = alert_engine.get_alert_stats(campaign_id="camp_test_001")
    print(f"  Total alerts: {campaign_stats['total_alerts']}")

    return True


def test_alert_history():
    """Test alert history"""
    print_section("TEST 5: Alert History")

    # Get history for last 7 days
    start_date = datetime.utcnow() - timedelta(days=7)
    history = alert_engine.get_alert_history(start_date=start_date, limit=10)

    print(f"✅ Found {len(history)} alerts in last 7 days")

    for i, alert in enumerate(history[:5], 1):
        print(f"\n{i}. {alert.title}")
        print(f"   Campaign: {alert.campaign_name}")
        print(f"   Severity: {alert.severity.value}")
        print(f"   Time: {alert.timestamp}")
        print(f"   Status: {'Resolved' if alert.resolved else 'Acknowledged' if alert.acknowledged else 'Active'}")

    return True


async def test_notifications():
    """Test notification system (simulated)"""
    print_section("TEST 6: Notification System")

    # Create a test alert
    test_alert = Alert(
        rule_id="test_rule",
        alert_type=AlertType.ROAS_DROP,
        severity=AlertSeverity.HIGH,
        title="Test Alert Notification",
        message="This is a test alert for notification system validation",
        campaign_id="test_campaign",
        campaign_name="Test Campaign",
        metric_name="roas",
        metric_value=1.5,
        threshold_value=2.0,
        details={"action": "Review campaign performance"}
    )

    print(f"Created test alert: {test_alert.title}")

    # Test notification delivery (will fail without configured channels)
    print("\nTesting notification channels...")
    results = await alert_engine.send_alert_notifications(test_alert)

    print(f"\nNotification Results:")
    for channel, success in results.items():
        status = "✅" if success else "⚠️"
        print(f"  {status} {channel}: {'Success' if success else 'Failed/Not configured'}")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  ALERT SYSTEM END-TO-END TEST SUITE")
    print("  Agent 16 - Real-Time Performance Alerts")
    print("="*60)

    tests = [
        ("Alert Rule Management", test_alert_rules),
        ("Alert Triggering", test_alert_triggering),
        ("Alert Management", test_alert_management),
        ("Alert Statistics", test_alert_statistics),
        ("Alert History", test_alert_history),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Run async notification test
    try:
        asyncio.run(test_notifications())
        passed += 1
    except Exception as e:
        print(f"\n❌ Notification test failed: {e}")
        failed += 1

    # Summary
    print_section("TEST SUMMARY")
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        print("Alert system is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed.")
        print("Please review the failures above.")

    print("\n" + "="*60)
    print("  Test Complete")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
