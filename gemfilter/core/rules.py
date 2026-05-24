"""
Core rules engine for SandFilter.
Defines detection rules for sensitive information.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectionRule:
    """A detection rule for identifying sensitive information.

    Attributes:
        name: Unique identifier for the rule (e.g., "email", "api_key")
        pattern: Regular expression pattern to match
        priority: Lower values are matched first (default: 100)
        sensitive_type: Category of sensitive data (e.g., "contact", "security")
        group: Group name for batch enable/disable (default: "default")
        enabled: Whether the rule is active (default: True)
        encryptable: Whether this sensitive type supports encryption (default: False)
        description: Human-readable description of what this rule detects
    """
    name: str
    pattern: str
    priority: int = 100
    sensitive_type: str = "general"
    group: str = "default"
    enabled: bool = True
    encryptable: bool = False
    description: str = ""

    def __post_init__(self):
        if not self.name:
            raise ValueError("Rule name cannot be empty")
        if not self.pattern:
            raise ValueError("Rule pattern cannot be empty")
        if self.description is None:
            self.description = ""


# Built-in rules registry
BUILTIN_RULES: dict[str, DetectionRule] = {}


def register_builtin_rule(rule: DetectionRule) -> None:
    """Register a built-in rule."""
    BUILTIN_RULES[rule.name] = rule


def get_builtin_rules() -> dict[str, DetectionRule]:
    """Get all built-in rules."""
    return BUILTIN_RULES.copy()


def get_builtin_rule(name: str) -> Optional[DetectionRule]:
    """Get a specific built-in rule by name."""
    return BUILTIN_RULES.get(name)


# Initialize built-in rules
def _init_builtin_rules() -> None:
    """Initialize all built-in detection rules."""

    # Contact information
    register_builtin_rule(DetectionRule(
        name="email",
        pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        priority=10,
        sensitive_type="contact",
        group="contact",
        encryptable=True,
        description="Email address"
    ))

    register_builtin_rule(DetectionRule(
        name="phone_cn",
        pattern=r"1[3-9]\d{9}",
        priority=11,
        sensitive_type="contact",
        group="contact",
        encryptable=True,
        description="Chinese mobile phone number"
    ))

    register_builtin_rule(DetectionRule(
        name="phone_us",
        pattern=r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        priority=12,
        sensitive_type="contact",
        group="contact",
        encryptable=True,
        description="US phone number"
    ))

    # Personal identification
    register_builtin_rule(DetectionRule(
        name="id_card_cn",
        pattern=r"[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]",
        priority=2,  # Higher priority than credit_card
        sensitive_type="identification",
        group="identification",
        encryptable=True,
        description="Chinese ID card number"
    ))

    register_builtin_rule(DetectionRule(
        name="passport",
        pattern=r"[A-Z]{1,2}\d{6,9}",
        priority=6,
        sensitive_type="identification",
        group="identification",
        encryptable=True,
        description="Passport number"
    ))

    # Financial information
    register_builtin_rule(DetectionRule(
        name="credit_card",
        pattern=r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        priority=3,
        sensitive_type="financial",
        group="financial",
        encryptable=True,
        description="Credit card number"
    ))

    register_builtin_rule(DetectionRule(
        name="bank_account_cn",
        pattern=r"\d{16,19}",
        priority=4,
        sensitive_type="financial",
        group="financial",
        encryptable=True,
        description="Chinese bank account number"
    ))

    # Security credentials
    register_builtin_rule(DetectionRule(
        name="password",
        pattern=r"(?:password|passwd|pwd)[=:\s]+[^\s]{4,}",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="Password in key-value format"
    ))

    register_builtin_rule(DetectionRule(
        name="api_key",
        pattern=r"(?:api[_-]?key|apikey)[=:\s]+[a-zA-Z0-9_-]{20,}",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="API key"
    ))

    register_builtin_rule(DetectionRule(
        name="github_token",
        pattern=r"\bgh[pousr]_[A-Za-z0-9_]{30,255}\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="GitHub access token"
    ))

    register_builtin_rule(DetectionRule(
        name="anthropic_api_key",
        pattern=r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="Anthropic API key"
    ))

    register_builtin_rule(DetectionRule(
        name="openai_api_key",
        pattern=r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="OpenAI API key"
    ))

    register_builtin_rule(DetectionRule(
        name="npm_token",
        pattern=r"\bnpm_[A-Za-z0-9]{30,}\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="npm access token"
    ))

    register_builtin_rule(DetectionRule(
        name="pypi_token",
        pattern=r"\bpypi-[A-Za-z0-9_-]{20,}\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="PyPI API token"
    ))

    register_builtin_rule(DetectionRule(
        name="jwt",
        pattern=r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="JSON Web Token"
    ))

    register_builtin_rule(DetectionRule(
        name="api_key_generic",
        pattern=r"sk-[a-zA-Z0-9]{20,}",
        priority=2,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="Generic API key (sk-...)"
    ))

    register_builtin_rule(DetectionRule(
        name="bearer_token",
        pattern=r"Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        priority=2,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="Bearer token (JWT)"
    ))

    register_builtin_rule(DetectionRule(
        name="aws_access_key",
        pattern=r"AKIA[0-9A-Z]{16}",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="AWS access key ID"
    ))

    register_builtin_rule(DetectionRule(
        name="aws_secret_key",
        pattern=r"(?:aws[_-]?secret[_-]?access[_-]?key|aws_secret_key)[=:\s]+[a-zA-Z0-9/+=]{40}",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="AWS secret access key"
    ))

    register_builtin_rule(DetectionRule(
        name="private_key",
        pattern=r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        priority=1,
        sensitive_type="security",
        group="security",
        encryptable=False,
        description="Private key header"
    ))

    register_builtin_rule(DetectionRule(
        name="database_url",
        pattern=r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s<>'\"{}|\\^`\[\]]+",
        priority=2,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description="Database connection URL"
    ))

    register_builtin_rule(DetectionRule(
        name="dotenv_secret",
        pattern=r"(?i)\b[A-Z0-9_]*(?:SECRET|TOKEN|API[_-]?KEY|PASSWORD|PASS|PRIVATE[_-]?KEY|ACCESS[_-]?KEY)[A-Z0-9_]*\s*=\s*[\"']?[^\"'\s#]{8,}[\"']?",
        priority=5,
        sensitive_type="security",
        group="security",
        encryptable=True,
        description=".env-style secret assignment"
    ))

    # Network identifiers
    register_builtin_rule(DetectionRule(
        name="ipv4",
        pattern=r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
        priority=50,
        sensitive_type="network",
        group="network",
        encryptable=False,
        description="IPv4 address"
    ))

    register_builtin_rule(DetectionRule(
        name="ipv6",
        pattern=r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}",
        priority=51,
        sensitive_type="network",
        group="network",
        encryptable=False,
        description="IPv6 address"
    ))

    register_builtin_rule(DetectionRule(
        name="mac_address",
        pattern=r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",
        priority=52,
        sensitive_type="network",
        group="network",
        encryptable=False,
        description="MAC address"
    ))

    # URL and domain
    register_builtin_rule(DetectionRule(
        name="url",
        pattern=r"https?://[^\s<>'\"{}|\\^`\[\]]+",
        priority=60,
        sensitive_type="network",
        group="network",
        encryptable=False,
        description="URL"
    ))

    # Miscellaneous
    register_builtin_rule(DetectionRule(
        name="mac_address",
        pattern=r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}",
        priority=52,
        sensitive_type="network",
        group="network",
        encryptable=False,
        description="MAC address"
    ))


# Initialize rules on module import
_init_builtin_rules()
