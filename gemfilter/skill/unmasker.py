"""
Gem Unmasker for GemFilter Skill.

Sanitizes LLM responses containing fake gem placeholders.
"""

import re
from typing import Dict, List, Optional, Tuple

from gemfilter.core.filter import SandFilter, FilterResult


class GemUnmasker:
    """
    Sanitizes responses containing fake gem placeholders.

    Ensures that:
    1. Fake placeholders are replaced with [FILTERED] markers
    2. Real gems never leak through
    3. New sensitive content in responses is also masked
    """

    # Marker for filtered content
    FILTERED_MARKER = "[FILTERED]"

    def __init__(
        self,
        filter_engine: Optional[SandFilter] = None,
        check_response_content: bool = True,
    ):
        """
        Initialize GemUnmasker.

        Args:
            filter_engine: SandFilter instance for detecting new gems in response.
                          If None, creates a default one.
            check_response_content: Whether to also mask NEW gems in LLM response.
                                   Default: True
        """
        self._filter_engine = filter_engine or SandFilter()
        self._check_response_content = check_response_content

    def restore(
        self,
        text: str,
        session_id: str,
        get_original_func: Optional[callable] = None,
    ) -> str:
        """
        Sanitize text by replacing fake placeholders with [FILTERED].

        IMPORTANT: Real gems never leave the machine. We NEVER return
        original values - only [FILTERED] markers.

        Args:
            text: LLM response text potentially containing fake placeholders
            session_id: Session ID to look up mappings
            get_original_func: Optional function(session_id, fake) -> original.
                               If not provided, uses in-memory mapping.

        Returns:
            Sanitized text with fake placeholders replaced by [FILTERED]
        """
        # Find all fake placeholders in text
        fake_values = self._find_fake_placeholders(text)

        if not fake_values:
            # No fakes found, still check for new gems if enabled
            if self._check_response_content:
                return self._mask_new_gems(text)
            return text

        # Replace all fake placeholders with [FILTERED]
        sanitized = text
        for fake in fake_values:
            sanitized = sanitized.replace(fake, self.FILTERED_MARKER)

        # Check for new gems in response if enabled
        if self._check_response_content:
            sanitized = self._mask_new_gems(sanitized)

        return sanitized

    def restore_with_marker(
        self,
        text: str,
        marker: Optional[str] = None,
    ) -> Tuple[str, int]:
        """
        Replace all fake placeholders with a custom marker.

        Args:
            text: Text containing fake placeholders
            marker: Custom marker string. If None, uses [FILTERED].

        Returns:
            Tuple of (sanitized_text, count_of_replacements)
        """
        if marker is None:
            marker = self.FILTERED_MARKER

        fake_values = self._find_fake_placeholders(text)
        count = 0

        sanitized = text
        for fake in fake_values:
            if fake in sanitized:
                sanitized = sanitized.replace(fake, marker)
                count += 1

        return sanitized, count

    def _find_fake_placeholders(self, text: str) -> List[str]:
        """
        Find all potential fake placeholder patterns in text.

        Looks for common fake patterns like:
        - t***@domain.com
        - 138****5678
        - sk-****xyz
        - AKIA***********XXXX
        - [API_KEY:xxxx***]
        - etc.

        Returns:
            List of detected fake placeholder strings
        """
        fake_patterns = [
            # Balanced email placeholders: <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>
            r"<EMAIL_LOCAL_\d+>@<EMAIL_DOMAIN_\d+>",
            # Typed GemFilter placeholders: <EMAIL_1>, <SECRET_2>, etc.
            r"<[A-Z][A-Z0-9_]*_\d+(?:_\d+)?>",
            # Email-ish patterns: t***@domain.com, t***@domain.com_ema
            r"[a-zA-Z0-9][\*]{2,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:_[a-zA-Z0-9]+)?",
            # Phone-ish patterns: 138****5678, (***) ***-1234
            r"1\d{2}[\*]{4}\d{4}",
            r"\(\*{3}\) \*{3}-\d{4}",
            # API key generic: sk-****xyz
            r"sk-[\*]{3,}[a-zA-Z0-9]{2,}",
            r"sk-[\*]{3,}",
            # AWS access key: AKIA***XXXX
            r"AKIA\*+[A-Z0-9]{4,}",
            # Bracketed API key: [API_KEY:xxxx***]
            r"\[API_KEY:[^\]]+\]",
            # Bearer token: Bearer [TOKEN]
            r"Bearer \[TOKEN\]",
            # Credit card: 4111 **** **** 1111
            r"\d{4} \*{4} \*{4} \d{4}",
            # Generic masked: A*********9
            r"[A-Z0-9][\*]{3,}[A-Z0-9]",
            # IP addresses with masks: 192.168.***.***
            r"\d{1,3}\.\d{1,3}\.\*{3}\.\*{3}",
            # MAC with masks: AA:***:***:***:***:FF
            r"[0-9A-Fa-f]{2}:[\*]{3}:[\*]{3}:[\*]{3}:[0-9A-Fa-f]{2}",
            # URL masked: https://***.example.com
            r"https?://\*\*\*\.[a-zA-Z0-9.-]+[^\s]*",
            # Generic bracketed: [FILTERED] or [PRIVATE_KEY] etc
            r"\[(?:FILTERED|PRIVATE_KEY|PASSWORD|API_KEY|TOKEN)\]",
            # Suffix pattern from our masker: xxx_type (e.g., xxx_ema, xxx_api)
            r"[\*a-zA-Z0-9]{4,}_(?:ema|api|pho|pas|cre|aws|url|ip4|ip6|mac)",
        ]

        found = []
        for pattern in fake_patterns:
            matches = re.findall(pattern, text)
            found.extend(matches)

        return list(set(found))  # Deduplicate

    def _mask_new_gems(self, text: str) -> str:
        """
        Mask any NEW sensitive content in the LLM response.

        This catches cases where the LLM generates its own
        sensitive information (e.g., example credentials).

        Args:
            text: Text to check

        Returns:
            Text with new gems masked
        """
        result: FilterResult = self._filter_engine.filter(text)

        if not result.detections:
            return text

        # Sort by position in reverse order for replacement
        sorted_detections = sorted(
            result.detections,
            key=lambda d: d.start,
            reverse=True,
        )

        masked_text = text
        for detection in sorted_detections:
            # Replace with generic marker based on rule name
            marker = f"[{detection.rule_name.upper()}]"
            masked_text = (
                masked_text[:detection.start]
                + marker
                + masked_text[detection.end:]
            )

        return masked_text

    def has_fake_placeholders(self, text: str) -> bool:
        """
        Check if text contains any fake placeholders.

        Args:
            text: Text to check

        Returns:
            True if fake placeholders found, False otherwise
        """
        return len(self._find_fake_placeholders(text)) > 0

    def get_fake_count(self, text: str) -> int:
        """
        Count fake placeholders in text.

        Args:
            text: Text to check

        Returns:
            Number of fake placeholders found
        """
        return len(self._find_fake_placeholders(text))


