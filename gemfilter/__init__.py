"""
GemFilter - Sensitive Information Filter

A lightweight, zero-dependency filter that detects and protects
sensitive information in text, like filtering gems from sand.
Perfect for privacy protection in LLM and AI applications.
"""

from gemfilter.core import (
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

__version__ = "0.2.1"

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
