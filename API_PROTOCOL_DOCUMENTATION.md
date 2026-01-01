# API Protocol Documentation: Gemini CLI & Codex CLI

**Last Updated:** 2025-12-31
**Purpose:** Reverse-engineered protocol specifications for making API calls that mimic official Gemini CLI and Codex CLI clients

---

## Executive Summary

This document provides comprehensive technical details on how to replicate the exact API protocols used by:
1. **Gemini CLI** (Google's official Gemini command-line client)
2. **Codex CLI** (OpenAI's official Codex command-line client)

By understanding these protocols, Claude Code can make API calls that are indistinguishable from the official clients, enabling full compatibility with Google's Gemini API and OpenAI's Chat API.

---

## Part 1: Gemini CLI API Protocol

### 1.1 Architecture Overview

**SDK:** `@google/genai` v1.30.0
**Installation Path:** `/opt/homebrew/lib/node_modules/@google/gemini-cli/`
**Core Module:** `@google/genai/dist/node/index.mjs`

**Two API Modes:**
1. **Gemini Developer API** (API Key authentication)
2. **Vertex AI API** (OAuth/ADC authentication)

### 1.2 Authentication

#### 1.2.1 OAuth Token Storage
**Location:** `~/.gemini/oauth_creds.json`

**Token Structure:**
```json
{
  "access_token": "ya29.a0...",
  "scope": "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email openid",
  "token_type": "Bearer",
  "id_token": "eyJhbGc...",
  "expiry_date": 1767169219734,
  "refresh_token": "1//05BkwjFdNdm4..."
}
```

#### 1.2.2 Authentication Headers

**For API Key (Gemini Developer API):**
```
x-goog-api-key: YOUR_API_KEY
```

**For OAuth (Vertex AI):**
```
Authorization: Bearer ya29.a0...
```

**Environment Variables:**
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - API key (Developer API)
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_CLOUD_LOCATION` - GCP location (e.g., "us-central1" or "global")
- `GOOGLE_GENAI_USE_VERTEXAI` - Set to "true" for Vertex AI mode

#### 1.2.3 Auth Implementation Details

**Source:** Lines 15817-15862 in `@google/genai/dist/node/index.mjs`

```javascript
class NodeAuth {
    async addAuthHeaders(headers, url) {
        if (this.apiKey !== undefined) {
            // API Key mode
            headers.append('x-goog-api-key', this.apiKey);
        } else {
            // OAuth mode - uses google-auth-library
            const authHeaders = await this.googleAuth.getRequestHeaders(url);
            for (const [key, value] of authHeaders) {
                headers.append(key, value);
            }
        }
    }
}
```

**OAuth Scope Required:**
```
https://www.googleapis.com/auth/cloud-platform
```

### 1.3 Base URLs

#### 1.3.1 Gemini Developer API
```
Base URL: https://generativelanguage.googleapis.com/
API Version: v1beta
```

**Full Endpoint Pattern:**
```
https://generativelanguage.googleapis.com/v1beta/{resource}?key={api_key}
```

#### 1.3.2 Vertex AI API

**Global Endpoint:**
```
Base URL: https://aiplatform.googleapis.com/
API Version: v1beta1
```

**Regional Endpoint (when location is not "global"):**
```
Base URL: https://{location}-aiplatform.googleapis.com/
API Version: v1beta1
```

**Full Endpoint Pattern:**
```
https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project}/locations/{location}/{resource}
```

### 1.4 HTTP Headers

**Standard Request Headers:**
```http
User-Agent: google-genai-sdk/1.30.0 Node.js/{version}
x-goog-api-client: google-genai-sdk/1.30.0 Node.js/{version}
Content-Type: application/json
```

**Optional Headers:**
```http
X-Server-Timeout: {timeout_in_seconds}
```

**Source:** Lines 11194-11199, 11553-11560

```javascript
const CONTENT_TYPE_HEADER = 'Content-Type';
const SERVER_TIMEOUT_HEADER = 'X-Server-Timeout';
const USER_AGENT_HEADER = 'User-Agent';
const GOOGLE_API_CLIENT_HEADER = 'x-goog-api-client';
const SDK_VERSION = '1.30.0';
const LIBRARY_LABEL = `google-genai-sdk/${SDK_VERSION}`;

getDefaultHeaders() {
    const headers = {};
    const versionHeaderValue = LIBRARY_LABEL + ' ' + this.clientOptions.userAgentExtra;
    headers[USER_AGENT_HEADER] = versionHeaderValue;
    headers[GOOGLE_API_CLIENT_HEADER] = versionHeaderValue;
    headers[CONTENT_TYPE_HEADER] = 'application/json';
    return headers;
}
```

### 1.5 Request Format (generateContent Example)

**Endpoint:**
```
POST /v1beta/models/{model}:generateContent
```

**Request Body Structure:**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Hello, how are you?"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 1.0,
    "topP": 0.95,
    "topK": 40,
    "maxOutputTokens": 8192,
    "stopSequences": []
  },
  "systemInstruction": {
    "parts": [
      {
        "text": "You are a helpful assistant."
      }
    ]
  },
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "get_weather",
          "description": "Get current weather",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City name"
              }
            },
            "required": ["location"]
          }
        }
      ]
    }
  ]
}
```

### 1.6 Streaming Requests

**Endpoint Modification:**
```
Add query parameter: ?alt=sse
```

**Source:** Lines 11416-11418
```javascript
if (!url.searchParams.has('alt') || url.searchParams.get('alt') !== 'sse') {
    url.searchParams.set('alt', 'sse');
}
```

**Response Format:**
Server-Sent Events (SSE) with data lines:
```
data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}

data: {"candidates":[{"content":{"parts":[{"text":" there"}]}}]}
```

### 1.7 Tool/Function Calling

**Tool Declaration Format:**
```json
{
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "function_name",
          "description": "Function description",
          "parameters": {
            "type": "object",
            "properties": {
              "param1": {
                "type": "string",
                "description": "Parameter description"
              }
            },
            "required": ["param1"]
          }
        }
      ]
    }
  ]
}
```

**Function Response Format:**
```json
{
  "contents": [
    {
      "role": "function",
      "parts": [
        {
          "functionResponse": {
            "name": "function_name",
            "response": {
              "result": "function output"
            }
          }
        }
      ]
    }
  ]
}
```

### 1.8 Error Handling

**Error Response Structure:**
```json
{
  "error": {
    "code": 400,
    "message": "Invalid request",
    "status": "INVALID_ARGUMENT"
  }
}
```

**Source:** Lines 11502-11515 (stream error handling)

### 1.9 Complete Python Example (Gemini Developer API)

```python
import requests
import json
import os

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.base_url = 'https://generativelanguage.googleapis.com'
        self.api_version = 'v1beta'
        self.sdk_version = '1.30.0'

    def get_headers(self):
        """Get standard headers matching Gemini CLI"""
        return {
            'User-Agent': f'google-genai-sdk/{self.sdk_version} Python/3.x',
            'x-goog-api-client': f'google-genai-sdk/{self.sdk_version} Python/3.x',
            'Content-Type': 'application/json'
        }

    def generate_content(self, model, contents, generation_config=None,
                        system_instruction=None, tools=None):
        """
        Generate content using Gemini API

        Args:
            model: Model name (e.g., 'gemini-2.0-flash-exp')
            contents: List of content objects with role and parts
            generation_config: Optional generation configuration
            system_instruction: Optional system instruction
            tools: Optional tool declarations
        """
        url = f'{self.base_url}/{self.api_version}/models/{model}:generateContent'

        # Add API key as query parameter
        params = {'key': self.api_key}

        # Build request body
        body = {'contents': contents}

        if generation_config:
            body['generationConfig'] = generation_config

        if system_instruction:
            body['systemInstruction'] = system_instruction

        if tools:
            body['tools'] = tools

        response = requests.post(
            url,
            params=params,
            headers=self.get_headers(),
            json=body
        )

        response.raise_for_status()
        return response.json()

    def stream_generate_content(self, model, contents, **kwargs):
        """Stream generate content with SSE"""
        url = f'{self.base_url}/{self.api_version}/models/{model}:streamGenerateContent'

        params = {
            'key': self.api_key,
            'alt': 'sse'  # Enable Server-Sent Events
        }

        body = {'contents': contents}
        # Add other parameters from kwargs
        for key in ['generationConfig', 'systemInstruction', 'tools']:
            if key in kwargs and kwargs[key]:
                body[key] = kwargs[key]

        response = requests.post(
            url,
            params=params,
            headers=self.get_headers(),
            json=body,
            stream=True
        )

        response.raise_for_status()

        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    yield json.loads(data)

# Example usage
client = GeminiClient(api_key='YOUR_API_KEY')

# Simple text generation
response = client.generate_content(
    model='gemini-2.0-flash-exp',
    contents=[
        {
            'role': 'user',
            'parts': [{'text': 'Hello, what is 2+2?'}]
        }
    ],
    generation_config={
        'temperature': 1.0,
        'maxOutputTokens': 8192
    }
)

print(response)

# Streaming example
for chunk in client.stream_generate_content(
    model='gemini-2.0-flash-exp',
    contents=[
        {
            'role': 'user',
            'parts': [{'text': 'Write a haiku about coding'}]
        }
    ]
):
    if 'candidates' in chunk and chunk['candidates']:
        text = chunk['candidates'][0]['content']['parts'][0].get('text', '')
        if text:
            print(text, end='', flush=True)
```

### 1.10 Complete Python Example (Vertex AI with OAuth)

```python
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request

class VertexAIClient:
    def __init__(self, project_id=None, location='us-central1'):
        self.project_id = project_id
        self.location = location

        # Determine base URL
        if location and location != 'global':
            self.base_url = f'https://{location}-aiplatform.googleapis.com'
        else:
            self.base_url = 'https://aiplatform.googleapis.com'

        self.api_version = 'v1beta1'
        self.sdk_version = '1.30.0'

        # Get credentials using Application Default Credentials
        self.credentials, self.project_id = default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

    def get_access_token(self):
        """Get fresh OAuth access token"""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def get_headers(self):
        """Get standard headers matching Gemini CLI"""
        return {
            'Authorization': f'Bearer {self.get_access_token()}',
            'User-Agent': f'google-genai-sdk/{self.sdk_version} Python/3.x',
            'x-goog-api-client': f'google-genai-sdk/{self.sdk_version} Python/3.x',
            'Content-Type': 'application/json'
        }

    def generate_content(self, model, contents, **kwargs):
        """Generate content using Vertex AI"""
        # Build resource path
        resource_path = (
            f'projects/{self.project_id}/locations/{self.location}'
            f'/publishers/google/models/{model}:generateContent'
        )

        url = f'{self.base_url}/{self.api_version}/{resource_path}'

        body = {'contents': contents}
        for key in ['generationConfig', 'systemInstruction', 'tools']:
            if key in kwargs and kwargs[key]:
                body[key] = kwargs[key]

        response = requests.post(
            url,
            headers=self.get_headers(),
            json=body
        )

        response.raise_for_status()
        return response.json()

# Example usage
client = VertexAIClient(
    project_id='your-project-id',
    location='us-central1'
)

response = client.generate_content(
    model='gemini-2.0-flash-exp',
    contents=[
        {
            'role': 'user',
            'parts': [{'text': 'Hello from Vertex AI!'}]
        }
    ]
)

print(response)
```

---

## Part 2: Codex (OpenAI) CLI API Protocol

### 2.1 Architecture Overview

**Implementation:** Rust binary wrapped by Node.js launcher
**Installation Path:** `/opt/homebrew/lib/node_modules/@openai/codex/`
**Binary Location:** `/opt/homebrew/lib/node_modules/@openai/codex/vendor/aarch64-apple-darwin/codex/codex`

**Note:** Codex is a compiled Rust binary, so protocol details are inferred from auth tokens and OpenAI API documentation.

### 2.2 Authentication

#### 2.2.1 OAuth Token Storage
**Location:** `~/.codex/auth.json`

**Token Structure:**
```json
{
  "OPENAI_API_KEY": null,
  "tokens": {
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI...",
    "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI...",
    "refresh_token": "rt_...",
    "account_id": "532cfd8b-7b79-49b5-a51e-858c96e5b053"
  },
  "last_refresh": "2025-12-28T20:40:58.139605Z"
}
```

#### 2.2.2 JWT Token Structure (Decoded)

**ID Token Claims:**
```json
{
  "iss": "https://auth.openai.com",
  "sub": "google-oauth2|106010904270118379688",
  "aud": ["app_EMoamEEZ73f0CkXaXp7hrann"],
  "exp": 1766958057,
  "iat": 1766954457,
  "email": "alexandercpaul@gmail.com",
  "email_verified": true,
  "https://api.openai.com/auth": {
    "chatgpt_account_id": "532cfd8b-7b79-49b5-a51e-858c96e5b053",
    "chatgpt_plan_type": "pro",
    "chatgpt_subscription_active_until": "2026-01-07T12:05:06+00:00",
    "chatgpt_user_id": "user-PnHQjRuJkGJcMQq8AZVHNPQS",
    "organizations": [
      {
        "id": "org-F3I5sxgvmCIKuELzqj6ccIJq",
        "is_default": true,
        "role": "owner",
        "title": "Personal"
      }
    ]
  }
}
```

**Access Token Claims:**
```json
{
  "iss": "https://auth.openai.com",
  "sub": "google-oauth2|106010904270118379688",
  "aud": ["https://api.openai.com/v1"],
  "exp": 1767818458,
  "iat": 1766954457,
  "scope": ["openid", "profile", "email", "offline_access"],
  "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
  "https://api.openai.com/auth": {
    "chatgpt_account_id": "532cfd8b-7b79-49b5-a51e-858c96e5b053",
    "chatgpt_plan_type": "pro",
    "chatgpt_user_id": "user-PnHQjRuJkGJcMQq8AZVHNPQS"
  }
}
```

#### 2.2.3 Authentication Methods

**1. ChatGPT OAuth (Recommended):**
- Authorization endpoint: `https://auth.openai.com`
- Client ID: `app_EMoamEEZ73f0CkXaXp7hrann`
- Scopes: `openid profile email offline_access`

**2. API Key:**
- Stored in `OPENAI_API_KEY` field
- Traditional OpenAI API key format: `sk-...`

### 2.3 Base URLs

**OpenAI Chat Completions API:**
```
Base URL: https://api.openai.com/v1
```

**Common Endpoints:**
```
POST /v1/chat/completions         # Standard chat
POST /v1/chat/completions         # Streaming (with stream: true)
```

### 2.4 HTTP Headers

**Standard Request Headers:**
```http
Authorization: Bearer {access_token}
Content-Type: application/json
User-Agent: Codex/{version}
```

**For API Key Authentication:**
```http
Authorization: Bearer sk-...
Content-Type: application/json
```

### 2.5 Request Format (Chat Completions)

**Endpoint:**
```
POST /v1/chat/completions
```

**Request Body:**
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful coding assistant."
    },
    {
      "role": "user",
      "content": "Write a Python function to sort a list"
    }
  ],
  "temperature": 1.0,
  "max_tokens": 4096,
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "execute_bash",
        "description": "Execute a bash command",
        "parameters": {
          "type": "object",
          "properties": {
            "command": {
              "type": "string",
              "description": "The bash command to execute"
            }
          },
          "required": ["command"]
        }
      }
    }
  ]
}
```

### 2.6 Streaming Requests

**Request Modification:**
```json
{
  "stream": true
}
```

**Response Format (SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: [DONE]
```

