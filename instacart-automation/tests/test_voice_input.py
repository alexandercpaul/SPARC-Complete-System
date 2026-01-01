#!/usr/bin/env python3
"""
Tests for voice input handler
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_input import VoiceInputHandler


class TestVoiceInputHandler:
    """Test voice input functionality"""

    def test_init_macos(self):
        """Test macOS initialization"""
        handler = VoiceInputHandler(method="macos")
        assert handler.method == "macos"

    def test_init_whisper(self):
        """Test Whisper initialization"""
        handler = VoiceInputHandler(method="whisper")
        assert handler.method == "whisper"

    def test_text_input(self):
        """Test text input fallback"""
        handler = VoiceInputHandler()
        # This would require user input, so just test the method exists
        assert callable(handler.get_text_input)

    def test_record_audio_setup(self):
        """Test audio recording setup"""
        handler = VoiceInputHandler()
        assert handler.audio_format is not None
        assert handler.channels == 1
        assert handler.rate == 16000
        assert handler.chunk == 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
