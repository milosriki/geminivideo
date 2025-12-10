#!/usr/bin/env python3
"""
Add Supabase secrets to GitHub using Personal Access Token
Requires: pip install PyNaCl requests
"""

import os
import sys
import base64
import json
import requests
from nacl import encoding, public
from nacl.public import SealedBox

REPO = "milosriki/geminivideo"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Secrets to add
SECRETS = {
    "SUPABASE_SECRET_KEY": "sb_secret_rL_TEpYtvcKoTOGwa1XthA_p8yxtuc3",
    "SUPABASE_ACCESS_TOKEN": "sbp_125c933334f63cbb1dbbe0d77bb6c29afc4ee0a8",
}

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a secret using the repository's public key with SealedBox."""
    # Decode the public key from base64
    public_key_bytes = base64.b64decode(public_key)
    public_key_obj = public.PublicKey(public_key_bytes, encoder=encoding.RawEncoder)
    
    # Use SealedBox for one-way encryption (GitHub has the private key)
    sealed_box = SealedBox(public_key_obj)
    
    # Encrypt the secret value
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    
    # GitHub expects the encrypted value as base64-encoded string
    return base64.b64encode(encrypted).decode("utf-8")

def get_public_key():
    """Get the repository's public key for encryption."""
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return data["key_id"], data["key"]

def add_secret(secret_name: str, secret_value: str, key_id: str, public_key: str):
    """Add a secret to GitHub repository."""
    encrypted_value = encrypt_secret(public_key, secret_value)
    
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [201, 204]:
        print(f"✅ {secret_name}: Added successfully")
        return True
    else:
        print(f"❌ {secret_name}: Failed (HTTP {response.status_code})")
        print(f"   Response: {response.text}")
        return False

def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export GITHUB_TOKEN=ghp_your_token_here")
        print("\nGet token from: https://github.com/settings/tokens")
        sys.exit(1)
    
    print("🔐 GitHub Secrets Automation")
    print("=" * 40)
    print()
    
    # Verify token
    print("🔍 Verifying GitHub token...")
    url = f"https://api.github.com/repos/{REPO}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("✅ Token verified")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Invalid GitHub token")
        elif e.response.status_code == 404:
            print("❌ Repository not found or no access")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)
    
    print()
    
    # Get public key
    print("🔑 Getting repository public key...")
    try:
        key_id, public_key = get_public_key()
        print("✅ Public key retrieved")
    except Exception as e:
        print(f"❌ Failed to get public key: {e}")
        sys.exit(1)
    
    print()
    
    # Add secrets
    print("📦 Adding secrets...")
    print()
    
    success_count = 0
    for secret_name, secret_value in SECRETS.items():
        if add_secret(secret_name, secret_value, key_id, public_key):
            success_count += 1
        print()
    
    # Ask for DB URL
    print("⚠️  Still need: SUPABASE_DB_URL")
    print("Get from: https://supabase.com/dashboard/project/akhirugwpozlxfvtqmvj/settings/database")
    print()
    
    db_url = input("Do you have SUPABASE_DB_URL to add now? (paste it or press Enter to skip): ").strip()
    if db_url:
        if add_secret("SUPABASE_DB_URL", db_url, key_id, public_key):
            success_count += 1
        print()
    
    print("=" * 40)
    print(f"✅ Added {success_count} secret(s)")
    print()
    print("Verify at: https://github.com/milosriki/geminivideo/settings/secrets/actions")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

