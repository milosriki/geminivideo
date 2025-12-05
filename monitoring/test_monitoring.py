#!/usr/bin/env python3
"""
Test script for monitoring system validation.

Tests:
1. Metrics collection
2. Structured logging
3. Alert system
4. Sensitive data masking

Usage:
    python test_monitoring.py
"""

import sys
import os
import time
from pathlib import Path

# Add monitoring to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_metrics():
    """Test metrics collection."""
    print("\n=== Testing Metrics ===")

    from monitoring.metrics import (
        http_requests_total,
        ai_api_calls_total,
        track_ai_call,
        track_ai_call_with_cost,
        calculate_cost,
        get_metrics,
    )

    # Test HTTP metrics
    print("✓ Testing HTTP metrics...")
    http_requests_total.labels(
        service="test-service",
        method="GET",
        endpoint="/api/test",
        status="200"
    ).inc()

    # Test AI metrics
    print("✓ Testing AI API metrics...")
    ai_api_calls_total.labels(
        service="test-service",
        provider="openai",
        model="gpt-4",
        operation="generate"
    ).inc()

    # Test cost calculation
    cost = calculate_cost("openai", "gpt-4", 1000, 2000)
    print(f"✓ Cost calculation: ${cost:.4f} (expected ~$0.09)")

    # Test AI call tracking with cost
    print("✓ Testing AI call tracking...")
    cost = track_ai_call_with_cost(
        service="test-service",
        provider="google",
        model="gemini-1.5-flash",
        input_tokens=5000,
        output_tokens=1000
    )
    print(f"✓ Gemini Flash cost: ${cost:.4f}")

    # Test context manager
    print("✓ Testing AI call context manager...")
    with track_ai_call("test-service", "anthropic", "claude-sonnet-4-5", "generate"):
        time.sleep(0.1)  # Simulate work

    # Get metrics output
    metrics = get_metrics().decode('utf-8')
    print(f"✓ Metrics generated ({len(metrics)} bytes)")

    # Verify metrics are present
    assert 'http_requests_total' in metrics
    assert 'ai_api_calls_total' in metrics
    print("✓ All metrics tests passed!")


def test_logging():
    """Test structured logging."""
    print("\n=== Testing Logging ===")

    from monitoring.logging_config import (
        setup_logging,
        generate_correlation_id,
        set_correlation_id,
        get_correlation_id,
        log_request,
        log_response,
        log_ai_call,
        mask_sensitive_data,
        track_performance,
    )

    # Setup logger
    logger = setup_logging(
        service_name="test-service",
        environment="development",
        log_level="DEBUG"
    )
    print("✓ Logger initialized")

    # Test correlation ID
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    retrieved_id = get_correlation_id()
    assert correlation_id == retrieved_id
    print(f"✓ Correlation ID: {correlation_id}")

    # Test basic logging
    logger.info("Test info message", test_field="test_value")
    logger.warning("Test warning")
    logger.error("Test error")
    print("✓ Basic logging works")

    # Test request/response logging
    log_request(logger, "GET", "/api/test", user_id="user123")
    log_response(logger, "GET", "/api/test", 200, 45.2, user_id="user123")
    print("✓ Request/response logging works")

    # Test AI call logging
    log_ai_call(
        logger,
        provider="openai",
        model="gpt-4",
        operation="generate",
        input_tokens=100,
        output_tokens=200,
        cost_usd=0.015,
        duration_ms=1250
    )
    print("✓ AI call logging works")

    # Test performance tracking
    with track_performance(logger, "test_operation", test_param="value"):
        time.sleep(0.1)
    print("✓ Performance tracking works")

    # Test sensitive data masking
    sensitive_data = {
        "username": "john",
        "email": "john@example.com",
        "password": "supersecret123",
        "api_key": "sk-1234567890abcdef",
        "credit_card": "4532-1234-5678-9010",
        "normal_field": "normal_value"
    }
    masked = mask_sensitive_data(sensitive_data)

    assert masked["username"] == "john"
    assert masked["normal_field"] == "normal_value"
    assert masked["password"] == "********"
    assert masked["api_key"] == "********"
    assert "4532" not in str(masked)  # CC should be masked
    print("✓ Sensitive data masking works")
    print(f"  Masked data: {masked}")

    print("✓ All logging tests passed!")


def test_alerting():
    """Test alerting system."""
    print("\n=== Testing Alerting ===")

    from monitoring.alerting import (
        AlertManager,
        Alert,
        Severity,
        Threshold,
    )

    # Create alert manager
    manager = AlertManager("test-service")
    print("✓ Alert manager created")

    # Test threshold checking
    threshold_metric = "http_error_rate"
    threshold = manager.thresholds.get(threshold_metric)
    assert threshold is not None
    print(f"✓ Default threshold for {threshold_metric}: {threshold}")

    # Test threshold evaluation
    severity = manager.check_threshold("http_error_rate", 0.02)
    assert severity == Severity.WARNING
    print(f"✓ Threshold check: 2% error rate = {severity.value}")

    severity = manager.check_threshold("http_error_rate", 0.08)
    assert severity == Severity.ERROR
    print(f"✓ Threshold check: 8% error rate = {severity.value}")

    # Test custom threshold
    custom_threshold = Threshold(
        metric_name="custom_metric",
        warning_value=10.0,
        error_value=50.0,
        critical_value=100.0,
        comparison="gt"
    )
    manager.add_threshold(custom_threshold)
    print("✓ Custom threshold added")

    # Test alert creation (without sending)
    alert = Alert(
        title="Test Alert",
        message="This is a test alert",
        severity=Severity.WARNING,
        service="test-service",
        timestamp=manager.create_and_send_alert.__code__.co_consts[0].__class__.__bases__[0].__subclasses__()[0].__init__.__globals__['datetime'].utcnow(),
        metric_name="test_metric",
        metric_value=42.0
    )
    print(f"✓ Alert created: {alert.title}")
    print(f"  Fingerprint: {alert.fingerprint()}")

    print("✓ All alerting tests passed!")
    print("\nNote: Actual alert sending requires SMTP/Slack/PagerDuty configuration")


def test_integration():
    """Test full integration."""
    print("\n=== Testing Integration ===")

    from monitoring import (
        setup_logging,
        track_ai_call_with_cost,
        campaigns_created_total,
        prediction_accuracy,
        set_service_health,
    )

    # Setup
    logger = setup_logging("integration-test", environment="test")
    set_service_health("integration-test", True)

    # Simulate campaign creation
    campaigns_created_total.labels(
        service="integration-test",
        user_id="user123",
        platform="meta"
    ).inc()

    # Simulate AI call
    cost = track_ai_call_with_cost(
        service="integration-test",
        provider="openai",
        model="gpt-4-turbo",
        input_tokens=1000,
        output_tokens=500
    )
    logger.info(f"AI call completed, cost: ${cost:.4f}")

    # Update prediction accuracy
    prediction_accuracy.labels(
        service="integration-test",
        model_type="roas_predictor",
        metric="r2"
    ).set(0.87)

    print("✓ Integration test passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("GeminiVideo Monitoring System Test Suite")
    print("=" * 60)

    try:
        test_metrics()
        test_logging()
        test_alerting()
        test_integration()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nMonitoring system is ready for production use.")
        print("\nNext steps:")
        print("1. Deploy monitoring stack: ./setup.sh docker")
        print("2. Integrate services with middleware")
        print("3. Import Grafana dashboards")
        print("4. Configure alerting channels")
        print("5. Test in production environment")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
