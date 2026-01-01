#!/usr/bin/env python3
"""Test OpenAI Responses API for Codex"""
import requests, json
from pathlib import Path

# Load auth
auth = json.loads((Path.home() / ".codex" / "auth.json").read_text())
access_token = auth["tokens"]["access_token"]

# Responses API endpoint (from binary)
url = "https://api.openai.com/v1/responses"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "User-Agent": "codex-cli/0.0.0"
}

# Responses API format (different from chat completions)
body = {
    "model": "gpt-5.2-codex",
    "messages": [{
        "role": "user",
        "content": "Say hello in 3 words"
    }],
    "reasoning_effort": "low"
}

print("🔍 Testing OpenAI Responses API...")
print(f"Model: {body['model']}")
print(f"Endpoint: {url}\n")

response = requests.post(url, headers=headers, json=body, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS! Codex Responses API working!")
    data = response.json()
    print(f"\nFull response:\n{json.dumps(data, indent=2)[:500]}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text[:800]}")
