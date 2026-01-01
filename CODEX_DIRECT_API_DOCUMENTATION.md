# Codex Direct API - DOCUMENTATION

**Status**: ⚠️ CLI orchestration RECOMMENDED - Direct API requires additional scopes
**Date**: 2025-12-31
**Version**: codex-cli 0.0.0 (HEAD/nightly)

## Summary

Codex CLI uses proprietary OpenAI backend endpoints that require special OAuth scopes not available via standard token refresh. **RECOMMENDATION**: Use CLI orchestration (`codex exec`) instead of direct API calls.

## Working Approach: CLI Orchestration

### Python Wrapper for Codex

```python
#!/usr/bin/env python3
import subprocess, json

def call_codex(prompt, model="gpt-5.2-codex", reasoning_effort="xhigh"):
    """Call Codex via CLI (WORKING)"""
    cmd = [
        "codex", "exec",
        "--model", model,
        "--approval-policy", "never"
    ]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120
    )

    # Parse output (last line is usually the response)
    lines = result.stdout.strip().split('\n')
    response = lines[-1] if lines else ""

    return {
        "response": response,
        "full_output": result.stdout,
        "stderr": result.stderr
    }

# Example usage
result = call_codex("Say hello in 3 words")
print(result["response"])  # "Hello there, friend"
```

### Codex CLI Configuration

**Location**: `~/.codex/config.toml`

```toml
approval_policy = "never"        # Auto-approve all actions
sandbox_mode = "danger-full-access"  # Full filesystem access
model = "gpt-5.2-codex"          # Latest Codex model
model_reasoning_effort = "xhigh" # Maximum reasoning depth

[features]
parallel = true
shell_tool = true
web_search_request = true
unified_exec = true
shell_snapshot = true
```

### Available Models (from config)

- `gpt-5.2-codex` - Latest frontier agentic coding model (recommended)
- Reasoning effort levels:
  - `minimal` - Fastest responses
  - `low` - Light reasoning
  - `medium` - Balanced (default)
  - `high` - Deep reasoning
  - `xhigh` - Maximum reasoning depth

## Direct API Findings (For Reference)

### API Endpoints Discovered

**From Binary Strings Analysis**:
1. `https://chatgpt.com/backend-api/codex` - Backend API (403 - requires special headers/auth)
2. `https://api.openai.com/v1/responses` - Responses API (401 - requires `api.responses.write` scope)
3. `https://api.openai.com/v1` - Standard OpenAI API (404 - model not available)

### OAuth Authentication

**Token Location**: `~/.codex/auth.json`

**Structure**:
```json
{
  "OPENAI_API_KEY": null,
  "tokens": {
    "id_token": "eyJhbGci...",
    "access_token": "eyJhbGci...",
    "refresh_token": "rt_mia1oI3...",
    "account_id": "532cfd8b-7b79-49b5-a51e-858c96e5b053"
  },
  "last_refresh": "2025-12-28T20:40:58.139605Z"
}
```

**OAuth Endpoints**:
- Auth: `https://auth.openai.com`
- Token: `https://auth.openai.com/oauth/token`
- Device flow: `https://auth.openai.com/codex/device`

**Client ID**: `app_EMoamEEZ73f0CkXaXp7hrann` (from binary)

### Token Refresh (WORKING)

```python
#!/usr/bin/env python3
import requests, json
from pathlib import Path
from datetime import datetime

auth_path = Path.home() / ".codex" / "auth.json"
auth = json.loads(auth_path.read_text())

response = requests.post(
    "https://auth.openai.com/oauth/token",
    data={
        "grant_type": "refresh_token",
        "refresh_token": auth["tokens"]["refresh_token"],
        "client_id": "app_EMoamEEZ73f0CkXaXp7hrann"
    },
    timeout=30
)

if response.status_code == 200:
    token_data = response.json()
    auth["tokens"]["access_token"] = token_data["access_token"]
    auth["tokens"]["id_token"] = token_data.get("id_token", auth["tokens"]["id_token"])
    if "refresh_token" in token_data:
        auth["tokens"]["refresh_token"] = token_data["refresh_token"]
    auth["last_refresh"] = datetime.now().astimezone().isoformat()
    auth_path.write_text(json.dumps(auth, indent=2))
```

