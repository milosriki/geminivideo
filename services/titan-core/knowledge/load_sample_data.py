#!/usr/bin/env python3
"""
Load Sample Knowledge Data
Agent 14: Knowledge Base Hot-Reload Engineer

This script loads all sample data into the knowledge base system.
Run this to quickly populate the system with example data.
"""
import json
import logging
from pathlib import Path
from manager import get_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sample_data():
    """Load all sample data files into the knowledge base"""

    manager = get_manager()
    sample_data_dir = Path(__file__).parent / "sample_data"

    if not sample_data_dir.exists():
        logger.error(f"Sample data directory not found: {sample_data_dir}")
        return False

    # Map of sample files to categories
    sample_files = {
        "brand_guidelines.json": "brand_guidelines",
        "hook_templates.json": "hook_templates",
        "storyboard_templates.json": "storyboard_templates",
        "winning_patterns.json": "winning_patterns",
    }

    results = []

    print("\n" + "="*80)
    print("LOADING SAMPLE KNOWLEDGE DATA")
    print("="*80 + "\n")

    for filename, category in sample_files.items():
        file_path = sample_data_dir / filename

        if not file_path.exists():
            logger.warning(f"Sample file not found: {file_path}")
            continue

        try:
            # Load JSON data
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Upload to knowledge base
            version_id = manager.upload_knowledge(
                category=category,
                data=data,
                description=f"Sample {category.replace('_', ' ')} data",
                author="sample_data_loader"
            )

            logger.info(f"✓ Loaded {category}: {version_id}")
            results.append({
                "category": category,
                "version_id": version_id,
                "success": True
            })

        except Exception as e:
            logger.error(f"✗ Failed to load {category}: {e}")
            results.append({
                "category": category,
                "error": str(e),
                "success": False
            })

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\nTotal: {len(results)} categories")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if successful > 0:
        print("\n✓ Successfully loaded:")
        for r in results:
            if r["success"]:
                print(f"  - {r['category']}: {r['version_id']}")

    if failed > 0:
        print("\n✗ Failed to load:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['category']}: {r.get('error', 'Unknown error')}")

    # Show status
    print("\n" + "="*80)
    print("KNOWLEDGE BASE STATUS")
    print("="*80 + "\n")

    status = manager.get_all_status()

    print(f"{'Category':<25} {'Active Version':<25} {'Total Versions'}")
    print("-" * 75)

    for category, info in status.items():
        active = info['active_version'] or 'None'
        if len(active) > 24:
            active = active[:21] + "..."
        print(f"{category:<25} {active:<25} {info['total_versions']}")

    print("\n" + "="*80)
    print("✓ Sample data loading complete!")
    print("="*80 + "\n")

    return successful == len(results)


def verify_data():
    """Verify that data was loaded correctly"""
    print("\n" + "="*80)
    print("VERIFYING LOADED DATA")
    print("="*80 + "\n")

    manager = get_manager()

    categories_to_verify = [
        "brand_guidelines",
        "hook_templates",
        "storyboard_templates",
        "winning_patterns"
    ]

    all_valid = True

    for category in categories_to_verify:
        try:
            data = manager.download_knowledge(category)

            if data:
                # Basic validation based on category
                if category == "brand_guidelines":
                    required = ["brand_name", "voice", "values"]
                    valid = all(k in data for k in required)
                    detail = f"Brand: {data.get('brand_name')}"

                elif category == "hook_templates":
                    valid = "templates" in data
                    detail = f"Templates: {len(data.get('templates', []))}"

                elif category == "storyboard_templates":
                    valid = "templates" in data
                    detail = f"Templates: {len(data.get('templates', []))}"

                elif category == "winning_patterns":
                    valid = "patterns" in data
                    detail = f"Patterns: {len(data.get('patterns', []))}"

                else:
                    valid = True
                    detail = "OK"

                status = "✓" if valid else "✗"
                print(f"{status} {category:<25} {detail}")

                if not valid:
                    all_valid = False
            else:
                print(f"✗ {category:<25} No data found")
                all_valid = False

        except Exception as e:
            print(f"✗ {category:<25} Error: {e}")
            all_valid = False

    print("\n" + "="*80)
    if all_valid:
        print("✓ All data verified successfully!")
    else:
        print("✗ Some data verification failed")
    print("="*80 + "\n")

    return all_valid


def main():
    """Main entry point"""
    try:
        # Load sample data
        success = load_sample_data()

        if not success:
            logger.error("Failed to load all sample data")
            return 1

        # Verify loaded data
        verified = verify_data()

        if not verified:
            logger.error("Data verification failed")
            return 1

        print("✓ Sample data loaded and verified successfully!")
        print("\nYou can now:")
        print("  1. Start the API server: python api.py")
        print("  2. Access knowledge via API: http://localhost:8004")
        print("  3. Use the web UI to manage knowledge")
        print("  4. Run example usage: python example_usage.py")

        return 0

    except Exception as e:
        logger.error(f"Failed to load sample data: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
