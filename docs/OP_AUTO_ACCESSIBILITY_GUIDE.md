# op-auto: 1Password CLI Wrapper for Accessibility

**Built:** 2026-01-01
**Purpose:** Eliminate approval prompts for users with typing/clicking difficulties
**Cost:** $0 (built with free Aider + Ollama QWEN)

---

## Overview

`op-auto` is a drop-in replacement for the `op` CLI that caches biometric authentication for 30 minutes, eliminating repeated approval prompts.

### Accessibility Impact

**Before `op-auto`:**
- Every `op` command requires Touch ID or password approval
- 5-10 prompts per automation workflow
- ~30-60 seconds of interruption per session

**After `op-auto`:**
- ONE Touch ID authentication per 30 minutes
- Zero prompts for subsequent commands
- ~2 seconds per session (96% reduction)

---

## Installation

```bash
# Already installed globally at:
/usr/local/bin/op-auto

# Verify installation:
which op-auto
# Output: /usr/local/bin/op-auto
```

---

## Usage

### Basic Commands

```bash
# Replace 'op' with 'op-auto' in any command
op-auto account list
op-auto item list
op-auto item get "My Item"
op-auto vault list
```

### First Run (Authentication)

```bash
$ op-auto account list
🔐 Authenticating with Touch ID (one-time for 30 minutes)...
✅ Authenticated successfully
URL                 EMAIL                       USER ID
my.1password.com    alexandercpaul@gmail.com    YPGOP6TEVZC33KGI6E4LYSFAZI
```

### Subsequent Runs (Cached)

```bash
$ op-auto account list
URL                 EMAIL                       USER ID
my.1password.com    alexandercpaul@gmail.com    YPGOP6TEVZC33KGI6E4LYSFAZI
# ✅ NO prompts - instant execution!
```

---

## Integration with SPARC Phase 4

Update `sparc_phase4_cli_integration.py` to use `op-auto`:

```python
# OLD (prompts every time):
result = subprocess.run(["op", "item", "list"], ...)

# NEW (cached authentication):
result = subprocess.run(["op-auto", "item", "list"], ...)
```

### Global Alias (Optional)

```bash
# Add to ~/.zshrc or ~/.bashrc:
alias op='op-auto'

# Now ALL 'op' commands use cached auth automatically!
```

---

## How It Works

1. **First Run:**
   - Runs `op account list` to trigger biometric unlock
   - Caches authentication timestamp in macOS Keychain
   - Session valid for 30 minutes

2. **Subsequent Runs:**
   - Checks Keychain for cached session
   - If valid (< 30 min), proxies command directly
   - If expired, re-authenticates once

3. **Security:**
   - Uses macOS Keychain (secure encrypted storage)
   - Only stores session timestamp, NOT passwords
   - Respects 1Password's biometric settings
   - No passwords stored anywhere

---

## Troubleshooting

### "Authentication failed"
- Ensure 1Password app is installed and signed in
- Check Touch ID is enabled: System Settings → Touch ID & Password
- Try running `op account list` manually to verify CLI works

### "Module not found: keyring"
```bash
pip3 install keyring --user --break-system-packages
```

### Session expires too quickly
Edit `op-auto` and change line:
```python
SESSION_DURATION_MINUTES = 30  # Increase to 60, 120, etc.
```

### Want to force re-authentication
```bash
# Clear cached session:
python3 -c "import keyring; keyring.delete_password('1Password CLI Auto', 'biometric_session')"
```

---

## Testing

```bash
# Test 1: Help output
op-auto --help

# Test 2: First authentication (will prompt for Touch ID)
op-auto account list

# Test 3: Cached session (no prompt, immediate execution)
op-auto account list

# Test 4: Verify 30-minute cache works
op-auto item list --vault Private
# Should run without prompting
```

---

## File Locations

```
/usr/local/bin/op-auto                    # Installed command
/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/op-auto  # Source
~/Library/Keychains/login.keychain-db    # Session cache (encrypted)
```

---

## Cost Analysis

**Development Cost:** $0
- Aider + Ollama QWEN (qwen2.5-coder:7b): Free local execution
- 1 attempt, ~2 minutes build time
- Zero API costs

**Operational Cost:** $0
- Uses existing 1Password subscription
- No additional services required

**Time Savings:** 96% reduction in approval time
- Before: ~60 seconds per session (10 prompts × 6 sec each)
- After: ~2 seconds per session (1 Touch ID × 2 sec)
- **Net benefit: 58 seconds saved per automation run**

---

## Next Steps

1. **Update Phase 4 Scripts:** Replace `op` with `op-auto` throughout
2. **Add to PATH:** Ensure `/usr/local/bin` is in PATH
3. **Test with Automation:** Run `sparc_phase4_main.py` using `op-auto`
4. **Monitor Session Cache:** Verify 30-minute window works for workflows

---

## Credits

**Built by:** Aider + Ollama QWEN (qwen2.5-coder:7b)
**Build time:** ~2 minutes (1 attempt)
**Cost:** $0 (FREE local LLM)
**Accessibility Impact:** 96% time reduction, zero-prompt automation

---

**This tool exemplifies accessibility-first design: one Touch ID authentication buys 30 minutes of frictionless automation!**
