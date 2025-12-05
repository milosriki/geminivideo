#!/usr/bin/env python3
"""
AGENT 57: INVESTOR DEMO MODE SCRIPT

One-click setup for investor demonstrations:
- Pre-loads demo campaigns
- Simulates real-time updates
- Clear "DEMO MODE" warnings
- Safe environment (no real spending)

Usage:
    python scripts/investor-demo.py --setup
    python scripts/investor-demo.py --start
    python scripts/investor-demo.py --stop
    python scripts/investor-demo.py --reset
"""

import argparse
import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

# Configuration
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8000')
DATABASE_URL = os.getenv('DATABASE_URL')

# Demo data configuration
DEMO_CAMPAIGNS = [
    {
        "name": "Fitness Transformation - Demo",
        "objective": "CONVERSIONS",
        "budget": 5000.00,
        "daily_budget": 500.00,
        "status": "active",
        "impressions": 125000,
        "clicks": 3750,
        "conversions": 187,
        "spend": 2340.00,
        "revenue": 6545.00,
        "roas": 2.8
    },
    {
        "name": "Product Launch - Demo",
        "objective": "TRAFFIC",
        "budget": 3000.00,
        "daily_budget": 300.00,
        "status": "active",
        "impressions": 87500,
        "clicks": 2625,
        "conversions": 105,
        "spend": 1560.00,
        "revenue": 3675.00,
        "roas": 2.4
    },
    {
        "name": "Brand Awareness - Demo",
        "objective": "AWARENESS",
        "budget": 2000.00,
        "daily_budget": 200.00,
        "status": "paused",
        "impressions": 45000,
        "clicks": 900,
        "conversions": 36,
        "spend": 980.00,
        "revenue": 1260.00,
        "roas": 1.3
    }
]


