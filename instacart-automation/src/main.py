#!/usr/bin/env python3
"""
Instacart Voice Automation - Main CLI
Complete voice → Instacart automation pipeline for accessibility
"""

import argparse
import sys
from pathlib import Path
import json

from voice_input import VoiceInputHandler
from grocery_parser import GroceryParser
from instacart_api import InstacartAPI
from browser_automation import InstacartBrowserAutomation


class InstacartVoiceAutomation:
    """Main automation orchestrator"""

    def __init__(
        self,
        email: str,
        password: str,
        voice_method: str = "whisper",
        use_browser: bool = False,
        dry_run: bool = True
    ):
        """
        Initialize automation system

        Args:
            email: Instacart account email
            password: Instacart account password
            voice_method: 'whisper' or 'macos' or 'text'
            use_browser: Use browser automation instead of API
            dry_run: Don't actually place orders
        """
        self.email = email
        self.password = password
        self.voice_method = voice_method
        self.use_browser = use_browser
        self.dry_run = dry_run

        # Initialize components
        self.voice_handler = VoiceInputHandler(method=voice_method)
        self.parser = GroceryParser(use_ai=True)

        if use_browser:
            self.browser = None  # Lazy initialization
            self.api = None
        else:
            self.api = InstacartAPI(email, password)
            self.browser = None

    def get_grocery_list(self) -> str:
        """
        Get grocery list from voice or text input

        Returns:
            Grocery list text
        """
        print(f"\n{'='*70}")
        print("🎤 VOICE → INSTACART AUTOMATION")
        print(f"{'='*70}")
        print(f"Method: {self.voice_method}")
        print(f"Mode: {'Browser' if self.use_browser else 'API'}")
        print(f"Dry Run: {self.dry_run}")
        print(f"{'='*70}\n")

        if self.voice_method == "text":
            return self.voice_handler.get_text_input("Enter your grocery list: ")
        else:
            print("🎤 Speak your grocery list now...")
            return self.voice_handler.get_voice_input(duration=10)

    def process_order(self, grocery_text: str) -> bool:
        """
        Process complete order from grocery text

        Args:
            grocery_text: Natural language grocery list

        Returns:
            True if order processed successfully
        """
        if not grocery_text:
            print("❌ No grocery list provided")
            return False

        # Parse grocery list
        items = self.parser.parse(grocery_text)

        if not items:
            print("❌ No items parsed from grocery list")
            return False

        # Confirm with user
        print(f"\n{'='*70}")
        print("📋 PARSED GROCERY LIST")
        print(f"{'='*70}")
        for i, item in enumerate(items, 1):
            qty = item.get('quantity', 1)
            unit = item.get('unit', '')
            name = item.get('name', '')
            print(f"{i}. {qty} {unit} {name}".strip())
        print(f"{'='*70}\n")

        confirmation = input("Continue with this order? (yes/no): ").lower().strip()

        if confirmation not in ['yes', 'y']:
            print("❌ Order cancelled by user")
            return False

        # Process order
        if self.use_browser:
            return self._process_with_browser(items)
        else:
            return self._process_with_api(items)

    def _process_with_api(self, items: list) -> bool:
        """Process order using API"""
        if not self.api or not self.api.authenticated:
            print("❌ Not authenticated with Instacart API")
            return False

        print(f"\n{'='*70}")
        print("🔄 PROCESSING ORDER VIA API")
        print(f"{'='*70}\n")

        for item in items:
            name = item.get('name', '')
            qty = item.get('quantity', 1)

            # Search for product
            products = self.api.search_products(name)

            if products:
                # Add first match to cart
                product_id = products[0].get('id')
                self.api.add_to_cart(product_id, quantity=qty)
            else:
                print(f"⚠️  Product not found: {name}")

        # View cart
        cart = self.api.get_cart()
        print(f"\nCart: {json.dumps(cart, indent=2)}")

        # Checkout
        if self.dry_run:
            print("\n✅ DRY RUN COMPLETE - Order NOT placed")
            return True
        else:
            return self.api.checkout()

    def _process_with_browser(self, items: list) -> bool:
        """Process order using browser automation"""
        print(f"\n{'='*70}")
        print("🌐 PROCESSING ORDER VIA BROWSER")
        print(f"{'='*70}\n")

        with InstacartBrowserAutomation(headless=False) as browser:
            # Login
            if not browser.login(self.email, self.password):
                print("❌ Browser login failed")
                return False

            # Select Costco
            browser.search_store("Costco")

            # Add items
            for item in items:
                name = item.get('name', '')
                qty = item.get('quantity', 1)
                browser.add_to_cart(name, quantity=qty)

            # View cart
            cart = browser.view_cart()
            print(f"\nCart: {json.dumps(cart, indent=2)}")

            # Checkout
            return browser.checkout(dry_run=self.dry_run)

    def run_interactive(self):
        """Run interactive mode"""
        while True:
            # Get grocery list
            grocery_text = self.get_grocery_list()

            # Process order
            success = self.process_order(grocery_text)

            if success:
                print("\n✅ ORDER PROCESSED SUCCESSFULLY!")
            else:
                print("\n❌ ORDER PROCESSING FAILED")

            # Continue?
            another = input("\nPlace another order? (yes/no): ").lower().strip()
            if another not in ['yes', 'y']:
                break

        print("\n👋 Goodbye!")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Voice-activated Instacart automation for accessibility"
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Instacart account email"
    )

    parser.add_argument(
        "--password",
        required=True,
        help="Instacart account password"
    )

    parser.add_argument(
        "--voice",
        choices=["whisper", "macos", "text"],
        default="text",
        help="Voice input method (default: text for testing)"
    )

    parser.add_argument(
        "--browser",
        action="store_true",
        help="Use browser automation instead of API"
    )

    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually place orders (default is dry-run)"
    )

    parser.add_argument(
        "--text",
        help="Provide grocery list as text instead of voice"
    )

    args = parser.parse_args()

    # Create automation instance
    automation = InstacartVoiceAutomation(
        email=args.email,
        password=args.password,
        voice_method=args.voice,
        use_browser=args.browser,
        dry_run=not args.no_dry_run
    )

    if args.text:
        # Process single order from text
        success = automation.process_order(args.text)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        automation.run_interactive()


if __name__ == "__main__":
    main()
