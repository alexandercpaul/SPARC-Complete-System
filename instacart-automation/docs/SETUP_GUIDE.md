# Instacart Voice Automation - Setup Guide

## Overview

Complete voice-activated grocery automation system for Instacart. Built for accessibility - enables hands-free grocery ordering with minimal typing.

## Quick Start

### 1. Installation

```bash
cd instacart-automation
./scripts/install.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Install Playwright browsers
- Install Ollama (if needed)
- Pull required AI models
- Create config file

### 2. Configuration

Edit `config/config.json`:

```json
{
  "instacart": {
    "email": "your-email@example.com",
    "password": "your-password"
  },
  "voice": {
    "method": "whisper",
    "duration": 10
  },
  "automation": {
    "use_browser": true,
    "dry_run": true
  }
}
```

### 3. Run Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

### 4. Quick Test (Dry Run)

```bash
./scripts/quick_test.sh
```

## Usage

### Text Input (Testing)

```bash
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --voice text \
    --text "I need milk, eggs, and bread"
```

### Voice Input (Whisper)

```bash
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --voice whisper
```

Speak when prompted: "I need 2 gallons of milk, a dozen eggs, and bread"

### macOS Dictation

```bash
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --voice macos
```

### Browser Mode (More Reliable)

```bash
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --browser
```

### Place Real Orders

⚠️ **WARNING**: This will place REAL orders!

```bash
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --no-dry-run
```

## Architecture

```
Voice Input (Whisper/macOS)
    ↓
Speech-to-Text
    ↓
Natural Language Parser (Ollama AI)
    ↓
Grocery List Extraction
    ↓
Instacart API/Browser Automation
    ↓
Cart Assembly
    ↓
Order Placement (with confirmation)
```

## Components

### 1. Voice Input Handler (`voice_input.py`)

- Supports OpenAI Whisper (recommended)
- Supports macOS native dictation
- Fallback to text input for testing

### 2. Grocery Parser (`grocery_parser.py`)

- AI-powered parsing using Ollama (qwen2.5-coder)
- Fallback regex parsing
- Extracts items, quantities, units
- Handles natural language variations

### 3. Instacart API Client (`instacart_api.py`)

- GraphQL API integration
- Session authentication
- Product search
- Cart management
- Checkout (needs completion)

### 4. Browser Automation (`browser_automation.py`)

- Playwright-based automation
- More reliable than API
- Full cart and checkout support
- Headless or visible mode

### 5. Main CLI (`main.py`)

- Unified interface
- Interactive and one-shot modes
- Dry-run safety mode
- User confirmation required

## Dependencies

### Required

- Python 3.8+
- Playwright (browser automation)
- PyAudio (audio recording)
- Requests (HTTP client)
- Ollama (local AI)

### Optional

- OpenAI Whisper (voice transcription)
- pytest (testing)

## Accessibility Features

### Voice Activation

- **macOS Shortcuts**: Create keyboard shortcut to trigger automation
- **Minimal Typing**: Only confirmation required
- **Voice Feedback**: Reads back parsed grocery list

### Safety Features

- **Dry-Run Mode**: Default mode doesn't place orders
- **User Confirmation**: Always confirms before checkout
- **Cart Preview**: Shows cart before proceeding

### Time Savings

- Traditional: 10-15 minutes of typing/clicking
- Voice automation: 30 seconds of speaking + confirmation
- **90%+ time reduction**

## Troubleshooting

### Voice Input Not Working

**Whisper Installation**:
```bash
pip install openai-whisper
```

**macOS Dictation**:
- System Preferences → Keyboard → Dictation
- Enable dictation
- Set keyboard shortcut (fn twice)

### Ollama Not Running

```bash
ollama serve
```

In another terminal:
```bash
ollama pull qwen2.5-coder:7b
```

### Playwright Browsers Missing

```bash
playwright install chromium
```

### API Authentication Failing

- Verify credentials in config
- Try browser mode instead: `--browser`
- Check Instacart account status

### Parser Not Extracting Items

- Check Ollama is running: `ollama list`
- Try regex mode: Set `use_ai=False` in code
- Verify input text format

## Advanced Usage

### Create macOS Shortcut

1. Open Automator
2. Create new "Quick Action"
3. Add "Run Shell Script"
4. Paste:
```bash
cd /path/to/instacart-automation
source venv/bin/activate
python src/main.py --voice whisper
```
5. Save as "Instacart Order"
6. Assign keyboard shortcut in System Preferences

### Scheduled Orders

```bash
# Add to crontab
0 9 * * 1 /path/to/instacart-automation/venv/bin/python /path/to/src/main.py --text "weekly groceries"
```

### Reorder Favorites

Create saved orders in `config/saved_orders.json`:
```json
{
  "weekly": "2 gallons milk, 2 dozen eggs, bread, bananas, chicken",
  "basics": "milk, eggs, bread, butter"
}
```

## Security

### Credential Storage

**Option 1: Environment Variables**
```bash
export INSTACART_EMAIL="your@email.com"
export INSTACART_PASSWORD="yourpassword"
```

**Option 2: 1Password CLI**
```bash
op read "op://Personal/Instacart/username"
op read "op://Personal/Instacart/password"
```

**Option 3: macOS Keychain**
```bash
security add-generic-password -s instacart -a email -w "your@email.com"
security find-generic-password -s instacart -a email -w
```

### Best Practices

- ✅ Use dry-run mode for testing
- ✅ Store credentials securely
- ✅ Never commit config.json to git
- ✅ Review cart before confirming
- ✅ Monitor orders for accuracy

## Development

### Running Tests

```bash
pytest tests/ -v
pytest tests/test_grocery_parser.py -v
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Support

For issues, bugs, or feature requests:
- Check troubleshooting section
- Review logs in terminal output
- Test in dry-run mode first

## License

MIT License - Personal use for accessibility

---

**Built for accessibility and independence.**
