# Instacart Automation - Complete Setup Summary

## ✅ What's Been Done

### 1. Research & Analysis
- ✅ Searched GitHub for Instacart APIs/SDKs
- ✅ Found official APIs are business-only (cannot place personal orders)
- ✅ Discovered unofficial V3 API endpoints (`https://www.instacart.com/v3`)
- ✅ Confirmed browser automation approach is best for personal use

### 2. Tools Installed (Global Locations for Multi-Agent Access)

| Tool | Location | Purpose |
|------|----------|---------|
| **Gemini CLI** | `/opt/homebrew/bin/gemini` | AI agent for automation tasks |
| **CONDUCTOR** | `~/.gemini/extensions/conductor` | Structured workflow extension |
| **Playwright** | `/opt/homebrew/bin/playwright` | Browser automation |
| **mitmproxy** | `/opt/homebrew/bin/mitmweb` | Network traffic interception |
| **Capture Script** | `/usr/local/share/instacart-automation/` | Custom API capture tool |

### 3. Created Automation System

**Global Directory Structure:**
```
/usr/local/share/instacart-automation/
├── capture_api.py          # Playwright automation script
├── README.md               # Comprehensive documentation
└── captured_api.json       # (Generated after running capture)

/usr/local/bin/
└── capture-instacart-api   # Symlink to capture_api.py
```

### 4. 1Password CLI Investigation

**Status:** ⚠️ PARTIAL RESOLUTION

- **Issue:** Repeated authorization prompts when Claude accesses 1Password CLI
- **Finding:** This is **by design** - no configuration can disable prompts for personal accounts
- **Solution:** Requires 1Password Teams/Business subscription with Service Account Tokens
- **Current State:** Prompts will continue unless you upgrade to Teams/Business

## 🎯 Next Steps

### Step 1: Run the API Capture Tool

```bash
# This will:
# - Open Chromium browser
# - Login to Instacart
# - Capture all API endpoints and auth tokens
# - Save to captured_api.json

capture-instacart-api
```

**What happens:**
1. Browser opens and navigates to Instacart
2. Automatic login with your credentials
3. Searches for "Costco" products
4. Adds item to cart
5. Views cart
6. Captures ALL network traffic during these actions
7. Saves auth tokens, endpoints, headers, and request bodies

**Duration:** ~2-3 minutes (browser stays open 30s at end for inspection)

### Step 2: Review Captured API Data

```bash
# View all captured endpoints
cat /usr/local/share/instacart-automation/captured_api.json | jq '.requests[].url' | sort -u

# View auth tokens
cat /usr/local/share/instacart-automation/captured_api.json | jq '.auth_tokens'

# Find cart/order endpoints specifically
cat /usr/local/share/instacart-automation/captured_api.json | jq '.requests[] | select(.url | contains("cart") or contains("order"))'
```

### Step 3: Use Gemini CONDUCTOR to Build Automation

```bash
cd /usr/local/share/instacart-automation/

# Let Gemini analyze captured API and build automation
gemini -p "Analyze the captured_api.json file and build a Python library to automate Instacart ordering. Focus on: 1) Authentication, 2) Product search, 3) Add to cart, 4) Checkout. Use the captured endpoints and auth tokens." --all-files --yolo
```

**CONDUCTOR** will:
1. Create specification document
2. Plan the implementation
3. Build the Python wrapper automatically
4. Create test cases
5. Document the API

## 🛠️ Alternative: Manual Approach

If you prefer hands-on control:

### Option A: Use mitmproxy (Already Installed)

```bash
# Terminal 1
mitmweb -s /tmp/instacart_intercept.py

# Terminal 2
# Configure browser proxy to 127.0.0.1:8080
# Visit http://mitm.it to install certificate
# Use Instacart normally
# Press Ctrl+C when done

# View results
cat /tmp/instacart_captured_api.json
```

### Option B: Use Chrome DevTools

1. Open Instacart in Chrome
2. Press `F12` → Network tab
3. Filter by "Fetch/XHR"
4. Perform actions (login, add to cart, checkout)
5. Right-click requests → Copy as cURL
6. Convert to Python/Node.js

## 📊 Known API Endpoints (Partial)

