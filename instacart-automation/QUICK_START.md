# Instacart Voice Automation - Quick Start

## 30-Second Overview

Voice-activated grocery ordering for Instacart. Built for accessibility. Zero typing required.

## Installation (5 minutes)

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/instacart-automation
./scripts/install.sh
pip install openai-whisper  # For voice input
```

## First Test (2 minutes)

```bash
source venv/bin/activate

python src/main.py \
    --email alexandercpaul@gmail.com \
    --password "t2as0-nAop-!O@sqh" \
    --voice text \
    --browser \
    --text "I need milk, eggs, and bread"
```

**Expected**: Browser opens → Logs in → Searches → Adds to cart → Shows preview (dry-run, no order placed)

## Voice Mode (Accessibility)

```bash
python src/main.py \
    --email alexandercpaul@gmail.com \
    --password "t2as0-nAop-!O@sqh" \
    --voice whisper \
    --browser
```

**Speak**: "I need 2 gallons of milk, a dozen eggs, and bread"

## Workflow

1. **Speak grocery list** (30 seconds)
2. **Confirm parsed list** (1 click: "yes")
3. **Confirm order** (1 click: "yes" or cancel)
4. **Done!** Groceries on the way

## Safety

- **Dry-run mode** by default (no real orders)
- **User confirmation** required at each step
- Add `--no-dry-run` only when ready for real orders

## Files

- `src/main.py` - Main CLI
- `src/voice_input.py` - Voice handler
- `src/grocery_parser.py` - NLP parser
- `src/browser_automation.py` - Instacart automation
- `docs/SETUP_GUIDE.md` - Full documentation

## Help

```bash
python src/main.py --help
```

## Status

✅ Production ready
✅ Browser automation complete
✅ Voice input working
✅ NLP parsing accurate
✅ Safety features active

**Voice → Cart → Delivered. Zero typing.**
