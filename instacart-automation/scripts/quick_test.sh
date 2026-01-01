#!/bin/bash
# Quick test script for dry-run testing

set -e

echo "=================================="
echo "Quick Test - Dry Run Mode"
echo "=================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Test with text input (no voice needed for quick test)
python src/main.py \
    --email "alexandercpaul@gmail.com" \
    --password "t2as0-nAop-!O@sqh" \
    --voice text \
    --browser \
    --text "I need milk, eggs, and bread"

echo ""
echo "✅ Test complete!"
