#!/usr/bin/env python3
"""
Natural Language Grocery List Parser
Converts spoken grocery requests into structured data
"""

import re
import json
from typing import List, Dict, Optional
import requests


class GroceryParser:
    """Parse natural language grocery requests into structured lists"""

    # Common quantity patterns
    QUANTITY_PATTERNS = [
        r'(\d+)\s*(dozen|doz)',
        r'(\d+)\s*(pounds?|lbs?)',
        r'(\d+)\s*(ounces?|oz)',
        r'(\d+)\s*(gallons?|gal)',
        r'(\d+)\s*(quarts?|qt)',
        r'(\d+)\s*(pints?|pt)',
        r'(\d+)\s*(liters?|l)',
        r'(\d+)\s*(bottles?)',
        r'(\d+)\s*(cans?)',
        r'(\d+)\s*(boxes?)',
        r'(\d+)\s*(packages?|pkgs?)',
        r'(\d+)',  # Just a number
    ]

    # Common command patterns to remove
    COMMAND_PATTERNS = [
        r'^(i need|i want|get me|add|buy|order|purchase)\s+',
        r'\s+(please|thanks|thank you)$',
    ]

    def __init__(self, use_ai: bool = True, ollama_url: str = "http://localhost:11434"):
        """
        Initialize parser

        Args:
            use_ai: Use AI (Ollama) for parsing instead of regex
            ollama_url: Ollama API URL
        """
        self.use_ai = use_ai
        self.ollama_url = ollama_url

    def parse_with_regex(self, text: str) -> List[Dict]:
        """
        Parse using regex patterns (fast, less accurate)

        Args:
            text: Input text

        Returns:
            List of parsed items
        """
        # Clean up text
        text = text.lower().strip()

        # Remove command patterns
        for pattern in self.COMMAND_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Split by common separators
        items_text = re.split(r',|\sand\s|\&', text)

        items = []

        for item_text in items_text:
            item_text = item_text.strip()
            if not item_text:
                continue

            # Extract quantity
            quantity = 1
            quantity_unit = None

            for pattern in self.QUANTITY_PATTERNS:
                match = re.search(pattern, item_text, re.IGNORECASE)
                if match:
                    quantity = int(match.group(1))
                    if len(match.groups()) > 1:
                        quantity_unit = match.group(2)
                    # Remove quantity from text
                    item_text = re.sub(pattern, '', item_text, flags=re.IGNORECASE).strip()
                    break

            items.append({
                "name": item_text,
                "quantity": quantity,
                "unit": quantity_unit,
                "original": item_text
            })

        return items

    def parse_with_ai(self, text: str) -> List[Dict]:
        """
        Parse using Ollama AI (more accurate)

        Args:
            text: Input text

        Returns:
            List of parsed items
        """
        prompt = f"""Parse this grocery list into structured JSON. Extract item name, quantity, and unit.

Input: "{text}"

Output JSON format:
[
  {{"name": "milk", "quantity": 1, "unit": "gallon"}},
  {{"name": "eggs", "quantity": 2, "unit": "dozen"}}
]

Rules:
- Default quantity is 1 if not specified
- Common units: gallon, dozen, pound, ounce, liter, bottle, can, box, package
- Ignore command words like "I need", "get me", "buy"
- Split items by commas, "and", "&"

JSON output only:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            result = response.json()["response"]

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group(0))

                # Add original text
                for item in items:
                    if "original" not in item:
                        item["original"] = item["name"]

                return items
            else:
                print("⚠️  AI parsing failed, falling back to regex")
                return self.parse_with_regex(text)

        except Exception as e:
            print(f"⚠️  AI parsing error: {e}, falling back to regex")
            return self.parse_with_regex(text)

    def parse(self, text: str) -> List[Dict]:
        """
        Parse grocery list from natural language

        Args:
            text: Input text

        Returns:
            List of parsed grocery items
        """
        if not text:
            return []

        print(f"\n{'='*60}")
        print("🧠 PARSING GROCERY LIST")
        print(f"{'='*60}")
        print(f"Input: {text}")
        print(f"Method: {'AI (Ollama)' if self.use_ai else 'Regex'}")
        print(f"{'='*60}\n")

        if self.use_ai:
            items = self.parse_with_ai(text)
        else:
            items = self.parse_with_regex(text)

        print(f"\n{'='*60}")
        print(f"📋 PARSED {len(items)} ITEMS")
        print(f"{'='*60}")
        for i, item in enumerate(items, 1):
            qty = item.get('quantity', 1)
            unit = item.get('unit', '')
            name = item.get('name', '')
            print(f"{i}. {qty} {unit} {name}".strip())
        print(f"{'='*60}\n")

        return items

    def to_instacart_format(self, items: List[Dict]) -> List[Dict]:
        """
        Convert parsed items to Instacart API format

        Args:
            items: Parsed items

        Returns:
            Items in Instacart format
        """
        instacart_items = []

        for item in items:
            instacart_items.append({
                "search_query": item["name"],
                "quantity": item.get("quantity", 1),
                "unit": item.get("unit"),
                "metadata": {
                    "original_text": item.get("original", item["name"])
                }
            })

        return instacart_items


def test_parser():
    """Test grocery parser"""
    parser = GroceryParser(use_ai=True)

    test_cases = [
        "I need milk, eggs, and bread",
        "Get me 2 dozen eggs and a gallon of milk",
        "Buy bananas and oat milk please",
        "Add 3 pounds of ground beef, 2 boxes of pasta, and tomato sauce",
        "Order chicken breast, broccoli, and rice"
    ]

    print("\n🎯 Testing Grocery Parser\n")

    for test in test_cases:
        items = parser.parse(test)
        print(f"✅ '{test}' → {len(items)} items\n")


if __name__ == "__main__":
    test_parser()
