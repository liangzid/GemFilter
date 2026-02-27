"""
SandFilter Python SDK

A lightweight, zero-dependency LLM filter that detects and masks
sensitive information in text without using any LLM APIs.

Usage:
    from sandfilter import SandFilter, Rule, Processors

    sf = SandFilter()
    result = sf.filter("我的邮箱是 test@example.com")
    print(result.text)  # 我的邮箱是 [EMAIL]
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
