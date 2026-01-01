#!/usr/bin/env python3
"""Test Codex direct API with properly scoped OAuth token"""
import requests
import json
import uuid
from pathlib import Path

def call_codex_direct_api(prompt, model="gpt-5.2-codex", reasoning_effort="medium"):
    """Call Codex /v1/responses API directly"""

    # Load token with api.responses.write scope
    auth_path = Path.home() / ".codex" / "auth_direct_api.json"

    if not auth_path.exists():
        print("❌ Token file not found!")
        print(f"   Expected: {auth_path}")
        print()
        print("Please run: python3 /tmp/codex_oauth_flow.py")
        return None

    tokens = json.loads(auth_path.read_text())
    access_token = tokens["access_token"]

    # API endpoint
    url = "https://api.openai.com/v1/responses"

    # Headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "codex-cli/0.0.0"
    }

    # Request body
    session_id = str(uuid.uuid4())
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "reasoning_effort": reasoning_effort,
        "session_id": session_id,
        "stream": False
    }

    print("=" * 80)
    print("🚀 Calling Codex Direct API")
    print("=" * 80)
    print(f"Endpoint: {url}")
    print(f"Model: {model}")
    print(f"Reasoning: {reasoning_effort}")
    print(f"Session: {session_id[:8]}...")
    print(f"Prompt: {prompt[:50]}...")
    print()

    response = requests.post(url, headers=headers, json=payload, timeout=120)

    print(f"Status: {response.status_code}")
    print()

    if response.status_code == 200:
        print("✅ SUCCESS! Codex direct API working!")
        print("=" * 80)
        data = response.json()

        # Extract response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            print("Response:")
            print(content)
            print()

        # Show usage
        if "usage" in data:
            usage = data["usage"]
            print(f"Tokens: {usage.get('total_tokens', 'N/A')} total "
                  f"({usage.get('prompt_tokens', 'N/A')} prompt + "
                  f"{usage.get('completion_tokens', 'N/A')} completion)")

        print("=" * 80)
        return content

    elif response.status_code == 401:
        print("❌ Unauthorized - Token may be expired or missing scope")
        print(response.text[:500])
        print()
        print("Try running: python3 /tmp/codex_oauth_flow.py")
        return None

    else:
        print(f"❌ Error {response.status_code}")
        print(response.text[:800])
        return None

if __name__ == "__main__":
    # Test with a simple prompt
    result = call_codex_direct_api(
        "Write a Python function that calculates the Fibonacci sequence. Keep it under 10 lines.",
        reasoning_effort="medium"
    )

    if result:
        print()
        print("🎉 Codex direct API is fully operational!")
