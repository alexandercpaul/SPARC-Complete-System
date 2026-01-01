# Instacart API Completion Guide

## Current Status

### ✅ What's Implemented

1. **Authentication**: Working login endpoint
2. **GraphQL Structure**: Discovered persisted query system
3. **Known Operations**: User data, search autosuggestions, store listings
4. **Session Management**: Cookie-based authentication

### ⚠️ What Needs Completion

1. **Cart Operations** (Most Critical)
   - Add to cart mutation
   - Update cart quantity
   - Remove from cart
   - Get cart contents

2. **Product Search** (Partially Complete)
   - Search autosuggestions working
   - Need full product details
   - Need product ID retrieval

3. **Checkout Operations** (Critical)
   - Select delivery time
   - Choose delivery address
   - Apply payment method
   - Place order mutation

4. **Order Management** (Nice to Have)
   - Get order history
   - Track order status
   - Reorder previous orders

## How to Complete API Implementation

### Step 1: Capture Missing Operations

**Method 1: Browser DevTools (Easiest)**

1. Open Chrome/Firefox
2. Open DevTools (F12)
3. Go to **Network** tab
4. Filter by **Fetch/XHR**
5. Login to Instacart
6. Perform these actions while monitoring:
   - Search for "milk"
   - Click on product
   - Add to cart
   - Change quantity
   - View cart
   - Go to checkout (but DON'T complete)

7. For each GraphQL request:
   - Right-click → **Copy as cURL**
   - Or copy **Request URL**
   - Extract:
     - `operationName`
     - `sha256Hash` from extensions
     - `variables` structure

**Method 2: Automated Capture Script**

Create `scripts/capture_api.py`:
```python
from playwright.sync_api import sync_playwright

def capture_instacart_operations():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Capture all GraphQL requests
        graphql_ops = []

        def handle_request(request):
            if 'graphql' in request.url:
                graphql_ops.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data
                })

        page.on('request', handle_request)

        # Login and perform actions
        page.goto('https://www.instacart.com')
        input("Press Enter after you've completed shopping flow...")

        # Save captured operations
        import json
        with open('captured_operations.json', 'w') as f:
            json.dump(graphql_ops, f, indent=2)

        browser.close()
```

### Step 2: Map Operations to Code

Once you have the GraphQL operations, add them to `instacart_api.py`:

```python
OPERATIONS = {
    # Existing operations...

    # Add to cart (example - needs real hash)
    "add_to_cart": {
        "name": "AddItemToCart",
        "hash": "CAPTURE_THIS_HASH_FROM_DEVTOOLS"
    },

    "get_cart": {
        "name": "GetCart",
        "hash": "CAPTURE_THIS_HASH"
    },

    "update_cart_item": {
        "name": "UpdateCartItemQuantity",
        "hash": "CAPTURE_THIS_HASH"
    },

    "checkout": {
        "name": "PlaceOrder",
        "hash": "CAPTURE_THIS_HASH"
    }
}
```

### Step 3: Implement Methods

```python
def add_to_cart(self, item_id: str, quantity: int = 1) -> bool:
    """Add item to cart"""
    variables = {
        "itemId": item_id,
        "quantity": quantity,
        # Add other required variables from capture
    }

    result = self.query("add_to_cart", variables)
    return result.get("data", {}).get("success", False)

def get_cart(self) -> Dict:
    """Get cart contents"""
    result = self.query("get_cart")
    return result.get("data", {}).get("cart", {})
```

### Step 4: Test Each Operation

```python
def test_complete_flow():
    api = InstacartAPI(email, password)

    # 1. Search for product
    products = api.search_products("milk")
    print(f"Found {len(products)} products")

    # 2. Add to cart
    if products:
        item_id = products[0]["id"]
        success = api.add_to_cart(item_id, quantity=2)
        print(f"Add to cart: {success}")

    # 3. Get cart
    cart = api.get_cart()
    print(f"Cart: {cart}")

    # 4. Checkout (dry run)
    # Don't implement this until everything else works!
```

## GraphQL Persisted Queries

### What They Are

Instacart uses **persisted queries** - the query text is stored on the server and referenced by SHA256 hash.

### Request Format

```
GET /graphql?operationName=AddItemToCart&variables={...}&extensions={...}

extensions = {
    "persistedQuery": {
        "version": 1,
        "sha256Hash": "abc123..."
    }
}
```

### How to Find Hashes

1. DevTools → Network → graphql request
2. Look at **Query String Parameters**
3. Find `extensions` parameter
4. Decode URL encoding
5. Extract `sha256Hash`

### Common Operation Patterns

**Queries** (GET data):
- CurrentUserFields
- SearchProducts
- GetCart
- GetOrderHistory

**Mutations** (Change data):
- AddItemToCart
- UpdateCartItemQuantity
- RemoveCartItem
- PlaceOrder

## Variables Structure

### Search Products
```json
{
  "query": "milk",
  "retailerId": "90",
  "zoneId": "85",
  "limit": 20
}
```

### Add to Cart (Example - needs verification)
```json
{
  "itemId": "12345",
  "quantity": 2,
  "retailerId": "90",
  "replacementPreference": "allow_substitutions"
}
```

### Checkout (Example - needs verification)
```json
{
  "cartId": "abc123",
  "deliveryTime": "tomorrow_afternoon",
  "deliveryAddressId": "456",
  "paymentMethodId": "789",
  "tipAmount": 5.00
}
```

## Browser Automation Alternative

**If API completion is too difficult**, the browser automation fallback is already implemented and working!

### Advantages of Browser Mode
- ✅ Already works
- ✅ No API reverse engineering needed
- ✅ More reliable for complex flows
- ✅ Handles all edge cases (CAPTCHAs, etc.)

### Disadvantages
- ❌ Slower than API
- ❌ Requires visible browser (can be headless)
- ❌ More fragile to UI changes

### Recommendation

**For accessibility use case**: Use browser automation. It's more reliable and already complete.

**For scaling/automation**: Complete API implementation.

## Testing Strategy

### Phase 1: Read-Only Operations
1. Test login
2. Test search
3. Test getting user data
4. Test viewing cart (if you manually added items)

### Phase 2: Cart Operations
1. Test add to cart in browser, verify via API
2. Test updating quantity
3. Test removing items
4. Test clearing cart

### Phase 3: Checkout (Dangerous!)
1. **Use separate test account**
2. **Start with dry-run mode**
3. **Verify every parameter**
4. **Check twice before placing test order**
5. **Immediately cancel test order if placed**

## Security Notes

### Rate Limiting
- Instacart may rate limit API requests
- Add delays between requests (1-2 seconds)
- Don't spam the API

### Bot Detection
- Use realistic User-Agent headers
- Mimic browser request timing
- Include all required headers
- Maintain session cookies properly

### Legal Considerations
- This is for **personal use only**
- Technically against Instacart ToS
- For accessibility purposes (disability accommodation)
- Don't sell or share API wrapper
- Don't scale beyond personal use

## Next Steps

1. **Capture cart operations** via DevTools
2. **Extract SHA256 hashes** for mutations
3. **Map variables structure** for each operation
4. **Implement add_to_cart()** first
5. **Test thoroughly** in dry-run mode
6. **Complete get_cart()** for verification
7. **Save checkout for last** (most dangerous)

## Alternative: Use Browser Automation

**Recommended for accessibility use case**:

The browser automation is complete and working. For a user with typing difficulty, this is actually **better** because:
- More visual feedback
- Easier to verify items
- Can see prices and images
- More reliable overall

**Just use**: `python src/main.py --browser`

---

**The browser automation fallback is production-ready. API completion is optional.**
