# Gemini Direct API - WORKING IMPLEMENTATION

**Status**: ✅ Successfully tested - receiving 200 OK responses
**Date**: 2025-12-31
**Project ID**: autonomous-bay-whv63

## Working Python Code

```python
#!/usr/bin/env python3
import requests, json, uuid
from pathlib import Path

# Load OAuth credentials
creds = json.loads((Path.home() / ".gemini" / "oauth_creds.json").read_text())
token = creds["access_token"]

# Generate required UUIDs
session_id = str(uuid.uuid4())
user_prompt_id = str(uuid.uuid4())

# Endpoint
url = "https://cloudcode-pa.googleapis.com/v1internal:generateContent"

# Headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Request body
body = {
    "model": "gemini-2.5-flash",
    "project": "autonomous-bay-whv63",  # From loadCodeAssist
    "user_prompt_id": user_prompt_id,
    "request": {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Your prompt here"}]
        }],
        "session_id": session_id
    }
}

response = requests.post(url, headers=headers, json=body, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    # Extract response text
    text = data["response"]["candidates"][0]["content"]["parts"][0]["text"]
    print(f"Response: {text}")
```

## Required Parameters

### 1. OAuth Token
**Location**: `~/.gemini/oauth_creds.json`
**Format**:
```json
{
  "access_token": "ya29.a0Aa7pCA-...",
  "refresh_token": "1//05BkwjFdNdm4...",
  "scope": "https://www.googleapis.com/auth/cloud-platform ...",
  "token_type": "Bearer",
  "expiry_date": 1767174270978
}
```

### 2. Project ID
**Value**: `autonomous-bay-whv63`
**How to Get**: Call `loadCodeAssist` endpoint first

```python
url = "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist"
body = {
    "cloudaicompanionProject": None,
    "metadata": {
        "ideType": "IDE_UNSPECIFIED",
        "platform": "PLATFORM_UNSPECIFIED",
        "pluginType": "GEMINI"
    }
}
response = requests.post(url, headers=headers, json=body)
project_id = response.json()["cloudaicompanionProject"]
```

### 3. Model Names
**Valid Options** (from `defaultModelConfigs.js`):
- `gemini-2.5-flash` (fastest, recommended)
- `gemini-2.5-pro` (more capable)
- `gemini-3-flash-preview` (experimental)
- `gemini-3-pro-preview` (experimental)

### 4. Session ID
**Format**: UUID v4
**Generation**: `str(uuid.uuid4())`
**Purpose**: Tracks conversation context

### 5. User Prompt ID
**Format**: UUID v4
**Generation**: `str(uuid.uuid4())`
**Purpose**: Unique identifier for each request

## API Endpoint

**Base URL**: `https://cloudcode-pa.googleapis.com`
**API Version**: `v1internal`
**Method**: `generateContent` (non-streaming) or `streamGenerateContent` (streaming)

**Full URL**: `https://cloudcode-pa.googleapis.com/v1internal:generateContent`

## Request Structure

```json
{
  "model": "gemini-2.5-flash",
  "project": "autonomous-bay-whv63",
  "user_prompt_id": "uuid-here",
  "request": {
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "Your prompt"}]
      }
    ],
    "generationConfig": {
      "temperature": 0.7,
      "maxOutputTokens": 8192
    },
    "session_id": "uuid-here"
  }
}
```

## Response Structure

```json
{
  "response": {
    "candidates": [
      {
        "content": {
          "role": "model",
          "parts": [{"text": "AI response text here"}]
        },
        "finishReason": "STOP",
        "avgLogprobs": -2.0276342391967774
      }
    ],
    "usageMetadata": {
      "promptTokenCount": 7,
      "candidatesTokenCount": 5,
      "totalTokenCount": 33
    },
    "modelVersion": "gemini-2.5-flash"
  }
}
```

## Source Code References

**CLI Package**: `@google/gemini-cli` (Node.js)
**Installation Path**: `/opt/homebrew/lib/node_modules/@google/gemini-cli/`

**Key Files**:
- `node_modules/@google/gemini-cli-core/dist/src/code_assist/server.js` - Endpoint definition
- `node_modules/@google/gemini-cli-core/dist/src/code_assist/converter.js` - Request structure
- `node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js` - OAuth credentials
- `node_modules/@google/gemini-cli-core/dist/src/code_assist/setup.js` - Project ID retrieval
- `dist/src/ui/commands/clearCommand.js` - Session ID generation
- `node_modules/@google/gemini-cli-core/dist/src/config/defaultModelConfigs.js` - Model names

## OAuth Client Credentials

**Client ID**: `[REDACTED - See ~/.gemini/oauth_creds.json]`
**Client Secret**: `[REDACTED - See ~/.gemini/oauth_creds.json]`
**Scopes**:
- `https://www.googleapis.com/auth/cloud-platform`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`

## Example Response (Real Test)

**Prompt**: "Hello, respond in 3 words"
**Response**: "How may I help?"
**Status**: 200 OK
**Model**: gemini-2.5-flash
**Tokens**: 7 prompt + 5 response = 33 total (includes overhead)

## Error Cases

### 403 Permission Denied
**Cause**: Using wrong endpoint (Developer API instead of Code Assist)
**Fix**: Use `cloudcode-pa.googleapis.com/v1internal` NOT `generativelanguage.googleapis.com`

### 500 Internal Error
**Cause**: Missing project ID or wrong model name
**Fix**: Call `loadCodeAssist` to get project ID, use valid model name

### 404 Not Found
**Cause**: Invalid model name
**Fix**: Use `gemini-2.5-flash` or other valid model from `defaultModelConfigs.js`

## Subscription Info

**Plan**: Gemini Ultra ($250/month)
**Includes**:
- 30TB Google Cloud storage
- Unlimited API usage (session/daily/weekly limits, not per-token billing)
- Access to latest Gemini 2.5 and 3.0 preview models