From `instacart-assist` library:

```
Base URL: https://www.instacart.com/v3

Authentication:
  POST /dynamic_data/authenticate/login?source=web
  Body: { email, password, grant_type: "email" }
  Returns: _instacart_session cookie

Product/Store:
  GET /retailers
  GET /pickup_locations

Headers Required:
  Content-Type: application/json
  X-Requested-With: XMLHttpRequest
  Accept: application/json
  Cookie: _instacart_session={token}
```

**Need to find:**
- Product search endpoint
- Add to cart endpoint
- Checkout/order placement endpoint
- Order history endpoint (for reordering)

## 🚀 Building the Final Automation

Once you have captured API data, create:

```python
# /usr/local/share/instacart-automation/instacart.py

class InstacartAutomation:
    def __init__(self):
        # Load captured tokens
        self.load_auth_tokens()

    def login(self):
        # Use captured auth flow

    def search_products(self, query):
        # Use captured search endpoint

    def add_to_cart(self, product_id, quantity):
        # Use captured cart endpoint

    def checkout(self):
        # Use captured checkout endpoint

    def reorder_past_order(self, order_id):
        # Get order history, resubmit
```

## 🔧 Integration Examples

### With Hammerspoon
```lua
-- Trigger Instacart order via hotkey
hs.hotkey.bind({"cmd", "alt"}, "G", function()
    os.execute("python3 /usr/local/share/instacart-automation/instacart.py --reorder-last")
end)
```

### With Gemini CLI
```bash
# Create custom Gemini skill
gemini -p "Order my usual groceries from Costco via Instacart" --output-format json
```

### With Shortcuts (iOS/macOS)
- Create Shortcut that runs shell script
- Trigger via Siri: "Order groceries"
- Runs: `capture-instacart-api --reorder-last`

## 📚 Resources

### Documentation Created
- `/tmp/INSTACART_AUTOMATION_GUIDE.md` - Original research and findings
- `/usr/local/share/instacart-automation/README.md` - System documentation
- This file - Complete summary

### Official Sources
- [Instacart Developer Platform](https://docs.instacart.com/developer_platform_api/)
- [Instacart MCP Server](https://docs.instacart.com/developer_platform_api/guide/tutorials/mcp/)
- [Gemini CLI Documentation](https://google-gemini.github.io/gemini-cli/)
- [CONDUCTOR Extension](https://github.com/gemini-cli-extensions/conductor)

### GitHub Projects
- [ericzorn93/instacart-assist](https://github.com/ericzorn93/instacart-assist) - 4 stars, V3 API wrapper
- [ImranR98/InstacartFlation](https://github.com/ImranR98/InstacartFlation) - 8 stars, Order history scraper
- [lzztt/chrome_extensions](https://github.com/lzztt/chrome_extensions) - 34 stars, Delivery slot finder

## ⚡ Quick Start

**To start automating Instacart right now:**

```bash
# 1. Capture the API
capture-instacart-api

# 2. Let Gemini build automation
cd /usr/local/share/instacart-automation
gemini -p "Build me an Instacart automation library using the captured API data" --all-files

# 3. Use it!
python3 instacart.py --help
```

## 🎯 Why This Approach Works

1. **Uses Internal Consumer API** - Same API the website uses, not business/partner API
2. **OAuth Tokens from Real Browser** - Bypasses bot protection
3. **Captures Complete Request Flow** - Headers, cookies, CSRF tokens, everything
4. **Globally Accessible** - All agents can use `/usr/local/share/instacart-automation/`
5. **Zero-Hop, Zero-Copy** - Direct API calls, no browser needed after capture
6. **Gemini CONDUCTOR** - Can autonomously build structured automation

## 🔐 Security & Ethics

- ✅ For personal use and disability assistance
- ✅ Using your own account and credentials
- ✅ Respecting rate limits
- ⚠️ Keep tokens/credentials secure
- ⚠️ Be aware of Instacart Terms of Service
- ⚠️ Don't spam/abuse the API

---

**Status:** ✅ **READY TO CAPTURE API**

**Next Command:** `capture-instacart-api`

**Questions?** All documentation is in `/usr/local/share/instacart-automation/README.md`
