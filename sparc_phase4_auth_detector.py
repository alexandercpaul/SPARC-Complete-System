#!/usr/bin/env python3
"""SPARC Phase 4 authentication detection utilities.

This module detects local authentication status for 1Password and browser
sessions using CLI checks and an optional macOS screenshot capture. It is
intended to be production-ready with robust error handling, logging, and
clear typing.

Functions:
- detect_1password_auth() -> bool
- check_cli_session() -> bool
- check_browser_session() -> bool
- screenshot_auth_detection() -> str
- get_confidence_score() -> float
- analyze_auth_status() -> AuthStatus
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple, Optional, Tuple


LOGGER = logging.getLogger(__name__)


class AuthStatus(NamedTuple):
    """Container for authentication analysis results.

    Attributes:
        is_authenticated: True if authentication is detected.
        confidence_score: Confidence in detection, normalized to 0.0-1.0.
        detected_method: Text description of the detection mechanism.
    """

    is_authenticated: bool
    confidence_score: float
    detected_method: str


class _CommandResult(NamedTuple):
    """Lightweight result wrapper for subprocess execution."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_command(command: Tuple[str, ...], timeout: float = 8.0) -> _CommandResult:
    """Run a command safely with logging and error handling.

    Args:
        command: Command tuple to execute.
        timeout: Seconds before raising a timeout.

    Returns:
        _CommandResult capturing stdout, stderr, and return code.
    """

    LOGGER.debug("Executing command: %s", " ".join(shlex.quote(c) for c in command))
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout = proc.stdout.strip() if proc.stdout else ""
        stderr = proc.stderr.strip() if proc.stderr else ""
        ok = proc.returncode == 0
        LOGGER.debug(
            "Command completed: ok=%s returncode=%s stdout_len=%s stderr_len=%s",
            ok,
            proc.returncode,
            len(stdout),
            len(stderr),
        )
        return _CommandResult(ok=ok, stdout=stdout, stderr=stderr, returncode=proc.returncode)
    except subprocess.TimeoutExpired as exc:
        LOGGER.debug("Command timeout: %s", exc)
        return _CommandResult(ok=False, stdout="", stderr="timeout", returncode=124)
    except FileNotFoundError as exc:
        LOGGER.debug("Command not found: %s", exc)
        return _CommandResult(ok=False, stdout="", stderr="not found", returncode=127)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.debug("Command execution error: %s", exc, exc_info=True)
        return _CommandResult(ok=False, stdout="", stderr=str(exc), returncode=1)


def _binary_exists(binary_name: str) -> bool:
    """Check if a binary is available on PATH."""

    result = _run_command(("/usr/bin/which", binary_name))
    return result.ok and bool(result.stdout)


def _safe_float(value: float) -> float:
    """Clamp a float to the 0.0-1.0 range."""

    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_1password_auth() -> bool:
    """Detect whether the 1Password CLI has an authenticated account.

    This checks `op account list` and verifies that at least one account is
    returned. It is conservative and returns False on errors.

    Returns:
        True if at least one account is detected via 1Password CLI.
    """

    if not _binary_exists("op"):
        LOGGER.debug("1Password CLI not found on PATH")
        return False

    result = _run_command(("op", "account", "list"))
    if not result.ok:
        LOGGER.debug("1Password CLI check failed: %s", result.stderr)
        return False

    # Heuristic: output should contain at least one non-empty line.
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    LOGGER.debug("1Password account list lines: %s", len(lines))
    return len(lines) > 0


def check_cli_session() -> bool:
    """Check for an active CLI session.

    For 1Password, a successful account list implies an active session.
    This function is separate to allow extension to other CLI tools.

    Returns:
        True if a CLI session is detected.
    """

    return detect_1password_auth()


def check_browser_session() -> bool:
    """Check for an authenticated browser session.

    This is a heuristic check that looks for common browser profile data
    indicative of a logged-in state. It is intentionally conservative and
    should return False if uncertain.

    Returns:
        True if a likely authenticated browser session is detected.
    """

    # Heuristic: existence of Chrome/Safari profile directories.
    # This is not definitive, so we keep it conservative.
    try:
        home = Path.home()
        chrome_profile = home / "Library" / "Application Support" / "Google" / "Chrome"
        safari_profile = home / "Library" / "Safari"
        firefox_profile = home / "Library" / "Application Support" / "Firefox"

        indicators = [chrome_profile, safari_profile, firefox_profile]
        existing = [p for p in indicators if p.exists()]
        LOGGER.debug("Browser profile paths found: %s", [str(p) for p in existing])

        # Require at least one profile directory with some data.
        for path in existing:
            if path.is_dir():
                # Count entries to avoid empty placeholder directories.
                try:
                    entries = list(path.iterdir())
                except PermissionError:
                    LOGGER.debug("Permission error reading: %s", path)
                    continue
                if len(entries) > 0:
                    return True
        return False
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.debug("Browser session check error: %s", exc, exc_info=True)
        return False


def screenshot_auth_detection() -> str:
    """Capture a macOS screenshot for manual authentication review.

    Uses the `screencapture` utility. If unavailable or capture fails,
    returns an empty string.

    Returns:
        The filesystem path to the saved screenshot, or "" on failure.
    """

    if os.uname().sysname != "Darwin":
        LOGGER.debug("screencapture only supported on macOS")
        return ""

    if not _binary_exists("screencapture"):
        LOGGER.debug("screencapture binary not found")
        return ""

    try:
        temp_dir = Path(tempfile.gettempdir())
        screenshot_path = temp_dir / "sparc_phase4_auth_screenshot.png"
        result = _run_command(("screencapture", "-x", str(screenshot_path)))
        if not result.ok:
            LOGGER.debug("screencapture failed: %s", result.stderr)
            return ""
        if screenshot_path.exists():
            return str(screenshot_path)
        return ""
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.debug("screencapture error: %s", exc, exc_info=True)
        return ""


def get_confidence_score() -> float:
    """Compute a confidence score for authentication detection.

    The score is based on a weighted combination of CLI and browser signals.
    This function is intentionally simple and deterministic.

    Returns:
        Float between 0.0 and 1.0 indicating confidence.
    """

    cli = check_cli_session()
    browser = check_browser_session()

    # Weight CLI higher than browser.
    score = 0.0
    if cli:
        score += 0.7
    if browser:
        score += 0.3

    return _safe_float(score)


def analyze_auth_status() -> AuthStatus:
    """Analyze authentication status and return structured results.

    Returns:
        AuthStatus containing is_authenticated, confidence_score, and
        detected_method.
    """

    cli = check_cli_session()
    browser = check_browser_session()
    confidence = _safe_float((0.7 if cli else 0.0) + (0.3 if browser else 0.0))

    if cli and browser:
        method = "cli+browser"
        is_authed = True
    elif cli:
        method = "cli"
        is_authed = True
    elif browser:
        method = "browser"
        # Browser-only signal is weaker but still indicates likely auth.
        is_authed = True
    else:
        method = "none"
        is_authed = False

    return AuthStatus(is_authenticated=is_authed, confidence_score=confidence, detected_method=method)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    status = analyze_auth_status()
    print(status)