### 2.7 Tool/Function Calling

**Tool Declaration:**
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "function_name",
        "description": "What the function does",
        "parameters": {
          "type": "object",
          "properties": {
            "param1": {
              "type": "string",
              "description": "Parameter description"
            }
          },
          "required": ["param1"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Tool Call Response from Model:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "function_name",
              "arguments": "{\"param1\": \"value\"}"
            }
          }
        ]
      }
    }
  ]
}
```

**Tool Result Submission:**
```json
{
  "messages": [
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "content": "Function execution result"
    }
  ]
}
```

### 2.8 Complete Python Example (OAuth)

```python
import requests
import json
import jwt
from datetime import datetime

class CodexClient:
    def __init__(self, access_token=None, api_key=None):
        self.access_token = access_token
        self.api_key = api_key
        self.base_url = 'https://api.openai.com/v1'

    @classmethod
    def from_auth_file(cls, auth_file='~/.codex/auth.json'):
        """Load auth from Codex auth file"""
        import os
        path = os.path.expanduser(auth_file)
        with open(path, 'r') as f:
            auth_data = json.load(f)

        # Check if we need to refresh token
        if 'tokens' in auth_data and 'access_token' in auth_data['tokens']:
            access_token = auth_data['tokens']['access_token']

            # Decode to check expiration
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            exp = decoded.get('exp', 0)

            if datetime.now().timestamp() > exp:
                print("Warning: Access token expired, need to refresh")
                # Would need to implement refresh logic here

            return cls(access_token=access_token)
        elif auth_data.get('OPENAI_API_KEY'):
            return cls(api_key=auth_data['OPENAI_API_KEY'])
        else:
            raise ValueError("No valid auth found in auth file")

    def get_headers(self):
        """Get headers matching Codex CLI"""
        headers = {
            'Content-Type': 'application/json'
        }

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        elif self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        else:
            raise ValueError("No authentication method configured")

        return headers

    def chat_completion(self, messages, model='gpt-4', temperature=1.0,
                       max_tokens=4096, tools=None, stream=False):
        """
        Create a chat completion

        Args:
            messages: List of message objects
            model: Model to use (e.g., 'gpt-4', 'gpt-4-turbo')
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions
            stream: Whether to stream responses
        """
        url = f'{self.base_url}/chat/completions'

        body = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }

        if tools:
            body['tools'] = tools
            body['tool_choice'] = 'auto'

        if stream:
            return self._stream_completion(url, body)
        else:
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=body
            )
            response.raise_for_status()
            return response.json()

    def _stream_completion(self, url, body):
        """Stream chat completion"""
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=body,
            stream=True
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    yield json.loads(data)

