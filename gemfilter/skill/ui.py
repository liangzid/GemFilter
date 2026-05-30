"""
UI Notifier for GemFilter Skill.

Handles user notifications and visual feedback.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .config import NotificationStyle


@dataclass
class Notification:
    """Represents a notification to display to the user."""
    message: str
    gem_count: int
    gem_types: List[str]
    style: NotificationStyle
    raw_notification: Optional[str] = None


class UINotifier:
    """
    Handles user notifications and partial masking display.

    Provides multiple notification styles and formats
    gems for display in the UI.
    """

    # Default banner template
    DEFAULT_BANNER = "🔒 GemFilter: {count} gem(s) protected"
    DEFAULT_INLINE = "🔒 ({count} gems filtered)"
    DEFAULT_DETAILED = """🔒 GemFilter Active
Protected: {count} gem(s)
Types: {types}"""

    PROMINENT_WIDTH = 50

    # LLM-facing header injected into masked text
    DEFAULT_LLM_HEADER = """\
[GEMFILTER SECURITY NOTICE]
The following text has been filtered to protect sensitive information.
Masked types: {types}
{count} item(s) were replaced with safe placeholders like [TYPE_NAME].
Do NOT attempt to reconstruct or infer the original masked values.
──────────────────────────────────────────────────
"""

    # Unicode symbols for gem types
    GEM_SYMBOLS: Dict[str, str] = {
        "email": "📧",
        "phone_cn": "📱",
        "phone_us": "📞",
        "id_card_cn": "🪪",
        "passport": "🛂",
        "credit_card": "💳",
        "api_key": "🔑",
        "api_key_generic": "🔑",
        "password": "🔐",
        "bearer_token": "🎫",
        "aws_access_key": "☁️",
        "private_key": "🔒",
        "ipv4": "🌐",
        "ipv6": "🌐",
        "mac_address": "📡",
        "url": "🔗",
    }

    def __init__(
        self,
        style: NotificationStyle = NotificationStyle.BANNER,
        show_types: bool = True,
        show_count: bool = True,
        custom_banner: Optional[str] = None,
    ):
        """
        Initialize UINotifier.

        Args:
            style: Notification style (banner, inline, detailed, silent)
            show_types: Whether to show gem types in notification
            show_count: Whether to show gem count in notification
            custom_banner: Custom banner template string
        """
        self._style = style
        self._show_types = show_types
        self._show_count = show_count
        self._custom_banner = custom_banner

    @property
    def style(self) -> NotificationStyle:
        """Get current notification style."""
        return self._style

    @style.setter
    def style(self, value: NotificationStyle) -> None:
        """Set notification style."""
        self._style = value

    def notify(
        self,
        gem_count: int,
        masked_types: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a notification message.

        Args:
            gem_count: Number of gems protected
            masked_types: List of gem types that were masked

        Returns:
            Formatted notification string
        """
        if self._style == NotificationStyle.SILENT:
            return ""

        if masked_types is None:
            masked_types = []

        types_str = ", ".join(masked_types) if masked_types else "unknown"

        if self._custom_banner:
            template = self._custom_banner
        elif self._style == NotificationStyle.BANNER:
            template = self.DEFAULT_BANNER
        elif self._style == NotificationStyle.INLINE:
            template = self.DEFAULT_INLINE
        elif self._style == NotificationStyle.DETAILED:
            template = self.DEFAULT_DETAILED
        elif self._style == NotificationStyle.PROMINENT:
            return self._build_prominent_notification(gem_count, types_str)
        else:
            template = self.DEFAULT_BANNER

        message = template.format(
            count=gem_count,
            types=types_str,
        )

        return message

    def _build_prominent_notification(self, gem_count: int, types_str: str) -> str:
        """Build a box-drawn prominent notification with proper alignment."""
        w = self.PROMINENT_WIDTH - 2  # inner width between borders
        count_str = f"{gem_count} item(s)"

        lines = [
            "╔" + "═" * (w + 2) + "╗",
            self._pad_line("⚠️  GEMFILTER: SENSITIVE INFO PROTECTED", w),
        ]
        if types_str and types_str != "unknown":
            detail = f"Masked: {types_str}"
            if len(detail) > w:
                detail = detail[:w - 1] + "…"
            lines.append(self._pad_line(detail, w))
        lines.append(self._pad_line(f"{count_str} protected in total", w))
        lines.append("╚" + "═" * (w + 2) + "╝")
        return "\n".join(lines)

    @staticmethod
    def _pad_line(text: str, width: int) -> str:
        """Pad a line with the box border and trailing spaces."""
        return "║ " + text.ljust(width) + " ║"

    def get_llm_header(
        self,
        gem_count: int,
        gem_types: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a header to prepend to masked text sent to the LLM.

        This informs the LLM about what types of information were masked,
        helping it understand why certain data appears as placeholders.

        Args:
            gem_count: Number of gems protected
            gem_types: List of gem types that were masked

        Returns:
            Header string to prepend to LLM-facing text
        """
        if self._style == NotificationStyle.SILENT or gem_count == 0:
            return ""
        if not gem_types:
            gem_types = []

        types_str = ", ".join(gem_types) if gem_types else "unknown"
        return self.DEFAULT_LLM_HEADER.format(
            count=gem_count,
            types=types_str,
        )

    def get_banner(self) -> str:
        """
        Get the standard GemFilter activation banner.

        Returns:
            Banner string (empty if silent mode)
        """
        return self.notify(0, [])

    def format_notification(
        self,
        gem_count: int,
        gem_types: List[str],
    ) -> Notification:
        """
        Format a complete notification object.

        Args:
            gem_count: Number of gems
            gem_types: Types of gems

        Returns:
            Notification object
        """
        message = self.notify(gem_count, gem_types if self._show_types else [])
        return Notification(
            message=message,
            gem_count=gem_count if self._show_count else 0,
            gem_types=gem_types,
            style=self._style,
        )

    def format_partial_mask(
        self,
        text: str,
        mapping: Dict[str, str],
        display_fakes: bool = True,
    ) -> str:
        """
        Format text with partial masking for user display.

        This shows the user what the masked values look like,
        while the real gems remain stored privately.

        Args:
            text: Original text with gems
            mapping: Dict of fake_placeholder -> original_value
            display_fakes: If True, replace gems with their fake versions.
                          If False, use generic [GEM] markers.

        Returns:
            Text formatted for display
        """
        if not mapping:
            return text

        formatted = text
        for fake, original in mapping.items():
            if display_fakes:
                # Show the fake placeholder
                formatted = formatted.replace(original, fake)
            else:
                # Show generic marker
                formatted = formatted.replace(
                    original,
                    f"[{self._get_gem_type(original)}]"
                )

        return formatted

    def _get_gem_type(self, original: str) -> str:
        """
        Get the gem type from an original value.

        This is a heuristic and may not be accurate.
        """
        if "@" in original:
            return "EMAIL"
        if original.startswith("sk-"):
            return "API_KEY"
        if len(original) == 11 and original.isdigit():
            return "PHONE"
        if len(original) == 16 and original.isdigit():
            return "CREDIT_CARD"
        return "GEM"

    def get_gem_symbol(self, gem_type: str) -> str:
        """
        Get the Unicode symbol for a gem type.

        Args:
            gem_type: The gem type (e.g., "email", "phone_cn")

        Returns:
            Unicode symbol or default gem emoji
        """
        return self.GEM_SYMBOLS.get(gem_type, "💎")

    def format_gem_list(
        self,
        mapping: Dict[str, str],
        gem_types: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """
        Format a list of gems for display.

        Args:
            mapping: Dict of fake -> original
            gem_types: Optional dict of fake -> gem_type

        Returns:
            List of formatted strings like "📧 t***@example.com"
        """
        formatted = []
        for fake, original in mapping.items():
            gem_type = (gem_types or {}).get(fake, "unknown")
            symbol = self.get_gem_symbol(gem_type)
            # Use fake for display
            display_value = fake if fake in mapping.values() else original
            formatted.append(f"{symbol} {display_value}")
        return formatted

    def create_activation_header(
        self,
        gem_count: int,
        gem_types: List[str],
    ) -> str:
        """
        Create a header to prepend to responses.

        Args:
            gem_count: Number of gems protected
            gem_types: Types of gems

        Returns:
            Header string with newlines
        """
        if self._style == NotificationStyle.SILENT:
            return ""

        parts = []

        if gem_count > 0:
            parts.append(self.notify(gem_count, gem_types if self._show_types else []))

        if self._style == NotificationStyle.DETAILED and gem_types:
            symbols = [self.get_gem_symbol(t) for t in gem_types]
            parts.append(f"Symbols: {', '.join(symbols)}")

        if parts:
            return "\n".join(parts) + "\n\n"

        return ""

    def create_footer(
        self,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Create a footer to append to responses.

        Args:
            session_id: Optional session ID for debugging

        Returns:
            Footer string
        """
        if self._style == NotificationStyle.SILENT:
            return ""

        parts = ["---"]

        if self._style == NotificationStyle.DETAILED:
            if session_id:
                parts.append(f"Session: {session_id[:8]}...")
            parts.append("Powered by GemFilter")

        return "\n".join(parts)

    @classmethod
    def from_config(cls, config) -> "UINotifier":
        """
        Create UINotifier from SkillConfig.

        Args:
            config: SkillConfig instance

        Returns:
            UINotifier instance
        """
        return cls(
            style=config.notification.style,
            show_types=config.notification.show_types,
            show_count=config.notification.show_count,
            custom_banner=config.notification.custom_banner,
        )


def format_masked_text_for_display(
    text: str,
    mapping: Dict[str, str],
    style: NotificationStyle = NotificationStyle.BANNER,
) -> Tuple[str, str]:
    """
    Convenience function to format text with masking for display.

    Args:
        text: Original text
        mapping: Dict of fake -> original
        style: Notification style

    Returns:
        Tuple of (display_text, notification_message)
    """
    notifier = UINotifier(style=style)

    # Count gems by type
    gem_types = []
    for fake in mapping.keys():
        if "email" in fake or "@" in fake:
            gem_types.append("email")
        elif "phone" in fake or fake[0] == "1" and len(fake) == 11:
            gem_types.append("phone")
        elif "api" in fake.lower():
            gem_types.append("api_key")
        elif "pass" in fake.lower():
            gem_types.append("password")
        else:
            gem_types.append("general")

    gem_types = list(set(gem_types))

    # Create display text
    display_text = text
    for fake, original in mapping.items():
        display_text = display_text.replace(original, fake)

    # Create notification
    notification = notifier.notify(len(mapping), gem_types)

    return display_text, notification