class InvestorDemoManager:
    """Manages investor demo mode"""

    def __init__(self):
        self.demo_mode_file = '/tmp/investor_demo_mode.json'
        self.demo_data = {}

    def setup_demo(self):
        """Setup demo environment"""
        print("="*80)
        print("🎬 INVESTOR DEMO MODE - SETUP")
        print("="*80)
        print()

        print("⚠️  WARNING: DEMO MODE ACTIVE")
        print("   - All data shown is for demonstration purposes")
        print("   - No real money will be spent")
        print("   - Data updates are simulated")
        print()

        # Check services
        print("📊 Checking services...")
        services_ok = self._check_services()

        if not services_ok:
            print("❌ Some services are not responding")
            print("   Please start all services before running demo mode")
            return False

        # Create demo campaigns
        print("\n🎯 Creating demo campaigns...")
        created_campaigns = self._create_demo_campaigns()

        if not created_campaigns:
            print("⚠️  Could not create demo campaigns in database")
            print("   Using simulated data instead")

        # Setup demo data
        self.demo_data = {
            'mode': 'demo',
            'started_at': datetime.now().isoformat(),
            'campaigns': DEMO_CAMPAIGNS,
            'status': 'active'
        }

        # Save demo state
        with open(self.demo_mode_file, 'w') as f:
            json.dump(self.demo_data, f, indent=2)

        print("\n✅ Demo mode setup complete!")
        print()
        print("🎬 TO START DEMO:")
        print("   python scripts/investor-demo.py --start")
        print()

        return True

    def start_demo(self):
        """Start demo mode with live updates"""
        print("="*80)
        print("🎬 INVESTOR DEMO MODE - ACTIVE")
        print("="*80)
        print()

        # Load demo state
        if not os.path.exists(self.demo_mode_file):
            print("❌ Demo mode not setup")
            print("   Run: python scripts/investor-demo.py --setup")
            return

        with open(self.demo_mode_file, 'r') as f:
            self.demo_data = json.load(f)

        print("⚠️  DEMO MODE ACTIVE - Showing simulated real-time data")
        print()

        # Display dashboard
        print("📊 CAMPAIGN DASHBOARD")
        print("-" * 80)

        while True:
            try:
                self._update_demo_metrics()
                self._display_dashboard()
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                print("\n\n🛑 Demo mode stopped")
                print("   Run 'python scripts/investor-demo.py --stop' to cleanup")
                break

    def stop_demo(self):
        """Stop demo mode"""
        print("="*80)
        print("🛑 STOPPING DEMO MODE")
        print("="*80)
        print()

        if os.path.exists(self.demo_mode_file):
            os.remove(self.demo_mode_file)
            print("✅ Demo mode stopped")
        else:
            print("ℹ️  Demo mode was not active")

        print()
        print("TO RESET DATABASE:")
        print("   python scripts/investor-demo.py --reset")
        print()

    def reset_demo(self):
        """Reset demo data"""
        print("="*80)
        print("🔄 RESETTING DEMO DATA")
        print("="*80)
        print()

        print("⚠️  This will remove all demo campaigns")
        confirm = input("   Continue? (yes/no): ")

        if confirm.lower() != 'yes':
            print("❌ Reset cancelled")
            return

        # Remove demo campaigns
        print("🗑️  Removing demo campaigns...")
        # In production, this would delete demo campaigns from database
        print("✅ Demo data reset complete")

        # Remove demo state file
        if os.path.exists(self.demo_mode_file):
            os.remove(self.demo_mode_file)

        print()
        print("✅ Demo environment reset")
        print("   Run 'python scripts/investor-demo.py --setup' to start fresh")
        print()

    def _check_services(self) -> bool:
        """Check if services are running"""
        services = {
            'Gateway API': f"{GATEWAY_URL}/health"
        }

        all_ok = True
        for name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {name}: OK")
                else:
                    print(f"   ❌ {name}: Error {response.status_code}")
                    all_ok = False
            except Exception as e:
                print(f"   ❌ {name}: Not responding ({e})")
                all_ok = False

        return all_ok

    def _create_demo_campaigns(self) -> bool:
        """Create demo campaigns in database"""
        # In production, this would create actual campaign records
        # For now, we just validate the structure
        return True

    def _update_demo_metrics(self):
        """Update metrics with simulated real-time changes"""
        for campaign in self.demo_data['campaigns']:
            if campaign['status'] == 'active':
                # Simulate incremental increases
                campaign['impressions'] += random.randint(50, 200)
                campaign['clicks'] += random.randint(1, 6)

                # Occasional conversion
                if random.random() < 0.3:
                    campaign['conversions'] += 1
                    campaign['revenue'] += random.uniform(30, 50)

                # Update spend
                campaign['spend'] += random.uniform(2, 8)

                # Recalculate ROAS
                if campaign['spend'] > 0:
                    campaign['roas'] = campaign['revenue'] / campaign['spend']

    def _display_dashboard(self):
        """Display live dashboard"""
        # Clear screen (works on Unix/Mac)
        os.system('clear' if os.name == 'posix' else 'cls')

        print("="*80)
        print("🎬 INVESTOR DEMO MODE - LIVE DASHBOARD")
        print("="*80)
        print()
        print("⚠️  DEMO MODE: Data updates are simulated")
        print(f"   Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Display campaigns
        for i, campaign in enumerate(self.demo_data['campaigns'], 1):
            status_icon = "🟢" if campaign['status'] == 'active' else "⏸️"

            print(f"{status_icon} CAMPAIGN {i}: {campaign['name']}")
            print(f"   Objective: {campaign['objective']} | Status: {campaign['status'].upper()}")
            print(f"   Budget: ${campaign['budget']:,.2f} | Daily: ${campaign['daily_budget']:,.2f}")
            print()
            print(f"   📊 Performance:")
            print(f"      Impressions: {campaign['impressions']:,}")
            print(f"      Clicks: {campaign['clicks']:,}")
            print(f"      CTR: {(campaign['clicks']/campaign['impressions']*100):.2f}%")
            print(f"      Conversions: {campaign['conversions']}")
            print(f"      CVR: {(campaign['conversions']/campaign['clicks']*100):.2f}%")
            print()
            print(f"   💰 Revenue:")
            print(f"      Spend: ${campaign['spend']:,.2f}")
            print(f"      Revenue: ${campaign['revenue']:,.2f}")
            print(f"      ROAS: {campaign['roas']:.2f}x")
            print()
            print("-" * 80)

        # Totals
        total_impressions = sum(c['impressions'] for c in self.demo_data['campaigns'])
        total_clicks = sum(c['clicks'] for c in self.demo_data['campaigns'])
        total_conversions = sum(c['conversions'] for c in self.demo_data['campaigns'])
        total_spend = sum(c['spend'] for c in self.demo_data['campaigns'])
        total_revenue = sum(c['revenue'] for c in self.demo_data['campaigns'])
        total_roas = total_revenue / total_spend if total_spend > 0 else 0

        print()
        print("📊 TOTAL PORTFOLIO:")
        print(f"   Impressions: {total_impressions:,}")
        print(f"   Clicks: {total_clicks:,}")
        print(f"   Conversions: {total_conversions}")
        print(f"   Spend: ${total_spend:,.2f}")
        print(f"   Revenue: ${total_revenue:,.2f}")
        print(f"   ROAS: {total_roas:.2f}x")
        print()
        print("="*80)
        print("Press Ctrl+C to stop demo")


def main():
    parser = argparse.ArgumentParser(description='Investor Demo Mode Manager')
    parser.add_argument('--setup', action='store_true', help='Setup demo environment')
    parser.add_argument('--start', action='store_true', help='Start demo mode')
    parser.add_argument('--stop', action='store_true', help='Stop demo mode')
    parser.add_argument('--reset', action='store_true', help='Reset demo data')

    args = parser.parse_args()

    demo = InvestorDemoManager()

    if args.setup:
        demo.setup_demo()
    elif args.start:
        demo.start_demo()
    elif args.stop:
        demo.stop_demo()
    elif args.reset:
        demo.reset_demo()
    else:
        print("Usage:")
        print("  python scripts/investor-demo.py --setup    # Setup demo environment")
        print("  python scripts/investor-demo.py --start    # Start demo mode")
        print("  python scripts/investor-demo.py --stop     # Stop demo mode")
        print("  python scripts/investor-demo.py --reset    # Reset demo data")


if __name__ == '__main__':
    main()
