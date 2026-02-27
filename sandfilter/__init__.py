"""
SandFilter - Sensitive Information Filter

A lightweight, zero-dependency LLM filter that detects and masks
sensitive information in text without using any LLM APIs.
"""

from sandfilter.core import (
    SandFilter,
    FilterPipeline,
    FilterResult,
    Detection,
    DetectionRule,
    Processor,
    Processors,
    get_builtin_rules,
    get_builtin_rule,
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
]
