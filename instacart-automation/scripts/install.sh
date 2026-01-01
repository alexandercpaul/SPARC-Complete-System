#!/bin/bash
# Installation script for Instacart Voice Automation

set -e

echo "=================================="
echo "Instacart Voice Automation Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || {
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r config/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Install Ollama (if not already installed)
echo "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Pull required models
echo "Pulling Ollama models..."
ollama pull qwen2.5-coder:7b

# Create config from example
if [ ! -f config/config.json ]; then
    echo "Creating config file..."
    cp config/config.example.json config/config.json
    echo "⚠️  Please edit config/config.json with your Instacart credentials"
fi

# Make scripts executable
chmod +x src/*.py
chmod +x scripts/*.sh

echo ""
echo "=================================="
echo "✅ Installation complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit config/config.json with your credentials"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run: python src/main.py --help"
echo ""
