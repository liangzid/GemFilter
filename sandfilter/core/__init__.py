"""
SandFilter - Sensitive Information Filter

A lightweight, zero-dependency LLM filter that detects and masks
sensitive information in text without using any LLM APIs.
"""

from .rules import DetectionRule, get_builtin_rules, get_builtin_rule
from .processors import Processor, Processors
from .filter import SandFilter, FilterPipeline, FilterResult, Detection
from .config import (
    load_config,
    load_rules_from_config,
    parse_rule_from_config,
    parse_processor_from_config,
    CONFIG_TEMPLATE,
    DEFAULT_CONFIG,
)

__version__ = "0.1.0"

__all__ = [
    "SandFilter",
    "FilterPipeline",
    "FilterResult",
    "Detection",
    "DetectionRule",
    "Processor",
    "Processors",
    "get_builtin_rules",
    "get_builtin_rule",
    "load_config",
    "load_rules_from_config",
    "parse_rule_from_config",
    "parse_processor_from_config",
    "CONFIG_TEMPLATE",
    "DEFAULT_CONFIG",
]
