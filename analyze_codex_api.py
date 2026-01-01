#!/usr/bin/env python3
"""Use Gemini to analyze Codex API structure from binary strings"""
import requests, json, uuid
from pathlib import Path

# Load Gemini auth
creds = json.loads((Path.home() / ".gemini" / "oauth_creds.json").read_text())
token = creds["access_token"]

# Binary strings we extracted
binary_findings = """
From Codex binary strings analysis:

## API Endpoints Found:
1. https://chatgpt.com/backend-api/codex
2. https://api.openai.com/v1/responses
3. https://api.openai.com/v1
4. https://auth.openai.com/oauth/token
5. https://auth.openai.com/codex/device

## Authentication:
- Client ID: app_EMoamEEZ73f0CkXaXp7hrann
- OAuth flow: authorization_code with code_verifier
- JWT claims include:
  - chatgpt_account_id
  - chatgpt_plan_type: "pro"
  - chatgpt_user_id
  - Required scopes: openid, profile, email, offline_access

## Model Information:
- Model: gpt-5.2-codex
- Reasoning efforts: minimal, low, medium, high, xhigh
- Features mentioned:
  - reasoning_summaries
  - parallel tool calls
  - web_search_request
  - shell_tool
  - unified_exec

## Request Structure Hints:
- "reasoning_effort" parameter
- "model" parameter
- "messages" array with role/content
- "session_id" field
- Possibly uses streaming (streamGenerateContent vs generateContent pattern)

## Error Messages:
- "You have insufficient permissions for this operation. Missing scopes: api.responses.write"
- "The model `gpt-5.2-codex` does not exist or you do not have access to it."

## Observations:
- /v1/responses endpoint requires api.responses.write scope
- Standard /v1/chat/completions doesn't have gpt-5.2-codex model
- Backend API (/backend-api/codex) likely needs special headers or session
"""

prompt = f"""You are an expert at reverse engineering API structures. Based on these findings from a binary analysis of the OpenAI Codex CLI, help me construct the exact HTTP request format:

{binary_findings}

Please analyze and provide:

1. **Most Likely API Endpoint**: Which endpoint should I use?
2. **Complete Request Format**: Full JSON structure with all required fields
3. **Required Headers**: What headers are needed (Authorization, Content-Type, etc.)?
4. **OAuth Scope Solution**: How can I get the api.responses.write scope?
5. **Streaming vs Non-streaming**: Should I use a streaming endpoint?

Based on your analysis, provide a working Python requests example that would successfully call the Codex API.
"""

# Call Gemini
response = requests.post(
    "https://cloudcode-pa.googleapis.com/v1internal:generateContent",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gemini-2.5-pro",  # Use Pro for complex analysis
        "project": "autonomous-bay-whv63",
        "user_prompt_id": str(uuid.uuid4()),
        "request": {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "session_id": str(uuid.uuid4()),
            "generationConfig": {"temperature": 0.3, "topP": 0.95, "topK": 40}
        }
    },
    timeout=120
)

if response.status_code == 200:
    analysis = response.json()["response"]["candidates"][0]["content"]["parts"][0]["text"]
    print("=" * 80)
    print("GEMINI ANALYSIS OF CODEX API STRUCTURE")
    print("=" * 80)
    print(analysis)
    print("=" * 80)

    # Save to file
    output_path = Path("/tmp/gemini_codex_api_analysis.md")
    output_path.write_text(f"# Gemini Analysis of Codex API\n\n{analysis}")
    print(f"\n✅ Analysis saved to {output_path}")
else:
    print(f"❌ Gemini API error: {response.status_code}")
    print(response.text)