class ResponseSanitizer:
    """
    High-level response sanitization with detailed reporting.
    """

    def __init__(self, unmasker: Optional[GemUnmasker] = None):
        """
        Initialize ResponseSanitizer.

        Args:
            unmasker: GemUnmasker instance. Creates default if None.
        """
        self._unmasker = unmasker or GemUnmasker()

    def sanitize(
        self,
        text: str,
        session_id: str,
        get_mapping_func: Optional[callable] = None,
    ) -> Tuple[str, Dict]:
        """
        Sanitize response and provide detailed report.

        Args:
            text: LLM response text
            session_id: Session ID for mapping lookup
            get_mapping_func: Optional function to get original value

        Returns:
            Tuple of (sanitized_text, report_dict)
        """
        report = {
            "original_length": len(text),
            "fake_placeholders_found": 0,
            "new_gems_masked": 0,
            "sanitized_length": 0,
            "had_sensitive_content": False,
        }

        # Find fake placeholders before sanitization
        fakes_before = self._unmasker.get_fake_count(text)
        report["fake_placeholders_found"] = fakes_before

        # Check for new gems before sanitization
        detections_before = self._unmasker._filter_engine.filter(text).detections
        report["new_gems_masked"] = len(detections_before)
        report["had_sensitive_content"] = (
            fakes_before > 0 or len(detections_before) > 0
        )

        # Perform sanitization
        sanitized = self._unmasker.restore(text, session_id, get_mapping_func)
        report["sanitized_length"] = len(sanitized)

        return sanitized, report

    def get_detections(self, text: str) -> List:
        """
        Get all gem detections in text.

        Args:
            text: Text to check

        Returns:
            List of Detection objects
        """
        return self._unmasker._filter_engine.filter(text).detections
