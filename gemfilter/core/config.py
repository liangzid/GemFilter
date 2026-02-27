"""
Configuration loader for SandFilter.
Supports YAML and JSON configuration files.
"""

import json
from pathlib import Path
from typing import Optional, Union

import yaml

from .rules import DetectionRule
from .processors import (
    Processor,
    Processors,
    ReplaceProcessor,
    PartialMaskProcessor,
    DeleteProcessor,
    HashProcessor,
)


def load_config(config_path: Union[str, Path]) -> dict:
    """Load configuration from YAML or JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f) or {}
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")


def parse_rule_from_config(rule_config: dict) -> DetectionRule:
    """Parse a DetectionRule from configuration dict.

    Args:
        rule_config: Rule configuration dictionary

    Returns:
        DetectionRule instance
    """
    return DetectionRule(
        name=rule_config["name"],
        pattern=rule_config["pattern"],
        priority=rule_config.get("priority", 100),
        sensitive_type=rule_config.get("sensitive_type", "general"),
        group=rule_config.get("group", "default"),
        enabled=rule_config.get("enabled", True),
        encryptable=rule_config.get("encryptable", False),
        description=rule_config.get("description", ""),
    )


def parse_processor_from_config(processor_config: Union[str, dict]) -> Processor:
    """Parse a Processor from configuration.

    Args:
        processor_config: Processor name or configuration dict

    Returns:
        Processor instance
    """
    if isinstance(processor_config, str):
        # Named processor
        name = processor_config.lower()
        if name == "replace" or name == "redact":
            return Processors.replace()
        elif name == "rule_name":
            return Processors.rule_name()
        elif name == "partial_mask":
            return Processors.partial_mask()
        elif name == "delete" or name == "remove":
            return Processors.delete()
        elif name == "hash":
            return Processors.hash()
        else:
            return Processors.replace(processor_config)

    # Dict configuration
    processor_type = processor_config.get("type", "replace").lower()

    if processor_type == "replace":
        return Processors.replace(processor_config.get("replacement", "[REDACTED]"))

    elif processor_type == "partial_mask":
        return Processors.partial_mask(
            mask_char=processor_config.get("mask_char", "*"),
            preserve_prefix=processor_config.get("preserve_prefix", 1),
            preserve_suffix=processor_config.get("preserve_suffix", 1),
        )

    elif processor_type == "delete":
        return Processors.delete()

    elif processor_type == "hash":
        return Processors.hash(processor_config.get("truncate", True))

    else:
        return Processors.replace()


def load_rules_from_config(config: dict) -> list[tuple[DetectionRule, Optional[Processor]]]:
    """Load rules and their processors from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        List of (DetectionRule, Processor) tuples
    """
    rules = []
    rules_config = config.get("rules", [])

    for rule_config in rules_config:
        rule = parse_rule_from_config(rule_config)

        # Get processor configuration
        processor = None
        if "processor" in rule_config:
            processor = parse_processor_from_config(rule_config["processor"])

        rules.append((rule, processor))

    return rules


# Example configuration template
CONFIG_TEMPLATE = """
# SandFilter Configuration Example

# Global settings
settings:
  # Default processor for rules without explicit processor
  default_processor: rule_name  # replace, rule_name, partial_mask, delete, hash

# Built-in rules can be enabled/disabled
rules:
  # Disable a built-in rule
  - name: email
    enabled: false

  # Configure processor for a built-in rule
  - name: phone_cn
    processor: partial_mask
    processor_config:
      preserve_prefix: 3
      preserve_suffix: 4

  # Add custom rule
  - name: student_id
    pattern: "STU\\\\d{8}"
    priority: 10
    sensitive_type: education
    group: custom
    processor: replace
    processor_config:
      replacement: "[STUDENT_ID]"
    description: Student ID number

# Rule groups for batch operations
groups:
  contact:
    - email
    - phone_cn
    - phone_us
  financial:
    - credit_card
    - bank_account_cn
  security:
    - password
    - api_key
    - api_key_generic
"""

DEFAULT_CONFIG = {
    "settings": {
        "default_processor": "rule_name",
    },
    "rules": [],
}
