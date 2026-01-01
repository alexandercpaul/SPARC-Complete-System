#!/usr/bin/env python3
"""Test direct OpenAI Codex API call"""
import requests, json
from pathlib import Path

# Load auth
auth = json.loads((Path.home() / ".codex" / "auth.json").read_text())
access_token = auth["tokens"]["access_token"]

# OpenAI API endpoint (from JWT aud claim)
url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Request body (standard OpenAI format)
body = {
    "model": "gpt-5.2-codex",
    "messages": [{
        "role": "user",
        "content": "Say hello in 3 words"
    }],
    "temperature": 0.7,
    "max_tokens": 100
}

print("🔍 Testing direct OpenAI Codex API...")
print(f"Model: {body['model']}")
print(f"Endpoint: {url}\n")

response = requests.post(url, headers=headers, json=body, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS! Direct Codex API working!")
    data = response.json()
    if "choices" in data and len(data["choices"]) > 0:
        text = data["choices"][0]["message"]["content"]
        print(f"Response: {text}")
    print(f"\nFull response:\n{json.dumps(data, indent=2)[:500]}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text[:800]}")
