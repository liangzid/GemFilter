"""
Hook Manager for GemFilter Skill.

Implements pre-send and post-receive hooks for AI agents.
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .session import SessionManager, get_session_manager, Session
from .masker import GemMasker
from .unmasker import GemUnmasker
from .ui import UINotifier, NotificationStyle
from .config import SkillConfig, load_skill_config


logger = logging.getLogger(__name__)


@dataclass
class HookResult:
    """Result of a hook execution."""
    success: bool
    payload: Any
    error: Optional[str] = None
    gems_detected: int = 0
    notification: Optional[str] = None


class HookManager:
    """
    Manages pre-send and post-receive hooks for gem filtering.

    This is the core orchestration class that coordinates
    masking, session management, and unmasking.
    """

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        masker: Optional[GemMasker] = None,
        unmasker: Optional[GemUnmasker] = None,
        notifier: Optional[UINotifier] = None,
        skill_config: Optional[SkillConfig] = None,
    ):
        """
        Initialize HookManager.

        Args:
            session_manager: SessionManager instance
            masker: GemMasker instance
            unmasker: GemUnmasker instance
            notifier: UINotifier instance
            skill_config: SkillConfig instance
        """
        self._session_manager = session_manager or get_session_manager()
        self._masker = masker or GemMasker()
        self._unmasker = unmasker or GemUnmasker()
        self._notifier = notifier or UINotifier()
        self._config = skill_config or load_skill_config()
        self._lock = threading.RLock()
        self._active_sessions: Dict[str, bool] = {}

    @property
    def config(self) -> SkillConfig:
        """Get skill configuration."""
        return self._config

    @property
    def masker(self) -> GemMasker:
        """Get masker instance."""
        return self._masker

    @property
    def unmasker(self) -> GemUnmasker:
        """Get unmasker instance."""
        return self._unmasker

    @property
    def session_manager(self) -> SessionManager:
        """Get session manager instance."""
        return self._session_manager

    def pre_send(
        self,
        payload: Any,
        session_id: Optional[str] = None,
    ) -> HookResult:
        """
        Pre-send hook: Mask gems before sending to LLM.

        Args:
            payload: The payload to send (usually text or dict with text fields)
            session_id: Optional session ID. Creates new if not provided.

        Returns:
            HookResult with masked payload and session info
        """
        with self._lock:
            try:
                # Create or get session
                if session_id is None:
                    session_id = self._session_manager.create_session()
                else:
                    # Ensure session exists
                    if self._session_manager.get_session(session_id) is None:
                        self._session_manager.create_session(session_id)

                self._active_sessions[session_id] = True

                # Extract text from payload
                text, is_dict, original_fields = self._extract_text(payload)

                if not text:
                    return HookResult(
                        success=True,
                        payload=payload,
                        gems_detected=0,
                    )

                # Detect gems
                detections = self._masker.get_detections(text)
                gem_count = len(detections)
                gem_types = list(set(d.rule_name for d in detections))

                if gem_count == 0:
                    return HookResult(
                        success=True,
                        payload=payload,
                        gems_detected=0,
                    )

                # Mask gems
                masked_text, mapping = self._masker.mask(text)

                # Store mapping in session
                # mapping is fake -> original
                reverse_mapping = {v: k for k, v in mapping.items()}  # original -> fake
                self._session_manager.add_mappings(
                    session_id,
                    reverse_mapping,  # Store as original -> fake for easy lookup
                    gem_type="mixed",
                )

                # Reconstruct payload
                output_payload = self._reconstruct_payload(
                    payload, masked_text, is_dict, original_fields
                )

                # Generate notification
                notification = self._notifier.notify(gem_count, gem_types)

                logger.info(
                    f"GemFilter pre_send: masked {gem_count} gems in session {session_id}"
                )

                return HookResult(
                    success=True,
                    payload=output_payload,
                    gems_detected=gem_count,
                    notification=notification,
                )

            except Exception as e:
                logger.error(f"GemFilter pre_send error: {e}")
                return HookResult(
                    success=False,
                    payload=payload,
                    error=str(e),
                )

    def post_receive(
        self,
        payload: Any,
        session_id: Optional[str] = None,
    ) -> HookResult:
        """
        Post-receive hook: Sanitize response and restore gems.

        Args:
            payload: The received payload (usually text or dict with text fields)
            session_id: Session ID to look up gem mappings

        Returns:
            HookResult with sanitized payload
        """
        with self._lock:
            try:
                if session_id is None or session_id not in self._active_sessions:
                    # No active session, still check for fake placeholders and new gems
                    text, is_dict, original_fields = self._extract_text(payload)
                    if not text:
                        return HookResult(success=True, payload=payload)

                    # First, replace any fake placeholders with [FILTERED]
                    sanitized_text, fake_count = self._unmasker.restore_with_marker(text)

                    # Then check for new gems in response
                    sanitized_text = self._unmasker._mask_new_gems(sanitized_text)

                    # If nothing changed, return early
                    if sanitized_text == text and fake_count == 0:
                        return HookResult(success=True, payload=payload)

                    output_payload = self._reconstruct_payload(
                        payload, sanitized_text, is_dict, original_fields
                    )
                    return HookResult(
                        success=True,
                        payload=output_payload,
                    )

                # Extract text from payload
                text, is_dict, original_fields = self._extract_text(payload)

                if not text:
                    return HookResult(
                        success=True,
                        payload=payload,
                    )

                # Check for fake placeholders
                fake_count = self._unmasker.get_fake_count(text)

                # Sanitize response
                sanitized_text = self._unmasker.restore(text, session_id)

                # Count masked gems in response
                new_gems = self._unmasker.get_fake_count(sanitized_text) - fake_count

                # Reconstruct payload
                output_payload = self._reconstruct_payload(
                    payload, sanitized_text, is_dict, original_fields
                )

                # Add notification header if needed
                notification = ""
                if new_gems > 0 or fake_count > 0:
                    total_masked = new_gems + fake_count
                    notification = self._notifier.notify(
                        total_masked,
                        ["response_content"] if new_gems > 0 else []
                    )

                # Clean up session
                self._session_manager.clear_session(session_id)
                del self._active_sessions[session_id]

                logger.info(
                    f"GemFilter post_receive: sanitized response in session {session_id}"
                )

                return HookResult(
                    success=True,
                    payload=output_payload,
                    gems_detected=fake_count + new_gems,
                    notification=notification,
                )

            except Exception as e:
                logger.error(f"GemFilter post_receive error: {e}")
                return HookResult(
                    success=False,
                    payload=payload,
                    error=str(e),
                )

    def _extract_text(
        self, payload: Any
    ) -> Tuple[str, bool, List[str]]:
        """
        Extract text from payload.

        Args:
            payload: Input payload

        Returns:
            Tuple of (text, is_dict, field_names)
        """
        if isinstance(payload, str):
            return payload, False, []
        elif isinstance(payload, dict):
            # Look for common text fields
            text_fields = ["text", "content", "message", "prompt", "input", "query"]
            for field in text_fields:
                if field in payload and isinstance(payload[field], str):
                    return payload[field], True, [field]
            # Check all string fields
            for key, value in payload.items():
                if isinstance(value, str) and len(value) > 0:
                    return value, True, [key]
            return "", True, []
        else:
            return str(payload), False, []

    def _reconstruct_payload(
        self,
        payload: Any,
        text: str,
        is_dict: bool,
        original_fields: List[str],
    ) -> Any:
        """
        Reconstruct payload with modified text.

        Args:
            payload: Original payload
            text: Modified text
            is_dict: Whether original was a dict
            original_fields: Field names that contained text

        Returns:
            Reconstructed payload
        """
        if is_dict:
            result = dict(payload)
            if original_fields:
                for field in original_fields:
                    result[field] = text
            else:
                result["text"] = text
            return result
        else:
            return text

    def register_with_agent(self, adapter) -> None:
        """
        Register hooks with an agent adapter.

        Args:
            adapter: AgentAdapter instance
        """
        adapter.register_hooks(
            pre_send=lambda p: self.pre_send(p),
            post_receive=lambda p: self.post_receive(p),
        )


# Global hook manager instance
_global_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get the global HookManager instance."""
    global _global_hook_manager
    if _global_hook_manager is None:
        _global_hook_manager = HookManager()
    return _global_hook_manager


