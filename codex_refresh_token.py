#!/usr/bin/env python3
"""Refresh Codex OAuth token"""
import requests, json
from pathlib import Path
from datetime import datetime

# Load current auth
auth_path = Path.home() / ".codex" / "auth.json"
auth = json.loads(auth_path.read_text())

refresh_token = auth["tokens"]["refresh_token"]
client_id = "app_EMoamEEZ73f0CkXaXp7hrann"  # From binary strings

# OAuth token endpoint
url = "https://auth.openai.com/oauth/token"

# Token refresh request
data = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "client_id": client_id
}

print("🔄 Refreshing access token...")
response = requests.post(url, data=data, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ Token refreshed!")
    token_data = response.json()

    # Update auth.json
    auth["tokens"]["access_token"] = token_data["access_token"]
    auth["tokens"]["id_token"] = token_data.get("id_token", auth["tokens"]["id_token"])
    if "refresh_token" in token_data:
        auth["tokens"]["refresh_token"] = token_data["refresh_token"]
    auth["last_refresh"] = datetime.utcnow().isoformat() + "Z"

    # Save
    auth_path.write_text(json.dumps(auth, indent=2))
    print(f"Saved new tokens to {auth_path}")
    print(f"New access token: {token_data['access_token'][:50]}...")
else:
    print(f"❌ Failed to refresh: {response.status_code}")
    print(f"Response: {response.text}")
