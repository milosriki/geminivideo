"""
Knowledge Base Manager - Example Usage
Agent 14: Knowledge Base Hot-Reload Engineer

This file demonstrates all major features of the knowledge base system.
"""
import logging
import time
from manager import KnowledgeBaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example 1: Basic upload, download, and list operations"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Operations")
    print("="*80)

    # Initialize manager
    manager = KnowledgeBaseManager()

    # Upload brand guidelines
    brand_data = {
        "brand_name": "FitPro",
        "voice": "energetic and motivational",
        "values": ["authenticity", "results-driven", "community"],
        "tone": "direct but empathetic",
        "keywords": ["transformation", "proven", "science-backed", "no-BS"],
        "avoid": ["gimmicks", "quick fixes", "unrealistic promises"],
        "target_audience": "busy professionals 30-45",
        "unique_selling_point": "15-minute science-backed workouts"
    }

    version_id = manager.upload_knowledge(
        category="brand_guidelines",
        data=brand_data,
        description="Initial brand guidelines for FitPro",
        author="marketing_team"
    )
    print(f"\n✓ Uploaded brand guidelines: {version_id}")

    # Download latest
    current = manager.download_knowledge("brand_guidelines")
    print(f"\n✓ Downloaded brand: {current['brand_name']}")
    print(f"  Voice: {current['voice']}")
    print(f"  Keywords: {', '.join(current['keywords'])}")

    # List versions
    versions = manager.list_versions("brand_guidelines")
    print(f"\n✓ Total versions: {len(versions)}")
    for v in versions:
        status = "ACTIVE" if v.is_active else "inactive"
        print(f"  - {v.version_id} [{status}] by {v.author}")


def example_versioning():
    """Example 2: Version management and activation"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Version Management")
    print("="*80)

    manager = KnowledgeBaseManager()

    # Upload multiple versions of hook templates
    versions_created = []

    # Version 1: Basic hooks
    hooks_v1 = {
        "templates": [
            {
                "name": "Before/After",
                "pattern": "Show transformation in first frame",
                "ctr": 4.8,
                "examples": ["Lost 47 pounds in 90 days", "From broke to $10k/month"]
            },
            {
                "name": "Contrarian",
                "pattern": "Challenge conventional wisdom",
                "ctr": 4.2,
                "examples": ["Cardio is keeping you fat", "College is a scam"]
            }
        ]
    }

    v1 = manager.upload_knowledge(
        category="hook_templates",
        data=hooks_v1,
        description="Basic hook templates",
        author="content_team"
    )
    versions_created.append(v1)
    print(f"\n✓ Created version 1: {v1}")

    time.sleep(1)  # Ensure different timestamps

    # Version 2: Added more templates
    hooks_v2 = {
        "templates": hooks_v1["templates"] + [
            {
                "name": "Problem Agitation",
                "pattern": "Agitate a pain point",
                "ctr": 3.7,
                "examples": ["Tried everything and still stuck?", "Tired of starting over?"]
            },
            {
                "name": "Social Proof",
                "pattern": "Show mass success",
                "ctr": 3.5,
                "examples": ["2,847 transformations", "10,000+ students"]
            }
        ]
    }

    v2 = manager.upload_knowledge(
        category="hook_templates",
        data=hooks_v2,
        description="Added problem agitation and social proof hooks",
        author="content_team"
    )
    versions_created.append(v2)
    print(f"✓ Created version 2: {v2}")

    # List all versions
    versions = manager.list_versions("hook_templates")
    print(f"\n✓ Version history:")
    for v in versions:
        status = "ACTIVE" if v.is_active else "inactive"
        size = len(manager.download_knowledge("hook_templates", v.version_id)["templates"])
        print(f"  - {v.version_id} [{status}] - {size} templates - {v.description}")

    # Activate version 1 (rollback)
    print(f"\n✓ Rolling back to version 1...")
    manager.activate_version("hook_templates", v1)

    current = manager.download_knowledge("hook_templates")
    print(f"  Active version now has {len(current['templates'])} templates")

    # Activate version 2 again
    print(f"\n✓ Activating version 2...")
    manager.activate_version("hook_templates", v2)

    current = manager.download_knowledge("hook_templates")
    print(f"  Active version now has {len(current['templates'])} templates")


def example_hot_reload():
    """Example 3: Hot-reload with callbacks"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Hot-Reload with Callbacks")
    print("="*80)

    manager = KnowledgeBaseManager()

    # Track updates
    updates_received = []

    def on_knowledge_update(category, new_version, old_version):
        """Callback when knowledge is updated"""
        updates_received.append({
            "category": category,
            "new_version": new_version,
            "old_version": old_version,
            "timestamp": time.time()
        })
        print(f"\n🔔 Knowledge Update Notification:")
        print(f"   Category: {category}")
        print(f"   Old Version: {old_version}")
        print(f"   New Version: {new_version}")

    # Subscribe to updates
    sub_id = manager.subscribe_to_updates(on_knowledge_update)
    print(f"\n✓ Subscribed to updates: {sub_id}")

    # Upload new winning patterns (will trigger callback)
    patterns = {
        "patterns": [
            {
                "type": "hook",
                "description": "Before/after split screen",
                "success_rate": 0.85,
                "avg_ctr": 4.8,
                "platform": "Meta"
            },
            {
                "type": "body",
                "description": "Pain-agitate-solve framework",
                "success_rate": 0.78,
                "avg_conversion": 3.2,
                "platform": "All"
            }
        ]
    }

    print(f"\n✓ Uploading winning patterns...")
    v1 = manager.upload_knowledge(
        category="winning_patterns",
        data=patterns,
        description="Meta high performers Q4 2023",
        author="ml_agent"
    )

    time.sleep(0.5)  # Give callback time to fire

    # Upload updated version (will trigger callback)
    patterns["patterns"].append({
        "type": "cta",
        "description": "Scarcity-based CTA",
        "success_rate": 0.82,
        "avg_conversion": 4.1,
        "platform": "All"
    })

    print(f"\n✓ Uploading updated patterns...")
    v2 = manager.upload_knowledge(
        category="winning_patterns",
        data=patterns,
        description="Added CTA patterns",
        author="ml_agent"
    )
    manager.activate_version("winning_patterns", v2)

    time.sleep(0.5)

    # Manually trigger reload (will trigger callback)
    print(f"\n✓ Triggering manual reload...")
    manager.trigger_reload("winning_patterns")

    time.sleep(0.5)

    # Show all updates received
    print(f"\n✓ Total updates received: {len(updates_received)}")
    for update in updates_received:
        print(f"  - {update['category']}: {update['old_version']} -> {update['new_version']}")

    # Unsubscribe
    manager.unsubscribe(sub_id)
    print(f"\n✓ Unsubscribed from updates")


