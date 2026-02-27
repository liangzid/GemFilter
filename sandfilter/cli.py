#!/usr/bin/env python3
"""
SandFilter CLI

Command-line interface for SandFilter.
"""

import argparse
import sys
import json
from pathlib import Path

from sandfilter import SandFilter


def filter_command(args):
    """Filter sensitive information from text."""
    sf = SandFilter.from_config(args.config) if args.config else SandFilter()

    # Disable rules if specified
    if args.disable:
        sf.disable_rules(*args.disable)

    # Enable rules if specified
    if args.enable:
        sf.enable_rules(*args.enable)

    # Disable groups if specified
    if args.disable_group:
        sf.disable_group(*args.disable_group)

    # Enable groups if specified
    if args.enable_group:
        sf.enable_group(*args.enable_group)

    # Read from file or stdin
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text or sys.stdin.read()

    if not text:
        print("Error: No text to filter", file=sys.stderr)
        return 1

    result = sf.filter(text)

    if args.json:
        print(json.dumps({
            "text": result.text,
            "detections": [
                {
                    "rule": d.rule_name,
                    "match": d.match,
                    "start": d.start,
                    "end": d.end,
                    "sensitive_type": d.sensitive_type,
                    "replacement": d.replacement,
                }
                for d in result.detections
            ],
            "summary": result.summary,
        }, ensure_ascii=False, indent=2))
    else:
        print(result.text)

    if args.verbose:
        print(f"\nDetected {len(result.detections)} sensitive items:", file=sys.stderr)
        for d in result.detections:
            print(f"  [{d.rule_name}] {d.match}", file=sys.stderr)

    return 0


def list_rules_command(args):
    """List available rules."""
    sf = SandFilter.from_config(args.config) if args.config else SandFilter()

    if args.json:
        print(json.dumps({
            "enabled": sf.get_enabled_rules(),
            "disabled": sf.get_disabled_rules(),
        }, indent=2))
    else:
        print("Enabled rules:")
        for rule in sf.get_enabled_rules():
            print(f"  - {rule}")

        if sf.get_disabled_rules():
            print("\nDisabled rules:")
            for rule in sf.get_disabled_rules():
                print(f"  - {rule}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SandFilter - Sensitive Information Filter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Filter command
    filter_parser = subparsers.add_parser(
        "filter",
        help="Filter sensitive information from text",
    )
    filter_parser.add_argument(
        "text",
        nargs="?",
        help="Text to filter (if not provided, reads from stdin)",
    )
    filter_parser.add_argument(
        "-i", "--input",
        help="Input file to read from",
    )
    filter_parser.add_argument(
        "-c", "--config",
        help="Path to config file",
    )
    filter_parser.add_argument(
        "--disable",
        nargs="+",
        help="Rules to disable",
    )
    filter_parser.add_argument(
        "--enable",
        nargs="+",
        help="Rules to enable",
    )
    filter_parser.add_argument(
        "--disable-group",
        nargs="+",
        help="Rule groups to disable",
    )
    filter_parser.add_argument(
        "--enable-group",
        nargs="+",
        help="Rule groups to enable",
    )
    filter_parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON",
    )
    filter_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detection details",
    )

    # List rules command
    list_parser = subparsers.add_parser(
        "rules",
        help="List available rules",
    )
    list_parser.add_argument(
        "-c", "--config",
        help="Path to config file",
    )
    list_parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if args.command == "filter":
        return filter_command(args)
    elif args.command == "rules":
        return list_rules_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