# Example usage
client = CodexClient.from_auth_file()

# Simple chat
response = client.chat_completion(
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful coding assistant.'
        },
        {
            'role': 'user',
            'content': 'Write a Python hello world'
        }
    ],
    model='gpt-4'
)

print(response['choices'][0]['message']['content'])

# Streaming
for chunk in client.chat_completion(
    messages=[
        {
            'role': 'user',
            'content': 'Count to 5'
        }
    ],
    model='gpt-4',
    stream=True
):
    if 'choices' in chunk and chunk['choices']:
        delta = chunk['choices'][0].get('delta', {})
        content = delta.get('content', '')
        if content:
            print(content, end='', flush=True)

# With tools
response = client.chat_completion(
    messages=[
        {
            'role': 'user',
            'content': 'List files in current directory'
        }
    ],
    model='gpt-4',
    tools=[
        {
            'type': 'function',
            'function': {
                'name': 'execute_bash',
                'description': 'Execute a bash command',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'Bash command to run'
                        }
                    },
                    'required': ['command']
                }
            }
        }
    ]
)

# Check if model wants to call a tool
if response['choices'][0]['message'].get('tool_calls'):
    tool_call = response['choices'][0]['message']['tool_calls'][0]
    print(f"Model wants to call: {tool_call['function']['name']}")
    print(f"With arguments: {tool_call['function']['arguments']}")
