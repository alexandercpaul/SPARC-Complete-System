# Instacart API Reverse Engineering - Findings

## Executive Summary

Successfully captured Instacart's consumer API structure through automated browser interception. **Instacart uses GraphQL** with persisted queries.

---

## GraphQL API Structure

### Base Endpoint
```
https://www.instacart.com/graphql
```

### Authentication Method
- **Session Cookie:** `_instacart_session`
- **Login Endpoint:** `/v3/dynamic_data/authenticate/login?source=web`

### GraphQL Query Pattern
Instacart uses **persisted queries** with SHA256 hashes:

```
GET /graphql?operationName=<OperationName>&variables=<JSON>&extensions={"persistedQuery":{"version":1,"sha256Hash":"<hash>"}}
```

---

## Discovered GraphQL Operations

### User & Authentication
| Operation | Purpose | Type |
|-----------|---------|------|
| `CurrentUserFields` | Get current user data | Query |
| `Geolocation` | Get user location | Query |
| `GeolocationFromIp` | Get location from IP | Query |
| `AuthenticateLayout` | Login UI data | Query |

**Hash:** `d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952`

### Product Search
| Operation | Purpose | Type |
|-----------|---------|------|
| `CrossRetailerSearchAutosuggestions` | Search autocomplete | Query |
| `CrossRetailerPopularSuggestions` | Popular searches | Query |
| `AutosuggestViewLayout` | Search UI layout | Query |

**Example - Search Autosuggestions:**
```
operationName=CrossRetailerSearchAutosuggestions
variables={
  "query": "",
  "limit": 10,
  "retailerIds": ["109","5","90",...],
  "zoneId": "85",
  "autosuggestionSessionId": "47f7ced5-8cfc-496e-b811-fd5b777b6c9a"
}
sha256Hash: 89ec32ea85c9b7ea89f7b4a071a5dd4ec1335831ff67035a0f92376725c306a3
```

### Store/Retailer Information
| Operation | Purpose | Type |
|-----------|---------|------|
| `HomepageShopCollection` | Available stores | Query |
| `LpsContextualizedShopsGroup` | Grouped store data | Query |
| `GetAccurateVisitorRetailerEtas` | Delivery ETAs | Query |
| `GetAccurateVisitorRetailerPickupEtas` | Pickup ETAs | Query |
| `PickupEtas` | Pickup time estimates | Query |
| `VisitorHomepageShopTags` | Store tags/categories | Query |

**Example - Homepage Shops:**
```
operationName=HomepageShopCollection
variables={
  "postalCode": "07010",
  "coordinates": {
    "latitude": 40.8177,
    "longitude": -73.9771
  }
}
sha256Hash: a1673521c0b83b8e73bda30552c5ae950fa24a4d31b599ec15c944d7fa3f45eb
```

### Still Need to Find (Requires Login)
- ❓ Add to Cart
- ❓ Update Cart Quantities
- ❓ Get Cart
- ❓ Checkout/Place Order
- ❓ Get Order History
- ❓ Get Product Details

---

## Other Endpoints

### Analytics & Tracking
```
POST https://www.instacart.com/ahoy/visits
POST https://mgs.instacart.com/v2/b
```

### Image CDN
```
https://www.instacart.com/image-server/<dimensions>/<path>
```

---

## Next Steps to Complete Capture

### Option 1: Fix Playwright Script (Quick)
The script timed out waiting for login. Modify to:
1. Increase timeout for `networkidle`
2. Or skip `networkidle` and use `domcontentloaded`
3. Add manual wait time for user to login

**Updated script location:** `/tmp/capture_instacart_api_v2.py`

### Option 2: Browser DevTools Manual Capture (Fastest)
1. Open Chrome DevTools (F12)
2. Go to **Network** tab
3. Filter by **Fetch/XHR**
4. Login to Instacart
5. Search for "Costco"
6. Add items to cart
7. Go to checkout
8. Right-click on GraphQL calls → **Copy as cURL** or **Copy as fetch**

Look for operations containing:
- `addItemToCart` or `addToCart`
- `updateCartItem` or `updateQuantity`
- `getCart` or `viewCart`
- `checkout` or `placeOrder`

### Option 3: GraphQL Schema Introspection
Try introspection query (may be disabled):
```graphql
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
      fields {
        name
        args {
          name
          type { name kind ofType { name kind } }
        }
      }
    }
  }
}
```

Send to: `https://www.instacart.com/graphql`

---

## How to Use GraphQL API

### 1. Authentication
```bash
curl -X POST 'https://www.instacart.com/v3/dynamic_data/authenticate/login?source=web' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'X-Requested-With: XMLHttpRequest' \
  --data-raw '{
    "email": "alexandercpaul@gmail.com",
    "password": "t2as0-nAop-!O@sqh",
    "grant_type": "email",
    "scope": ""
  }' \
  -c cookies.txt
```

Extract `_instacart_session` cookie from `cookies.txt`

### 2. Query GraphQL
```bash
SESSION_COOKIE="_instacart_session=<your_session_cookie>"

curl 'https://www.instacart.com/graphql?operationName=CurrentUserFields&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952%22%7D%7D' \
  -H "Cookie: $SESSION_COOKIE" \
  -H 'Accept: application/json'
```

