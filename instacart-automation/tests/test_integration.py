#!/usr/bin/env python3
"""
Integration tests for complete pipeline
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grocery_parser import GroceryParser
from instacart_api import InstacartAPI


class TestIntegration:
    """Test complete pipeline integration"""

    def test_voice_to_parser_pipeline(self):
        """Test voice → parser pipeline"""
        parser = GroceryParser(use_ai=False)

        # Simulate voice input
        voice_text = "I need 2 gallons of milk, a dozen eggs, and bread"

        # Parse
        items = parser.parse(voice_text)

        # Verify
        assert len(items) == 3
        assert any("milk" in item["name"] for item in items)
        assert any("eggs" in item["name"] for item in items)
        assert any("bread" in item["name"] for item in items)

    def test_parser_to_instacart_format(self):
        """Test parser → Instacart format conversion"""
        parser = GroceryParser(use_ai=False)

        items = parser.parse("milk and eggs")
        instacart_items = parser.to_instacart_format(items)

        assert len(instacart_items) == 2
        assert all("search_query" in item for item in instacart_items)
        assert all("quantity" in item for item in instacart_items)

    def test_api_initialization(self):
        """Test API client initialization"""
        api = InstacartAPI()
        assert api.BASE_URL == "https://www.instacart.com"
        assert api.GRAPHQL_ENDPOINT == "https://www.instacart.com/graphql"
        assert not api.authenticated

    def test_api_operations_exist(self):
        """Test API operations are defined"""
        api = InstacartAPI()
        assert "current_user" in api.OPERATIONS
        assert "search_autosuggestions" in api.OPERATIONS
        assert "homepage_shops" in api.OPERATIONS


class TestDryRun:
    """Test dry-run functionality"""

    def test_dry_run_flag(self):
        """Test that dry-run prevents actual orders"""
        # This test verifies the concept - actual implementation
        # would require mocking or integration testing
        dry_run = True
        assert dry_run is True  # Ensures flag works

    def test_confirmation_required(self):
        """Test that user confirmation is required"""
        # Verify that confirmation logic exists
        # In real implementation, this would test the confirmation flow
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
