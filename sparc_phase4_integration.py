#!/usr/bin/env python3
"""
SPARC Phase 4: Integration Orchestrator Module - Production Implementation

This module coordinates all Phase 4 components in correct sequence:
1. Auth status detection (Module 13)
2. Session manager initialization (Module 14)
3. Browser automation via Playwright (Module 15)
4. CLI integration & token validation (Module 16)
5. Screenshot analysis for debugging (Module 17)

Provides state machine orchestration with comprehensive error handling,
logging, and performance timing.

Author: SPARC Phase 4 Integration
Date: 2026-01-01
Status: PRODUCTION-READY
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Awaitable, TypeVar
from datetime import datetime

# Phase 4 module imports
from sparc_phase4_auth_detector import analyze_auth_status, AuthStatus
from sparc_phase4_session_manager import SessionManager
from sparc_phase4_browser_automation import (
    AsyncPlaywrightDriver,
    fill_service_account_form,
    navigate_to_service_account_page,
    navigate_wizard_steps,
    extract_token
)
from sparc_phase4_cli_integration import (
    validate_token_format,
    save_token_to_env,
    test_token,
    ServiceAccountResult
)
from sparc_phase4_screenshot_analyzer import ScreenshotAnalyzer
from sparc_phase4_decision_engine import DecisionEngine, RetryStrategy

# Autonomous mode modules (imported conditionally)
try:
    from sparc_phase4_macos_control import MacAutomation
except ImportError:
    MacAutomation = None


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

T = TypeVar("T")

# ============================================================================
# ENUMS AND STATE MACHINE
# ============================================================================

class OrchestrationState(Enum):
    """State machine states for orchestration workflow."""
    INIT = "init"
    CHECK_AUTH = "check_auth"
    SESSION_INIT = "session_init"
    BROWSER_OPEN = "browser_open"
    NAVIGATE = "navigate"
    FILL_FORM = "fill_form"
    WIZARD_NAV = "wizard_nav"
    EXTRACT_TOKEN = "extract_token"
    VALIDATE_TOKEN = "validate_token"
    SAVE_TOKEN = "save_token"
    TEST_TOKEN = "test_token"
    CLEANUP = "cleanup"
    COMPLETE = "complete"
    ERROR = "error"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class OrchestrationResult:
    """
    Result of orchestration workflow.

    Attributes:
        success: Whether workflow completed successfully
        service_account_name: Name of created service account
        token: Service account token (if success)
        error_message: Error message (if failed)
        duration_seconds: Total execution time
        final_state: Final state machine state
        state_transitions: List of states visited
        auth_status: Initial authentication status
        token_validated: Whether token passed validation
        token_saved: Whether token was saved to environment
        token_tested: Whether token CLI test passed
    """
    success: bool
    service_account_name: str
    token: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    final_state: OrchestrationState = OrchestrationState.INIT
    state_transitions: List[OrchestrationState] = field(default_factory=list)
    auth_status: Optional[AuthStatus] = None
    token_validated: bool = False
    token_saved: bool = False
    token_tested: bool = False
    session_manager: Optional[SessionManager] = None

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "SUCCESS" if self.success else "FAILED"
        duration = f"{self.duration_seconds:.1f}s"

        return (
            f"[{status}] Account: {self.service_account_name} | "
            f"Duration: {duration} | "
            f"State: {self.final_state.value} | "
            f"Token: {'✓' if self.token else '✗'} | "
            f"Saved: {'✓' if self.token_saved else '✗'} | "
            f"Tested: {'✓' if self.token_tested else '✗'}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "service_account_name": self.service_account_name,
            "token": self.token[:20] + "..." if self.token else None,  # Redacted
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "final_state": self.final_state.value,
            "state_transitions": [s.value for s in self.state_transitions],
            "auth_status": self.auth_status.detected_method if self.auth_status else None,
            "token_validated": self.token_validated,
            "token_saved": self.token_saved,
            "token_tested": self.token_tested,
        }


@dataclass
class OrchestrationContext:
    """
    Mutable state during orchestration workflow.

    Attributes:
        account_name: Service account name
        vaults: List of vault names
        headless: Whether to run browser headless
        autonomous: Whether to use autonomous mode (native UI control)
        max_retries: Maximum number of retries for failed operations
        current_state: Current state machine state
        session_manager: SessionManager instance
        auth_status: Authentication status result
        page: Playwright page object
        token: Extracted service account token
        error: Current error message
        start_time: Workflow start timestamp
    """
    account_name: str
    vaults: List[str]
    headless: bool = False
    autonomous: bool = False
    max_retries: int = 3
    current_state: OrchestrationState = OrchestrationState.INIT
    session_manager: Optional[SessionManager] = None
    auth_status: Optional[AuthStatus] = None
    page: Optional[Any] = None
    token: Optional[str] = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    state_transitions: List[OrchestrationState] = field(default_factory=list)


# ============================================================================
# ORCHESTRATOR CLASS
# ============================================================================

class Orchestrator:
    """
    Main orchestration engine for Phase 4 workflow.

    Coordinates all Phase 4 modules in correct sequence with state machine,
    error handling, logging, and performance timing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize orchestrator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.context: Optional[OrchestrationContext] = None
        self.playwright_driver: Optional[AsyncPlaywrightDriver] = None

        # Initialize autonomous modules if enabled
        self.autonomous = self.config.get('autonomous', False)
        self.max_retries = self.config.get('max_retries', 3)

        if self.autonomous:
            self.decision_engine = DecisionEngine()
            if MacAutomation is not None:
                self.macos_control = MacAutomation()
                logger.info("Autonomous mode enabled with MacAutomation")
            else:
                self.macos_control = None
                logger.warning("Autonomous mode enabled but MacAutomation not available")
        else:
            self.decision_engine = None
            self.macos_control = None

        logger.info(f"Orchestrator initialized (autonomous={self.autonomous})")

    async def orchestrate(
        self,
        account_name: str,
        vaults: List[str],
        headless: bool = False
    ) -> OrchestrationResult:
        """
        Full workflow orchestration - main entry point.

        Orchestrates complete workflow:
        1. Check authentication status
        2. Initialize session manager
        3. Open browser (Playwright)
        4. Navigate to 1Password service account page
        5. Fill service account form
        6. Navigate wizard steps
        7. Extract token
        8. Validate token format
        9. Save token to ~/.zshrc
        10. Test token with CLI
        11. Cleanup and return results

        Args:
            account_name: Service account name
            vaults: List of vault names for permissions
            headless: Run browser in headless mode (default: False)

        Returns:
            OrchestrationResult with detailed execution info

        Example:
            >>> orchestrator = Orchestrator()
            >>> result = await orchestrator.orchestrate(
            ...     account_name="SPARC-Automation",
            ...     vaults=["Automation"],
            ...     headless=False
            ... )
            >>> if result.success:
            ...     print(f"Token saved: {result.token[:20]}...")
        """
        # Initialize context
        self.context = OrchestrationContext(
            account_name=account_name,
            vaults=vaults,
            headless=headless,
            autonomous=self.autonomous,
            max_retries=self.max_retries
        )

        start_time = time.time()
        logger.info(
            f"Starting orchestration: account={account_name}, "
            f"vaults={vaults}, headless={headless}"
        )

        try:
            # State 1: Check authentication
            await self._transition_state(OrchestrationState.CHECK_AUTH)
            await self._retry_with_backoff(
                self._check_auth_status,
                step_name="check_auth_status"
            )

            # State 2: Initialize session manager
            await self._transition_state(OrchestrationState.SESSION_INIT)
            await self._init_session_manager()

            # State 3: Open browser
            await self._transition_state(OrchestrationState.BROWSER_OPEN)
            await self._open_browser()

            # State 4: Navigate to service account page
            await self._transition_state(OrchestrationState.NAVIGATE)
            await self._retry_with_backoff(
                self._navigate_to_page,
                step_name="navigate_to_page"
            )

            # State 5: Fill form
            await self._transition_state(OrchestrationState.FILL_FORM)
            await self._retry_with_backoff(
                self._fill_account_form,
                step_name="fill_account_form"
            )

            # State 6: Navigate wizard
            await self._transition_state(OrchestrationState.WIZARD_NAV)
            await self._retry_with_backoff(
                self._navigate_wizard,
                step_name="navigate_wizard"
            )

            # State 7: Extract token
            await self._transition_state(OrchestrationState.EXTRACT_TOKEN)
            await self._retry_with_backoff(
                self._extract_service_token,
                step_name="extract_service_token"
            )

            # State 8: Validate token
            await self._transition_state(OrchestrationState.VALIDATE_TOKEN)
            self._validate_token()

            # State 9: Save token
            await self._transition_state(OrchestrationState.SAVE_TOKEN)
            await self._save_token_to_env()

            # State 10: Test token
            await self._transition_state(OrchestrationState.TEST_TOKEN)
            await self._test_token_with_cli()

            # State 11: Cleanup
            await self._transition_state(OrchestrationState.CLEANUP)
            await self._cleanup()

            # State 12: Complete
            await self._transition_state(OrchestrationState.COMPLETE)

            duration = time.time() - start_time
            logger.info(
                f"Orchestration completed successfully in {duration:.1f}s"
            )

            return OrchestrationResult(
                success=True,
                service_account_name=account_name,
                token=self.context.token,
                duration_seconds=duration,
                final_state=self.context.current_state,
                state_transitions=self.context.state_transitions,
                auth_status=self.context.auth_status,
                token_validated=True,
                token_saved=True,
                token_tested=True,
                session_manager=self.context.session_manager
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Orchestration failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            await self._transition_state(OrchestrationState.ERROR)

            try:
                await self._cleanup()
            except Exception as cleanup_err:
                logger.warning(f"Cleanup failed during error handling: {cleanup_err}")

            return OrchestrationResult(
                success=False,
                service_account_name=account_name,
                error_message=error_msg,
                duration_seconds=duration,
                final_state=self.context.current_state,
                state_transitions=self.context.state_transitions,
                auth_status=self.context.auth_status,
                session_manager=self.context.session_manager
            )

    # ========================================================================
    # STATE TRANSITION LOGIC
    # ========================================================================

    async def _transition_state(self, new_state: OrchestrationState) -> None:
        """
        Transition to new state with logging.

        Args:
            new_state: Target state to transition to
        """
        if self.context is None:
            raise RuntimeError("Context not initialized")

        old_state = self.context.current_state
        self.context.current_state = new_state
        self.context.state_transitions.append(new_state)

        logger.info(
            f"State transition: {old_state.value} → {new_state.value}"
        )

    async def _retry_with_backoff(
        self,
        operation: Callable[[], Awaitable[T]],
        step_name: Optional[str] = None
    ) -> T:
        """
        Retry an async operation with exponential backoff.

        Uses DecisionEngine.get_retry_strategy() and respects config max_retries.
        """
        name = step_name or getattr(operation, "__name__", "operation")
        attempt = 0

        while True:
            try:
                return await operation()
            except Exception as exc:
                strategy = await DecisionEngine.get_retry_strategy(exc)
                max_attempts = self._resolve_max_attempts(strategy)

                if not strategy.retryable:
                    logger.error(
                        f"{name} failed with non-retryable error: {exc} "
                        f"(strategy={strategy.name}, reason={strategy.reason})"
                    )
                    raise
                if max_attempts <= 0:
                    logger.error(
                        f"{name} failed with retries disabled: {exc} "
                        f"(strategy={strategy.name}, reason={strategy.reason})"
                    )
                    raise

                attempt += 1
                if attempt >= max_attempts:
                    logger.error(
                        f"{name} failed after {attempt}/{max_attempts} attempts: {exc} "
                        f"(strategy={strategy.name}, reason={strategy.reason})"
                    )
                    raise

                delay = strategy.next_delay_sec(attempt)
                logger.warning(
                    f"{name} failed (attempt {attempt}/{max_attempts}); "
                    f"retrying in {delay:.2f}s - "
                    f"strategy={strategy.name}, reason={strategy.reason}, error={exc}"
                )
                await asyncio.sleep(delay)

    def _resolve_max_attempts(self, strategy: RetryStrategy) -> int:
        """Resolve the effective retry cap using config max_retries."""
        configured = self.config.get("max_retries")
        if configured is None:
            return max(0, int(strategy.max_attempts))

        try:
            configured_int = int(configured)
        except (TypeError, ValueError):
            logger.warning(
                f"Invalid max_retries config ({configured}); "
                f"using strategy default of {strategy.max_attempts}"
            )
            return max(0, int(strategy.max_attempts))

        if configured_int < 0:
            logger.warning(
                f"Negative max_retries config ({configured_int}); treating as 0"
            )
            return 0

        if strategy.max_attempts <= 0:
            return 0

        return min(int(strategy.max_attempts), configured_int)

    # ========================================================================
    # ORCHESTRATION STEPS
    # ========================================================================

    async def _check_auth_status(self) -> None:
        """
        Step 1: Check authentication status using auth detector module.

        Raises:
            RuntimeError if not authenticated
        """
        if self.context is None:
            raise RuntimeError("Context not initialized")

        logger.info("Checking 1Password authentication status...")

        self.context.auth_status = analyze_auth_status()

        if not self.context.auth_status.is_authenticated:
            raise RuntimeError(
                f"Not authenticated: {self.context.auth_status.detected_method} "
                f"(confidence: {self.context.auth_status.confidence_score:.0%})"
            )

        logger.info(
            f"Authentication confirmed: {self.context.auth_status.detected_method} "
            f"(confidence: {self.context.auth_status.confidence_score:.0%})"
        )

    async def _init_session_manager(self) -> None:
        """
        Step 2: Initialize session manager with persistent state.
        """
        if self.context is None:
            raise RuntimeError("Context not initialized")

        logger.info("Initializing session manager...")

        self.context.session_manager = SessionManager(
            user_data_dir="/tmp/1password_session"
        )

        logger.debug("Session manager initialized")

    async def _open_browser(self) -> None:
        """
        Step 3: Open browser using AsyncPlaywrightDriver.

        Raises:
            RuntimeError if browser launch fails
        """
        if self.context is None:
            raise RuntimeError("Context not initialized")

        logger.info("Opening browser...")

        config = {
            "browser": {
                "headless": self.context.headless,
                "window_size": [1920, 1080],
                "timeout": 30000,
            },
            "session_file": "/tmp/1password_session.json",
            "save_session": True,
        }

        try:
            self.playwright_driver = AsyncPlaywrightDriver(
                config,
                macos_control=self.macos_control if self.autonomous else None
            )
            driver = await self.playwright_driver.__aenter__()

            self.context.page = driver.page

            logger.info(f"Browser opened (headless={self.context.headless})")

        except Exception as e:
            raise RuntimeError(f"Failed to open browser: {e}")

    async def _navigate_to_page(self) -> None:
        """
        Step 4: Navigate to 1Password service account creation page.

        Raises:
            RuntimeError if navigation fails
        """
        if self.context is None or self.context.page is None:
            raise RuntimeError("Context or page not initialized")

        logger.info("Navigating to 1Password service account page...")

        nav_result = await navigate_to_service_account_page(self.context.page)

        if nav_result["status"] != "success":
            raise RuntimeError(
                f"Navigation failed: {nav_result.get('message', 'Unknown error')}"
            )

        logger.info(f"Successfully navigated to: {nav_result['url']}")

    async def _fill_account_form(self) -> None:
        """
        Step 5: Fill service account form with name and vault selections.

        Raises:
            RuntimeError if form filling fails
        """
        if self.context is None or self.context.page is None:
            raise RuntimeError("Context or page not initialized")

        logger.info(
            f"Filling form: account={self.context.account_name}, "
            f"vaults={self.context.vaults}"
        )

        form_result = await fill_service_account_form(
            self.context.page,
            self.context.account_name,
            self.context.vaults,
            macos_control=self.macos_control if self.autonomous else None,
            autonomous=self.autonomous
        )

        if not form_result.get("success", False):
            raise RuntimeError(
                f"Form filling failed: {form_result.get('message', 'Unknown error')}"
            )

        logger.info("Form filled successfully")

    async def _navigate_wizard(self) -> None:
        """
        Step 6: Navigate through wizard steps to token display.

        Raises:
            RuntimeError if wizard navigation fails
        """
        if self.context is None or self.context.page is None:
            raise RuntimeError("Context or page not initialized")

        logger.info("Navigating through wizard steps...")

        wizard_result = await navigate_wizard_steps(
            self.context.page,
            max_steps=5,
            macos_control=self.macos_control if self.autonomous else None,
            autonomous=self.autonomous
        )

        if not wizard_result.get("success", False):
            raise RuntimeError(
                f"Wizard navigation failed: "
                f"{wizard_result.get('message', 'Unknown error')}"
            )

        steps_taken = wizard_result.get("steps_taken", 0)
        logger.info(f"Wizard navigation complete ({steps_taken} steps)")

    async def _extract_service_token(self) -> None:
        """
        Step 7: Extract service account token from page.

        Raises:
            RuntimeError if token extraction fails
        """
        if self.context is None or self.context.page is None:
            raise RuntimeError("Context or page not initialized")

        logger.info("Extracting service account token...")

        self.context.token = await extract_token(self.context.page)

        if not self.context.token:
            raise RuntimeError("Token extraction failed")

        # Log redacted token for security
        redacted = (
            f"{self.context.token[:8]}..."
            f"{self.context.token[-8:]}"
        )
        logger.info(f"Token extracted successfully: {redacted}")

    def _validate_token(self) -> None:
        """
        Step 8: Validate token format.

        Raises:
            RuntimeError if token validation fails
        """
        if self.context is None or not self.context.token:
            raise RuntimeError("Token not available for validation")

        logger.info("Validating token format...")

        if not validate_token_format(self.context.token):
            raise RuntimeError(
                f"Token validation failed: invalid format"
            )

        logger.info("Token validation passed")

    async def _save_token_to_env(self) -> None:
        """
        Step 9: Save token to ~/.zshrc environment variable.

        Raises:
            RuntimeError if token save fails
        """
        if self.context is None or not self.context.token:
            raise RuntimeError("Token not available for saving")

        logger.info("Saving token to ~/.zshrc...")

        persist_result = save_token_to_env(
            self.context.token,
            env_var_name="OP_SERVICE_ACCOUNT_TOKEN"
        )

        if not persist_result.success:
            raise RuntimeError(
                f"Token persistence failed: {persist_result.error_message}"
            )

        logger.info(
            f"Token saved to ~/.zshrc (backup: {persist_result.backup_path})"
        )

    async def _test_token_with_cli(self) -> None:
        """
        Step 10: Test token with 1Password CLI (op whoami).

        Raises:
            RuntimeError if token test fails
        """
        if self.context is None or not self.context.token:
            raise RuntimeError("Token not available for testing")

        logger.info("Testing token with 1Password CLI...")

        # Set token in current process environment
        import os
        os.environ["OP_SERVICE_ACCOUNT_TOKEN"] = self.context.token

        cli_result = test_token()

        if not cli_result.success:
            raise RuntimeError(
                f"Token test failed: {cli_result.error_message}"
            )

        logger.info(
            f"Token test passed: {cli_result.service_account_name}"
        )

    async def _cleanup(self) -> None:
        """
        Step 11: Clean up browser and session resources.
        """
        logger.info("Cleaning up resources...")

        try:
            # Close Playwright driver if open
            if self.playwright_driver:
                await self.playwright_driver.__aexit__(None, None, None)
                logger.debug("Playwright driver closed")

            # Close session manager if open
            if self.context and self.context.session_manager:
                await self.context.session_manager.close_session()
                logger.debug("Session manager closed")

        except Exception as e:
            logger.warning(f"Cleanup error (non-fatal): {e}")

        logger.info("Cleanup complete")


# ============================================================================
# SYNCHRONOUS WRAPPER
# ============================================================================

def orchestrate_sync(
    account_name: str,
    vaults: List[str],
    headless: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> OrchestrationResult:
    """
    Synchronous wrapper for orchestrate() using asyncio.run().

    Allows calling async orchestration from synchronous code.

    Args:
        account_name: Service account name
        vaults: List of vault names
        headless: Run browser in headless mode
        config: Optional configuration dictionary

    Returns:
        OrchestrationResult with detailed execution info

    Example:
        >>> result = orchestrate_sync("SPARC-Automation", ["Automation"])
        >>> print(result)
        [SUCCESS] Account: SPARC-Automation | Duration: 45.2s | ...
    """
    orchestrator = Orchestrator(config=config)

    return asyncio.run(
        orchestrator.orchestrate(
            account_name=account_name,
            vaults=vaults,
            headless=headless
        )
    )


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

async def main():
    """
    Command-line interface for orchestration.

    Usage:
        python sparc_phase4_integration.py
    """
    print("=" * 70)
    print("SPARC PHASE 4 - INTEGRATION ORCHESTRATOR")
    print("=" * 70)
    print()

    # Example orchestration
    account_name = "SPARC-Automation"
    vaults = ["Automation"]

    orchestrator = Orchestrator()

    try:
        result = await orchestrator.orchestrate(
            account_name=account_name,
            vaults=vaults,
            headless=False
        )

        print()
        print("=" * 70)
        print("ORCHESTRATION RESULT")
        print("=" * 70)
        print(result)
        print()
        print("Detailed Result:")
        print("-" * 70)

        for key, value in result.to_dict().items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")

        print("=" * 70)

        return 0 if result.success else 1

    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"Orchestration failed: {e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