### 3. Python Example
```python
import requests
import json
from urllib.parse import urlencode

# After authentication
session = requests.Session()
session.cookies.set("_instacart_session", "your_session_cookie_here")

# GraphQL query
operation = "CurrentUserFields"
variables = {}
extensions = {
    "persistedQuery": {
        "version": 1,
        "sha256Hash": "d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952"
    }
}

params = {
    "operationName": operation,
    "variables": json.dumps(variables),
    "extensions": json.dumps(extensions)
}

response = session.get(
    f"https://www.instacart.com/graphql?{urlencode(params)}",
    headers={
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
)

print(response.json())
```

---

## Persisted Query System

Instacart uses **persisted queries** which means:
- Query text is not sent in requests
- Only the SHA256 hash is sent
- Server looks up the query by hash
- More efficient, harder to reverse engineer

### To Find Missing Operations:
1. Search browser DevTools for operation names
2. Copy SHA256 hash from request
3. Store hash → operation mapping

### Known Hash Mappings:
```python
GRAPHQL_OPERATIONS = {
    # User
    "d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952": "CurrentUserFields",

    # Search
    "89ec32ea85c9b7ea89f7b4a071a5dd4ec1335831ff67035a0f92376725c306a3": "CrossRetailerSearchAutosuggestions",
    "74373b8dd331dc423d46f34f8a8a2fee2343905a94c04a8e5402561e27508778": "CrossRetailerPopularSuggestions",
    "4b32aee85cd15b407bef20ace522529ce71d1bd32b9b3541e86926299e0a3b57": "AutosuggestViewLayout",

    # Stores
    "a1673521c0b83b8e73bda30552c5ae950fa24a4d31b599ec15c944d7fa3f45eb": "HomepageShopCollection",
    "6c4ae0153aa59639cd6eabb086f5055966e2b0a5395c8d615555cb92e0857e32": "LpsContextualizedShopsGroup",
    "69273595be20f766a8c9051bbf46fa6392eb7692e00f9c05519831b606a10d88": "GetAccurateVisitorRetailerEtas",
    "df43db9cd849b63b2c9dc7f1d7b397196484e94d3fea2ef5c438802ae263906f": "GetAccurateVisitorRetailerPickupEtas",
    "fb21135380e4d386826c6c6022471083275b120cfc8d56533c26b1efa07912e9": "PickupEtas",
    "c0d04c49b095fe875fece036f318b6b1e781ed1a6fd598bd7b9813889b66ea20": "VisitorHomepageShopTags",

    # Geolocation
    "bf8acabc0060950a92f3e0e82eea380ec755518c67949016470ef5d98b740bfb": "Geolocation",
    "c6172e49ede2ba281e14f794bb9ea7c27bb28fb68af985c975e20ee1b501ec09": "GeolocationFromIp",

    # Auth
    "fc6f362a66992c89fcd4842c9adfba059951e979c9b19c23d12f1fa5b9c66f37": "AuthenticateLayout",

    # Other
    "bb6d108f50f961bad24792b0f5bf8506d5f7b88942d2abd4fa644eed2607356b": "LandingAppTrackingProperties",
    "9ba2208eb3fc4cccd2eed3fc544f2aeb61be25e72085abfd5d2e6831ded95a10": "LoxCombineAddressStepsVariant",
    "a0f82382d1d01631f3a0744ae0b34c0790154550e11b8c5b08f194c46fb0c02f": "LandingFeatureVariant",
}
```

---

## Required Headers

```python
HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instacart.com/",
    "Cookie": "_instacart_session=<your_session_cookie>"
}
```

---

## Building the Python Wrapper

Now that we know it's GraphQL with persisted queries:

```python
class InstacartGraphQL:
    BASE_URL = "https://www.instacart.com"
    GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql"

    OPERATIONS = {
        "current_user": {
            "name": "CurrentUserFields",
            "hash": "d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952"
        },
        "search": {
            "name": "CrossRetailerSearchAutosuggestions",
            "hash": "89ec32ea85c9b7ea89f7b4a071a5dd4ec1335831ff67035a0f92376725c306a3"
        },
        # Add more as we discover them
    }

    def __init__(self, session_cookie):
        self.session = requests.Session()
        self.session.cookies.set("_instacart_session", session_cookie)
        self.session.headers.update({
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 ..."
        })

    def query(self, operation_key, variables=None):
        """Execute a GraphQL persisted query"""
        op = self.OPERATIONS[operation_key]

        params = {
            "operationName": op["name"],
            "variables": json.dumps(variables or {}),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": op["hash"]
                }
            })
        }

        response = self.session.get(
            f"{self.GRAPHQL_ENDPOINT}?{urlencode(params)}"
        )
        return response.json()
```

---

## Action Items

- [ ] Manually capture cart/checkout operations via DevTools
- [ ] Document cart GraphQL mutation hashes
- [ ] Test authentication flow
- [ ] Build complete Python wrapper
- [ ] Create reorder automation script

**Status:** GraphQL API structure discovered! Need cart/order mutations.
**Next:** Manual DevTools capture of authenticated operations