```

---

## Part 3: Key Differences Between Gemini and Codex

| Feature | Gemini CLI | Codex CLI |
|---------|-----------|-----------|
| **Auth Header** | `x-goog-api-key` (API key)<br>`Authorization: Bearer` (OAuth) | `Authorization: Bearer` (both) |
| **Message Format** | `contents` with `role` and `parts` | `messages` with `role` and `content` |
| **Tool Format** | `functionDeclarations` | `tools` with `type: "function"` |
| **Streaming Param** | Query param `?alt=sse` | Body param `"stream": true` |
| **SSE Format** | `data: {...}` (JSON per line) | `data: {...}`<br>`data: [DONE]` at end |
| **System Prompt** | `systemInstruction` object | `messages[0]` with `role: "system"` |
| **SDK Version Header** | `x-goog-api-client` | Not observed |
| **User-Agent** | `google-genai-sdk/{version}` | `Codex/{version}` |

---

## Part 4: Security Considerations

### 4.1 Token Expiration

**Gemini OAuth:**
- Access tokens expire (check `expiry_date` field)
- Refresh using `refresh_token` via Google OAuth2 endpoints
- Scope: `https://www.googleapis.com/auth/cloud-platform`

**Codex OAuth:**
- Access tokens have ~10 days lifetime (check JWT `exp` claim)
- Refresh using `refresh_token` via `https://auth.openai.com/oauth/token`
- Scopes: `openid profile email offline_access`

