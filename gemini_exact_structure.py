#!/usr/bin/env python3
"""Exact structure from CLI source code"""
import requests, json, uuid
from pathlib import Path

# Load OAuth
creds = json.loads((Path.home() / ".gemini" / "oauth_creds.json").read_text())
token = creds["access_token"]

# Generate IDs
session_id = str(uuid.uuid4())
user_prompt_id = str(uuid.uuid4())

# Endpoint
url = "https://cloudcode-pa.googleapis.com/v1internal:generateContent"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Exact structure from toGenerateContentRequest()
body = {
    "model": "gemini-2.5-flash",
    "project": "autonomous-bay-whv63",
    "user_prompt_id": user_prompt_id,
    "request": {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Say hello in 3 words"}]
        }],
        "session_id": session_id,
        "generationConfig": {
            "temperature": 1,
            "topP": 0.95,
            "topK": 64
        }
    }
}

print(f"🔍 Testing with exact CLI structure...")
print(f"Model: {body['model']}")
print(f"Project: {body['project']}")
print(f"Session ID: {session_id[:8]}...")
print(f"User Prompt ID: {user_prompt_id[:8]}...\n")

response = requests.post(url, headers=headers, json=body, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS!")
    data = response.json()
    if "response" in data and "candidates" in data["response"]:
        text = data["response"]["candidates"][0]["content"]["parts"][0]["text"]
        print(f"Response: {text}")
    print(f"\nFull response:\n{json.dumps(data, indent=2)[:500]}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"Response: {response.text}")
