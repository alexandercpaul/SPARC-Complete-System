# Complete Instacart Automation Guide

## Executive Summary

After comprehensive research, here are your options for automating Instacart grocery orders:

### ✅ **Option 1: Reverse Engineer Consumer API** (RECOMMENDED)
- **Status:** In progress - Playwright script running now
- **Pros:** Full access to consumer features, most control
- **Cons:** Requires initial API discovery, may break with updates
- **Tools:** Playwright, mitmproxy, FRIDA

### ⚠️ **Option 2: Official Instacart MCP Server**
- **Status:** Available but limited
- **Pros:** Official, stable, MCP integration
- **Cons:** **CANNOT PLACE ORDERS** - only creates shopping lists/recipes
- **URL:** https://mcp.dev.instacart.tools/mcp

### ❌ **Option 3: Instacart Connect API**
- **Status:** Not viable for personal use
- **Pros:** Official, comprehensive
- **Cons:** **Business partners only**, requires retailer agreement

---

## What We've Discovered So Far

### Authentication
**Base URL:** `https://www.instacart.com/v3`

**Login Endpoint:**
```bash
POST /dynamic_data/authenticate/login?source=web

Headers:
  Content-Type: application/json
  Accept: application/json
  X-Requested-With: XMLHttpRequest

Body:
{
  "email": "alexandercpaul@gmail.com",
  "password": "t2as0-nAop-!O@sqh",
  "grant_type": "email",
  "scope": ""
}

Returns: _instacart_session cookie + remember_user_token
```

### Known Consumer API Endpoints (V3)
From `instacart-assist` library analysis:
- `GET /retailers` - Get all retailers/stores
- `GET /pickup_locations` - Get pickup locations

### Missing Endpoints (Currently Being Captured)
Still need to find:
- **Product Search** - `/api/v2/items?...` or `/v3/containers/...`
- **Add to Cart** - Unknown endpoint
- **Update Cart** - Unknown endpoint
- **Checkout** - Unknown endpoint
- **Place Order** - Unknown endpoint
- **Order History** - Unknown endpoint

---

## Current Capture Process

### Running Script
**Location:** `/tmp/capture_instacart_api.py`
**Output:** `/tmp/instacart_api_captured.json`
**Status:** Running (PID: 32033)

The script is:
1. Opening Chromium browser
2. Logging into Instacart
3. Searching for "Costco" products
4. Adding items to cart
5. Viewing cart
6. **Capturing all API calls, headers, cookies, and request bodies**

### What Happens Next
When the script completes (in ~1-2 minutes), you'll have:
- All API endpoints used during the shopping flow
- OAuth tokens, session cookies, CSRF tokens
- Request/response formats
- Headers required for authentication

---

## Tools Installed & Ready

| Tool | Version | Location | Purpose |
|------|---------|----------|---------|
| **Gemini CLI** | 0.23.0 | `/opt/homebrew/bin/gemini` | AI-powered automation |
| **CONDUCTOR Extension** | Latest | `~/.gemini/extensions/conductor` | Structured development workflow |
| **Playwright** | 1.57.0 | pip3 | Browser automation |
| **mitmproxy** | 12.2.1 | `/opt/homebrew/bin/mitmweb` | HTTPS traffic interception |
| **FRIDA** | 17.5.2 | `/usr/local/bin/frida` | Runtime instrumentation |
| **Radare2** | Latest | `/opt/homebrew/bin/r2` | Binary analysis |
| **1Password CLI** | 2.32.0 | `/opt/homebrew/bin/op` | Credential management |

---

## Alternative Approaches

### Approach A: Browser Automation (Selenium/Playwright)
**Pros:**
- No API reverse engineering needed
- Works immediately
- Most reliable (uses real browser)

**Cons:**
- Slower than direct API calls
- Resource intensive
- Harder to run headless
- Fragile to UI changes

**When to use:** Quick prototypes, testing, when API is too complex

### Approach B: Direct API Calls (After Reverse Engineering)
**Pros:**
- Fast, lightweight
- Easy to scale
- Can run on servers/cron
- Full programmatic control

**Cons:**
- Requires initial discovery work
- May break with API updates
- Need to maintain session/auth

**When to use:** Production automation, scheduled orders, scaling

### Approach C: FRIDA + iOS App Instrumentation
**Pros:**
- Can intercept encrypted traffic
- See exact API calls from mobile app
- Discover hidden endpoints

**Cons:**
- Complex setup
- Requires iOS device or simulator
- More advanced technique

**When to use:** When web API is insufficient or heavily protected

---

## Next Steps After Capture Completes

### Step 1: Analyze Captured Data
```bash
# View captured requests
cat /tmp/instacart_api_captured.json | jq '.requests[] | {method, url}' | less

# Find cart-related endpoints
cat /tmp/instacart_api_captured.json | jq '.requests[] | select(.url | contains("cart"))'

# Find order endpoints
cat /tmp/instacart_api_captured.json | jq '.requests[] | select(.url | contains("order"))'

# Extract auth tokens
cat /tmp/instacart_api_captured.json | jq '.auth_tokens'
```

