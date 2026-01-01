"""
Session Manager Module for Instacart Automation
Manages browser sessions with persistent state using Playwright async API

Usage:
    # Context manager pattern (recommended)
    async with SessionManager() as session:
        page = await session.create_session(headless=False)
        await page.goto("https://instacart.com")
        await session.save_session("/tmp/session.json")

    # Manual lifecycle
    manager = SessionManager()
    page = await manager.create_session()
    is_auth = await manager.is_authenticated()
    await manager.restore_session("/tmp/session.json")
    await manager.close_session()
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Error as PlaywrightError
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages browser sessions with persistent state for automation.

    Features:
    - Async Playwright browser lifecycle management
    - Cookie and localStorage persistence
    - Session save/restore capabilities
    - Authentication state detection
    - Context manager support for automatic cleanup
    - Resource leak prevention

    Attributes:
        browser: Playwright Browser instance
        context: BrowserContext with persistent state
        page: Active Page object for automation
        playwright: Playwright instance handle
        user_data_dir: Path to persistent browser data
    """

    def __init__(self, user_data_dir: Optional[str] = None):
        """
        Initialize SessionManager.

        Args:
            user_data_dir: Optional path for persistent browser data.
                          Defaults to /tmp/playwright_session
        """
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None

        # Default user data directory for persistent storage
        if user_data_dir is None:
            user_data_dir = "/tmp/playwright_session"

        self.user_data_dir = Path(user_data_dir)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"SessionManager initialized with user_data_dir: {self.user_data_dir}")

    async def create_session(
        self,
        headless: bool = False,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        extra_http_headers: Optional[Dict[str, str]] = None
    ) -> Page:
        """
        Initialize browser with persistent context.

        Args:
            headless: Run browser in headless mode (default: False)
            viewport: Custom viewport size, e.g., {"width": 1920, "height": 1080}
            user_agent: Custom user agent string
            extra_http_headers: Additional HTTP headers for all requests

        Returns:
            Page object ready for automation

        Raises:
            PlaywrightError: If browser launch fails
            RuntimeError: If session already exists

        Example:
            page = await manager.create_session(
                headless=False,
                viewport={"width": 1920, "height": 1080}
            )
        """
        if self.browser is not None:
            logger.warning("Session already exists, closing existing session first")
            await self.close_session()

        try:
            logger.info("Launching Playwright browser...")
            self.playwright = await async_playwright().start()

            # Launch Chromium with persistent context
            launch_options = {
                "headless": headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",  # Evade detection
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            }

            self.browser = await self.playwright.chromium.launch(**launch_options)
            logger.debug(f"Browser launched (headless={headless})")

            # Create persistent context with user data directory
            context_options: Dict[str, Any] = {
                "viewport": viewport or {"width": 1280, "height": 720},
                "user_agent": user_agent,
                "accept_downloads": True,
                "has_touch": False,
                "is_mobile": False,
                "java_script_enabled": True,
                "locale": "en-US",
                "timezone_id": "America/Los_Angeles"
            }

            if extra_http_headers:
                context_options["extra_http_headers"] = extra_http_headers

            # Remove None values
            context_options = {k: v for k, v in context_options.items() if v is not None}

            self.context = await self.browser.new_context(**context_options)
            logger.debug("Browser context created with persistent options")

            # Create new page
            self.page = await self.context.new_page()
            logger.info("Browser page created successfully")

            # Set default timeout (30 seconds)
            self.page.set_default_timeout(30000)

            return self.page

        except PlaywrightError as e:
            logger.error(f"Playwright error during session creation: {e}")
            await self.close_session()  # Cleanup on failure
            raise
        except Exception as e:
            logger.error(f"Unexpected error during session creation: {e}")
            await self.close_session()
            raise RuntimeError(f"Failed to create session: {e}")

    async def save_session(self, path: str) -> bool:
        """
        Save session state (cookies, localStorage) to file.

        Args:
            path: File path to save session data (JSON format)

        Returns:
            True if save successful, False otherwise

        Raises:
            RuntimeError: If no active session exists

        Example:
            success = await manager.save_session("/tmp/my_session.json")
        """
        if self.context is None or self.page is None:
            raise RuntimeError("No active session to save. Call create_session() first.")

        try:
            logger.info(f"Saving session state to {path}...")

            # Extract cookies from context
            cookies = await self.context.cookies()
            logger.debug(f"Extracted {len(cookies)} cookies")

            # Extract localStorage from page
            local_storage = await self.page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            logger.debug(f"Extracted {len(local_storage)} localStorage items")

            # Extract sessionStorage from page
            session_storage = await self.page.evaluate("""
                () => {
                    const storage = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                    return storage;
                }
            """)
            logger.debug(f"Extracted {len(session_storage)} sessionStorage items")

            # Combine into session state
            session_state = {
                "cookies": cookies,
                "localStorage": local_storage,
                "sessionStorage": session_storage,
                "url": self.page.url,
                "timestamp": datetime.now().isoformat(),
                "user_agent": await self.page.evaluate("navigator.userAgent")
            }

            # Save to file
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'w') as f:
                json.dump(session_state, f, indent=2)

            logger.info(f"Session state saved successfully to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    async def restore_session(self, path: str) -> bool:
        """
        Restore session from saved state.

        Args:
            path: File path to load session data from

        Returns:
            True if restore successful, False otherwise

        Raises:
            RuntimeError: If no active session exists
            FileNotFoundError: If session file doesn't exist

        Example:
            await manager.create_session()
            success = await manager.restore_session("/tmp/my_session.json")
        """
        if self.context is None or self.page is None:
            raise RuntimeError("No active session to restore into. Call create_session() first.")

        load_path = Path(path)
        if not load_path.exists():
            raise FileNotFoundError(f"Session file not found: {path}")

        try:
            logger.info(f"Restoring session state from {path}...")

            # Load session state from file
            with open(load_path, 'r') as f:
                session_state = json.load(f)

            # Restore cookies to context
            cookies = session_state.get("cookies", [])
            if cookies:
                await self.context.add_cookies(cookies)
                logger.debug(f"Restored {len(cookies)} cookies")

            # Navigate to saved URL first (required for localStorage/sessionStorage)
            saved_url = session_state.get("url", "about:blank")
            if saved_url and saved_url != "about:blank":
                await self.page.goto(saved_url, wait_until="domcontentloaded")
                logger.debug(f"Navigated to saved URL: {saved_url}")

            # Restore localStorage to page
            local_storage = session_state.get("localStorage", {})
            if local_storage:
                await self.page.evaluate("""
                    (storage) => {
                        for (const [key, value] of Object.entries(storage)) {
                            localStorage.setItem(key, value);
                        }
                    }
                """, local_storage)
                logger.debug(f"Restored {len(local_storage)} localStorage items")

            # Restore sessionStorage to page
            session_storage = session_state.get("sessionStorage", {})
            if session_storage:
                await self.page.evaluate("""
                    (storage) => {
                        for (const [key, value] of Object.entries(storage)) {
                            sessionStorage.setItem(key, value);
                        }
                    }
                """, session_storage)
                logger.debug(f"Restored {len(session_storage)} sessionStorage items")

            # Reload page to apply restored state
            await self.page.reload(wait_until="domcontentloaded")

            logger.info("Session state restored successfully")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid session file format: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return False

    async def is_authenticated(self, check_patterns: Optional[List[str]] = None) -> bool:
        """
        Check if session is authenticated (e.g., 1Password login, Instacart login).

        Args:
            check_patterns: List of cookie/localStorage keys to check for auth.
                           Defaults to common auth patterns.

        Returns:
            True if authenticated, False otherwise

        Example:
            is_auth = await manager.is_authenticated(
                check_patterns=["session_token", "user_id"]
            )
        """
        if self.context is None or self.page is None:
            logger.warning("No active session to check authentication")
            return False

        # Default auth patterns (common session indicators)
        if check_patterns is None:
            check_patterns = [
                "session",
                "auth",
                "token",
                "user_id",
                "logged_in",
                "access_token",
                "refresh_token"
            ]

        try:
            logger.debug("Checking authentication state...")

            # Check cookies for auth patterns
            cookies = await self.context.cookies()
            cookie_names = [c["name"].lower() for c in cookies]

            for pattern in check_patterns:
                if any(pattern.lower() in name for name in cookie_names):
                    logger.info(f"Authentication detected via cookie pattern: {pattern}")
                    return True

            # Check localStorage for auth patterns
            local_storage = await self.page.evaluate("""
                () => {
                    const keys = [];
                    for (let i = 0; i < localStorage.length; i++) {
                        keys.push(localStorage.key(i));
                    }
                    return keys;
                }
            """)

            for pattern in check_patterns:
                if any(pattern.lower() in key.lower() for key in local_storage):
                    logger.info(f"Authentication detected via localStorage pattern: {pattern}")
                    return True

            logger.debug("No authentication indicators found")
            return False

        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False

    async def close_session(self):
        """
        Clean up browser resources.

        Ensures proper cleanup of page, context, browser, and Playwright instance.
        Safe to call multiple times.

        Example:
            await manager.close_session()
        """
        logger.info("Closing browser session...")

        try:
            # Close in reverse order of creation
            if self.page is not None:
                await self.page.close()
                self.page = None
                logger.debug("Page closed")

            if self.context is not None:
                await self.context.close()
                self.context = None
                logger.debug("Context closed")

            if self.browser is not None:
                await self.browser.close()
                self.browser = None
                logger.debug("Browser closed")

            if self.playwright is not None:
                await self.playwright.stop()
                self.playwright = None
                logger.debug("Playwright stopped")

            logger.info("Browser session closed successfully")

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            # Force cleanup even on error
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    async def __aenter__(self):
        """
        Context manager entry: creates session automatically.

        Example:
            async with SessionManager() as manager:
                page = manager.page
                await page.goto("https://example.com")
        """
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit: ensures cleanup on exception or normal exit.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        await self.close_session()

        # Don't suppress exceptions
        return False


# Example usage and testing
async def main():
    """
    Example usage demonstrating SessionManager features.
    """
    print("=" * 60)
    print("SessionManager Demo")
    print("=" * 60)

    # Example 1: Context manager pattern (recommended)
    print("\n[Example 1] Context manager pattern:")
    async with SessionManager() as manager:
        page = manager.page
        await page.goto("https://example.com")
        print(f"  Navigated to: {page.url}")

        # Save session
        await manager.save_session("/tmp/example_session.json")
        print("  Session saved to /tmp/example_session.json")

    # Example 2: Manual lifecycle with session restore
    print("\n[Example 2] Manual lifecycle with restore:")
    manager = SessionManager()

    try:
        page = await manager.create_session(headless=False)
        print(f"  Browser created (headless=False)")

        # Restore previous session
        restore_success = await manager.restore_session("/tmp/example_session.json")
        print(f"  Session restored: {restore_success}")
        print(f"  Current URL: {page.url}")

        # Check authentication
        is_auth = await manager.is_authenticated()
        print(f"  Authenticated: {is_auth}")

    finally:
        await manager.close_session()
        print("  Session closed")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
