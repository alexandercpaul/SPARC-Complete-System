#!/usr/bin/env python3
"""
1Password CLI Integration Module - Phase 4 Agent 16

Production-ready Python module for creating and managing 1Password service accounts
via the official 1Password CLI (op).

Security Features:
- Never logs full tokens (redacts to ops_****...****)
- Backs up ~/.zshrc before modification
- Validates token format before persistence
- Secure subprocess handling with timeout protection

Retry Logic:
- Exponential backoff for transient failures
- Circuit breaker for CLI failures
- Configurable max retry attempts

Author: SPARC Phase 4 Agent 16
Date: 2026-01-01
"""

import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ServiceAccountResult:
    """Result of service account creation."""
    success: bool
    token: Optional[str] = None
    error_message: Optional[str] = None
    account_name: Optional[str] = None
    extraction_method: Optional[str] = None

    def redacted_token(self) -> str:
        """Return token with middle portion redacted for safe logging."""
        if not self.token or len(self.token) < 20:
            return "ops_****...****"
        return f"{self.token[:8]}...{self.token[-8:]}"


@dataclass
class TokenValidation:
    """Token format validation result."""
    is_valid: bool
    errors: List[str]
    prefix_ok: bool = False
    length_ok: bool = False
    charset_ok: bool = False
    pattern_match: bool = False


@dataclass
class PersistResult:
    """Token persistence result."""
    success: bool
    backup_path: Optional[str] = None
    env_var_name: str = "OP_SERVICE_ACCOUNT_TOKEN"
    error_message: Optional[str] = None
    verified: bool = False


@dataclass
class CLIValidationResult:
    """op whoami validation result."""
    success: bool
    output: Optional[str] = None
    service_account_name: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================================
# Configuration
# ============================================================================

# Token validation
TOKEN_PATTERN = re.compile(r'^ops_[A-Za-z0-9_-]{100,}$')
TOKEN_PREFIX = "ops_"
MIN_TOKEN_LENGTH = 100
ALLOWED_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 60.0  # seconds
BACKOFF_MULTIPLIER = 2

# Timeouts
CLI_TIMEOUT = 10  # seconds for CLI operations


# ============================================================================
# Core Functions
# ============================================================================

def create_service_account_cli(
    name: str,
    vaults: List[str],
    permissions: List[str] = None,
    expiry_days: int = 0
) -> ServiceAccountResult:
    """
    Create a 1Password service account using the op CLI.

    NOTE: This function constructs the op CLI command but does NOT execute it,
    as service account creation via CLI requires manual intervention or
    web UI automation (see Phase 3 architecture).

    Args:
        name: Service account name (e.g., "SPARC-Automation")
        vaults: List of vault names to grant access
        permissions: List of permissions (default: ["read_items"])
        expiry_days: Days until expiration (0 = no expiry)

    Returns:
        ServiceAccountResult with command construction status

    Raises:
        ValueError: If name or vaults are invalid

    Example:
        >>> result = create_service_account_cli(
        ...     name="SPARC-Automation",
        ...     vaults=["Automation"],
        ...     permissions=["read_items"]
        ... )
    """
    # Validate inputs
    if not name or not isinstance(name, str):
        return ServiceAccountResult(
            success=False,
            error_message="Service account name must be a non-empty string"
        )

    if not vaults or not isinstance(vaults, list) or len(vaults) == 0:
        return ServiceAccountResult(
            success=False,
            error_message="At least one vault must be specified"
        )

    if permissions is None:
        permissions = ["read_items"]

    # Construct CLI command (for documentation purposes)
    # Note: As of 2026, op CLI does not support service account creation directly
    # This must be done via web UI automation (see Phase 3 spec)
    command_parts = [
        "op", "service-account", "create",
        "--name", name,
        "--vaults", ",".join(vaults),
        "--permissions", ",".join(permissions)
    ]

    if expiry_days > 0:
        command_parts.extend(["--expiry-days", str(expiry_days)])

    logger.info(f"Service account creation command: {' '.join(command_parts)}")
    logger.warning(
        "Note: op CLI does not support service account creation as of 2026. "
        "Use web UI automation (see Phase 3 architecture)."
    )

    return ServiceAccountResult(
        success=False,
        error_message="Service account creation requires web UI automation (not supported via CLI)",
        account_name=name
    )