def example_category_status():
    """Example 4: Get status of all categories"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Category Status")
    print("="*80)

    manager = KnowledgeBaseManager()

    # Upload some data to different categories
    categories_data = {
        "brand_guidelines": {
            "brand_name": "TestBrand",
            "voice": "professional",
            "values": ["quality", "innovation"]
        },
        "competitor_analysis": {
            "competitors": [
                {"name": "Competitor A", "strengths": ["price"], "weaknesses": ["quality"]},
                {"name": "Competitor B", "strengths": ["brand"], "weaknesses": ["price"]}
            ]
        },
        "industry_benchmarks": {
            "avg_ctr": 3.5,
            "avg_conversion": 2.1,
            "top_performer_ctr": 5.2,
            "industry": "fitness"
        }
    }

    for category, data in categories_data.items():
        try:
            manager.upload_knowledge(
                category=category,
                data=data,
                description=f"Example {category}",
                author="demo"
            )
            print(f"✓ Uploaded {category}")
        except Exception as e:
            print(f"✗ Failed to upload {category}: {e}")

    # Get status of all categories
    status = manager.get_all_status()

    print(f"\n{'Category':<25} {'Active Version':<25} {'Total':<8} {'Cached'}")
    print("-" * 80)

    for category, info in status.items():
        active = info['active_version'] or 'None'
        if len(active) > 24:
            active = active[:21] + "..."

        cached = "✓" if info['cached'] else "✗"
        print(f"{category:<25} {active:<25} {info['total_versions']:<8} {cached}")


def example_validation():
    """Example 5: Data validation"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Data Validation")
    print("="*80)

    manager = KnowledgeBaseManager()

    # Valid data
    print("\n✓ Testing valid brand_guidelines...")
    valid_brand = {
        "brand_name": "ValidBrand",
        "voice": "friendly",
        "values": ["trust", "quality"]
    }

    try:
        version = manager.upload_knowledge(
            category="brand_guidelines",
            data=valid_brand,
            description="Valid test",
            author="test"
        )
        print(f"  SUCCESS: Uploaded as {version}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # Invalid data - missing required fields
    print("\n✗ Testing invalid brand_guidelines (missing required fields)...")
    invalid_brand = {
        "brand_name": "InvalidBrand"
        # Missing 'voice' and 'values'
    }

    try:
        version = manager.upload_knowledge(
            category="brand_guidelines",
            data=invalid_brand,
            description="Invalid test",
            author="test"
        )
        print(f"  UNEXPECTED: Should have failed but got {version}")
    except ValueError as e:
        print(f"  EXPECTED ERROR: {e}")

    # Valid hook_templates
    print("\n✓ Testing valid hook_templates...")
    valid_hooks = {
        "templates": [
            {"name": "Hook 1", "pattern": "Pattern 1"},
            {"name": "Hook 2", "pattern": "Pattern 2"}
        ]
    }

    try:
        version = manager.upload_knowledge(
            category="hook_templates",
            data=valid_hooks,
            description="Valid hooks",
            author="test"
        )
        print(f"  SUCCESS: Uploaded as {version}")
    except Exception as e:
        print(f"  FAILED: {e}")

    # Invalid hook_templates
    print("\n✗ Testing invalid hook_templates (missing 'templates')...")
    invalid_hooks = {
        "hooks": []  # Wrong key name
    }

    try:
        version = manager.upload_knowledge(
            category="hook_templates",
            data=invalid_hooks,
            description="Invalid hooks",
            author="test"
        )
        print(f"  UNEXPECTED: Should have failed but got {version}")
    except ValueError as e:
        print(f"  EXPECTED ERROR: {e}")


def example_import_export():
    """Example 6: Import/Export functionality"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Import/Export")
    print("="*80)

    manager = KnowledgeBaseManager()

    # Create sample data
    sample_data = {
        "templates": [
            {
                "name": "Template 1",
                "description": "First template",
                "scenes": [
                    {"duration": 3, "visual": "Hook"},
                    {"duration": 10, "visual": "Problem"},
                    {"duration": 5, "visual": "Solution"}
                ]
            },
            {
                "name": "Template 2",
                "description": "Second template",
                "scenes": [
                    {"duration": 5, "visual": "Before/After"},
                    {"duration": 8, "visual": "Proof"},
                    {"duration": 2, "visual": "CTA"}
                ]
            }
        ]
    }

    # Upload
    version = manager.upload_knowledge(
        category="storyboard_templates",
        data=sample_data,
        description="Sample storyboard templates",
        author="demo"
    )
    print(f"\n✓ Uploaded storyboard templates: {version}")

    # Export (download and save to file)
    import json
    from pathlib import Path

    export_dir = Path("/tmp/knowledge_export")
    export_dir.mkdir(exist_ok=True)

    exported_data = manager.download_knowledge("storyboard_templates")
    export_file = export_dir / f"storyboard_templates_{version}.json"

    with open(export_file, 'w') as f:
        json.dump(exported_data, f, indent=2)

    print(f"✓ Exported to: {export_file}")
    print(f"  Size: {export_file.stat().st_size} bytes")

    # Import (read from file and upload)
    with open(export_file, 'r') as f:
        imported_data = json.load(f)

    # Modify slightly to create new version
    imported_data["templates"][0]["description"] = "Modified template"

    new_version = manager.upload_knowledge(
        category="storyboard_templates",
        data=imported_data,
        description="Imported and modified templates",
        author="demo"
    )
    print(f"✓ Imported as new version: {new_version}")

    # List versions
    versions = manager.list_versions("storyboard_templates")
    print(f"\n✓ Total versions: {len(versions)}")
    for v in versions:
        status = "ACTIVE" if v.is_active else "inactive"
        print(f"  - {v.version_id} [{status}] - {v.description}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("KNOWLEDGE BASE MANAGER - EXAMPLE USAGE")
    print("Agent 14: Knowledge Base Hot-Reload Engineer")
    print("="*80)

    try:
        # Run examples
        example_basic_usage()
        example_versioning()
        example_hot_reload()
        example_category_status()
        example_validation()
        example_import_export()

        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
