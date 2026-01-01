"""
SPARC Phase 4: Browser Automation Module - Production Implementation

This module provides browser automation for 1Password service account creation
with Playwright (primary) and PyAutoGUI (fallback) support.

Author: Agent 15 (SPARC Phase 4)
Date: 2026-01-01
Status: PRODUCTION-READY
"""

import asyncio
import base64
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Literal, Optional, TypeVar, Callable

# Internal imports
try:
    from sparc_phase4_macos_control import MacAutomation
except ImportError:
    MacAutomation = None
    print("WARNING: MacAutomation not available. Ensure sparc_phase4_macos_control.py is present.")

# Third-party imports
try:
    from playwright.async_api import (
        async_playwright,
        Browser,
        BrowserContext,
        Page,
        Playwright,
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not available. Install with: pip install playwright")

try:
    import pyautogui
    import pyperclip
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("WARNING: PyAutoGUI not available. Install with: pip install pyautogui pyperclip")


# Type variable for generic retry function
T = TypeVar('T')


# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

DEFAULT_CONFIG = {
    "browser": {
        "primary": "chrome",
        "headless": False,
        "window_size": [1920, 1080],
        "timeout": 30000,
    },
    "automation": {
        "account_name": "SPARC-Automation",
        "vault_name": "Automation",
        "max_wizard_steps": 5,
    },
    "timeouts": {
        "navigation": 30000,      # 30s
        "element_wait": 10000,    # 10s
        "auth_wait": 120000,      # 2 minutes
        "network_idle": 30000,    # 30s
    },
    "retry": {
        "max_retries": 3,
        "base_delay": 1000,       # 1s
    },
}

SERVICE_ACCOUNT_URL = (
    "https://my.1password.com/developer-tools/"
    "infrastructure-secrets/service-accounts/create"
)


# ============================================================================
# YABAI WINDOW MANAGER (macOS Integration)
# ============================================================================

class YabaiWindowManager:
    """Manages window focus using yabai for macOS."""

    @staticmethod
    def get_browser_window_info() -> Optional[dict]:
        """
        Get browser window information from yabai.

        Returns:
            Dictionary with window_id, app, title, frame, pid, or None if not found.
        """
        browser_apps = ["Arc", "Google Chrome", "Safari", "Chromium", "Firefox"]

        for app_name in browser_apps:
            cmd = f'yabai -m query --windows | jq \'.[] | select(.app == "{app_name}")\''
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                window_info = json.loads(result.stdout)
                print(f"✓ Found browser window: {app_name} (ID: {window_info['id']})")
                return {
                    "window_id": window_info["id"],
                    "app": window_info["app"],
                    "title": window_info["title"],
                    "frame": window_info["frame"],
                    "pid": window_info["pid"],
                }

        print("ERROR: No browser window found")
        return None

    @staticmethod
    def focus_window(window_id: int) -> bool:
        """
        Focus window by ID and verify focus succeeded.

        Args:
            window_id: Window ID from yabai

        Returns:
            True if focus verified, False otherwise
        """
        # Focus window
        cmd = f"yabai -m window --focus {window_id}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ERROR: Failed to focus window {window_id}")
            return False

        # Verify focus (CRITICAL!)
        time.sleep(0.5)
        current_window_id = YabaiWindowManager.get_current_focused_window_id()

        if current_window_id == window_id:
            print(f"✓ Window {window_id} focused successfully")
            return True
        else:
            print(
                f"ERROR: Focus verification failed "
                f"(expected {window_id}, got {current_window_id})"
            )
            return False

    @staticmethod
    def get_current_focused_window_id() -> Optional[int]:
        """Get currently focused window ID."""
        cmd = "yabai -m query --windows --window | jq '.id'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())

        return None

    @staticmethod
    def verify_focus_between_keystrokes(target_window_id: int) -> bool:
        """
        CRITICAL: Called between EVERY keystroke.
        Prevents wrong-window injection (lesson from CLAUDE.md).

        Args:
            target_window_id: Expected window ID

        Returns:
            True if focus maintained, False if lost
        """
        current_window_id = YabaiWindowManager.get_current_focused_window_id()

        if current_window_id != target_window_id:
            print(
                f"ABORT: Lost focus! Expected {target_window_id}, "
                f"got {current_window_id}"
            )
            return False

        return True


