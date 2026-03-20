"""
Gem Masker for GemFilter Skill.

Generates fake placeholders that look similar to real gems.
"""

import re
import random
import string
from typing import Dict, List, Tuple, Optional, Callable

from gemfilter.core.filter import SandFilter, FilterResult, Detection


# Type alias for masking functions
MaskFunc = Callable[[str, Optional[str]], str]


class GemMasker:
    """
    Masks sensitive gems with fake placeholders.

    Generates visually similar but fake values to replace real gems
    before they are sent to LLM APIs.
    """

    # Default masking functions for built-in types
    DEFAULT_MASKERS: Dict[str, MaskFunc] = {}

    def __init__(
        self,
        filter_engine: Optional[SandFilter] = None,
        custom_maskers: Optional[Dict[str, MaskFunc]] = None,
    ):
        """
        Initialize GemMasker.

        Args:
            filter_engine: SandFilter instance for detecting gems.
                         If None, creates a default one.
            custom_maskers: Custom masking functions for specific gem types.
                           Format: {gem_type: lambda fake_placeholder, original: ...}
        """
        self._filter_engine = filter_engine or SandFilter()
        self._maskers: Dict[str, MaskFunc] = {}
        self._maskers.update(self._get_default_maskers())
        if custom_maskers:
            self._maskers.update(custom_maskers)

    def _get_default_maskers(self) -> Dict[str, MaskFunc]:
        """Get default masking functions for built-in types."""
        return {
            "email": self._mask_email,
            "phone_cn": self._mask_phone_cn,
            "phone_us": self._mask_phone_us,
            "id_card_cn": self._mask_id_card_cn,
            "passport": self._mask_passport,
            "credit_card": self._mask_credit_card,
            "api_key": self._mask_api_key,
            "api_key_generic": self._mask_api_key_generic,
            "bearer_token": self._mask_bearer_token,
            "aws_access_key": self._mask_aws_access_key,
            "password": self._mask_password,
            "private_key": self._mask_private_key,
            "ipv4": self._mask_ipv4,
            "ipv6": self._mask_ipv6,
            "mac_address": self._mask_mac_address,
            "url": self._mask_url,
        }

    def register_masker(self, gem_type: str, mask_func: MaskFunc) -> None:
        """
        Register a custom masking function for a gem type.

        Args:
            gem_type: The gem type (e.g., "email", "phone")
            mask_func: Function that takes (fake_placeholder, original) and returns masked text
        """
        self._maskers[gem_type] = mask_func

    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask all gems in the text.

        Args:
            text: Input text containing gems

        Returns:
            Tuple of (masked_text, {fake_placeholder: original_value})
        """
        # Detect gems in text
        result: FilterResult = self._filter_engine.filter(text)

        if not result.detections:
            return text, {}

        # Sort detections by position (reverse order for replacement)
        sorted_detections = sorted(
            result.detections,
            key=lambda d: d.start,
            reverse=True,
        )

        mapping: Dict[str, str] = {}
        masked_text = text

        for detection in sorted_detections:
            original = detection.match
            gem_type = detection.rule_name

            # Generate fake placeholder
            fake = self._generate_fake(gem_type, original)

            # Track mapping (fake -> original)
            mapping[fake] = original

            # Replace in text
            masked_text = (
                masked_text[:detection.start]
                + fake
                + masked_text[detection.end:]
            )

        return masked_text, mapping

    def _generate_fake(self, gem_type: str, original: str) -> str:
        """
        Generate a fake placeholder for a gem.

        Args:
            gem_type: The type of gem
            original: The original value

        Returns:
            Fake placeholder value
        """
        masker = self._maskers.get(gem_type)
        if masker:
            # Generate a unique fake placeholder first
            fake_base = masker(original, None)
            # Make it unique to avoid collisions
            return self._ensure_unique(fake_base, gem_type)

        # Fallback: generic masking
        return self._mask_generic(original, gem_type)

    def _ensure_unique(self, fake_base: str, gem_type: str) -> str:
        """
        Ensure fake value is unique by adding a suffix.

        Args:
            fake_base: Base fake value
            gem_type: Gem type for suffix differentiation

        Returns:
            Unique fake value
        """
        # Use a short hash suffix for uniqueness
        suffix = f"_{gem_type[:3]}"
        return f"{fake_base}{suffix}"

    def _mask_email(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask email: t***@example.com"""
        if not original:
            return "***@***.***"
        if "@" not in original:
            return self._mask_generic(original, "email")
        local, domain = original.rsplit("@", 1)
        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 1)
        return f"{masked_local}@{domain}"

    def _mask_phone_cn(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask Chinese phone: 138****5678"""
        if not original:
            return "1******5678"
        if len(original) < 7:
            return "*" * len(original)
        return f"{original[:3]}****{original[-4:]}"

    def _mask_phone_us(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask US phone: (***) ***-5678"""
        if not original:
            return "(***) ***-****"
        digits = re.sub(r"\D", "", original)
        if len(digits) < 4:
            return "*" * len(original)
        return f"(***) ***-{digits[-4:]}"

    def _mask_id_card_cn(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask Chinese ID: A*********9"""
        if not original:
            return "***********"
        if len(original) < 4:
            return "*" * len(original)
        return f"{original[0]}{'*' * (len(original) - 2)}{original[-1]}"

    def _mask_passport(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask passport: A****5678"""
        if not original:
            return "****5678"
        if len(original) < 4:
            return "*" * len(original)
        return f"{original[0]}{'*' * (len(original) - 4)}{original[-4:]}"

    def _mask_credit_card(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask credit card: 4111 **** **** 1111"""
        if not original:
            return "**** **** **** ****"
        digits = re.sub(r"\D", "", original)
        if len(digits) < 8:
            return "*" * len(original)
        return f"{digits[:4]} **** **** {digits[-4:]}"

    def _mask_api_key(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask API key: api_key=***"""
        if not original:
            return "[API_KEY]"
        return f"[API_KEY:{original[:4]}***]"

    def _mask_api_key_generic(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask generic API key: sk-***xyz"""
        if not original:
            return "sk-***"
        if len(original) < 6:
            return "sk-***"
        return f"sk-***{original[-3:]}"

    def _mask_bearer_token(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask bearer token: Bearer ***"""
        if not original:
            return "Bearer ***"
        return "Bearer [TOKEN]"

    def _mask_aws_access_key(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask AWS access key: AKIA***XXXX"""
        if not original:
            return "AKIA***********"
        if len(original) < 8:
            return "AKIA***"
        return f"AKIA{'*' * 8}{original[-4:]}"

    def _mask_password(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask password: password=***"""
        if not original:
            return "[PASSWORD]"
        return "[PASSWORD]"

    def _mask_private_key(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask private key header: [PRIVATE_KEY]"""
        return "[PRIVATE_KEY]"

    def _mask_ipv4(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask IPv4: 192.168.***.***"""
        if not original:
            return "***.***.***.***"
        parts = original.split(".")
        if len(parts) != 4:
            return "***.***.***.***"
        return f"{parts[0]}.{parts[1]}.***.***"

    def _mask_ipv6(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask IPv6: 2001:***:***:***:***:***:***:****"""
        if not original:
            return "***:***:***:***:***:***:***:****"
        parts = original.split(":")
        if len(parts) < 4:
            return "***"
        return f"{parts[0]}:{'***'}:{'***'}:{'***'}:{'***'}:{'***'}:{'***'}:{parts[-1]}"

    def _mask_mac_address(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask MAC address: AA:***:***:***:***:FF"""
        if not original:
            return "**:**:**:**:**:**"
        parts = re.split(r"[:-]", original)
        if len(parts) != 6:
            return "**:**:**:**:**:**"
        return f"{parts[0]}:***:***:***:***:{parts[-1]}"

    def _mask_url(self, original: Optional[str], _fake: Optional[str]) -> str:
        """Mask URL: https://***.example.com/path"""
        if not original:
            return "[URL]"
        # Try to preserve the domain structure
        match = re.match(r"(https?://)([^/]+)(/.*)?", original)
        if match:
            protocol, domain, path = match.groups()
            # Mask domain but keep TLD
            if "." in domain:
                base, tld = domain.rsplit(".", 1)
                masked_domain = f"***.{tld}"
            else:
                masked_domain = "***"
            return f"{protocol}{masked_domain}{path or ''}"
        return "[URL]"

    def _mask_generic(self, original: str, gem_type: str) -> str:
        """Generic masking that preserves some structure."""
        if not original:
            return f"[{gem_type.upper()}]"

        # For strings longer than 6 chars, mask middle
        if len(original) <= 4:
            return "*" * len(original)
        elif len(original) <= 8:
            return f"{original[0]}{'*' * (len(original) - 2)}{original[-1]}"
        else:
            preserve = min(3, len(original) // 4)
            return f"{original[:preserve]}{'*' * (len(original) - preserve * 2)}{original[-preserve:]}"

    def get_detections(self, text: str) -> List[Detection]:
        """
        Get all gem detections in text without masking.

        Args:
            text: Input text

        Returns:
            List of Detection objects
        """
        result: FilterResult = self._filter_engine.filter(text)
        return result.detections

    def get_detection_summary(self, text: str) -> Dict[str, int]:
        """
        Get summary of gem detections in text.

        Args:
            text: Input text

        Returns:
            Dict of {gem_type: count}
        """
        result: FilterResult = self._filter_engine.filter(text)
        return result.summary