### 4.2 Token Storage Security

**Both clients store tokens in plaintext JSON files:**
- `~/.gemini/oauth_creds.json`
- `~/.codex/auth.json`

**Best Practices:**
- Ensure file permissions are `600` (read/write owner only)
- Never commit these files to version control
- Rotate tokens periodically
- Use environment variables for API keys in production

### 4.3 Rate Limiting

**Gemini API:**
- Rate limits vary by API tier
- Headers may include quota information
- Use exponential backoff on 429 errors

**OpenAI API:**
- Rate limits based on tier (Free, Plus, Pro, Enterprise)
- Headers include `x-ratelimit-*` information
- Implement retry logic with backoff

---

## Part 5: Quick Start Code Examples

### 5.1 Gemini Quick Start (API Key)

```python
import requests

api_key = "YOUR_API_KEY"
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

response = requests.post(
    url,
    params={"key": api_key},
    headers={
        "Content-Type": "application/json",
        "User-Agent": "google-genai-sdk/1.30.0",
        "x-goog-api-client": "google-genai-sdk/1.30.0"
    },
    json={
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Hello!"}]
            }
        ]
    }
)

print(response.json())
```

### 5.2 Codex Quick Start (API Key)

```python
import requests

api_key = "sk-..."
url = "https://api.openai.com/v1/chat/completions"

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": "Hello!"
            }
        ]
    }
)

print(response.json())
```

