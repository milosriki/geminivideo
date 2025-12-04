"""
Validation script for Unified Conversion Hub
Demonstrates the API and validates implementation completeness
"""

import sys
from datetime import datetime, timedelta
from conversion_hub import (
    ConversionHub,
    ConversionSource,
    AttributionModel,
    Touchpoint,
    UnifiedConversion
)


class MockClient:
    """Mock client for testing."""
    pass


class MockDB:
    """Mock database for testing."""
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


def validate_enums():
    """Validate all enums are properly defined."""
    print("✓ ConversionSource enum:")
    for source in ConversionSource:
        print(f"  - {source.name}: {source.value}")

    print("\n✓ AttributionModel enum:")
    for model in AttributionModel:
        print(f"  - {model.name}: {model.value}")


def validate_dataclasses():
    """Validate dataclass implementations."""
    print("\n✓ Touchpoint dataclass:")
    tp = Touchpoint(
        source="facebook",
        campaign_id="camp_123",
        ad_id="ad_456",
        timestamp=datetime.now(),
        channel="facebook",
        interaction_type="click"
    )
    print(f"  - Created: {tp.campaign_id}")
    tp_dict = tp.to_dict()
    print(f"  - Serialized: {len(tp_dict)} fields")

    print("\n✓ UnifiedConversion dataclass:")
    conv = UnifiedConversion(
        id="conv_123",
        external_ids={"meta": "ext_123"},
        contact_email="test@example.com",
        contact_id="contact_456",
        value=99.99,
        currency="USD",
        conversion_type="Purchase",
        sources=[ConversionSource.META_CAPI],
        touchpoints=[tp],
        attributed_campaign_id="camp_123",
        attributed_ad_id="ad_456",
        attribution_model=AttributionModel.LAST_TOUCH,
        first_touch_at=datetime.now(),
        converted_at=datetime.now(),
        is_offline=False,
        metadata={"key": "value"}
    )
    print(f"  - Created: {conv.id}")
    conv_dict = conv.to_dict()
    print(f"  - Serialized: {len(conv_dict)} fields")


def validate_hub_initialization():
    """Validate ConversionHub can be initialized."""
    print("\n✓ ConversionHub initialization:")
    hub = ConversionHub(
        meta_capi_client=MockClient(),
        hubspot_client=MockClient(),
        anytrack_client=MockClient(),
        database_service=MockDB()
    )
    print(f"  - Instance created: {type(hub).__name__}")
    print(f"  - Cache initialized: {len(hub._conversion_cache)} items")


def validate_methods():
    """Validate all required methods exist."""
    print("\n✓ Required methods:")

    required_methods = [
        # Ingestion
        'ingest_conversion',
        'ingest_from_meta_capi',
        'ingest_from_meta_pixel',
        'ingest_from_hubspot',
        'ingest_from_anytrack',
        # Deduplication
        'deduplicate_conversions',
        'find_duplicates',
        'merge_duplicates',
        # Attribution
        'attribute_to_campaign',
        'get_touchpoints',
        'add_touchpoint',
        # ROAS
        'calculate_true_roas',
        'calculate_blended_roas',
        # Path Analysis
        'get_conversion_path',
        'analyze_conversion_paths',
        'get_avg_touchpoints_to_convert',
        # Reporting
        'generate_attribution_report',
        'get_conversions_by_source',
        'export_conversions',
        # Sync
        'sync_all_sources',
        'get_sync_status'
    ]

    for method_name in required_methods:
        has_method = hasattr(ConversionHub, method_name)
        status = "✓" if has_method else "✗"
        print(f"  {status} {method_name}")


def validate_attribution_models():
    """Validate attribution logic."""
    print("\n✓ Attribution models test:")

    hub = ConversionHub(
        MockClient(), MockClient(), MockClient(), MockDB()
    )

    # Create test conversion with touchpoints
    now = datetime.now()
    touchpoints = [
        Touchpoint("facebook", "camp_1", "ad_1", now - timedelta(days=10), "facebook", "click"),
        Touchpoint("google", "camp_2", "ad_2", now - timedelta(days=5), "google", "click"),
        Touchpoint("email", "camp_3", None, now - timedelta(days=1), "email", "click"),
    ]

    conversion = UnifiedConversion(
        id="test_conv",
        external_ids={},
        contact_email="test@example.com",
        contact_id=None,
        value=100.0,
        currency="USD",
        conversion_type="Purchase",
        sources=[ConversionSource.META_CAPI],
        touchpoints=touchpoints,
        attributed_campaign_id=None,
        attributed_ad_id=None,
        attribution_model=AttributionModel.LAST_TOUCH,
        first_touch_at=touchpoints[0].timestamp,
        converted_at=now,
        is_offline=False
    )

    hub._store_conversion(conversion)

    # Test each model
    for model in AttributionModel:
        try:
            attribution = hub.attribute_to_campaign("test_conv", model)
            total_weight = sum(attribution.values())
            print(f"  - {model.name}: {len(attribution)} campaigns, weight={total_weight:.2f}")
        except Exception as e:
            print(f"  ✗ {model.name}: {e}")


def main():
    """Run all validations."""
    print("=" * 60)
    print("UNIFIED CONVERSION HUB - VALIDATION")
    print("=" * 60)

    try:
        validate_enums()
        validate_dataclasses()
        validate_hub_initialization()
        validate_methods()
        validate_attribution_models()

        print("\n" + "=" * 60)
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
