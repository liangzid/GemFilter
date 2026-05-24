"""
Gem Masker for GemFilter Skill.

Generates fake placeholders that look similar to real gems.
"""

import re
import random
import string
from urllib.parse import urlsplit, urlunsplit
from typing import Dict, List, Tuple, Optional, Callable

from gemfilter.core.filter import SandFilter, FilterResult, Detection
from gemfilter.skill.config import MaskingMode


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
        masking_mode: str | MaskingMode = MaskingMode.BALANCED,
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
        self._masking_mode = self._parse_masking_mode(masking_mode)
        self._maskers: Dict[str, MaskFunc] = {}
        self._custom_masker_types: set[str] = set()
        self._maskers.update(self._get_default_maskers())
        if custom_maskers:
            self._maskers.update(custom_maskers)
            self._custom_masker_types.update(custom_maskers.keys())

    @property
    def masking_mode(self) -> MaskingMode:
        """Get the active masking mode."""
        return self._masking_mode

    def set_masking_mode(self, masking_mode: str | MaskingMode) -> None:
        """Set the active masking mode."""
        self._masking_mode = self._parse_masking_mode(masking_mode)

    def _parse_masking_mode(self, masking_mode: str | MaskingMode) -> MaskingMode:
        if isinstance(masking_mode, MaskingMode):
            return masking_mode
        return MaskingMode(str(masking_mode).lower())

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
        self._custom_masker_types.add(gem_type)

    def mask(
        self,
        text: str,
        existing_mapping: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Dict[str, str]]:
        """
        Mask all gems in the text.

        Args:
            text: Input text containing gems

        Returns:
            existing_mapping: Optional prior fake -> original mapping for
                              deterministic multi-turn sessions.

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
        original_to_fake: Dict[str, str] = {}
        if existing_mapping:
            original_to_fake.update(
                {original: fake for fake, original in existing_mapping.items()}
            )
        masked_text = text

        for detection in sorted_detections:
            original = detection.match
            gem_type = detection.rule_name

            # Reuse existing fake placeholders for deterministic sessions.
            fake = original_to_fake.get(original)
            if fake is None:
                fake = self._generate_fake(
                    gem_type,
                    original,
                    mapping={**(existing_mapping or {}), **mapping},
                )
                original_to_fake[original] = fake

            # Track mapping (fake -> original)
            mapping[fake] = original

            # Replace in text
            masked_text = (
                masked_text[:detection.start]
                + fake
                + masked_text[detection.end:]
            )

        return masked_text, mapping

    def _generate_fake(
        self,
        gem_type: str,
        original: str,
        mapping: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate a fake placeholder for a gem.

        Args:
            gem_type: The type of gem
            original: The original value

        Returns:
            Fake placeholder value
        """
        mapping = mapping or {}

        if gem_type in self._custom_masker_types:
            fake_base = self._maskers[gem_type](original, None)
            return self._ensure_unique(fake_base, gem_type)

        if self._masking_mode == MaskingMode.STRICT:
            return self._typed_placeholder(gem_type, mapping)

        if self._masking_mode == MaskingMode.BALANCED:
            return self._balanced_fake(gem_type, original, mapping)

        if self._masking_mode == MaskingMode.UTILITY:
            return self._utility_fake(gem_type, original, mapping)

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

    def _typed_placeholder(self, gem_type: str, mapping: Dict[str, str]) -> str:
        """Generate a non-revealing typed placeholder."""
        label = self._label_for_type(gem_type)
        next_id = self._next_id(label, mapping)
        return f"<{label}_{next_id}>"

    def _balanced_fake(
        self,
        gem_type: str,
        original: str,
        mapping: Dict[str, str],
    ) -> str:
        """Preserve useful syntax while hiding sensitive values."""
        label = self._label_for_type(gem_type)

        if self._is_secret_type(gem_type):
            return self._typed_placeholder(gem_type, mapping)

        if gem_type == "email":
            idx = self._next_id("EMAIL_LOCAL", mapping)
            return f"<EMAIL_LOCAL_{idx}>@<EMAIL_DOMAIN_{idx}>"

        if gem_type == "url":
            return self._balanced_url(original, mapping)

        if gem_type == "ipv4":
            idx = self._next_id("IPV4", mapping)
            return f"10.0.{idx}.1"

        if gem_type == "ipv6":
            idx = self._next_id("IPV6", mapping)
            return f"2001:db8::{idx}"

        if gem_type == "mac_address":
            idx = self._next_id("MAC", mapping)
            return f"02:00:00:00:00:{idx % 256:02x}"

        if gem_type in {"phone_cn", "phone_us", "id_card_cn", "passport", "credit_card"}:
            return self._typed_placeholder(gem_type, mapping)

        return self._typed_placeholder(gem_type, mapping)

    def _balanced_url(self, original: str, mapping: Dict[str, str]) -> str:
        idx = self._next_id("HOST", mapping)
        try:
            parts = urlsplit(original)
        except ValueError:
            return f"https://<HOST_{idx}>"

        scheme = parts.scheme or "https"
        netloc = f"<HOST_{idx}>"
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
        path = self._mask_path_structure(parts.path, "PATH", idx)
        query = "<QUERY>" if parts.query else ""
        fragment = "<FRAGMENT>" if parts.fragment else ""
        return urlunsplit((scheme, netloc, path, query, fragment))

    def _utility_fake(
        self,
        gem_type: str,
        original: str,
        mapping: Dict[str, str],
    ) -> str:
        """Generate syntactically plausible fake values for coding tasks."""
        idx = self._next_id(self._label_for_type(gem_type), mapping)

        if gem_type == "email":
            return f"user{idx}@example.test"

        if gem_type == "phone_cn":
            return f"1390000{idx:04d}"[-11:]

        if gem_type == "phone_us":
            return f"(555) 010-{idx % 10000:04d}"

        if gem_type == "url":
            return self._utility_url(original, idx)

        if gem_type == "ipv4":
            return f"192.0.2.{(idx % 254) + 1}"

        if gem_type == "ipv6":
            return f"2001:db8::{idx}"

        if gem_type == "mac_address":
            return f"02:00:00:00:00:{idx % 256:02x}"

        if gem_type == "credit_card":
            return "4111 1111 1111 1111"

        if gem_type == "api_key_generic":
            return f"sk-test{'a' * 20}{idx}"

        if self._is_secret_type(gem_type):
            return self._typed_placeholder(gem_type, mapping)

        return self._typed_placeholder(gem_type, mapping)

    def _utility_url(self, original: str, idx: int) -> str:
        try:
            parts = urlsplit(original)
        except ValueError:
            return f"https://service{idx}.example.test"

        scheme = parts.scheme or "https"
        netloc = f"service{idx}.example.test"
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
        return urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))

    def _mask_path_structure(self, path: str, label: str, idx: int) -> str:
        if not path:
            return ""
        segments = [segment for segment in path.split("/") if segment]
        if not segments:
            return "/"
        return "/" + "/".join(f"<{label}_{idx}_{i + 1}>" for i, _ in enumerate(segments))

    def _label_for_type(self, gem_type: str) -> str:
        labels = {
            "api_key": "SECRET",
            "api_key_generic": "SECRET",
            "openai_api_key": "OPENAI_KEY",
            "anthropic_api_key": "ANTHROPIC_KEY",
            "github_token": "GITHUB_TOKEN",
            "npm_token": "NPM_TOKEN",
            "pypi_token": "PYPI_TOKEN",
            "jwt": "JWT",
            "database_url": "DATABASE_URL",
            "dotenv_secret": "SECRET",
            "aws_access_key": "AWS_ACCESS_KEY",
            "aws_secret_key": "AWS_SECRET",
            "bearer_token": "TOKEN",
            "password": "PASSWORD",
            "private_key": "PRIVATE_KEY",
            "phone_cn": "PHONE",
            "phone_us": "PHONE",
            "id_card_cn": "ID_CARD",
            "credit_card": "CREDIT_CARD",
            "bank_account_cn": "BANK_ACCOUNT",
            "mac_address": "MAC",
        }
        return labels.get(gem_type, gem_type.upper())

    def _is_secret_type(self, gem_type: str) -> bool:
        return gem_type in {
            "api_key",
            "api_key_generic",
            "openai_api_key",
            "anthropic_api_key",
            "github_token",
            "npm_token",
            "pypi_token",
            "jwt",
            "database_url",
            "dotenv_secret",
            "aws_access_key",
            "aws_secret_key",
            "bearer_token",
            "password",
            "private_key",
        }

    def _next_id(self, label: str, mapping: Dict[str, str]) -> int:
        pattern = re.compile(rf"<{re.escape(label)}_(\d+)>")
        max_id = 0
        for fake in mapping:
            for match in pattern.finditer(fake):
                max_id = max(max_id, int(match.group(1)))
        return max_id + 1 if max_id else len(mapping) + 1

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
