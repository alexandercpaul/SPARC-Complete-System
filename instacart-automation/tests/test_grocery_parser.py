#!/usr/bin/env python3
"""
Tests for grocery list parser
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grocery_parser import GroceryParser


class TestGroceryParser:
    """Test grocery list parsing"""

    def setup_method(self):
        """Setup test parser"""
        self.parser = GroceryParser(use_ai=False)  # Use regex for fast tests

    def test_simple_item(self):
        """Test parsing single item"""
        items = self.parser.parse("milk")
        assert len(items) == 1
        assert items[0]["name"] == "milk"
        assert items[0]["quantity"] == 1

    def test_multiple_items(self):
        """Test parsing multiple items"""
        items = self.parser.parse("milk, eggs, and bread")
        assert len(items) == 3
        names = [item["name"] for item in items]
        assert "milk" in names
        assert "eggs" in names
        assert "bread" in names

    def test_quantity_parsing(self):
        """Test quantity extraction"""
        items = self.parser.parse("2 gallons of milk")
        assert len(items) == 1
        assert items[0]["quantity"] == 2
        assert "milk" in items[0]["name"]

    def test_dozen_parsing(self):
        """Test dozen quantity"""
        items = self.parser.parse("2 dozen eggs")
        assert len(items) == 1
        assert items[0]["quantity"] == 2
        assert items[0]["unit"] == "dozen"

    def test_command_removal(self):
        """Test command word removal"""
        items = self.parser.parse("I need milk please")
        assert len(items) == 1
        assert items[0]["name"] == "milk"

    def test_ampersand_separator(self):
        """Test ampersand as separator"""
        items = self.parser.parse("bread & butter")
        assert len(items) == 2

    def test_empty_input(self):
        """Test empty input"""
        items = self.parser.parse("")
        assert len(items) == 0

    def test_instacart_format_conversion(self):
        """Test conversion to Instacart format"""
        items = self.parser.parse("2 gallons of milk")
        instacart_items = self.parser.to_instacart_format(items)
        assert len(instacart_items) == 1
        assert "search_query" in instacart_items[0]
        assert instacart_items[0]["quantity"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
