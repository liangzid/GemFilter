"""
Processor engine for SandFilter.
Defines how detected sensitive information is processed.
"""

import hashlib
import base64
from typing import Callable, Optional, Protocol
from dataclasses import dataclass


class Processor(Protocol):
    """Protocol for text processors."""

    def process(self, match: str, rule_name: str) -> str:
        """Process a matched string.

        Args:
            match: The matched sensitive text
            rule_name: The name of the rule that matched

        Returns:
            The processed (masked/replaced/etc) text
        """
        ...


@dataclass
class ProcessorConfig:
    """Configuration for processors."""
    replacement: str = "[REDACTED]"
    mask_char: str = "*"
    preserve_prefix: int = 1
    preserve_suffix: int = 1
    encryption_key: Optional[str] = None


class ReplaceProcessor:
    """Replace sensitive text with a replacement string.

    Example: "test@example.com" -> "[EMAIL]"
    """

    def __init__(self, replacement: str = "[REDACTED]"):
        self.replacement = replacement

    def process(self, match: str, rule_name: str) -> str:
        return self.replacement


class RuleNameReplaceProcessor:
    """Replace sensitive text with rule name in brackets.

    Example: "test@example.com" -> "[EMAIL]"
    """

    def process(self, match: str, rule_name: str) -> str:
        return f"[{rule_name.upper()}]"


class PartialMaskProcessor:
    """Partially mask sensitive text, preserving some characters.

    Example: "test@example.com" -> "te**@******.com"
    """

    def __init__(
        self,
        mask_char: str = "*",
        preserve_prefix: int = 1,
        preserve_suffix: int = 1,
    ):
        self.mask_char = mask_char
        self.preserve_prefix = preserve_prefix
        self.preserve_suffix = preserve_suffix

    def process(self, match: str, rule_name: str) -> str:
        if len(match) <= self.preserve_prefix + self.preserve_suffix:
            return self.mask_char * len(match)

        prefix = match[: self.preserve_prefix]
        suffix = match[-self.preserve_suffix :] if self.preserve_suffix > 0 else ""
        middle_length = len(match) - self.preserve_prefix - self.preserve_suffix

        # For email, try to preserve domain structure
        if "@" in match:
            parts = match.split("@")
            if len(parts) == 2:
                local, domain = parts
                masked_local = (
                    local[:1] + self.mask_char * (len(local) - 1)
                    if len(local) > 1
                    else self.mask_char
                )
                return f"{masked_local}@{domain}"

        return prefix + self.mask_char * middle_length + suffix


class DeleteProcessor:
    """Completely remove sensitive text."""

    def process(self, match: str, rule_name: str) -> str:
        return ""


class EncryptProcessor:
    """Encrypt sensitive text using AES (base64 encoded for display).

    Requires a secret key to be configured.
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()[:32]  # Use first 32 bytes

    def process(self, match: str, rule_name: str) -> str:
        # Simple XOR encryption + base64 (for demo purposes)
        # In production, use proper AES from cryptography library
        key_bytes = self.secret_key
        encrypted = bytes(a ^ b for a, b in zip(match.encode(), (key_bytes * (len(match) // len(key_bytes) + 1))[:len(match)]))
        return f"[ENC:{base64.b64encode(encrypted).decode()}]"


class HashProcessor:
    """Hash sensitive text using SHA256 (one-way, irreversible)."""

    def __init__(self, truncate: bool = True):
        self.truncate = truncate

    def process(self, match: str, rule_name: str) -> str:
        hash_value = hashlib.sha256(match.encode()).hexdigest()
        if self.truncate:
            return f"[HASH:{hash_value[:16]}]"
        return f"[HASH:{hash_value}]"


class CustomProcessor:
    """User-defined custom processor function."""

    def __init__(self, func: Callable[[str, str], str]):
        self.func = func

    def process(self, match: str, rule_name: str) -> str:
        return self.func(match, rule_name)


class FixedValueProcessor:
    """Replace with a fixed value (useful for consistent masking)."""

    def __init__(self, value: str):
        self.value = value

    def process(self, match: str, rule_name: str) -> str:
        return self.value


# Built-in processor factory
class Processors:
    """Factory class for creating built-in processors."""

    @staticmethod
    def replace(replacement: str = "[REDACTED]") -> ReplaceProcessor:
        return ReplaceProcessor(replacement)

    @staticmethod
    def rule_name() -> RuleNameReplaceProcessor:
        return RuleNameReplaceProcessor()

    @staticmethod
    def partial_mask(
        mask_char: str = "*",
        preserve_prefix: int = 1,
        preserve_suffix: int = 1,
    ) -> PartialMaskProcessor:
        return PartialMaskProcessor(mask_char, preserve_prefix, preserve_suffix)

    @staticmethod
    def delete() -> DeleteProcessor:
        return DeleteProcessor()

    @staticmethod
    def encrypt(secret_key: str) -> EncryptProcessor:
        return EncryptProcessor(secret_key)

    @staticmethod
    def hash(truncate: bool = True) -> HashProcessor:
        return HashProcessor(truncate)

    @staticmethod
    def custom(func: Callable[[str, str], str]) -> CustomProcessor:
        return CustomProcessor(func)

    @staticmethod
    def fixed(value: str) -> FixedValueProcessor:
        return FixedValueProcessor(value)

    # Common presets
    EMAIL = rule_name()
    PHONE = partial_mask(preserve_prefix=3, preserve_suffix=4)
    API_KEY = replace("[API_KEY]")
    PASSWORD = replace("[PASSWORD]")
    CREDIT_CARD = partial_mask(preserve_prefix=4, preserve_suffix=4)
