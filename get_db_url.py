#!/usr/bin/env python3
"""
Get database connection string from Supabase
Uses the access token to construct the connection string
"""

import requests
import sys

ACCESS_TOKEN = "sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8"
PROJECT_REF = "akhirugwpozlxfvtqmvj"
REGION = "ap-southeast-1"

print("🔍 Getting database connection info...")
print()

# Get project info
url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    project_data = response.json()
    
    print("✅ Project info retrieved")
    print(f"   Project: {project_data.get('name', 'N/A')}")
    print(f"   Region: {project_data.get('region', REGION)}")
    print()
    
    # Connection string format
    print("📋 Database Connection String Format:")
    print()
    print("Transaction Mode (recommended for serverless):")
    print(f"postgres://postgres.{PROJECT_REF}:[YOUR-PASSWORD]@aws-0-{REGION}.pooler.supabase.com:6543/postgres")
    print()
    print("Session Mode (for persistent connections):")
    print(f"postgres://postgres.{PROJECT_REF}:[YOUR-PASSWORD]@aws-0-{REGION}.pooler.supabase.com:5432/postgres")
    print()
    print("⚠️  Note: You need to replace [YOUR-PASSWORD] with your database password")
    print("   Get it from: https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
    print()
    print("💡 Or get the full connection string from the dashboard:")
    print(f"   https://supabase.com/dashboard/project/{PROJECT_REF}/settings/database")
    print("   → Scroll to 'Connection string' → Copy the full string")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

