#!/usr/bin/env python3
"""
SPARC Phase 4: Decision Engine for Autonomous Browser Automation

This module analyzes browser page state (DOM, URL, visible elements),
selects the next automation action, provides retry strategies for
errors, and logs decisions with explicit reasoning.

Author: SPARC Phase 4
Date: 2026-01-01
Status: PRODUCTION-READY
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

class ActionType(Enum):
    """Supported action types for browser automation."""

    CLICK = "click"
    FILL = "fill"
    NAVIGATE = "navigate"
    EXTRACT = "extract"
    RETRY = "retry"


@dataclass
class Action:
    """Represents the next automation action with reasoning."""

    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    reason: str = ""
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize action for logging or debugging."""
        return {
            "action_type": self.action_type.value,
            "selector": self.selector,
            "value": self.value,
            "url": self.url,
            "description": self.description,
            "reason": self.reason,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class RetryStrategy:
    """Retry strategy for recoverable errors."""

    name: str
    max_attempts: int
    base_delay_sec: float = 1.0
    max_delay_sec: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.2
    retryable: bool = True
    reason: str = ""

    def next_delay_sec(self, attempt: int) -> float:
        """Compute the next delay using exponential backoff with jitter."""
        if attempt < 1:
            attempt = 1
        delay = self.base_delay_sec * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay_sec)
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0.0, delay)

    def should_retry(self, attempt: int) -> bool:
        """Return True if another retry should be attempted."""
        return self.retryable and attempt < self.max_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Serialize strategy for logging or debugging."""
        return {
            "name": self.name,
            "max_attempts": self.max_attempts,
            "base_delay_sec": self.base_delay_sec,
            "max_delay_sec": self.max_delay_sec,
            "backoff_factor": self.backoff_factor,
            "jitter": self.jitter,
            "retryable": self.retryable,
            "reason": self.reason,
        }


@dataclass
class DecisionContext:
    """Mutable decision context derived from page state."""

    url: str = ""
    dom: str = ""
    visible_elements: List[Dict[str, Any]] = field(default_factory=list)
    intent: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    last_action: Optional[Action] = None
    last_result: Optional[Any] = None
    last_error: Optional[Exception] = None
    retry_count: int = 0
    history: List[Action] = field(default_factory=list)
    decision_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_page_state(cls, page_state: Dict[str, Any]) -> "DecisionContext":
        """Create or update a context from page state."""
        existing = page_state.get("context")
        if isinstance(existing, cls):
            existing.update_from_page_state(page_state)
            return existing

        return cls(
            url=str(page_state.get("url", "") or ""),
            dom=str(page_state.get("dom", "") or ""),
            visible_elements=_coerce_elements(page_state.get("visible_elements") or []),
            intent=dict(page_state.get("intent") or {}),
            errors=_coerce_error_list(page_state.get("errors") or page_state.get("error")),
            last_action=page_state.get("last_action"),
            last_result=page_state.get("last_result"),
            last_error=page_state.get("last_error"),
            retry_count=int(page_state.get("retry_count", 0) or 0),
            metadata=dict(page_state.get("metadata") or {}),
        )

    def update_from_page_state(self, page_state: Dict[str, Any]) -> None:
        """Update context with new page state data."""
        self.url = str(page_state.get("url", self.url) or self.url)
        dom = page_state.get("dom")
        if dom is not None:
            self.dom = str(dom)
        visible = page_state.get("visible_elements")
        if visible is not None:
            self.visible_elements = _coerce_elements(visible)
        intent = page_state.get("intent")
        if intent is not None:
            self.intent = dict(intent)
        errors = page_state.get("errors") or page_state.get("error")
        if errors:
            self.errors = _coerce_error_list(errors)
        if "last_action" in page_state:
            self.last_action = page_state.get("last_action")
        if "last_result" in page_state:
            self.last_result = page_state.get("last_result")
        if "last_error" in page_state:
            self.last_error = page_state.get("last_error")
        if "retry_count" in page_state:
            self.retry_count = int(page_state.get("retry_count") or 0)
        if "metadata" in page_state:
            self.metadata = dict(page_state.get("metadata") or {})

    def record_decision(self, action: Action) -> None:
        """Record a decision into the context log."""
        self.last_action = action
        self.history.append(action)
        self.decision_log.append(
            {
                "timestamp": time.time(),
                "action": action.to_dict(),
                "reason": action.reason,
                "confidence": action.confidence,
            }
        )


@dataclass
class PageAnalysis:
    """Structured analysis of the current page state."""

    url: str
    dom_text: str
    visible_elements: List[Dict[str, Any]]
    clickables: List[Dict[str, Any]]
    inputs: List[Dict[str, Any]]
    errors: List[str]
    signals: Dict[str, bool]


# ---------------------------------------------------------------------------
# CORE DECISION ENGINE
# ---------------------------------------------------------------------------

class DecisionEngine:
    """Async decision engine that selects the next action."""

    def __init__(self, logger_: Optional[logging.Logger] = None) -> None:
        self._logger = logger_ or logger

    @staticmethod
    async def get_retry_strategy(error: Exception) -> RetryStrategy:
        """Expose retry strategy selection for external callers."""
        return await get_retry_strategy(error)

    async def decide(self, context: DecisionContext) -> Action:
        """Analyze page state and decide the next action."""
        analysis = await self._analyze(context)
        action = await self._select_action(context, analysis)
        context.record_decision(action)
        self._log_decision(context, action, analysis)
        return action

    async def _analyze(self, context: DecisionContext) -> PageAnalysis:
        """Analyze DOM, URL, and visible elements."""
        await asyncio.sleep(0)
        url = context.url
        dom_text = _normalize_text(context.dom)
        visible = _coerce_elements(context.visible_elements)
        clickables = [el for el in visible if _is_clickable(el)]
        inputs = [el for el in visible if _is_input(el)]
        errors = _extract_errors(dom_text, visible, context.errors)
        signals = {
            "has_error": bool(errors),
            "has_inputs": bool(inputs),
            "has_clickables": bool(clickables),
            "is_login": _detect_login(dom_text, url, visible),
            "has_captcha": _detect_captcha(dom_text),
        }
        return PageAnalysis(
            url=url,
            dom_text=dom_text,
            visible_elements=visible,
            clickables=clickables,
            inputs=inputs,
            errors=errors,
            signals=signals,
        )

    async def _select_action(
        self,
        context: DecisionContext,
        analysis: PageAnalysis,
    ) -> Action:
        """Select the next action based on analysis and intent."""
        retry_action = await self._maybe_retry(context)
        if retry_action is not None:
            return retry_action

        if analysis.signals.get("has_captcha"):
            return Action(
                action_type=ActionType.RETRY,
                reason="captcha_detected",
                description="Captcha detected; retrying after delay",
                confidence=0.2,
                metadata={"requires_manual": True},
            )

        if analysis.signals.get("has_error"):
            return Action(
                action_type=ActionType.RETRY,
                reason="page_error_detected",
                description="Detected error markers in DOM or visible elements",
                confidence=0.4,
                metadata={"errors": analysis.errors},
            )

        navigate_action = self._maybe_navigate(context, analysis)
        if navigate_action is not None:
            return navigate_action

        extract_action = self._maybe_extract(context, analysis)
        if extract_action is not None:
            return extract_action

        fill_action = self._maybe_fill(context, analysis)
        if fill_action is not None:
            return fill_action

        click_action = self._maybe_click(context, analysis)
        if click_action is not None:
            return click_action

        return Action(
            action_type=ActionType.RETRY,
            reason="no_action_candidates",
            description="No clear action candidates; retrying after delay",
            confidence=0.1,
        )

    async def _maybe_retry(self, context: DecisionContext) -> Optional[Action]:
        """Retry if the last result indicates a failure."""
        if context.last_result is None:
            return None

        result_ok = await evaluate_result(context.last_result)
        if result_ok:
            return None

        strategy = None
        if context.last_error is not None:
            strategy = await get_retry_strategy(context.last_error)

        if strategy is not None and not strategy.retryable:
            return None

        if strategy is not None and not strategy.should_retry(context.retry_count):
            return Action(
                action_type=ActionType.RETRY,
                reason="retry_exhausted",
                description="Retry limit reached for last error",
                confidence=0.2,
                metadata={"strategy": strategy.to_dict()},
            )

        return Action(
            action_type=ActionType.RETRY,
            reason="last_result_failed",
            description="Last action failed; retrying",
            confidence=0.5,
            metadata={"strategy": strategy.to_dict() if strategy else None},
        )

    def _maybe_navigate(
        self,
        context: DecisionContext,
        analysis: PageAnalysis,
    ) -> Optional[Action]:
        """Decide if navigation is needed."""
        target_url = _first_truthy(
            context.intent.get("target_url"),
            context.metadata.get("target_url"),
        )
        if not target_url:
            return None

        if _url_matches(analysis.url, target_url):
            return None

        return Action(
            action_type=ActionType.NAVIGATE,
            url=target_url,
            reason="target_url_mismatch",
            description=f"Navigate to target URL: {target_url}",
            confidence=0.9,
        )

    def _maybe_extract(
        self,
        context: DecisionContext,
        analysis: PageAnalysis,
    ) -> Optional[Action]:
        """Decide if extraction should occur."""
        extract_targets = _first_truthy(
            context.intent.get("extract"),
            context.intent.get("extract_selectors"),
            context.metadata.get("extract"),
            context.metadata.get("extract_selectors"),
        )
        if not extract_targets:
            return None

        return Action(
            action_type=ActionType.EXTRACT,
            reason="extraction_requested",
            description="Extraction targets provided in intent",
            confidence=0.8,
            metadata={"targets": extract_targets},
        )

    def _maybe_fill(
        self,
        context: DecisionContext,
        analysis: PageAnalysis,
    ) -> Optional[Action]:
        """Decide if a form field should be filled."""
        if not analysis.inputs:
            return None

        form_data = _first_truthy(
            context.intent.get("form_data"),
            context.intent.get("inputs"),
            context.metadata.get("form_data"),
        )

        if isinstance(form_data, dict) and form_data:
            candidate = _select_best_input(analysis.inputs, form_data)
            if candidate is not None:
                element, field_key, value, score = candidate
                return Action(
                    action_type=ActionType.FILL,
                    selector=element.get("selector"),
                    value=str(value),
                    reason=f"fill_field:{field_key}",
                    description="Fill input based on form_data mapping",
                    confidence=min(1.0, 0.4 + score * 0.6),
                    metadata={"field": field_key, "match_score": score},
                )

        query_value = _first_truthy(
            context.intent.get("query"),
            context.intent.get("text"),
            context.intent.get("value"),
        )
        if query_value:
            search_input = _select_search_input(analysis.inputs)
            if search_input:
                return Action(
                    action_type=ActionType.FILL,
                    selector=search_input.get("selector"),
                    value=str(query_value),
                    reason="fill_search_query",
                    description="Fill search input with query",
                    confidence=0.6,
                )

        return None

    def _maybe_click(
        self,
        context: DecisionContext,
        analysis: PageAnalysis,
    ) -> Optional[Action]:
        """Decide if a click action should be taken."""
        if not analysis.clickables:
            return None

        selector_override = context.intent.get("click_selector")
        if selector_override:
            return Action(
                action_type=ActionType.CLICK,
                selector=str(selector_override),
                reason="click_selector_override",
                description="Click selector provided by intent",
                confidence=0.8,
            )

        text_override = context.intent.get("click_text")
        if text_override:
            match = _match_click_text(analysis.clickables, str(text_override))
            if match is not None:
                return Action(
                    action_type=ActionType.CLICK,
                    selector=match.get("selector"),
                    reason="click_text_override",
                    description="Click element matching intent text",
                    confidence=0.7,
                    metadata={"matched_text": text_override},
                )

        candidate = _select_best_click(analysis.clickables)
        if candidate is None:
            return None

        element, label, score = candidate
        return Action(
            action_type=ActionType.CLICK,
            selector=element.get("selector"),
            reason=f"click_candidate:{label}",
            description="Click highest-priority visible element",
            confidence=min(1.0, 0.3 + score * 0.7),
            metadata={"label": label, "score": score},
        )

    def _log_decision(
        self,
        context: DecisionContext,
        action: Action,
        analysis: PageAnalysis,
    ) -> None:
        """Log the decision with reasoning."""
        self._logger.info(
            "Decision: %s | reason=%s | url=%s | confidence=%.2f",
            action.action_type.value,
            action.reason,
            analysis.url,
            action.confidence,
        )


# ---------------------------------------------------------------------------
# PUBLIC API FUNCTIONS (ASYNC)
# ---------------------------------------------------------------------------

async def decide_next_action(page_state: Dict[str, Any]) -> Action:
    """
    Analyze the page state and decide the next automation action.

    Args:
        page_state: Dictionary containing url, dom, visible_elements, and intent.

    Returns:
        Action describing what to do next.
    """
    context = DecisionContext.from_page_state(page_state)
    engine = DecisionEngine()
    return await engine.decide(context)


async def evaluate_result(result: Any) -> bool:
    """
    Evaluate whether an automation result indicates success.

    Args:
        result: Any result object from the automation layer.

    Returns:
        True if result indicates success, False otherwise.
    """
    await asyncio.sleep(0)

    if result is None:
        return False
    if isinstance(result, bool):
        return result
    if isinstance(result, dict):
        if "success" in result:
            return bool(result.get("success"))
        if "ok" in result:
            return bool(result.get("ok"))
        if "status" in result:
            status = str(result.get("status")).lower()
            return status in {"ok", "success", "completed", "done", "true"}
        if "error" in result:
            return False
    if hasattr(result, "ok"):
        return bool(getattr(result, "ok"))
    if hasattr(result, "status"):
        try:
            status_val = int(getattr(result, "status"))
            return 200 <= status_val < 300
        except (TypeError, ValueError):
            pass

    return True


async def get_retry_strategy(error: Exception) -> RetryStrategy:
    """
    Map an error to a retry strategy.

    Args:
        error: The exception that occurred.

    Returns:
        RetryStrategy describing how to retry.
    """
    await asyncio.sleep(0)

    if isinstance(error, asyncio.TimeoutError):
        return RetryStrategy(
            name="timeout",
            max_attempts=3,
            base_delay_sec=1.0,
            backoff_factor=2.0,
            jitter=0.3,
            reason="Timeout while waiting for page or element",
        )

    if isinstance(error, (ConnectionError, OSError)):
        return RetryStrategy(
            name="network",
            max_attempts=5,
            base_delay_sec=1.5,
            backoff_factor=2.0,
            jitter=0.2,
            reason="Network or transport error",
        )

    error_text = str(error).lower()
    if "timeout" in error_text:
        return RetryStrategy(
            name="timeout",
            max_attempts=3,
            base_delay_sec=1.0,
            backoff_factor=2.0,
            jitter=0.3,
            reason="Timeout reported by error message",
        )
    if "captcha" in error_text:
        return RetryStrategy(
            name="captcha",
            max_attempts=1,
            base_delay_sec=5.0,
            backoff_factor=1.0,
            jitter=0.0,
            reason="Captcha detected; allow manual resolution",
        )
    if any(token in error_text for token in ("invalid", "not found", "missing")):
        return RetryStrategy(
            name="non_retryable",
            max_attempts=0,
            retryable=False,
            reason="Non-retryable input or selector error",
        )

    return RetryStrategy(
        name="generic",
        max_attempts=2,
        base_delay_sec=1.0,
        backoff_factor=2.0,
        jitter=0.2,
        reason="Unhandled error; default retry strategy",
    )


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower()
    return re.sub(r"\s+", " ", lowered).strip()


def _coerce_elements(elements: Iterable[Any]) -> List[Dict[str, Any]]:
    coerced: List[Dict[str, Any]] = []
    for item in elements:
        if isinstance(item, dict):
            coerced.append(item)
        elif isinstance(item, str):
            coerced.append({"text": item, "visible": True})
        else:
            coerced.append({"text": str(item), "visible": True})
    return coerced


def _coerce_error_list(errors: Any) -> List[str]:
    if errors is None:
        return []
    if isinstance(errors, list):
        return [str(err) for err in errors]
    return [str(errors)]


def _extract_errors(dom_text: str, elements: List[Dict[str, Any]], errors: List[str]) -> List[str]:
    found = list(errors)
    if "error" in dom_text or "failed" in dom_text or "try again" in dom_text:
        found.append("dom_error_marker")
    for el in elements:
        text = _element_text(el)
        if any(token in text for token in ("error", "failed", "invalid", "try again")):
            found.append(text)
    return found


def _element_text(element: Dict[str, Any]) -> str:
    parts = [
        element.get("text"),
        element.get("label"),
        element.get("aria_label"),
        element.get("name"),
        element.get("placeholder"),
        element.get("value"),
    ]
    combined = " ".join([str(p) for p in parts if p])
    return _normalize_text(combined)


def _is_clickable(element: Dict[str, Any]) -> bool:
    if element.get("visible") is False:
        return False
    role = str(element.get("role", "")).lower()
    tag = str(element.get("tag", "")).lower()
    if element.get("clickable") is True:
        return True
    if role in {"button", "link", "menuitem", "tab"}:
        return True
    if tag in {"button", "a"}:
        return True
    return False


def _is_input(element: Dict[str, Any]) -> bool:
    if element.get("visible") is False:
        return False
    role = str(element.get("role", "")).lower()
    tag = str(element.get("tag", "")).lower()
    input_type = str(element.get("type", "")).lower()
    if role in {"textbox", "combobox", "searchbox"}:
        return True
    if tag in {"input", "textarea", "select"}:
        return True
    if input_type in {"text", "email", "password", "search", "tel", "url"}:
        return True
    return False


def _detect_login(dom_text: str, url: str, elements: List[Dict[str, Any]]) -> bool:
    if any(token in url.lower() for token in ("login", "signin", "sign-in")):
        return True
    if any(token in dom_text for token in ("password", "sign in", "log in")):
        return True
    for el in elements:
        if any(token in _element_text(el) for token in ("sign in", "log in", "password")):
            return True
    return False


def _detect_captcha(dom_text: str) -> bool:
    return any(token in dom_text for token in ("captcha", "recaptcha", "hcaptcha"))


def _first_truthy(*values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None


def _url_matches(current_url: str, target_url: str) -> bool:
    if not current_url or not target_url:
        return False
    if current_url == target_url:
        return True
    if current_url.startswith(target_url):
        return True
    return target_url in current_url


def _select_best_input(
    inputs: List[Dict[str, Any]],
    form_data: Dict[str, Any],
) -> Optional[Tuple[Dict[str, Any], str, Any, float]]:
    best: Optional[Tuple[Dict[str, Any], str, Any, float]] = None
    for element in inputs:
        if _is_filled(element):
            continue
        element_text = _element_text(element)
        for field_key, value in form_data.items():
            score = _score_match(element_text, str(field_key))
            if score <= 0:
                continue
            if best is None or score > best[3]:
                best = (element, str(field_key), value, score)
    return best


def _select_search_input(inputs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for element in inputs:
        if _is_filled(element):
            continue
        text = _element_text(element)
        if "search" in text:
            return element
        input_type = str(element.get("type", "")).lower()
        if input_type == "search":
            return element
    return None


def _select_best_click(
    clickables: List[Dict[str, Any]],
) -> Optional[Tuple[Dict[str, Any], str, float]]:
    priority = [
        "continue",
        "next",
        "submit",
        "save",
        "ok",
        "yes",
        "allow",
        "accept",
        "sign in",
        "log in",
        "login",
        "create",
        "start",
        "finish",
        "done",
    ]
    best: Optional[Tuple[Dict[str, Any], str, float]] = None
    for element in clickables:
        text = _element_text(element)
        for rank, label in enumerate(priority):
            if label in text:
                score = 1.0 - (rank / max(1, len(priority)))
                if best is None or score > best[2]:
                    best = (element, label, score)
    return best


def _match_click_text(
    clickables: List[Dict[str, Any]],
    target_text: str,
) -> Optional[Dict[str, Any]]:
    target = _normalize_text(target_text)
    if not target:
        return None
    for element in clickables:
        if target in _element_text(element):
            return element
    return None


def _is_filled(element: Dict[str, Any]) -> bool:
    value = element.get("value")
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return bool(value)


def _score_match(element_text: str, field_key: str) -> float:
    if not element_text or not field_key:
        return 0.0
    element_text = _normalize_text(element_text)
    field_key = _normalize_text(field_key)
    if element_text == field_key:
        return 1.0
    if field_key in element_text:
        return 0.8
    if element_text in field_key:
        return 0.6
    tokens = set(field_key.split())
    if tokens and any(token in element_text for token in tokens):
        return 0.4
    return 0.0
