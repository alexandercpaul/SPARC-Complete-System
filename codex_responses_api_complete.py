#!/usr/bin/env python3
"""Complete Codex /v1/responses API implementation based on Gemini analysis"""
import requests, json, uuid
from pathlib import Path

# Load auth
auth = json.loads((Path.home() / ".codex" / "auth.json").read_text())
access_token = auth["tokens"]["access_token"]
account_id = auth["tokens"]["account_id"]

# API endpoint (from Gemini analysis)
url = "https://api.openai.com/v1/responses"

# Headers (as recommended by Gemini)
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "chatgpt-account-id": account_id,  # Additional header from source code
    "User-Agent": "codex-cli/0.0.0"
}

# Generate session ID
session_id = str(uuid.uuid4())

# Complete request payload (from Gemini analysis + binary findings)
payload = {
    "model": "gpt-5.2-codex",
    "messages": [{
        "role": "user",
        "content": "Say hello in 3 words"
    }],
    "reasoning_effort": "medium",  # minimal, low, medium, high, xhigh
    "session_id": session_id,
    "stream": False
}

print("🔍 Testing Codex /v1/responses API")
print(f"Endpoint: {url}")
print(f"Model: {payload['model']}")
print(f"Session ID: {session_id[:8]}...")
print(f"Account ID: {account_id[:8]}...\n")

response = requests.post(url, headers=headers, json=payload, timeout=120)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS! Codex direct API working!")
    data = response.json()
    print(f"\nResponse:\n{json.dumps(data, indent=2)[:1000]}")
elif response.status_code == 401:
    print(f"❌ Authorization error (as expected - missing scope)")
    print(f"Error: {response.text[:500]}")
    print("\n💡 Solution: Need OAuth flow with api.responses.write scope")
    print("   Client ID: app_EMoamEEZ73f0CkXaXp7hrann")
elif response.status_code == 404:
    print(f"❌ Not Found - wrong endpoint or model")
    print(f"Error: {response.text[:500]}")
else:
    print(f"❌ Error {response.status_code}")
    print(f"Response: {response.text[:800]}")
