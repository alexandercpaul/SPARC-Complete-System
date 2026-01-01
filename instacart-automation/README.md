# Instacart Voice Automation System

Complete voice-activated grocery ordering system for Instacart. **Built for accessibility** - enables hands-free grocery shopping for users with typing difficulties or disabilities.

## Features

- 🎤 **Voice Input**: OpenAI Whisper or macOS dictation
- 🧠 **AI Parsing**: Natural language understanding via Ollama
- 🛒 **Automated Shopping**: Search, add to cart, checkout
- 🌐 **Browser Automation**: Reliable Playwright-based automation
- 🔒 **Safety Features**: Dry-run mode, user confirmation
- ♿ **Accessibility First**: Minimal typing, maximum independence

## Quick Start

### Installation

```bash
cd instacart-automation
./scripts/install.sh
```

### Basic Usage

```bash
# Test with text input (no voice)
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --voice text \
    --text "I need milk, eggs, and bread"

# Voice input with Whisper
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --voice whisper

# Browser automation (more reliable)
python src/main.py \
    --email your@email.com \
    --password yourpassword \
    --browser
```

## Architecture

```
Voice Input (30 seconds)
    ↓
Speech-to-Text (Whisper/macOS)
    ↓
Natural Language Parser (Ollama AI)
    ↓
Grocery List Extraction
    ↓
Instacart API/Browser Automation
    ↓
Cart Assembly & Verification
    ↓
User Confirmation
    ↓
Order Placed
```

## Components

### 1. Voice Input Handler
- OpenAI Whisper (95%+ accuracy)
- macOS native dictation
- Text input fallback

### 2. Grocery Parser
- AI-powered parsing (Ollama)
- Extracts items, quantities, units
- Handles natural language variations

### 3. Instacart Integration
- GraphQL API client (partial)
- Browser automation (complete)
- Session management
- Cart operations

### 4. Main CLI
- Interactive and one-shot modes
- Dry-run safety mode
- User confirmation system

## File Structure

```
instacart-automation/
├── src/
│   ├── main.py                 # Main CLI interface
│   ├── voice_input.py          # Voice/audio handling
│   ├── grocery_parser.py       # NLP parsing
│   ├── instacart_api.py        # GraphQL API client
│   └── browser_automation.py   # Playwright automation
├── tests/
│   ├── test_voice_input.py
│   ├── test_grocery_parser.py
│   └── test_integration.py
├── config/
│   ├── requirements.txt
│   └── config.example.json
├── scripts/
│   ├── install.sh
│   └── quick_test.sh
└── docs/
    ├── SETUP_GUIDE.md
    ├── ACCESSIBILITY_GUIDE.md
    └── API_COMPLETION_GUIDE.md
```

## Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)**: Installation and configuration
- **[Accessibility Guide](docs/ACCESSIBILITY_GUIDE.md)**: Accessibility features and usage
- **[API Completion Guide](docs/API_COMPLETION_GUIDE.md)**: Technical API details

## Usage Examples

### Text Input (Testing)
```bash
python src/main.py \
    --email user@example.com \
    --password pass123 \
    --voice text \
    --text "2 gallons of milk, a dozen eggs, bread"
```

### Voice Input
```bash
python src/main.py \
    --email user@example.com \
    --password pass123 \
    --voice whisper
```

Speak: "I need bananas, oat milk, and chicken breast"

### Browser Mode (Recommended)
```bash
python src/main.py \
    --email user@example.com \
    --password pass123 \
    --browser
```

### Place Real Orders
⚠️ **WARNING**: This places REAL orders!
```bash
python src/main.py \
    --email user@example.com \
    --password pass123 \
    --no-dry-run
```

## Dependencies

### Core
- Python 3.8+
- Playwright (browser automation)
- PyAudio (audio recording)
- Requests (HTTP client)
- Ollama (local AI server)

### Optional
- OpenAI Whisper (voice transcription)
- pytest (testing)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific component
pytest tests/test_grocery_parser.py -v

# Quick integration test
./scripts/quick_test.sh
```

## Safety Features

### Dry-Run Mode (Default)
- **Never places real orders** without explicit flag
- Shows what would be ordered
- Perfect for testing and verification

### User Confirmation
- Shows parsed grocery list before proceeding
- Requires explicit "yes" confirmation
- Can cancel at any time

### Cart Preview
- Displays all items before checkout
- Shows quantities and prices
- Final check before order

## Accessibility Benefits

### Time Savings
- Traditional: 10-15 minutes of typing/clicking
- Voice automation: 30 seconds speaking + confirmation
- **90%+ time reduction**

### Physical Effort
- **Zero typing** required for main workflow
- **2 clicks** total (confirm list, confirm order)
- **No precise mouse control** needed

### Independence
- Order groceries without assistance
- Reorder favorites easily
- Schedule recurring orders

## Advanced Features

### Saved Shopping Lists
Create frequently used lists in `config/saved_lists.json`

### macOS Keyboard Shortcut
Press one key combination to trigger automation

### Scheduled Orders
Use cron for automatic weekly orders

### Reorder Favorites
One command to reorder previous orders

## Troubleshooting

### Voice Not Working
- Check microphone permissions
- Install Whisper: `pip install openai-whisper`
- Enable macOS dictation in System Preferences

### Parser Errors
- Ensure Ollama is running: `ollama serve`
- Check models installed: `ollama list`
- Test with simple phrases first

### API Authentication Failing
- Verify credentials in config
- Try browser mode: `--browser`
- Check account status on Instacart

### Playwright Issues
- Install browsers: `playwright install chromium`
- Check for updates: `pip install --upgrade playwright`

## Security

### Credentials
- Store in config file (not committed to git)
- Use environment variables
- Consider 1Password CLI integration

### Privacy
- Voice processed locally (Whisper)
- No cloud services for transcription
- API calls only to Instacart

### Safety
- Dry-run mode prevents accidents
- User confirmation required
- Cart preview before checkout

## Development

### Code Style
```bash
black src/ tests/
```

### Type Checking
```bash
mypy src/
```

### Running Tests
```bash
pytest tests/ -v --cov=src
```

## Known Limitations

### API Completeness
- Cart operations need manual capture from browser
- Checkout endpoint requires completion
- Some GraphQL mutations need discovery

### Browser Automation
- Requires visible browser (can run headless)
- UI changes may break selectors
- Slower than direct API calls

### Voice Recognition
- Background noise affects accuracy
- Accent variations may need adjustment
- Complex product names may be misheard

## Future Enhancements

- [ ] Complete Instacart API cart operations
- [ ] iOS/Android app for mobile ordering
- [ ] Smart suggestions based on history
- [ ] Price tracking and budget alerts
- [ ] Multi-store support (Target, Walmart)
- [ ] Meal planning integration
- [ ] Nutrition tracking
- [ ] Dietary restriction filtering

## Contributing

This is a personal accessibility project. If you have suggestions or improvements:
1. Test thoroughly in dry-run mode
2. Document accessibility impact
3. Ensure backwards compatibility

## License

MIT License - Built for personal use and accessibility

## Support

For issues or questions:
- Check documentation in `docs/`
- Review troubleshooting section
- Test in dry-run mode first

## Acknowledgments

Built for accessibility and independence. Inspired by the need to make grocery shopping accessible to everyone, regardless of typing ability.

---

**Accessibility is not a feature - it's a requirement.**

**Voice → Cart → Delivered. Zero typing required.**
