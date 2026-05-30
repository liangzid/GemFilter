"""
Command-line installer for GemFilter agent adapters.
"""

import argparse
import sys

from gemfilter.skill.adapters.base import create_adapter


SUPPORTED_AGENTS = ("claude_code", "opencode", "coodex")


def install_agent(agent: str) -> int:
    """Install GemFilter hooks for an agent."""
    adapter = create_adapter(agent)
    if adapter.install():
        print(f"GemFilter installed for {adapter.name}")
        return 0
    print(f"Failed to install GemFilter for {agent}", file=sys.stderr)
    return 1


def uninstall_agent(agent: str) -> int:
    """Uninstall GemFilter hooks for an agent."""
    adapter = create_adapter(agent)
    if adapter.uninstall():
        print(f"GemFilter uninstalled for {adapter.name}")
        return 0
    print(f"Failed to uninstall GemFilter for {agent}", file=sys.stderr)
    return 1


def status_agent(agent: str) -> int:
    """Show GemFilter install status for an agent."""
    adapter = create_adapter(agent)
    status = "installed" if adapter.validate_installation() else "not installed"
    print(f"{adapter.name}: {status}")
    return 0


def main() -> int:
    """Entry point for `python -m gemfilter.skill.install`."""
    parser = argparse.ArgumentParser(
        description="Install GemFilter hooks for AI coding agents",
    )
    parser.add_argument(
        "--agent",
        choices=SUPPORTED_AGENTS,
        help="Agent adapter to manage",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall GemFilter from the selected agent",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show installation status",
    )

    args = parser.parse_args()

    if args.status:
        agents = [args.agent] if args.agent else SUPPORTED_AGENTS
        exit_code = 0
        for agent in agents:
            exit_code |= status_agent(agent)
        return exit_code

    if not args.agent:
        parser.error("--agent is required unless --status is used")

    if args.uninstall:
        return uninstall_agent(args.agent)

    return install_agent(args.agent)


if __name__ == "__main__":
    sys.exit(main())
