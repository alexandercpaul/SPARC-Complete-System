#!/usr/bin/env python3
"""Test Codex backend API (chatgpt.com/backend-api/codex)"""
import requests, json
from pathlib import Path

# Load auth
auth = json.loads((Path.home() / ".codex" / "auth.json").read_text())
access_token = auth["tokens"]["access_token"]

# Codex backend API endpoint (from binary strings)
url = "https://chatgpt.com/backend-api/codex"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Try different request formats
bodies = [
    # Format 1: Standard chat completions
    {
        "model": "gpt-5.2-codex",
        "messages": [{
            "role": "user",
            "content": "Say hello in 3 words"
        }]
    },
    # Format 2: With reasoning_effort
    {
        "model": "gpt-5.2-codex",
        "messages": [{
            "role": "user",
            "content": "Say hello in 3 words"
        }],
        "reasoning_effort": "xhigh"
    },
    # Format 3: Minimal
    {
        "model": "gpt-5.2-codex",
        "prompt": "Say hello in 3 words"
    }
]

for i, body in enumerate(bodies, 1):
    print(f"\n🔍 Test {i}: {list(body.keys())}")
    response = requests.post(url, headers=headers, json=body, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print(f"✅ SUCCESS! Format {i} works!")
        print(f"Response preview: {response.text[:200]}")
        break
    else:
        print(f"Response: {response.text[:300]}")
