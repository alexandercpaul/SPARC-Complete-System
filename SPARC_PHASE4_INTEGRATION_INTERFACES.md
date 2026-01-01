# SPARC Phase 4: Integration Orchestrator - Key Interfaces

## Quick Reference

### Import
```python
from sparc_phase4_integration import (
    Orchestrator,
    OrchestrationResult,
    OrchestrationContext,
    OrchestrationState,
    orchestrate_sync
)
```

## Class: OrchestrationState (Enum)

State machine states for workflow orchestration.

```python
class OrchestrationState(Enum):
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
```

## Class: OrchestrationResult (Dataclass)

Result of orchestration workflow.

### Attributes
```python
@dataclass
class OrchestrationResult:
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
```

### Methods
```python
def __str__(self) -> str:
    """Human-readable representation"""
    return (
        f"[{status}] Account: {self.service_account_name} | "
        f"Duration: {duration}s | "
        f"State: {self.final_state.value} | "
        f"Token: {'✓' if self.token else '✗'} | "
        f"Saved: {'✓' if self.token_saved else '✗'} | "
        f"Tested: {'✓' if self.token_tested else '✗'}"
    )

def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for JSON serialization"""
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
```

## Class: OrchestrationContext (Dataclass)

Mutable state during orchestration workflow.

### Attributes
```python
@dataclass
class OrchestrationContext:
    account_name: str
    vaults: List[str]
    headless: bool = False
    current_state: OrchestrationState = OrchestrationState.INIT
    session_manager: Optional[SessionManager] = None
    auth_status: Optional[AuthStatus] = None
    page: Optional[Any] = None
    token: Optional[str] = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    state_transitions: List[OrchestrationState] = field(default_factory=list)
```

## Class: Orchestrator

Main orchestration engine for Phase 4 workflow.

### Constructor
```python
def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize orchestrator.
    
    Args:
        config: Optional configuration dictionary
    
    Example:
        >>> orchestrator = Orchestrator(config={
        ...     "browser": {"headless": True}
        ... })
    """
```

### Main Orchestration Method
```python
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
    
    Raises:
        RuntimeError: If any step fails
    
    Example:
        >>> orchestrator = Orchestrator()
        >>> result = await orchestrator.orchestrate(
        ...     account_name="SPARC-Automation",
        ...     vaults=["Automation"],
        ...     headless=False
        ... )
        >>> if result.success:
        ...     print(f"Token: {result.token[:20]}...")
    """
```

### Step Methods (Private)

Each step method represents one phase of the workflow:

```python
async def _check_auth_status(self) -> None:
    """Step 1: Check 1Password authentication status"""

async def _init_session_manager(self) -> None:
    """Step 2: Initialize browser session manager"""

async def _open_browser(self) -> None:
    """Step 3: Launch Playwright browser"""

async def _navigate_to_page(self) -> None:
    """Step 4: Navigate to service account creation page"""

async def _fill_account_form(self) -> None:
    """Step 5: Fill account name and vault selections"""

async def _navigate_wizard(self) -> None:
    """Step 6: Navigate through wizard steps"""

async def _extract_service_token(self) -> None:
    """Step 7: Extract service account token from page"""

def _validate_token(self) -> None:
    """Step 8: Validate token format"""

async def _save_token_to_env(self) -> None:
    """Step 9: Save token to ~/.zshrc"""

async def _test_token_with_cli(self) -> None:
    """Step 10: Test token with 1Password CLI"""

async def _cleanup(self) -> None:
    """Step 11: Clean up browser and session resources"""

async def _transition_state(self, new_state: OrchestrationState) -> None:
    """Transition to new state with logging"""
```

## Function: orchestrate_sync

Synchronous wrapper for orchestrate() using asyncio.run().

```python
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
```

## Usage Patterns

### Pattern 1: Async Usage
```python
import asyncio
from sparc_phase4_integration import Orchestrator

async def main():
    orchestrator = Orchestrator()
    result = await orchestrator.orchestrate(
        account_name="MyAccount",
        vaults=["MyVault"],
        headless=False
    )
    
    if result.success:
        print(f"Success: {result.token[:20]}...")
    else:
        print(f"Failed: {result.error_message}")
    
    return 0 if result.success else 1

exit_code = asyncio.run(main())
```

### Pattern 2: Synchronous Usage
```python
from sparc_phase4_integration import orchestrate_sync

result = orchestrate_sync(
    account_name="MyAccount",
    vaults=["MyVault"],
    headless=False
)

print(result)
print(result.to_dict())
```

### Pattern 3: Advanced Configuration
```python
from sparc_phase4_integration import Orchestrator

config = {
    "browser": {
        "headless": True,
        "window_size": [1920, 1080],
        "timeout": 30000,
    },
    "session_file": "/tmp/my_session.json",
    "save_session": True,
}

orchestrator = Orchestrator(config=config)
result = orchestrator.orchestrate(
    account_name="ProductionAccount",
    vaults=["Production"],
    headless=True
)
```

### Pattern 4: Result Inspection
```python
result = orchestrate_sync("Account", ["Vault"])

# Check success
if result.success:
    # Access token (first 20 chars shown)
    print(f"Token: {result.token[:20]}...")
    
    # Check validation status
    print(f"Token validated: {result.token_validated}")
    print(f"Token saved: {result.token_saved}")
    print(f"Token tested: {result.token_tested}")
    
    # Check execution time
    print(f"Duration: {result.duration_seconds:.1f}s")
    
    # Check state transitions
    print(f"States visited: {[s.value for s in result.state_transitions]}")
else:
    # Check error reason
    print(f"Failed at: {result.final_state.value}")
    print(f"Reason: {result.error_message}")
    
    # Check auth status
    if result.auth_status:
        print(f"Auth method: {result.auth_status.detected_method}")
        print(f"Auth confidence: {result.auth_status.confidence_score:.0%}")
```

## Error Handling

All step methods raise `RuntimeError` with descriptive messages:

```python
try:
    result = await orchestrator.orchestrate(
        account_name="Account",
        vaults=["Vault"],
        headless=False
    )
except Exception as e:
    print(f"Orchestration error: {e}")
    # Check result for details even on exception
```

## Logging

All state transitions and steps are logged at INFO level:

```
2026-01-01 12:34:56 - [sparc_phase4_integration] - INFO - Starting orchestration: account=SPARC-Automation, vaults=['Automation'], headless=False
2026-01-01 12:34:56 - [sparc_phase4_integration] - INFO - State transition: init → check_auth
2026-01-01 12:34:58 - [sparc_phase4_integration] - INFO - Checking 1Password authentication status...
2026-01-01 12:34:59 - [sparc_phase4_integration] - INFO - Authentication confirmed: CLI session (op account list) (confidence: 95%)
2026-01-01 12:34:59 - [sparc_phase4_integration] - INFO - State transition: check_auth → session_init
...
```

Enable debug logging for more details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Created:** 2026-01-01  
**Status:** PRODUCTION-READY  
**Module:** `/tmp/sparc_phase4_integration.py`