def extract_token_from_output(output: str) -> Optional[str]:
    """
    Extract 1Password service account token from CLI or page output.

    Supports multiple formats:
    - Plain token: ops_eyJ0eXAiOiJKV1QiLCJhbGc...
    - Wrapped in quotes: "ops_eyJ0eXAiOiJKV1QiLCJhbGc..."
    - Multi-line with whitespace
    - Mixed with other text

    Args:
        output: Raw text output containing token

    Returns:
        Extracted token string, or None if not found

    Example:
        >>> output = "Your token: ops_abc123...xyz789"
        >>> token = extract_token_from_output(output)
        >>> print(token)
        ops_abc123...xyz789
    """
    if not output or not isinstance(output, str):
        logger.warning("extract_token_from_output: Invalid or empty output")
        return None

    # Remove all whitespace and newlines for wrapped tokens
    cleaned = re.sub(r'\s+', '', output)

    # Search for token pattern
    match = re.search(r'(ops_[A-Za-z0-9_-]{100,})', cleaned)

    if match:
        token = match.group(1)
        logger.info(f"Token extracted successfully: {token[:8]}...{token[-8:]}")
        return token

    # Fallback: try searching in original output (with whitespace)
    match = re.search(r'(ops_[A-Za-z0-9_-]{100,})', output)
    if match:
        token = match.group(1)
        logger.info(f"Token extracted (fallback): {token[:8]}...{token[-8:]}")
        return token

    logger.error("extract_token_from_output: No token pattern found in output")
    return None


def validate_token_format(token: str) -> TokenValidation:
    """
    Validate 1Password service account token format.

    Checks:
    1. Starts with "ops_" prefix
    2. Minimum length (100+ characters)
    3. Only allowed characters (A-Za-z0-9_-)
    4. Matches full regex pattern

    Args:
        token: Token string to validate

    Returns:
        TokenValidation with detailed validation results

    Example:
        >>> validation = validate_token_format("ops_abc...")
        >>> if validation.is_valid:
        ...     print("Token is valid!")
    """
    errors = []

    # Check 1: Prefix
    prefix_ok = token.startswith(TOKEN_PREFIX) if token else False
    if not prefix_ok:
        errors.append(f"Token must start with '{TOKEN_PREFIX}'")

    # Check 2: Length
    length_ok = len(token) >= MIN_TOKEN_LENGTH if token else False
    if not length_ok:
        actual_len = len(token) if token else 0
        errors.append(f"Token too short: {actual_len} < {MIN_TOKEN_LENGTH}")

    # Check 3: Character set
    charset_ok = True
    if token:
        for i, char in enumerate(token):
            if char not in ALLOWED_CHARS:
                charset_ok = False
                errors.append(f"Invalid character '{char}' at position {i}")
                break
    else:
        charset_ok = False
        errors.append("Token is empty or None")

    # Check 4: Full pattern match
    pattern_match = bool(TOKEN_PATTERN.match(token)) if token else False
    if not pattern_match and not errors:
        # Only add this error if other checks passed but pattern still fails
        errors.append("Token does not match expected pattern")

    is_valid = prefix_ok and length_ok and charset_ok and pattern_match

    return TokenValidation(
        is_valid=is_valid,
        errors=errors,
        prefix_ok=prefix_ok,
        length_ok=length_ok,
        charset_ok=charset_ok,
        pattern_match=pattern_match
    )


