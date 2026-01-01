# Instacart Automation Guide

## Summary of Findings

### Option Analysis

1. **Official Instacart Developer Platform API** ❌
   - Only creates shopping lists/recipes
   - Cannot place orders
   - Requires business partnership

2. **Instacart Connect API** ❌
   - Can place orders
   - ONLY for retailer/business partners
   - Not for personal use

3. **Reverse Engineered Consumer API** ✅ **RECOMMENDED**
   - Access to full consumer functionality
   - Can place orders programmatically
   - Already partially documented

## Discovered API Information

### Base API Details
- **Base URL:** `https://www.instacart.com/v3`
- **Authentication:** Email/Password → Session Cookie
- **Login Endpoint:** `POST /dynamic_data/authenticate/login?source=web`

### Authentication Flow
```python
# Login Request
POST https://www.instacart.com/v3/dynamic_data/authenticate/login?source=web
Headers:
  Content-Type: application/json
  Accept: application/json
  X-Requested-With: XMLHttpRequest

Body:
{
  "email": "your@email.com",
  "password": "yourpassword",
  "grant_type": "email",
  "scope": ""
}

# Returns: _instacart_session cookie
```

### Known Endpoints
- `GET /retailers` - Get all retailers
- `GET /pickup_locations` - Get pickup locations
- **NEED TO FIND:** Order placement, cart management, checkout endpoints

### Current Issue
Instacart has bot protection (`x-instacart-edge-limiter: true`) that blocks direct API calls. We need to capture real browser headers/cookies.

## Next Steps: Capture Real API Traffic

### Step 1: Start Mitmproxy
```bash
# Terminal 1: Start mitmproxy with capture script
mitmweb -s /tmp/instacart_intercept.py --listen-port 8080

# This will open a web interface at http://127.0.0.1:8081
```

### Step 2: Configure Browser Proxy
1. Open Safari/Chrome browser settings
2. Set HTTP/HTTPS Proxy to: `127.0.0.1:8080`
3. Install mitmproxy CA certificate:
   - Visit: http://mitm.it
   - Download and install the certificate for your browser
   - On macOS: Trust the certificate in Keychain Access

### Step 3: Capture Instacart Traffic
1. With proxy configured, visit: https://www.instacart.com
2. **Login** with your credentials
3. **Browse** products (try searching for Costco items)
4. **Add items** to cart
5. **Start checkout** (don't complete the order unless you want to!)
6. Press `Ctrl+C` in the mitmproxy terminal when done

### Step 4: Analyze Captured Data
```bash
# View captured API calls
cat /tmp/instacart_captured_api.json | jq '.[] | {method, url}'

# Find order/cart endpoints
cat /tmp/instacart_captured_api.json | jq '.[] | select(.url | contains("cart") or contains("order"))'
```

## Alternative: Browser DevTools Method

If mitmproxy is too complex:

1. Open Instacart in browser
2. Press `F12` to open DevTools
3. Go to **Network** tab
4. Filter by **Fetch/XHR**
5. Perform actions (login, add to cart, checkout)
6. Right-click requests → **Copy as cURL** or **Copy as fetch**
7. Document the endpoints, headers, and body

## Building the Automation

Once we have the endpoints, we'll create a Python wrapper:

```python
# instacart_automation.py structure
class InstacartAutomation:
    def __init__(self, email, password):
        self.session = requests.Session()
        self.authenticate(email, password)

    def authenticate(self, email, password):
        # Login and get session cookie
        pass

    def search_products(self, query, retailer_id):
        # Search for products
        pass

    def add_to_cart(self, product_id, quantity):
        # Add item to cart
        pass

    def checkout(self, delivery_time, address):
        # Place the order
        pass

    def get_past_orders(self):
        # Get order history for reordering
        pass
```

## Tools Available
- **FRIDA:** `/usr/local/bin/frida` (v17.5.2) - For iOS app instrumentation
- **Radare2:** `/opt/homebrew/bin/r2` - For binary analysis
- **mitmproxy:** `/opt/homebrew/bin/mitmweb` (v12.2.1) - For traffic interception
- **1Password CLI:** For secure credential management

## Your Credentials
- **Email:** alexandercpaul@gmail.com
- **Password:** Available in 1Password (`op://Personal/Instacart/password`)

## Sources & References

### Official Documentation
- [Instacart Developer Platform](https://docs.instacart.com/developer_platform_api/)
- [Instacart Connect APIs](https://docs.instacart.com/connect/)
- [Instacart MCP Server](https://docs.instacart.com/developer_platform_api/guide/tutorials/mcp/)

### GitHub Projects
- [ericzorn93/instacart-assist](https://github.com/ericzorn93/instacart-assist) - 4 stars, Node.js V3 API wrapper
- [ImranR98/InstacartFlation](https://github.com/ImranR98/InstacartFlation) - 8 stars, Python scraper
- [lzztt/chrome_extensions](https://github.com/lzztt/chrome_extensions) - 34 stars, Delivery slot finder
- [Instacart Topics on GitHub](https://github.com/topics/instacart?o=desc&s=stars)

### MCP Integration
- **Composio Instacart MCP**: https://mcp.composio.dev/instacart
- **Apify Instacart Scraper MCP**: https://apify.com/ecomscrape/instacart-product-search-scraper/api/mcp

## Security & Ethics Note
This automation is for personal use to assist with your disability-related needs. Be mindful of:
- Instacart's Terms of Service
- Rate limiting (don't spam requests)
- Keep credentials secure
- Only automate your own account

---

**Status:** Ready to capture API traffic with mitmproxy
**Next Action:** Start mitmproxy and capture browser traffic while using Instacart