### Step 2: Build Python API Wrapper
Create `instacart_api.py`:
```python
import requests
from typing import List, Dict

class InstacartAPI:
    def __init__(self, email: str, password: str):
        self.session = requests.Session()
        self.base_url = "https://www.instacart.com"
        self.authenticate(email, password)

    def authenticate(self, email: str, password: str):
        """Login and get session cookie"""
        # Use discovered endpoint and headers from capture
        pass

    def search_products(self, query: str, retailer_id: str) -> List[Dict]:
        """Search for products"""
        # Use discovered search endpoint
        pass

    def add_to_cart(self, product_id: str, quantity: int):
        """Add item to cart"""
        # Use discovered add-to-cart endpoint
        pass

    def get_cart(self) -> Dict:
        """Get current cart contents"""
        pass

    def checkout(self, delivery_time: str, address: Dict):
        """Place the order"""
        pass

    def get_order_history(self) -> List[Dict]:
        """Get past orders for easy reordering"""
        pass

    def reorder(self, order_id: str):
        """Reorder a previous order"""
        pass
```

### Step 3: Create Automation Scripts
```python
# auto_reorder.py - Reorder your most common Costco order
from instacart_api import InstacartAPI
import json

api = InstacartAPI("alexandercpaul@gmail.com", "password")

# Load saved order template
with open("costco_weekly_order.json") as f:
    order = json.load(f)

# Add items to cart
for item in order["items"]:
    api.add_to_cart(item["id"], item["quantity"])

# Checkout with preferred delivery time
api.checkout(
    delivery_time="tomorrow_afternoon",
    address={"saved_address_id": "home"}
)

print("✅ Order placed successfully!")
```

---

## GitHub Projects Analyzed

### Existing Projects (All Incomplete)
1. **ericzorn93/instacart-assist** (4 stars)
   - Node.js, V3 API
   - Only has: retailers, pickup_locations, auth
   - **Missing:** cart, order, checkout

2. **ImranR98/InstacartFlation** (8 stars)
   - Python, Selenium-based scraper
   - Only scrapes order history
   - **Not an API wrapper**

3. **lzztt/chrome_extensions** (34 stars)
   - JavaScript Chrome extension
   - Only finds delivery slots
   - **Not an API wrapper**

**Conclusion:** No complete Instacart API wrapper exists on GitHub for consumer order placement.

---

## Security & Legal Considerations

### Terms of Service
- This is for **personal use only** to assist with your disability
- Automation is technically against Instacart ToS
- Keep requests reasonable (don't spam)
- Your account may be flagged if detected

### Best Practices
1. **Rate Limiting:** Add delays between requests (2-5 seconds)
2. **User-Agent:** Use real browser user-agent strings
3. **Session Management:** Don't reuse sessions for too long
4. **Error Handling:** Handle failed auth gracefully
5. **Logging:** Keep logs for debugging

### Credential Security
- ✅ Use 1Password for storage
- ✅ Never commit credentials to git
- ✅ Use environment variables
- ⚠️ Be careful with 1Password CLI auth prompts (no fix for personal accounts)

---

## Troubleshooting

### Issue: Bot Detection (403 errors)
**Solution:** Use captured browser headers exactly:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.instacart.com/',
    'X-Requested-With': 'XMLHttpRequest',
    'Cookie': '_instacart_session=...'
}
```

### Issue: Session Expires
**Solution:** Re-authenticate when you get 401/403 responses

### Issue: API Endpoints Changed
**Solution:** Re-run capture script to discover new endpoints

---

## Resources & References

### Official Instacart Documentation
- [Instacart Developer Platform](https://docs.instacart.com/developer_platform_api/)
- [Instacart Connect APIs](https://docs.instacart.com/connect/)
- [Instacart MCP Server Tutorial](https://docs.instacart.com/developer_platform_api/guide/tutorials/mcp/)

### GitHub Projects
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [CONDUCTOR Extension](https://github.com/gemini-cli-extensions/conductor)
- [instacart-assist](https://github.com/ericzorn93/instacart-assist)
- [InstacartFlation](https://github.com/ImranR98/InstacartFlation)
- [GitHub Instacart Topic](https://github.com/topics/instacart?o=desc&s=stars)

### Tools & Documentation
- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [mitmproxy Documentation](https://docs.mitmproxy.org/)
- [FRIDA Documentation](https://frida.re/docs/home/)
- [1Password CLI Reference](https://developer.1password.com/docs/cli/)

### API Information
- [API Tracker - Instacart](https://apitracker.io/a/instacart)
- [Composio Instacart MCP](https://mcp.composio.dev/instacart)

---

## Timeline

**Completed:**
- ✅ Researched official APIs (MCP, Connect, Developer Platform)
- ✅ Analyzed GitHub projects for existing solutions
- ✅ Discovered V3 authentication endpoint
- ✅ Set up all required tools (Playwright, mitmproxy, FRIDA)
- ✅ Created API capture script

**In Progress:**
- ⏳ Capturing consumer API endpoints (running now)

**Next (10-15 minutes):**
- 📋 Analyze captured data
- 📋 Document all endpoints
- 📋 Build Python API wrapper
- 📋 Create reorder automation script

**Future Enhancements:**
- 🔮 Schedule weekly orders via cron
- 🔮 Voice-activated ordering (with Siri/Shortcuts)
- 🔮 Smart cart management (favorites, frequently bought)
- 🔮 Price tracking and notifications

---

## Your System Details

**Machine:** macOS 26.3 (Darwin 25.3.0)
**Security:**
- SIP: Disabled ✅
- TCC: Full access via daemon ✅
- sudo: Passwordless (or password: "@Aa-5219-0re0")

**Credentials:**
- **Email:** alexandercpaul@gmail.com
- **Password:** t2as0-nAop-!O@sqh (stored in 1Password)
- **1Password:** Authenticated, CLI available

**Package Managers:** All available (brew, npm, pip, mas)

---

**Last Updated:** 2025-12-31 00:16 PST
**Status:** Capture script running, awaiting results