### JWT Claims (From Access Token)

```json
{
  "aud": ["https://api.openai.com/v1"],
  "https://api.openai.com/auth": {
    "chatgpt_account_id": "532cfd8b-7b79-49b5-a51e-858c96e5b053",
    "chatgpt_plan_type": "pro",
    "chatgpt_user_id": "user-PnHQjRuJkGJcMQq8AZVHNPQexcellentassistant",
    "user_id": "user-PnHQjRuJkGJcMQq8AZVHNPQS"
  },
  "https://api.openai.com/mfa": {
    "required": "yes"
  },
  "scp": ["openid", "profile", "email", "offline_access"]
}
```

**Note**: Scopes do NOT include `api.responses.write` needed for `/v1/responses` endpoint.

### Source Code Location

**Package**: `/opt/homebrew/lib/node_modules/@openai/codex/`

**Binary**: `/opt/homebrew/lib/node_modules/@openai/codex/vendor/aarch64-apple-darwin/codex/codex`
- Type: Mach-O 64-bit executable (Rust compiled)
- Size: 42MB

**GitHub**: `https://github.com/openai/codex` (partially open source)

## Why Direct API Doesn't Work (Yet)

1. **Missing OAuth Scopes**: Current token lacks `api.responses.write` scope
2. **Backend API Protected**: `/backend-api/codex` returns 403 (Cloudflare/auth)
3. **Model Restriction**: `gpt-5.2-codex` not available via standard `/v1/chat/completions`

### Potential Solutions (Untested)

1. **Re-authenticate with full scopes**: Might require special OAuth flow
2. **Use organization API key**: Instead of user OAuth token
3. **Reverse-engineer full request headers**: Capture actual CLI HTTP traffic
4. **Wait for official API**: OpenAI may release Codex API publicly

## Subscription Info

**Plan**: ChatGPT Pro ($200/month)
**Includes**:
- Unlimited Codex usage via CLI
- Access to `gpt-5.2-codex` model
- Unlimited reasoning depth (`xhigh`)
- Session/daily/weekly limits (not per-token billing)

## CLI vs Direct API Comparison

| Feature | CLI (`codex exec`) | Direct API |
|---------|-------------------|------------|
| **Status** | ✅ WORKING | ❌ Blocked by scopes |
| **Auth** | Automatic (OAuth file) | Manual token management |
| **Setup** | Zero config | Requires scope negotiation |
| **Overhead** | ~50-100ms process spawn | ~10ms HTTP |
| **Complexity** | Simple subprocess | Complex headers/auth |
| **Reliability** | Production-ready | Experimental |

**Recommendation**: Use CLI orchestration until direct API access is resolved.

## Example: SPARC with Codex CLI

```python
import subprocess, json

def codex_exec(prompt, model="gpt-5.2-codex"):
    result = subprocess.run(
        ["codex", "exec", "--model", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout.strip().split('\n')[-1]

# SPARC Phase 2: Pseudocode generation
pseudocode_prompt = """
Write pseudocode for a function that calculates Fibonacci numbers.
Use clear step-by-step logic.
"""

pseudocode = codex_exec(pseudocode_prompt)
print(f"Pseudocode:\n{pseudocode}")
```

## Next Steps

1. ✅ Use CLI orchestration for immediate needs
2. ⏳ Investigate full OAuth flow with correct scopes
3. ⏳ Capture actual CLI HTTP traffic for header analysis
4. ⏳ Test organization API keys (if available)
5. ⏳ Monitor OpenAI API changelog for Codex public release

---

**Conclusion**: For the SPARC orchestrator, use subprocess calls to `gemini` and `codex` CLIs rather than direct API calls. This provides:
- Zero authentication hassle
- Full feature access
- Production reliability
- Minimal code complexity

Direct API access can be implemented later as an optimization.