def set_hook_manager(manager: HookManager) -> None:
    """Set the global HookManager instance."""
    global _global_hook_manager
    _global_hook_manager = manager


# Standalone hook functions for direct use
def pre_send_hook(payload: Any, session_id: Optional[str] = None) -> HookResult:
    """
    Pre-send hook function.

    Can be registered with Claude Code hooks or called directly.

    Args:
        payload: The payload to filter
        session_id: Optional session ID

    Returns:
        HookResult
    """
    manager = get_hook_manager()
    return manager.pre_send(payload, session_id)


def post_receive_hook(payload: Any, session_id: Optional[str] = None) -> HookResult:
    """
    Post-receive hook function.

    Can be registered with Claude Code hooks or called directly.

    Args:
        payload: The payload to sanitize
        session_id: Optional session ID

    Returns:
        HookResult
    """
    manager = get_hook_manager()
    return manager.post_receive(payload, session_id)


# Convenience functions
def filter_text(text: str) -> Tuple[str, Dict[str, str], str]:
    """
    Filter gems from text.

    Args:
        text: Input text

    Returns:
        Tuple of (masked_text, mapping, notification)
    """
    manager = get_hook_manager()
    result = manager.pre_send(text)
    if result.success:
        mapping = {}
        # We don't have access to mapping directly, so we re-detect
        detections = manager.masker.get_detections(text)
        masked_text = result.payload if isinstance(result.payload, str) else text
        return masked_text, mapping, result.notification or ""
    return text, {}, ""


def sanitize_response(text: str, session_id: str) -> Tuple[str, str]:
    """
    Sanitize LLM response.

    Args:
        text: Response text
        session_id: Session ID

    Returns:
        Tuple of (sanitized_text, notification)
    """
    manager = get_hook_manager()
    result = manager.post_receive(text, session_id)
    if result.success:
        return result.payload, result.notification or ""
    return text, ""