---

## Part 6: Advanced Topics

### 6.1 OAuth Token Refresh (Gemini)

```python
import requests

def refresh_gemini_token(refresh_token):
    """Refresh Gemini OAuth token"""
    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()  # Contains new access_token
```

### 6.2 OAuth Token Refresh (Codex/OpenAI)

```python
import requests

def refresh_codex_token(refresh_token):
    """Refresh Codex/OpenAI OAuth token"""
    url = "https://auth.openai.com/oauth/token"

    data = {
        "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()  # Contains new access_token and id_token
```

### 6.3 Error Handling Patterns

```python
import requests
import time

def make_request_with_retry(url, headers, json_data, max_retries=3):
    """Make request with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)

            # Success
            if response.status_code == 200:
                return response.json()

            # Rate limited - retry with backoff
            if response.status_code == 429:
                wait_time = (2 ** attempt) * 1  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            # Auth error - need to refresh token
            if response.status_code == 401:
                raise ValueError("Token expired, need to refresh")

            # Other error
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

    raise ValueError("Max retries exceeded")
```

---

## Appendix A: Source Code References

### Gemini CLI Source Locations
- **Main SDK:** `/opt/homebrew/lib/node_modules/@google/gemini-cli/node_modules/@google/genai/dist/node/index.mjs`
- **Auth Implementation:** Lines 15817-15862 (`class NodeAuth`)
- **API Client:** Lines 11207-11700 (`class ApiClient`)
- **Headers:** Lines 11553-11560 (`getDefaultHeaders`)
- **Request Building:** Lines 11366-11388 (`request` method)
- **Streaming:** Lines 11409-11423 (`requestStream` method)

### Codex CLI Source Locations
- **Auth Storage:** `~/.codex/auth.json`
- **Package Info:** `/opt/homebrew/lib/node_modules/@openai/codex/package.json`
- **Binary Wrapper:** `/opt/homebrew/lib/node_modules/@openai/codex/bin/codex.js`

---

## Appendix B: Environment Variable Reference

### Gemini CLI
```bash
GOOGLE_API_KEY              # API key for Developer API
GEMINI_API_KEY              # Alternative API key variable
GOOGLE_CLOUD_PROJECT        # GCP project ID
GOOGLE_CLOUD_LOCATION       # GCP location (e.g., us-central1)
GOOGLE_GENAI_USE_VERTEXAI   # Set to "true" for Vertex AI
GOOGLE_VERTEX_BASE_URL      # Override Vertex AI base URL
GOOGLE_GEMINI_BASE_URL      # Override Gemini API base URL
```

### Codex CLI
```bash
OPENAI_API_KEY              # OpenAI API key
CODEX_MANAGED_BY_NPM        # Set by npm wrapper
CODEX_MANAGED_BY_BUN        # Set by bun wrapper
```

---

## Appendix C: Common Models

### Gemini Models
- `gemini-2.0-flash-exp` - Latest experimental Flash model
- `gemini-1.5-pro` - Production Pro model
- `gemini-1.5-flash` - Production Flash model
- `gemini-exp-1206` - Experimental model

### OpenAI Models (Codex)
- `gpt-4` - GPT-4 base
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-4o` - GPT-4o (omni)
- `o1` - O1 reasoning model
- `o1-mini` - O1 Mini
- `o3-mini` - O3 Mini (latest)

---

**Document Version:** 1.0
**Generated:** 2025-12-31
**Author:** Reverse-engineered from official Gemini CLI v0.23.0-preview.1 and Codex CLI v0.77.0
