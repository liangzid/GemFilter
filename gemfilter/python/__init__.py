"""
GemFilter Python SDK

A lightweight, zero-dependency filter that detects and protects
sensitive information in text, like filtering gems from sand.
Perfect for privacy protection in LLM and AI applications.

Usage:
    from gemfilter import SandFilter, Rule, Processors

    sf = SandFilter()
    result = sf.filter("我的邮箱是 test@example.com")
    print(result.text)  # 我的邮箱是 [EMAIL]
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