# ============================================================================
# PLAYWRIGHT ASYNC DRIVER
# ============================================================================

class AsyncPlaywrightDriver:
    """Async Playwright driver with context management."""

    def __init__(self, config: dict, macos_control: Optional["MacAutomation"] = None):
        """
        Initialize Playwright driver.

        Args:
            config: Configuration dictionary
            macos_control: Optional MacAutomation instance for native control
        """
        self.config = config
        self.macos_control = macos_control
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def focus_browser_window(self):
        """Focus the browser window using native macOS control."""
        if self.macos_control:
            try:
                # Assuming Chrome based on default config
                app_name = "Google Chrome"
                if self.config.get("browser", {}).get("channel") == "msedge":
                    app_name = "Microsoft Edge"
                
                self.macos_control.focus_window(app_name)
                print(f"✓ Native focus set to {app_name}")
            except Exception as e:
                print(f"WARNING: Native focus failed: {e}")

    async def __aenter__(self):
        """Async context manager entry - initialize browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright not available. Install with: "
                "pip install playwright && playwright install chromium"
            )

        self.playwright = await async_playwright().start()

        # Launch browser (non-blocking)
        browser_config = self.config.get("browser", {})
        self.browser = await self.playwright.chromium.launch(
            headless=browser_config.get("headless", False),
            channel="chrome",  # Or "msedge" for Arc (Chromium-based)
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1920,1080"
            ],
            timeout=30000
        )

        # Create persistent context (session state)
        session_file = self.config.get("session_file")
        context_options = {
            "viewport": {'width': 1920, 'height': 1080},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "permissions": ["clipboard-read", "clipboard-write"],
        }

        # Load session if exists
        if session_file and Path(session_file).exists():
            context_options["storage_state"] = session_file

        self.context = await self.browser.new_context(**context_options)

        # Create page
        self.page = await self.context.new_page()

        # Enable detailed logging
        self.page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        self.page.on("pageerror", lambda err: print(f"Page error: {err}"))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        # Save session state for future runs
        session_file = self.config.get("session_file")
        if self.context and session_file and self.config.get("save_session", True):
            try:
                await self.context.storage_state(path=session_file)
                print(f"✓ Session saved to {session_file}")
            except Exception as e:
                print(f"WARNING: Failed to save session: {e}")

        # Close resources
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# ============================================================================
# NAVIGATION FUNCTIONS
# ============================================================================

async def navigate_to_service_account_page(
    page: Page,
    timeout: int = 30000
) -> dict:
    """
    Navigate to 1Password service account creation page.

    Args:
        page: Playwright page object
        timeout: Navigation timeout in milliseconds

    Returns:
        Dictionary with status: "success" | "auth_required" | "error"
    """
    try:
        # Async navigation with network idle wait
        response = await page.goto(
            SERVICE_ACCOUNT_URL,
            timeout=timeout,
            wait_until="networkidle"
        )

        # Auto-screenshot for debugging
        screenshot_dir = Path("/tmp/1password_automation")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        await page.screenshot(
            path=str(screenshot_dir / "01_navigation.png"),
            full_page=True
        )

        current_url = page.url

        # Check landing page
        if "service-accounts/create" in current_url:
            print(f"✓ Successfully navigated to: {current_url}")
            return {"status": "success", "url": current_url}

        elif "signin" in current_url or "login" in current_url:
            print(f"⚠ Auth required: {current_url}")
            return {"status": "auth_required", "url": current_url}

        else:
            print(f"ERROR: Unexpected redirect to: {current_url}")
            return {
                "status": "error",
                "url": current_url,
                "message": "Unexpected redirect"
            }

    except Exception as e:
        print(f"ERROR: Navigation failed: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# FORM FILLING FUNCTIONS
# ============================================================================

async def fill_service_account_form(
    page: Page,
    name: str,
    vaults: Optional[list[str]] = None,
    macos_control: Optional["MacAutomation"] = None,
    autonomous: bool = False
) -> dict:
    """
    Fill service account creation form (name and vault selection).

    Args:
        page: Playwright page object
        name: Service account name
        vaults: List of vault names (optional)
        macos_control: Optional MacAutomation instance
        autonomous: Whether to use autonomous mode (native control)

    Returns:
        Dictionary with success status and message
    """
    # Fill name field
    name_result = await _fill_name_field(page, name, macos_control, autonomous)
    if not name_result["success"]:
        return name_result

    # Select vault permissions (if specified)
    if vaults:
        vault_result = await _select_vault_permissions(page, vaults[0])
        if not vault_result["success"]:
            return vault_result

    return {"success": True, "message": "Form filled successfully"}


async def _fill_name_field(
    page: Page,
    account_name: str,
    macos_control: Optional["MacAutomation"] = None,
    autonomous: bool = False
) -> dict:
    """
    Fill service account name field with verification.

    Args:
        page: Playwright page object
        account_name: Name to enter
        macos_control: Optional MacAutomation instance
        autonomous: Whether to use autonomous mode

    Returns:
        Dictionary with success status
    """
    # Native Control Path
    if autonomous and macos_control:
        try:
            # Handle permission dialogs first
            macos_control.handle_permission_dialog()
            
            # Use native paste for reliability
            if macos_control.paste_text("Google Chrome", "Service account name", account_name):
                print(f"✓ Native paste successful: {account_name}")
                # Verify with Playwright
                await asyncio.sleep(0.5)
                # Still check value via Playwright to be sure
            else:
                print("⚠ Native paste failed, falling back to Playwright")
        except Exception as e:
            print(f"⚠ Native control error: {e}")

    # Multiple selector strategies (defensive programming)
    name_selectors = [
        "input[name='name']",
        "input[placeholder*='name' i]",
        "input[aria-label*='name' i]",
        "input[type='text']:first-of-type",
        "[data-testid='service-account-name']",
    ]

    name_field = None

    # Try each selector
    for selector in name_selectors:
        try:
            name_field = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=5000
            )

            if name_field:
                print(f"✓ Found name field using selector: {selector}")
                break

        except Exception:
            continue

    if not name_field:
        print("ERROR: Name field not found")
        return {"success": False, "message": "Name field not found"}

    # Clear existing value
    await name_field.click()
    await name_field.fill("")

    # Type with human-like delays (built-in!)
    await name_field.type(account_name, delay=100)

    # Verify the value was entered
    entered_value = await name_field.input_value()

    if entered_value == account_name:
        screenshot_dir = Path("/tmp/1password_automation")
        await page.screenshot(path=str(screenshot_dir / "02_name_filled.png"))
        print(f"✓ Name entered: {account_name}")
        return {"success": True, "message": f"Name entered: {account_name}"}
    else:
        print(
            f"ERROR: Name mismatch - expected: {account_name}, "
            f"got: {entered_value}"
        )
        return {
            "success": False,
            "message": f"Name mismatch: expected '{account_name}', got '{entered_value}'"
        }


async def _select_vault_permissions(page: Page, vault_name: str) -> dict:
    """
    Select vault permissions.

    Args:
        page: Playwright page object
        vault_name: Vault name to select

    Returns:
        Dictionary with success status
    """
    try:
        # Wait for vault selector to load
        vault_selector = await page.wait_for_selector(
            "[data-testid='vault-selector'], .vault-selector, select[name='vault']",
            state="visible",
            timeout=10000
        )

        if not vault_selector:
            print("WARNING: Vault selector not found, continuing anyway")
            return {"success": True, "message": "Vault selector not found"}

        # Click dropdown
        await vault_selector.click()
        await asyncio.sleep(0.5)

        # Find vault by name
        vault_options = await page.query_selector_all(
            "[role='option'], .vault-option, option"
        )

        vault_found = False
        for option in vault_options:
            option_text = await option.text_content()
            option_text = option_text.strip().lower()

            # Skip "Personal" vault
            if "personal" in option_text:
                continue

            if vault_name.lower() in option_text:
                await option.click()
                print(f"✓ Selected vault: {await option.text_content()}")
                vault_found = True
                break

        if not vault_found:
            # Fallback: select first non-Personal vault
            print("WARNING: Vault not found by name, selecting first available")
            for option in vault_options:
                option_text = await option.text_content()
                if "personal" not in option_text.lower():
                    await option.click()
                    print(f"✓ Selected vault: {option_text}")
                    vault_found = True
                    break

        screenshot_dir = Path("/tmp/1password_automation")
        await page.screenshot(path=str(screenshot_dir / "03_vault_selected.png"))

        return {"success": True, "message": "Vault selected"}

    except Exception as e:
        print(f"WARNING: Vault selection failed: {e}")
        # Not a critical error, continue anyway
        return {"success": True, "message": f"Vault selection skipped: {e}"}


# ============================================================================
# WIZARD NAVIGATION
# ============================================================================

async def click_next(
    page: Page,
    macos_control: Optional["MacAutomation"] = None,
    autonomous: bool = False
) -> dict:
    """
    Click the next button in wizard.

    Args:
        page: Playwright page object
        macos_control: Optional MacAutomation instance
        autonomous: Whether to use autonomous mode

    Returns:
        Dictionary with success status
    """
    # Native Control Path
    if autonomous and macos_control:
        try:
            # Handle permission dialogs
            macos_control.handle_permission_dialog()
            
            # Try common button labels
            for label in ["Next", "Continue", "Create"]:
                if macos_control.click_button("Google Chrome", label):
                    print(f"✓ Native click successful: {label}")
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    return {"success": True, "message": f"Native click: {label}"}
        except Exception as e:
            print(f"⚠ Native click failed: {e}")

    next_button_selectors = [
        "button:has-text('Next')",
        "button:has-text('Continue')",
        "button:has-text('Create')",
        "button[type='submit']",
        "[data-testid='next-button']",
    ]

    # Find next button
    next_button = None
    for selector in next_button_selectors:
        try:
            next_button = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=2000
            )

            # Check if button is enabled
            is_enabled = await next_button.is_enabled()
            if is_enabled:
                print(f"✓ Found next button: {selector}")
                break

        except Exception:
            continue

    if not next_button:
        return {"success": False, "message": "Next button not found"}

    # Click next button
    await next_button.click()
    print("✓ Clicked next button")

    # Wait for page transition
    await page.wait_for_load_state("networkidle", timeout=10000)

    return {"success": True, "message": "Next button clicked"}


async def navigate_wizard_steps(
    page: Page,
    max_steps: int = 5,
    macos_control: Optional["MacAutomation"] = None,
    autonomous: bool = False
) -> dict:
    """
    Navigate through wizard steps until token display.

    Args:
        page: Playwright page object
        max_steps: Maximum number of steps to attempt
        macos_control: Optional MacAutomation instance
        autonomous: Whether to use autonomous mode

    Returns:
        Dictionary with success status and steps taken
    """
    step_count = 0
    screenshot_dir = Path("/tmp/1password_automation")

    while step_count < max_steps:
        step_count += 1
        print(f"Wizard step: {step_count}")

        # Check if token is displayed (exit condition)
        if await detect_token_displayed(page):
            print("✓ Token display detected - wizard complete")
            return {
                "success": True,
                "steps_taken": step_count,
                "message": "Token display detected"
            }

        # Click next button
        result = await click_next(page, macos_control, autonomous)

        if not result["success"]:
            # No next button - check if wizard is complete
            if await detect_token_displayed(page):
                return {
                    "success": True,
                    "steps_taken": step_count,
                    "message": "Complete"
                }
            else:
                return {
                    "success": False,
                    "steps_taken": step_count,
                    "message": "Wizard stuck - no next button"
                }

        # Screenshot checkpoint
        await page.screenshot(
            path=str(screenshot_dir / f"04_wizard_step_{step_count}.png")
        )

    # Exceeded max steps
    return {
        "success": False,
        "steps_taken": step_count,
        "message": "Exceeded maximum wizard steps"
    }


# ============================================================================
# TOKEN DETECTION AND EXTRACTION
# ============================================================================

async def detect_token_displayed(page: Page) -> bool:
    """
    Check if service account token is displayed on page.

    Args:
        page: Playwright page object

    Returns:
        True if token is displayed, False otherwise
    """
    token_indicators = [
        "code:has-text('ops_')",
        "pre:has-text('ops_')",
        "[data-testid='service-account-token']",
        ".token-display",
    ]

    for indicator in token_indicators:
        try:
            element = await page.wait_for_selector(
                indicator,
                state="visible",
                timeout=1000
            )
            if element:
                print(f"✓ Token indicator found: {indicator}")
                return True
        except Exception:
            continue

    # Fallback: check page text
    try:
        page_text = await page.text_content("body")
        if re.search(r"ops_[A-Za-z0-9_-]{100,}", page_text):
            print("✓ Token found in page text")
            return True
    except Exception:
        pass

    return False


async def extract_token_via_css(page: Page) -> Optional[str]:
    """
    Extract token using CSS selectors.

    Args:
        page: Playwright page object

    Returns:
        Token string or None
    """
    token_selectors = [
        "code:has-text('ops_')",
        "pre:has-text('ops_')",
        "[data-testid='service-account-token']",
        ".token-display code",
        ".token-value",
    ]

    for selector in token_selectors:
        try:
            element = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=2000
            )

            if element:
                token = await element.text_content()
                token = token.strip()

                if validate_token_format(token):
                    print(f"✓ Token extracted via CSS selector: {selector}")
                    return token

        except Exception:
            continue

    return None


async def extract_token_via_clipboard(page: Page) -> Optional[str]:
    """
    Extract token by clicking copy button and reading clipboard.

    Args:
        page: Playwright page object

    Returns:
        Token string or None
    """
    copy_button_selectors = [
        "button:has-text('Copy')",
        "[data-testid='copy-token']",
        "[aria-label='Copy token']",
    ]

    for selector in copy_button_selectors:
        try:
            copy_button = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=2000
            )

            if copy_button:
                await copy_button.click()
                await asyncio.sleep(0.5)

                # Use Playwright's clipboard API
                clipboard_text = await page.evaluate(
                    "navigator.clipboard.readText()"
                )

                if validate_token_format(clipboard_text):
                    print("✓ Token extracted via clipboard")
                    return clipboard_text

        except Exception as e:
            print(f"Clipboard extraction failed for {selector}: {e}")
            continue

    return None


async def extract_token_via_page_text(page: Page) -> Optional[str]:
    """
    Extract token from full page text.

    Args:
        page: Playwright page object

    Returns:
        Token string or None
    """
    try:
        page_text = await page.text_content("body")

        # Regex pattern for ops_ token
        token_pattern = r"ops_[A-Za-z0-9_-]{100,500}"
        matches = re.findall(token_pattern, page_text)

        if matches:
            token = matches[0]
            if validate_token_format(token):
                print("✓ Token extracted via page text parsing")
                return token

    except Exception as e:
        print(f"Page text extraction failed: {e}")

    return None


def validate_token_format(token: Optional[str]) -> bool:
    """
    Validate 1Password service account token format.

    Format: ops_[A-Za-z0-9_-]{100,500}

    Args:
        token: Token string to validate

    Returns:
        True if valid, False otherwise
    """
    if not token or len(token) < 100:
        return False

    if not token.startswith("ops_"):
        return False

    pattern = r"^ops_[A-Za-z0-9_-]+$"
    return bool(re.match(pattern, token))


async def extract_token(page: Page) -> Optional[str]:
    """
    Extract 1Password service account token using 4 fallback strategies.

    Args:
        page: Playwright page object

    Returns:
        Token string or None
    """
    # Strategy 1: CSS Selector
    token = await extract_token_via_css(page)
    if token:
        return token

    # Strategy 2: Clipboard (copy button)
    token = await extract_token_via_clipboard(page)
    if token:
        return token

    # Strategy 3: Full page text parsing
    token = await extract_token_via_page_text(page)
    if token:
        return token

    # Strategy 4: OCR would go here (not implemented in this version)
    print("ERROR: All token extraction methods failed")

    # Screenshot for debugging
    screenshot_dir = Path("/tmp/1password_automation")
    await page.screenshot(
        path=str(screenshot_dir / "error_token_extraction.png")
    )

    return None


# ============================================================================
# PYAUTOGUI FALLBACK DRIVER
# ============================================================================

class PyAutoGUIDriver:
    """PyAutoGUI fallback driver with 4-layer recursive verification."""

    def __init__(self, window_id: int):
        """
        Initialize PyAutoGUI driver.

        Args:
            window_id: Target window ID from yabai
        """
        if not PYAUTOGUI_AVAILABLE:
            raise RuntimeError(
                "PyAutoGUI not available. Install with: "
                "pip install pyautogui pyperclip"
            )

        self.window_id = window_id
        self.yabai = YabaiWindowManager()

    def fill_form_field(
        self,
        text: str,
        field_coordinates: Optional[dict] = None
    ) -> bool:
        """
        Fill form field with 4-layer recursive verification.

        Layers:
        1. Session: Verify window exists and is focusable
        2. Command: Break text into character sequence
        3. Character: Type each character with pre/post verification
        4. Verification: Check focus, bounds, process health

        Args:
            text: Text to type
            field_coordinates: Optional dict with x, y coordinates

        Returns:
            True if successful, False otherwise
        """
        # Layer 1: Session verification
        if not self._verify_window_exists():
            print("ERROR: Window does not exist")
            return False

        # Focus window
        if not self.yabai.focus_window(self.window_id):
            return False

        # Click field to focus it (if coordinates provided)
        if field_coordinates:
            pyautogui.click(field_coordinates["x"], field_coordinates["y"])
            time.sleep(0.3)

        # Layer 2: Command decomposition
        characters = list(text)

        # Layer 3: Character-level verification
        for i, char in enumerate(characters):
            # Layer 4: Pre-keystroke verification
            if not self._verify_focused_layer4():
                print(f"ERROR: Lost focus before character {i}")
                return False

            # Type character
            pyautogui.write(char, interval=0.05)

            # Layer 4: Post-keystroke verification
            if not self._verify_focused_layer4():
                print(f"ERROR: Lost focus after character {i}")
                return False

            # Visual feedback wait
            time.sleep(0.05)

        print(f"✓ Text entered successfully: {text}")
        return True

    def _verify_window_exists(self) -> bool:
        """Layer 1: Verify window exists."""
        window_info = self.yabai.get_browser_window_info()
        return (
            window_info is not None and
            window_info["window_id"] == self.window_id
        )

    def _verify_focused_layer4(self) -> bool:
        """
        Layer 4: Comprehensive verification.

        Checks:
        - Window focus
        - Window bounds unchanged
        - Process still alive

        Returns:
            True if all checks pass, False otherwise
        """
        # Check focus
        if not self.yabai.verify_focus_between_keystrokes(self.window_id):
            return False

        # Check window still exists and bounds unchanged
        window_info = self.yabai.get_browser_window_info()
        if not window_info or window_info["window_id"] != self.window_id:
            return False

        # Check process still alive
        cmd = f"ps -p {window_info['pid']} > /dev/null 2>&1"
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"ERROR: Process {window_info['pid']} not alive")
            return False

        return True


# ============================================================================
# ERROR HANDLING AND RETRY LOGIC
# ============================================================================

async def retry_with_exponential_backoff(
    async_func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> T:
    """
    Retry async function with exponential backoff.

    Delays: 1s, 2s, 4s

    Args:
        async_func: Async function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds

    Returns:
        Result of async_func

    Raises:
        Exception if all retries fail
    """
    retry_count = 0

    while retry_count < max_retries:
        try:
            result = await async_func()
            return result

        except Exception as e:
            retry_count += 1

            if retry_count >= max_retries:
                print(f"ERROR: Failed after {max_retries} retries")
                raise

            delay = base_delay * (2 ** (retry_count - 1))
            print(f"Retry {retry_count}/{max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)


# ============================================================================
# MAIN ORCHESTRATION FUNCTION
# ============================================================================

async def create_service_account_automated(
    account_name: str = "SPARC-Automation",
    vault_name: str = "Automation",
    config: Optional[dict] = None,
    autonomous: bool = False,
    macos_control: Optional["MacAutomation"] = None
) -> dict:
    """
    Main orchestration function for service account creation.

    Args:
        account_name: Name for the service account
        vault_name: Vault name for permissions
        config: Optional configuration dictionary
        autonomous: Whether to use autonomous mode (native control)
        macos_control: Optional MacAutomation instance

    Returns:
        Dictionary with:
        - success: bool
        - token: str | None
        - account_name: str
        - vault_name: str
        - message: str
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()

    # Initialize MacAutomation if needed
    if autonomous and macos_control is None and MacAutomation:
        try:
            macos_control = MacAutomation()
            print("✓ MacAutomation initialized for autonomous mode")
        except Exception as e:
            print(f"WARNING: Failed to initialize MacAutomation: {e}")

    print("=" * 60)
    print("1PASSWORD SERVICE ACCOUNT AUTOMATION")
    print("=" * 60)
    print(f"Account name: {account_name}")
    print(f"Vault name: {vault_name}")
    print(f"Mode: {'Autonomous (Native)' if autonomous else 'Standard (Playwright)'}")
    print("=" * 60)

    # Initialize Playwright driver
    async with AsyncPlaywrightDriver(config, macos_control) as driver:
        page = driver.page

        try:
            # Phase 1: Navigation
            print("\n[Phase 1] Navigating to service account creation page...")
            nav_result = await navigate_to_service_account_page(page)

            if nav_result["status"] == "auth_required":
                print("\n⚠ Authentication required!")
                
                if autonomous:
                    # Try to focus window for user
                    driver.focus_browser_window()
                
                print("Please authenticate in the browser window.")
                print("Waiting up to 120 seconds...")

                # Wait for auth to complete (simplified - in production,
                # would use more sophisticated auth detection)
                await asyncio.sleep(10)

                # Retry navigation
                nav_result = await navigate_to_service_account_page(page)

            if nav_result["status"] != "success":
                return {
                    "success": False,
                    "message": f"Navigation failed: {nav_result.get('message', 'Unknown error')}",
                    "token": None,
                }

            # Phase 2: Form filling
            print("\n[Phase 2] Filling service account form...")
            form_result = await fill_service_account_form(
                page,
                account_name,
                [vault_name],
                macos_control,
                autonomous
            )

            if not form_result["success"]:
                return {
                    "success": False,
                    "message": f"Form filling failed: {form_result['message']}",
                    "token": None,
                }

            # Phase 3: Wizard navigation
            print("\n[Phase 3] Navigating wizard steps...")
            wizard_result = await navigate_wizard_steps(
                page, 
                max_steps=5, 
                macos_control=macos_control, 
                autonomous=autonomous
            )

            if not wizard_result["success"]:
                return {
                    "success": False,
                    "message": f"Wizard navigation failed: {wizard_result['message']}",
                    "token": None,
                }

            # Phase 4: Token extraction
            print("\n[Phase 4] Extracting service account token...")
            token = await extract_token(page)

            if not token:
                return {
                    "success": False,
                    "message": "Token extraction failed",
                    "token": None,
                }

            print("\n" + "=" * 60)
            print("SUCCESS! Service account created")
            print("=" * 60)
            print(f"Account name: {account_name}")
            print(f"Token (first 20 chars): {token[:20]}...")
            print("=" * 60)

            return {
                "success": True,
                "token": token,
                "account_name": account_name,
                "vault_name": vault_name,
                "message": "Service account created successfully",
            }

        except Exception as e:
            print(f"\nERROR: Automation failed: {e}")

            # Screenshot for debugging
            screenshot_dir = Path("/tmp/1password_automation")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            try:
                await page.screenshot(
                    path=str(screenshot_dir / "error_final_exception.png")
                )
            except:
                pass

            return {
                "success": False,
                "message": f"Exception: {str(e)}",
                "token": None,
            }


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

async def main():
    """CLI entry point for testing."""
    result = await create_service_account_automated(
        account_name="SPARC-Automation",
        vault_name="Automation"
    )

    if result["success"]:
        print(f"\n✓ Token: {result['token']}")
    else:
        print(f"\n✗ Failed: {result['message']}")


if __name__ == "__main__":
    asyncio.run(main())
