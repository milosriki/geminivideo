"""
Quick integration script for actuals fetcher
Adds necessary imports and endpoint registration to main.py

Run this script to automatically integrate Agent 8 actuals fetcher:
    python integrate_actuals_fetcher.py
"""

import os
import sys


def integrate():
    """Integrate actuals fetcher into main.py"""

    main_py_path = "/home/user/geminivideo/services/ml-service/src/main.py"

    print("🔧 Integrating Actuals Fetcher (Agent 8) into ML Service...")

    # Check if file exists
    if not os.path.exists(main_py_path):
        print(f"❌ Error: {main_py_path} not found")
        return False

    # Read current content
    with open(main_py_path, 'r') as f:
        content = f.read()

    # Check if already integrated
    if 'actuals_endpoints' in content:
        print("✅ Actuals fetcher already integrated in main.py")
        return True

    print("\n📝 Integration steps:")
    print("\n1. Add these imports after existing imports:")
    print("=" * 60)
    print("""
from src.actuals_endpoints import register_actuals_endpoints, start_actuals_scheduler
""")

    print("\n2. Add this line in the root() endpoint (in the 'endpoints' dict):")
    print("=" * 60)
    print("""
            "actuals_fetcher": {
                "fetch_single": "/api/ml/actuals/fetch/{ad_id}",
                "sync_all": "/api/ml/actuals/sync",
                "scheduler_status": "/api/ml/actuals/scheduler-status",
                "fetcher_stats": "/api/ml/actuals/stats"
            }
""")

    print("\n3. Add this line after creating the FastAPI app (after app = FastAPI(...)):")
    print("=" * 60)
    print("""
# Register actuals fetcher endpoints (Agent 8)
register_actuals_endpoints(app)
""")

    print("\n4. Add this in the startup_event() function (after training scheduler starts):")
    print("=" * 60)
    print("""
    # Start actuals fetcher scheduler (Agent 8 - Investment Grade)
    start_actuals_scheduler()
""")

    print("\n" + "=" * 60)
    print("\n✅ Manual integration steps complete!")
    print("\n📋 Next steps:")
    print("   1. Set Meta API credentials in .env:")
    print("      META_ACCESS_TOKEN=your-token")
    print("      META_AD_ACCOUNT_ID=act_123456")
    print("      META_APP_SECRET=your-secret")
    print("      META_APP_ID=your-app-id")
    print("\n   2. Restart ML service:")
    print("      python src/main.py")
    print("\n   3. Verify scheduler is running:")
    print("      curl http://localhost:8003/api/ml/actuals/scheduler-status")
    print("\n" + "=" * 60)

    return True


if __name__ == "__main__":
    integrate()