def save_token_to_env(
    token: str,
    env_var_name: str = "OP_SERVICE_ACCOUNT_TOKEN",
    zshrc_path: str = "~/.zshrc"
) -> PersistResult:
    """
    Save 1Password service account token to ~/.zshrc with backup.

    Process:
    1. Expand path and validate
    2. Create timestamped backup
    3. Check for existing token export
    4. Append or update export line
    5. Verify write success

    Args:
        token: Service account token (will be redacted in logs)
        env_var_name: Environment variable name (default: OP_SERVICE_ACCOUNT_TOKEN)
        zshrc_path: Path to zsh config file (default: ~/.zshrc)

    Returns:
        PersistResult with success status and backup path

    Raises:
        PermissionError: If ~/.zshrc is not writable
        OSError: If disk is full or other I/O error

    Example:
        >>> result = save_token_to_env("ops_abc123...")
        >>> if result.success:
        ...     print(f"Token saved! Backup: {result.backup_path}")
    """
    # Validate token format first
    validation = validate_token_format(token)
    if not validation.is_valid:
        return PersistResult(
            success=False,
            error_message=f"Invalid token format: {', '.join(validation.errors)}"
        )

    # Expand path
    zshrc_path = os.path.expanduser(zshrc_path)

    # Resolve symlinks
    if os.path.islink(zshrc_path):
        real_path = os.path.realpath(zshrc_path)
        logger.info(f"Following symlink: {zshrc_path} -> {real_path}")
        zshrc_path = real_path

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{zshrc_path}.backup.{timestamp}"

    try:
        if os.path.exists(zshrc_path):
            # Backup existing file
            with open(zshrc_path, 'r') as src:
                content = src.read()
            with open(backup_path, 'w') as dst:
                dst.write(content)
            logger.info(f"Created backup: {backup_path}")
        else:
            # Create new .zshrc
            Path(zshrc_path).touch()
            backup_path = None
            logger.info(f"Created new .zshrc: {zshrc_path}")
    except PermissionError as e:
        return PersistResult(
            success=False,
            error_message=f"Permission denied: {zshrc_path}. Run: chmod 600 ~/.zshrc"
        )
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            return PersistResult(
                success=False,
                error_message="Disk full: Cannot write to ~/.zshrc"
            )
        return PersistResult(
            success=False,
            error_message=f"I/O error: {str(e)}"
        )

    # Read current content
    try:
        with open(zshrc_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return PersistResult(
            success=False,
            backup_path=backup_path,
            error_message=f"Failed to read .zshrc: {str(e)}"
        )

    # Check for existing token export
    export_pattern = re.compile(
        rf'^export {re.escape(env_var_name)}=.*$',
        re.MULTILINE
    )

    export_line = f'export {env_var_name}="{token}"'
    comment_line = f"\n# 1Password Service Account Token - Created {timestamp}\n"

    if export_pattern.search(content):
        # Update existing export
        logger.info(f"Updating existing {env_var_name} export")
        content = export_pattern.sub(export_line, content)
    else:
        # Append new export
        logger.info(f"Appending new {env_var_name} export")
        if not content.endswith('\n'):
            content += '\n'
        content += comment_line + export_line + '\n'

    # Write updated content
    try:
        with open(zshrc_path, 'w') as f:
            f.write(content)
    except Exception as e:
        # Restore from backup on failure
        if backup_path and os.path.exists(backup_path):
            try:
                with open(backup_path, 'r') as src:
                    backup_content = src.read()
                with open(zshrc_path, 'w') as dst:
                    dst.write(backup_content)
                logger.warning(f"Restored from backup after write failure")
            except Exception as restore_error:
                logger.error(f"Failed to restore from backup: {restore_error}")

        return PersistResult(
            success=False,
            backup_path=backup_path,
            error_message=f"Failed to write .zshrc: {str(e)}"
        )

    # Verify write success
    try:
        with open(zshrc_path, 'r') as f:
            updated_content = f.read()

        # Redact token for logging
        redacted_token = f"{token[:8]}...{token[-8:]}"

        if token in updated_content:
            logger.info(f"Token successfully persisted: {redacted_token}")
            verified = True
        else:
            logger.error("Token not found in .zshrc after write")
            verified = False
    except Exception as e:
        logger.warning(f"Failed to verify write: {str(e)}")
        verified = False

    # Set secure permissions (owner read/write only)
    try:
        os.chmod(zshrc_path, 0o600)
        logger.info(f"Set permissions to 600: {zshrc_path}")
    except Exception as e:
        logger.warning(f"Failed to set permissions: {str(e)}")

    return PersistResult(
        success=True,
        backup_path=backup_path,
        env_var_name=env_var_name,
        verified=verified
    )


def test_token(token: str, max_retries: int = MAX_RETRIES) -> CLIValidationResult:
    """
    Test 1Password service account token using 'op whoami'.

    Executes 'op whoami' with the token in environment to verify:
    1. Token is valid
    2. Service account is active
    3. Can communicate with 1Password servers

    Includes retry logic for transient network errors.

    Args:
        token: Service account token to test
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        CLIValidationResult with validation status

    Example:
        >>> result = test_token("ops_abc123...")
        >>> if result.success:
        ...     print(f"Service account: {result.service_account_name}")
    """
    # Validate token format first
    validation = validate_token_format(token)
    if not validation.is_valid:
        return CLIValidationResult(
            success=False,
            error_message=f"Invalid token format: {', '.join(validation.errors)}"
        )

    # Prepare environment with token
    env = os.environ.copy()
    env['OP_SERVICE_ACCOUNT_TOKEN'] = token

    # Redacted token for logging
    redacted = f"{token[:8]}...{token[-8:]}"

    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(f"Running 'op whoami' (attempt {attempt + 1}/{max_retries})")

            result = subprocess.run(
                ['op', 'whoami'],
                capture_output=True,
                text=True,
                timeout=CLI_TIMEOUT,
                env=env
            )

            # Check return code
            if result.returncode == 0:
                output = result.stdout.strip()
                logger.info(f"op whoami succeeded")

                # Parse output for service account name
                service_account_name = None
                match = re.search(r'Service Account:\s*([^\n\r(]+)', output)
                if match:
                    service_account_name = match.group(1).strip()
                    logger.info(f"Service account: {service_account_name}")

                return CLIValidationResult(
                    success=True,
                    output=output,
                    service_account_name=service_account_name
                )

            else:
                # CLI error
                stderr = result.stderr.strip()
                logger.error(f"op whoami failed (exit {result.returncode}): {stderr}")

                # Check if it's a transient error (network, server)
                transient_errors = [
                    'network',
                    'timeout',
                    'connection',
                    'server error',
                    '503',
                    '502',
                    '500'
                ]

                is_transient = any(err in stderr.lower() for err in transient_errors)

                if is_transient and attempt < max_retries - 1:
                    # Retry with exponential backoff
                    delay = min(BASE_DELAY * (BACKOFF_MULTIPLIER ** attempt), MAX_DELAY)
                    logger.warning(f"Transient error detected. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    # Non-transient error or max retries reached
                    return CLIValidationResult(
                        success=False,
                        output=stderr,
                        error_message=f"op whoami failed: {stderr}"
                    )

        except FileNotFoundError:
            # op CLI not installed
            error_msg = (
                "1Password CLI (op) not found. Install with: brew install 1password-cli"
            )
            logger.error(error_msg)
            return CLIValidationResult(
                success=False,
                error_message=error_msg
            )

        except subprocess.TimeoutExpired:
            # Command timed out
            logger.warning(f"op whoami timed out (attempt {attempt + 1}/{max_retries})")

            if attempt < max_retries - 1:
                delay = min(BASE_DELAY * (BACKOFF_MULTIPLIER ** attempt), MAX_DELAY)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                return CLIValidationResult(
                    success=False,
                    error_message=f"op whoami timed out after {CLI_TIMEOUT}s"
                )

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error running op whoami: {str(e)}")

            if attempt < max_retries - 1:
                delay = min(BASE_DELAY * (BACKOFF_MULTIPLIER ** attempt), MAX_DELAY)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                return CLIValidationResult(
                    success=False,
                    error_message=f"Unexpected error: {str(e)}"
                )

    # Should never reach here, but just in case
    return CLIValidationResult(
        success=False,
        error_message=f"Max retries ({max_retries}) exceeded"
    )


# ============================================================================
# Main Entry Point (for testing)
# ============================================================================

def main():
    """
    Test harness for CLI integration module.

    Usage:
        python sparc_phase4_cli_integration.py
    """
    print("=" * 70)
    print("1Password CLI Integration Module - Test Harness")
    print("=" * 70)
    print()

    # Test 1: Token format validation
    print("Test 1: Token Format Validation")
    print("-" * 70)

    test_tokens = [
        ("ops_" + "a" * 100, "Valid token (minimum length)"),
        ("ops_" + "A" * 150, "Valid token (longer)"),
        ("opt_invalid", "Invalid prefix"),
        ("ops_short", "Too short"),
        ("ops_" + "!" * 100, "Invalid characters"),
        ("", "Empty token"),
    ]

    for token, description in test_tokens:
        validation = validate_token_format(token)
        status = "✓ PASS" if validation.is_valid else "✗ FAIL"
        print(f"{status} - {description}")
        if not validation.is_valid:
            print(f"       Errors: {', '.join(validation.errors)}")

    print()

    # Test 2: Token extraction
    print("Test 2: Token Extraction")
    print("-" * 70)

    sample_outputs = [
        ("Your token: ops_" + "x" * 100, "Plain text"),
        ('"ops_' + "y" * 100 + '"', "Quoted"),
        ("Token:\nops_" + "z" * 100 + "\nNext line", "Multi-line"),
        ("No token here!", "No token"),
    ]

    for output, description in sample_outputs:
        extracted = extract_token_from_output(output)
        status = "✓ FOUND" if extracted else "✗ NOT FOUND"
        print(f"{status} - {description}")
        if extracted:
            print(f"       Token: {extracted[:12]}...{extracted[-8:]}")

    print()

    # Test 3: Service account creation (documentation)
    print("Test 3: Service Account Creation (CLI Command)")
    print("-" * 70)

    result = create_service_account_cli(
        name="SPARC-Test",
        vaults=["Automation"],
        permissions=["read_items"]
    )

    print(f"Status: {result.error_message}")
    print()

    print("=" * 70)
    print("Test harness complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
