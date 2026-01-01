#!/usr/bin/env python3
"""
Browser Automation Fallback for Instacart
Uses Playwright to automate instacart.com when API is insufficient
"""

from playwright.sync_api import sync_playwright, Page, Browser
from typing import List, Dict, Optional
import time
import json


class InstacartBrowserAutomation:
    """Automate Instacart via browser when API is limited"""

    def __init__(self, headless: bool = False):
        """
        Initialize browser automation

        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.authenticated = False

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

    def start(self):
        """Start browser"""
        print(f"\n{'='*60}")
        print("🌐 STARTING BROWSER AUTOMATION")
        print(f"{'='*60}")
        print(f"Headless: {self.headless}")
        print(f"{'='*60}\n")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()

    def stop(self):
        """Stop browser"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, email: str, password: str) -> bool:
        """
        Login to Instacart

        Args:
            email: Account email
            password: Account password

        Returns:
            True if login successful
        """
        print(f"\n{'='*60}")
        print("🔐 LOGGING IN TO INSTACART")
        print(f"{'='*60}")
        print(f"Email: {email}")
        print(f"{'='*60}\n")

        try:
            # Navigate to login page
            self.page.goto("https://www.instacart.com/accounts/login")

            # Wait for login form
            self.page.wait_for_selector('input[type="email"]', timeout=10000)

            # Fill in credentials
            self.page.fill('input[type="email"]', email)
            self.page.fill('input[type="password"]', password)

            # Submit form
            self.page.click('button[type="submit"]')

            # Wait for navigation
            self.page.wait_for_load_state("networkidle", timeout=15000)

            # Check if logged in
            if "accounts/login" not in self.page.url:
                self.authenticated = True
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def search_store(self, store_name: str = "Costco") -> bool:
        """
        Select a store

        Args:
            store_name: Store name to search for

        Returns:
            True if store selected
        """
        if not self.authenticated:
            print("⚠️  Not logged in")
            return False

        print(f"\n{'='*60}")
        print(f"🏪 SELECTING STORE: {store_name}")
        print(f"{'='*60}\n")

        try:
            # Search for store
            search_box = self.page.wait_for_selector('input[placeholder*="Search"]', timeout=5000)
            search_box.fill(store_name)

            # Wait for results and click first Costco
            time.sleep(2)
            self.page.click(f'text=/{store_name}/i')

            print(f"✅ Selected {store_name}")
            return True

        except Exception as e:
            print(f"❌ Store selection error: {e}")
            return False

    def search_products(self, query: str) -> List[Dict]:
        """
        Search for products

        Args:
            query: Search query

        Returns:
            List of products found
        """
        if not self.authenticated:
            print("⚠️  Not logged in")
            return []

        print(f"\n{'='*60}")
        print(f"🔍 SEARCHING: {query}")
        print(f"{'='*60}\n")

        try:
            # Find search box
            search_box = self.page.wait_for_selector('input[placeholder*="Search"]', timeout=5000)
            search_box.fill(query)
            search_box.press("Enter")

            # Wait for results
            self.page.wait_for_load_state("networkidle", timeout=10000)

            # Extract product information
            products = []
            product_cards = self.page.query_selector_all('[data-testid*="product"], .product-card')

            for card in product_cards[:5]:  # Limit to first 5
                try:
                    name = card.query_selector('.product-name, [data-testid="product-name"]')
                    price = card.query_selector('.product-price, [data-testid="product-price"]')

                    products.append({
                        "name": name.inner_text() if name else "Unknown",
                        "price": price.inner_text() if price else "Unknown",
                        "element": card
                    })
                except:
                    pass

            print(f"Found {len(products)} products")

            return products

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def add_to_cart(self, product_name: str, quantity: int = 1) -> bool:
        """
        Add product to cart

        Args:
            product_name: Product name
            quantity: Quantity to add

        Returns:
            True if added successfully
        """
        if not self.authenticated:
            print("⚠️  Not logged in")
            return False

        print(f"➕ Adding to cart: {product_name} (qty: {quantity})")

        try:
            # Search for the product first
            products = self.search_products(product_name)

            if not products:
                print(f"⚠️  Product not found: {product_name}")
                return False

            # Click "Add to Cart" on first matching product
            product_element = products[0]["element"]
            add_button = product_element.query_selector('button[data-testid="add-to-cart"], button:has-text("Add")')

            if add_button:
                add_button.click()

                # Handle quantity if > 1
                if quantity > 1:
                    for _ in range(quantity - 1):
                        increase_button = product_element.query_selector('button[data-testid="increase-quantity"]')
                        if increase_button:
                            increase_button.click()
                            time.sleep(0.5)

                print(f"✅ Added {quantity}x {product_name}")
                return True
            else:
                print(f"⚠️  Add button not found for {product_name}")
                return False

        except Exception as e:
            print(f"❌ Add to cart error: {e}")
            return False

    def view_cart(self) -> Dict:
        """
        View cart contents

        Returns:
            Cart data
        """
        if not self.authenticated:
            print("⚠️  Not logged in")
            return {}

        print("\n🛒 Viewing cart...")

        try:
            # Click cart icon
            self.page.click('[data-testid="cart"], [aria-label*="cart"]')
            time.sleep(2)

            # Extract cart items
            cart_items = []
            item_elements = self.page.query_selector_all('.cart-item, [data-testid="cart-item"]')

            for item in item_elements:
                try:
                    name = item.query_selector('.item-name')
                    qty = item.query_selector('.item-quantity')
                    price = item.query_selector('.item-price')

                    cart_items.append({
                        "name": name.inner_text() if name else "Unknown",
                        "quantity": qty.inner_text() if qty else "1",
                        "price": price.inner_text() if price else "Unknown"
                    })
                except:
                    pass

            print(f"Cart has {len(cart_items)} items")

            return {
                "items": cart_items,
                "count": len(cart_items)
            }

        except Exception as e:
            print(f"❌ View cart error: {e}")
            return {}

    def checkout(self, dry_run: bool = True) -> bool:
        """
        Proceed to checkout (DRY RUN by default for safety)

        Args:
            dry_run: If True, stop before placing order

        Returns:
            True if checkout successful
        """
        if not self.authenticated:
            print("⚠️  Not logged in")
            return False

        print("\n💳 Proceeding to checkout...")

        if dry_run:
            print("⚠️  DRY RUN MODE - Will NOT place actual order")

        try:
            # Click checkout button
            self.page.click('[data-testid="checkout"], button:has-text("Checkout")')

            # Wait for checkout page
            self.page.wait_for_load_state("networkidle", timeout=10000)

            if dry_run:
                print("✅ Checkout page reached (DRY RUN - stopping here)")
                return True
            else:
                # WARNING: This would place a REAL order
                print("⚠️  REAL ORDER PLACEMENT NOT IMPLEMENTED FOR SAFETY")
                print("   To enable, set dry_run=False and implement order confirmation")
                return False

        except Exception as e:
            print(f"❌ Checkout error: {e}")
            return False


def test_browser_automation():
    """Test browser automation"""
    email = "alexandercpaul@gmail.com"
    password = "t2as0-nAop-!O@sqh"

    print("\n🎯 Testing Browser Automation\n")

    with InstacartBrowserAutomation(headless=False) as bot:
        # Login
        if bot.login(email, password):
            # Select Costco
            bot.search_store("Costco")

            # Add items
            bot.add_to_cart("milk", quantity=1)
            bot.add_to_cart("eggs", quantity=2)

            # View cart
            cart = bot.view_cart()
            print(f"\n Cart: {json.dumps(cart, indent=2)}")

            # Checkout (dry run)
            bot.checkout(dry_run=True)

        else:
            print("❌ Login failed, cannot continue")


if __name__ == "__main__":
    test_browser_automation()
