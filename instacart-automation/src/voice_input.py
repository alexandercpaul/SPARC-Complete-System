#!/usr/bin/env python3
"""
Voice Input Handler for Instacart Automation
Supports both macOS native dictation and OpenAI Whisper
"""

import subprocess
import os
import tempfile
import time
from pathlib import Path
from typing import Optional
import pyaudio
import wave


class VoiceInputHandler:
    """Handles voice input via macOS dictation or Whisper"""

    def __init__(self, method: str = "macos"):
        """
        Initialize voice input handler

        Args:
            method: 'macos' for native dictation or 'whisper' for OpenAI Whisper
        """
        self.method = method
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024

    def record_audio(self, duration: int = 5) -> Path:
        """
        Record audio from microphone

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded WAV file
        """
        print(f"🎤 Recording for {duration} seconds...")

        audio = pyaudio.PyAudio()

        # Open audio stream
        stream = audio.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        frames = []

        # Record audio
        for i in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        # Stop recording
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save to temporary file
        temp_file = Path(tempfile.gettempdir()) / f"voice_input_{int(time.time())}.wav"

        with wave.open(str(temp_file), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))

        print(f"✅ Audio saved to {temp_file}")
        return temp_file

    def transcribe_macos(self, audio_file: Path) -> str:
        """
        Transcribe using macOS native dictation (requires Automator or AppleScript)

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        # macOS doesn't have CLI dictation, so we use a workaround
        # This triggers dictation via AppleScript keyboard simulation

        applescript = f'''
        tell application "System Events"
            -- Press fn key twice to activate dictation
            key code 63
            delay 0.5
            key code 63
            delay 2
        end tell
        '''

        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            print("⏳ Waiting for macOS dictation to process...")
            time.sleep(5)  # Wait for dictation to complete

            # Get clipboard content (dictation usually places text there)
            result = subprocess.run(
                ['pbpaste'],
                capture_output=True,
                text=True,
                check=True
            )

            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ macOS dictation failed: {e}")
            return ""

    def transcribe_whisper(self, audio_file: Path) -> str:
        """
        Transcribe using OpenAI Whisper

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        try:
            import whisper

            print("⏳ Loading Whisper model...")
            model = whisper.load_model("base")

            print("⏳ Transcribing audio...")
            result = model.transcribe(str(audio_file))

            return result["text"].strip()
        except ImportError:
            print("❌ Whisper not installed. Install with: pip install openai-whisper")
            return ""
        except Exception as e:
            print(f"❌ Whisper transcription failed: {e}")
            return ""

    def get_voice_input(self, duration: int = 5) -> str:
        """
        Get voice input and transcribe it

        Args:
            duration: Recording duration in seconds

        Returns:
            Transcribed text
        """
        print(f"\n{'='*60}")
        print("🎤 VOICE INPUT MODE")
        print(f"{'='*60}")
        print(f"Method: {self.method}")
        print(f"Duration: {duration}s")
        print(f"{'='*60}\n")

        # Record audio
        audio_file = self.record_audio(duration)

        # Transcribe based on method
        if self.method == "macos":
            text = self.transcribe_macos(audio_file)
        elif self.method == "whisper":
            text = self.transcribe_whisper(audio_file)
        else:
            print(f"❌ Unknown method: {self.method}")
            return ""

        print(f"\n{'='*60}")
        print(f"📝 Transcribed: {text}")
        print(f"{'='*60}\n")

        # Cleanup
        try:
            audio_file.unlink()
        except:
            pass

        return text

    def get_text_input(self, prompt: str = "Enter grocery list: ") -> str:
        """
        Fallback: Get text input directly (for testing/accessibility)

        Args:
            prompt: Input prompt

        Returns:
            User input text
        """
        return input(prompt).strip()


def test_voice_input():
    """Test voice input functionality"""
    handler = VoiceInputHandler(method="whisper")  # or "macos"

    print("\n🎯 Testing Voice Input Handler")
    print("Speak your grocery list when recording starts...")

    text = handler.get_voice_input(duration=5)

    if text:
        print(f"✅ Success! Got: {text}")
    else:
        print("❌ Failed to get voice input")


if __name__ == "__main__":
    test_voice_input()
