#!/usr/bin/env python3
"""Screenshot analysis utilities for macOS using OCR + LLaVA (Ollama)."""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Union


@dataclass
class AnalysisResult:
    """Structured result for auth-element detection."""

    has_auth_form: bool
    confidence: float
    detected_elements: List[str] = field(default_factory=list)
    ocr_text: str = ""
    llava_response: str = ""


class ScreenshotAnalyzer:
    """Capture and analyze screenshots for authentication UI elements."""

    def __init__(
        self,
        llava_model: str = "llava",
        ollama_host: str = "http://localhost:11434",
        request_timeout_sec: float = 30.0,
    ) -> None:
        self.llava_model = llava_model
        self.ollama_host = ollama_host.rstrip("/")
        self.request_timeout_sec = request_timeout_sec

    def capture_screenshot(self, region: Optional[Union[str, Sequence[int]]] = None) -> str:
        """Capture a screenshot and return the image path."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"screenshot_{timestamp}.png"
        output_path = Path(tempfile.gettempdir()) / filename

        cmd = ["screencapture", "-x"]

        if region is not None:
            region_arg = self._normalize_region(region)
            cmd.extend(["-R", region_arg])

        cmd.append(str(output_path))

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("macOS 'screencapture' command not found.") from exc

        if result.returncode != 0:
            raise RuntimeError(
                "Failed to capture screenshot: "
                f"exit={result.returncode}, stderr={result.stderr.strip()}"
            )

        if not output_path.exists():
            raise RuntimeError("Screenshot command succeeded but file was not created.")

        return str(output_path)

    @staticmethod
    def _normalize_region(region: Union[str, Sequence[int]]) -> str:
        """Normalize region input for `screencapture -R`."""
        if isinstance(region, str):
            if not re.match(r"^\d+,\d+,\d+,\d+$", region.strip()):
                raise ValueError("Region string must be formatted as 'x,y,w,h'.")
            return region.strip()

        if isinstance(region, (list, tuple)):
            if len(region) != 4:
                raise ValueError("Region sequence must be length 4: (x, y, w, h).")
            if not all(isinstance(x, int) and x >= 0 for x in region):
                raise ValueError("Region values must be non-negative integers.")
            return ",".join(str(x) for x in region)

        raise ValueError("Unsupported region type; use None, string, or 4-int sequence.")

    def encode_image(self, image_path: str) -> str:
        """Base64-encode the image at the given path."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            data = path.read_bytes()
        except OSError as exc:
            raise RuntimeError(f"Failed to read image: {image_path}") from exc

        return base64.b64encode(data).decode("utf-8")

    def analyze_with_llava(self, image_path: str, prompt: str) -> str:
        """Analyze an image using a local Ollama LLaVA model."""
        image_b64 = self.encode_image(image_path)
        url = f"{self.ollama_host}/api/generate"

        payload = {
            "model": self.llava_model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout_sec) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Unable to connect to Ollama at "
                f"{self.ollama_host}. Is Ollama running?"
            ) from exc
        except TimeoutError as exc:
            raise RuntimeError("Ollama request timed out.") from exc

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "response" in parsed:
                return str(parsed.get("response", "")).strip()
        except json.JSONDecodeError:
            pass

        lines = [line for line in raw.splitlines() if line.strip()]
        responses: List[str] = []
        for line in lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "response" in obj:
                    responses.append(str(obj.get("response", "")))
            except json.JSONDecodeError:
                continue

        if responses:
            return "".join(responses).strip()

        raise RuntimeError("Unexpected response from Ollama LLaVA endpoint.")

    def extract_text_ocr(self, image_path: str) -> str:
        """Extract text from the image using tesseract OCR."""
        if shutil.which("tesseract") is None:
            raise RuntimeError(
                "tesseract not found in PATH. Install with: brew install tesseract"
            )

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_base = Path(tmpdir) / "ocr_output"
            cmd = ["tesseract", str(path), str(out_base), "-l", "eng"]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "tesseract OCR failed: "
                    f"exit={result.returncode}, stderr={result.stderr.strip()}"
                )

            out_txt = out_base.with_suffix(".txt")
            if not out_txt.exists():
                return ""
            return out_txt.read_text(encoding="utf-8", errors="replace").strip()

    def detect_auth_elements(self, image_path: str) -> AnalysisResult:
        """Detect authentication UI elements using OCR + LLaVA."""
        ocr_text = ""
        llava_response = ""

        try:
            ocr_text = self.extract_text_ocr(image_path)
        except Exception as exc:  # noqa: BLE001 - we want resilient analysis
            ocr_text = f"[OCR_ERROR] {exc}"

        prompt = (
            "You are analyzing a screenshot for authentication UI elements. "
            "List any login/auth-related elements you can see, such as username/email "
            "fields, password fields, sign-in buttons, MFA/OTP prompts, or "
            "account creation links. If none are visible, say 'none'."
        )
        try:
            llava_response = self.analyze_with_llava(image_path, prompt)
        except Exception as exc:  # noqa: BLE001 - resilient analysis
            llava_response = f"[LLAVA_ERROR] {exc}"

        detected_elements = self._extract_auth_elements(ocr_text, llava_response)
        confidence = self._score_confidence(detected_elements, ocr_text, llava_response)
        has_auth_form = confidence >= 0.55 and len(detected_elements) > 0

        return AnalysisResult(
            has_auth_form=has_auth_form,
            confidence=confidence,
            detected_elements=detected_elements,
            ocr_text=ocr_text,
            llava_response=llava_response,
        )

    @staticmethod
    def _extract_auth_elements(ocr_text: str, llava_text: str) -> List[str]:
        """Extract auth-related elements from OCR and LLaVA responses."""
        keywords = {
            "username": ["username", "user name", "userid", "user id"],
            "email": ["email", "e-mail"],
            "password": ["password", "passcode"],
            "sign_in": ["sign in", "log in", "login", "sign-in", "log-in"],
            "sign_up": ["sign up", "create account", "register"],
            "forgot_password": ["forgot password", "reset password"],
            "mfa": ["mfa", "2fa", "two-factor", "verification code", "otp"],
            "remember_me": ["remember me", "keep me signed in"],
            "auth": ["authenticate", "authentication", "authorization"],
        }

        haystack = f"{ocr_text}\n{llava_text}".lower()
        found: List[str] = []
        for label, terms in keywords.items():
            if any(term in haystack for term in terms):
                found.append(label)

        return found

    @staticmethod
    def _score_confidence(
        detected: List[str],
        ocr_text: str,
        llava_text: str,
    ) -> float:
        """Compute a confidence score from signals."""
        score = 0.0

        if detected:
            score += min(0.6, 0.1 * len(detected))

        strong_terms = ["password", "sign in", "log in", "login", "otp", "verification code"]
        if any(term in ocr_text.lower() for term in strong_terms):
            score += 0.25

        if any(term in llava_text.lower() for term in strong_terms):
            score += 0.20

        if "[OCR_ERROR]" in ocr_text:
            score -= 0.10
        if "[LLAVA_ERROR]" in llava_text:
            score -= 0.10

        return max(0.0, min(1.0, score))
