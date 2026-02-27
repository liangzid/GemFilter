"""
Pipeline and Filter for SandFilter.
Orchestrates rules and processors to filter sensitive information.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from .rules import DetectionRule, get_builtin_rules
from .processors import Processor, Processors, RuleNameReplaceProcessor


@dataclass
class Detection:
    """Represents a detected sensitive information."""
    rule_name: str
    match: str
    start: int
    end: int
    sensitive_type: str
    replacement: str


@dataclass
class FilterResult:
    """Result of filtering operation."""
    text: str
    detections: list[Detection] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.summary:
            # Build summary from detections
            for d in self.detections:
                self.summary[d.rule_name] = self.summary.get(d.rule_name, 0) + 1


class FilterPipeline:
    """Pipeline that applies rules and processors to filter text."""

    def __init__(self):
        self._rules: list[DetectionRule] = []
        self._rule_to_processor: dict[str, Processor] = {}
        self._compiled_patterns: dict[str, re.Pattern] = {}

    def add_rule(
        self,
        rule: DetectionRule,
        processor: Optional[Processor] = None,
    ) -> "FilterPipeline":
        """Add a rule with optional processor.

        Args:
            rule: The detection rule to add
            processor: Optional processor (defaults to rule name replacement)

        Returns:
            Self for chaining
        """
        # Add to rules list
        self._rules.append(rule)

        # Set default processor if not provided
        if processor is None:
            processor = RuleNameReplaceProcessor()

        self._rule_to_processor[rule.name] = processor

        # Compile regex pattern
        self._compiled_patterns[rule.name] = re.compile(rule.pattern)

        return self

    def set_processor(
        self,
        rule_name: str,
        processor: Processor,
    ) -> "FilterPipeline":
        """Set or update processor for a rule.

        Args:
            rule_name: Name of the rule
            processor: Processor to use

        Returns:
            Self for chaining
        """
        self._rule_to_processor[rule_name] = processor
        return self

    def get_processor(self, rule_name: str) -> Optional[Processor]:
        """Get processor for a rule."""
        return self._rule_to_processor.get(rule_name)

    def process(self, text: str) -> FilterResult:
        """Process text and filter sensitive information.

        Args:
            text: Input text to filter

        Returns:
            FilterResult with filtered text and detection details
        """
        detections: list[Detection] = []
        result_text = text
        replaced_ranges: list[tuple[int, int]] = []  # Track replaced positions

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(self._rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            pattern = self._compiled_patterns.get(rule.name)
            if not pattern:
                continue

            processor = self._rule_to_processor.get(rule.name)
            if not processor:
                continue

            # Find all matches
            for match in pattern.finditer(result_text):
                start, end = match.start(), match.end()

                # Skip if this range overlaps with already replaced text
                if any(s < end and e > start for s, e in replaced_ranges):
                    continue

                matched_text = match.group()
                replacement = processor.process(matched_text, rule.name)

                detection = Detection(
                    rule_name=rule.name,
                    match=matched_text,
                    start=start,
                    end=end,
                    sensitive_type=rule.sensitive_type,
                    replacement=replacement,
                )
                detections.append(detection)

                # Track this replacement
                replaced_ranges.append((start, start + len(replacement)))

                # Replace in text
                result_text = (
                    result_text[:start]
                    + replacement
                    + result_text[end:]
                )

        return FilterResult(text=result_text, detections=detections)

    def get_rules(self) -> list[DetectionRule]:
        """Get all registered rules."""
        return self._rules.copy()

    def enable_rule(self, rule_name: str, enabled: bool = True) -> "FilterPipeline":
        """Enable or disable a rule."""
        for rule in self._rules:
            if rule.name == rule_name:
                rule.enabled = enabled
        return self

    def disable_rule(self, rule_name: str) -> "FilterPipeline":
        """Disable a rule."""
        return self.enable_rule(rule_name, False)


class SandFilter:
    """Main SandFilter class for filtering sensitive information."""

    def __init__(
        self,
        default_processor: Optional[Processor] = None,
        load_builtin_rules: bool = True,
    ):
        """Initialize SandFilter.

        Args:
            default_processor: Default processor for rules (defaults to [RULE_NAME])
            load_builtin_rules: Whether to load built-in rules (default: True)
        """
        self._pipeline = FilterPipeline()
        self._default_processor = default_processor or RuleNameReplaceProcessor()

        # Load built-in rules if requested
        if load_builtin_rules:
            self._load_builtin_rules()

    @classmethod
    def from_config(
        cls,
        config_path: str,
        default_processor: Optional[Processor] = None,
    ) -> "SandFilter":
        """Create SandFilter instance from config file.

        Args:
            config_path: Path to YAML or JSON config file
            default_processor: Default processor for rules

        Returns:
            SandFilter instance
        """
        from .config import load_config, parse_rule_from_config, parse_processor_from_config

        config = load_config(config_path)

        # Get default processor from config
        settings = config.get("settings", {})
        if default_processor is None:
            processor_name = settings.get("default_processor", "rule_name")
            if isinstance(processor_name, str):
                default_processor = Processors.rule_name() if processor_name == "rule_name" else Processors.replace()

        # Create instance with built-in rules (will be configured below)
        sf = cls(default_processor=default_processor, load_builtin_rules=True)

        # Apply rule configurations from config
        rules_config = config.get("rules", [])
        for rule_config in rules_config:
            rule_name = rule_config.get("name")

            # Check if rule has a pattern (new custom rule)
            if "pattern" in rule_config:
                # New custom rule
                rule = parse_rule_from_config(rule_config)
                processor = parse_processor_from_config(rule_config.get("processor", "rule_name"))
                sf.add_rule(rule, processor)
            else:
                # Configure existing built-in rule
                if "enabled" in rule_config:
                    if rule_config["enabled"]:
                        sf.enable_rules(rule_name)
                    else:
                        sf.disable_rules(rule_name)

                if "processor" in rule_config:
                    processor = parse_processor_from_config(rule_config["processor"])
                    sf.set_processor(rule_name, processor)

        return sf

    def _load_builtin_rules(self) -> None:
        """Load all built-in rules (create copies to avoid shared state)."""
        builtin = get_builtin_rules()
        for rule in builtin.values():
            # Create a copy to avoid modifying the original rule
            rule_copy = DetectionRule(
                name=rule.name,
                pattern=rule.pattern,
                priority=rule.priority,
                sensitive_type=rule.sensitive_type,
                group=rule.group,
                enabled=rule.enabled,
                encryptable=rule.encryptable,
                description=rule.description,
            )
            self._pipeline.add_rule(rule_copy, self._default_processor)

    def filter(self, text: str) -> FilterResult:
        """Filter sensitive information from text.

        Args:
            text: Input text to filter

        Returns:
            FilterResult with filtered text and detection details
        """
        return self._pipeline.process(text)

    def add_rule(
        self,
        rule: DetectionRule,
        processor: Optional[Processor] = None,
    ) -> "SandFilter":
        """Add a custom rule.

        Args:
            rule: The detection rule to add
            processor: Optional processor (defaults to [RULE_NAME])

        Returns:
            Self for chaining
        """
        self._pipeline.add_rule(rule, processor or self._default_processor)
        return self

    def set_processor(
        self,
        rule_name: str,
        processor: Processor,
    ) -> "SandFilter":
        """Set processor for a specific rule.

        Args:
            rule_name: Name of the rule
            processor: Processor to use

        Returns:
            Self for chaining
        """
        self._pipeline.set_processor(rule_name, processor)
        return self

    def enable_rules(self, *rule_names: str) -> "SandFilter":
        """Enable specific rules."""
        for name in rule_names:
            self._pipeline.enable_rule(name, True)
        return self

    def disable_rules(self, *rule_names: str) -> "SandFilter":
        """Disable specific rules."""
        for name in rule_names:
            self._pipeline.disable_rule(name)
        return self

    def enable_group(self, group: str) -> "SandFilter":
        """Enable all rules in a group."""
        for rule in self._pipeline.get_rules():
            if rule.group == group:
                rule.enabled = True
        return self

    def disable_group(self, group: str) -> "SandFilter":
        """Disable all rules in a group."""
        for rule in self._pipeline.get_rules():
            if rule.group == group:
                rule.enabled = False
        return self

    def disable_groups_except(self, *groups: str) -> "SandFilter":
        """Disable all rules except those in the specified groups."""
        for rule in self._pipeline.get_rules():
            if rule.group not in groups:
                rule.enabled = False
        return self

    def get_enabled_rules(self) -> list[str]:
        """Get list of enabled rule names."""
        return [r.name for r in self._pipeline.get_rules() if r.enabled]

    def get_disabled_rules(self) -> list[str]:
        """Get list of disabled rule names."""
        return [r.name for r in self._pipeline.get_rules() if not r.enabled]
