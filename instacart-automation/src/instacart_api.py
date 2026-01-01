#!/usr/bin/env python3
"""
Instacart GraphQL API Client
Handles authentication, product search, cart management, and checkout
"""

import requests
import json
from typing import List, Dict, Optional
from urllib.parse import urlencode
import time


class InstacartAPI:
    """Instacart GraphQL API client with persisted queries"""

    BASE_URL = "https://www.instacart.com"
    GRAPHQL_ENDPOINT = f"{BASE_URL}/graphql"
    LOGIN_ENDPOINT = f"{BASE_URL}/v3/dynamic_data/authenticate/login"

    # Known GraphQL persisted query hashes
    OPERATIONS = {
        "current_user": {
            "name": "CurrentUserFields",
            "hash": "d7d1050d8a8efb9a24d2fd0d9c39f58d852ab84ea709370bcbedbca790112952"
        },
        "search_autosuggestions": {
            "name": "CrossRetailerSearchAutosuggestions",
            "hash": "89ec32ea85c9b7ea89f7b4a071a5dd4ec1335831ff67035a0f92376725c306a3"
        },
        "homepage_shops": {
            "name": "HomepageShopCollection",
            "hash": "a1673521c0b83b8e73bda30552c5ae950fa24a4d31b599ec15c944d7fa3f45eb"
        },
        "retailer_etas": {
            "name": "GetAccurateVisitorRetailerEtas",
            "hash": "69273595be20f766a8c9051bbf46fa6392eb7692e00f9c05519831b606a10d88"
        },
    }

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize API client

        Args:
            email: Instacart account email
            password: Instacart account password
        """
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instacart.com/",
        })

        self.authenticated = False
        self.user_data = None

        if email and password:
            self.authenticate(email, password)

    def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with Instacart

        Args:
            email: Account email
            password: Account password

        Returns:
            True if authentication successful
        """
        print(f"\n{'='*60}")
        print("🔐 AUTHENTICATING WITH INSTACART")
        print(f"{'='*60}")
        print(f"Email: {email}")
        print(f"{'='*60}\n")

        try:
            response = self.session.post(
                f"{self.LOGIN_ENDPOINT}?source=web",
                headers={"Content-Type": "application/json"},
                json={
                    "email": email,
                    "password": password,
                    "grant_type": "email",
                    "scope": ""
                }
            )

            if response.status_code == 200:
                # Session cookie is automatically stored in session
                self.authenticated = True
                print("✅ Authentication successful!")

                # Get user data
                self.user_data = self.query("current_user")

                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def query(self, operation_key: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL persisted query

        Args:
            operation_key: Operation key from OPERATIONS dict
            variables: Query variables

        Returns:
            Query response data
        """
        if operation_key not in self.OPERATIONS:
            raise ValueError(f"Unknown operation: {operation_key}")

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

        try:
            response = self.session.get(
                f"{self.GRAPHQL_ENDPOINT}?{urlencode(params)}"
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Query failed: {response.status_code}")
                return {}

        except Exception as e:
            print(f"⚠️  Query error: {e}")
            return {}

    def search_products(self, query: str, retailer_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for products

        Args:
            query: Search query
            retailer_ids: List of retailer IDs to search (default: Costco)

        Returns:
            List of matching products
        """
        if not self.authenticated:
            print("⚠️  Not authenticated. Call authenticate() first.")
            return []

        # Default to Costco (ID: 90)
        if retailer_ids is None:
            retailer_ids = ["90"]

        print(f"\n{'='*60}")
        print(f"🔍 SEARCHING PRODUCTS: {query}")
        print(f"{'='*60}")

        variables = {
            "query": query,
            "limit": 10,
            "retailerIds": retailer_ids,
            "zoneId": "85",  # May need to be dynamic based on location
        }

        result = self.query("search_autosuggestions", variables)

        # Extract products from response
        # Note: Actual structure may vary, needs verification from real API
        products = []
        try:
            if "data" in result:
                # Parse GraphQL response structure
                # This is a placeholder - actual structure depends on API
                products = result.get("data", {}).get("products", [])
        except Exception as e:
            print(f"⚠️  Error parsing products: {e}")

        print(f"Found {len(products)} products\n")

        return products

    def add_to_cart(self, product_id: str, quantity: int = 1) -> bool:
        """
        Add item to cart

        Args:
            product_id: Product ID
            quantity: Quantity to add

        Returns:
            True if successful
        """
        if not self.authenticated:
            print("⚠️  Not authenticated")
            return False

        print(f"➕ Adding to cart: {product_id} (qty: {quantity})")

        # This endpoint needs to be discovered from actual API
        # Placeholder implementation
        print("⚠️  Add to cart endpoint not yet implemented")
        print("   Need to capture from browser DevTools")

        return False

    def get_cart(self) -> Dict:
        """
        Get current cart contents

        Returns:
            Cart data
        """
        if not self.authenticated:
            print("⚠️  Not authenticated")
            return {}

        print("🛒 Getting cart...")

        # This endpoint needs to be discovered
        print("⚠️  Get cart endpoint not yet implemented")

        return {}

    def checkout(self, delivery_time: Optional[str] = None) -> bool:
        """
        Place order

        Args:
            delivery_time: Preferred delivery time

        Returns:
            True if order placed successfully
        """
        if not self.authenticated:
            print("⚠️  Not authenticated")
            return False

        print("💳 Placing order...")

        # This endpoint needs to be discovered
        print("⚠️  Checkout endpoint not yet implemented")
        print("   Need to capture from browser DevTools")

        return False


def test_api():
    """Test Instacart API client"""
    # NOTE: Replace with actual credentials for testing
    email = "alexandercpaul@gmail.com"
    password = "t2as0-nAop-!O@sqh"

    print("\n🎯 Testing Instacart API Client\n")

    api = InstacartAPI(email, password)

    if api.authenticated:
        print("✅ Authentication successful!")

        # Test product search
        products = api.search_products("milk")
        print(f"✅ Found {len(products)} products")

    else:
        print("❌ Authentication failed")


if __name__ == "__main__":
    test_api()
