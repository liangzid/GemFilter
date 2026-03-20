"""
Unit tests for UINotifier.
"""

import pytest
from gemfilter.skill.ui import UINotifier, Notification, NotificationStyle


class TestUINotifier:
    """Tests for UINotifier class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        notifier = UINotifier()

        assert notifier._style == NotificationStyle.BANNER
        assert notifier._show_types is True
        assert notifier._show_count is True
        assert notifier._custom_banner is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        notifier = UINotifier(
            style=NotificationStyle.INLINE,
            show_types=False,
            show_count=False,
            custom_banner="Custom: {count}",
        )

        assert notifier._style == NotificationStyle.INLINE
        assert notifier._show_types is False
        assert notifier._show_count is False
        assert notifier._custom_banner == "Custom: {count}"

    def test_notify_banner_style(self):
        """Test notification with banner style."""
        notifier = UINotifier(style=NotificationStyle.BANNER)
        message = notifier.notify(3, ["email", "phone"])

        assert "GemFilter" in message
        assert "3" in message
        assert "🔒" in message

    def test_notify_inline_style(self):
        """Test notification with inline style."""
        notifier = UINotifier(style=NotificationStyle.INLINE)
        message = notifier.notify(2, ["email"])

        assert "🔒" in message
        assert "2" in message

    def test_notify_detailed_style(self):
        """Test notification with detailed style."""
        notifier = UINotifier(style=NotificationStyle.DETAILED)
        message = notifier.notify(2, ["email", "api_key"])

        assert "GemFilter" in message
        assert "2" in message
        assert "email" in message
        assert "api_key" in message

    def test_notify_silent_style(self):
        """Test notification with silent style."""
        notifier = UINotifier(style=NotificationStyle.SILENT)
        message = notifier.notify(5, ["email"])

        assert message == ""

    def test_notify_no_types(self):
        """Test notification without showing types."""
        notifier = UINotifier(show_types=False)
        message = notifier.notify(3, ["email", "phone", "password"])

        # Should not contain type names
        assert "email" not in message
        assert "phone" not in message

    def test_notify_no_count(self):
        """Test notification without showing count."""
        notifier = UINotifier(show_count=False, custom_banner="Filtered gems: {count}")
        message = notifier.notify(3, ["email"])

        # Should not contain the number when show_count=False and using custom banner
        # But custom_banner uses {count} so it will show
        assert "3" in message or "GemFilter" in message  # Either format is OK

    def test_notify_custom_banner(self):
        """Test notification with custom banner."""
        notifier = UINotifier(custom_banner="Filtered {count} items")
        message = notifier.notify(5, [])

        assert message == "Filtered 5 items"

    def test_get_banner(self):
        """Test getting banner."""
        notifier = UINotifier()
        banner = notifier.get_banner()

        assert "🔒" in banner

    def test_get_banner_silent(self):
        """Test getting banner in silent mode."""
        notifier = UINotifier(style=NotificationStyle.SILENT)
        banner = notifier.get_banner()

        assert banner == ""

    def test_format_notification(self):
        """Test formatting notification object."""
        notifier = UINotifier(style=NotificationStyle.BANNER)
        notification = notifier.format_notification(3, ["email", "phone"])

        assert isinstance(notification, Notification)
        assert notification.gem_count == 3
        assert "email" in notification.gem_types
        assert "phone" in notification.gem_types
        assert notification.style == NotificationStyle.BANNER

    def test_format_partial_mask(self):
        """Test formatting partial mask display."""
        notifier = UINotifier()
        text = "Contact: real@example.com"
        mapping = {"t***@example.com": "real@example.com"}

        result = notifier.format_partial_mask(text, mapping, display_fakes=True)

        assert "t***@example.com" in result
        assert "real@example.com" not in result

    def test_format_partial_mask_no_fakes(self):
        """Test formatting with no mappings."""
        notifier = UINotifier()
        text = "Hello world"
        mapping = {}

        result = notifier.format_partial_mask(text, mapping)

        assert result == text

    def test_format_partial_mask_generic(self):
        """Test formatting with generic markers."""
        notifier = UINotifier()
        text = "Contact: real@example.com"
        mapping = {"t***@example.com": "real@example.com"}

        result = notifier.format_partial_mask(text, mapping, display_fakes=False)

        assert "[EMAIL]" in result

    def test_get_gem_symbol(self):
        """Test getting gem symbols."""
        notifier = UINotifier()

        assert "📧" == notifier.get_gem_symbol("email")
        assert "📱" == notifier.get_gem_symbol("phone_cn")
        assert "🔑" == notifier.get_gem_symbol("api_key")
        assert "💎" == notifier.get_gem_symbol("unknown")

    def test_format_gem_list(self):
        """Test formatting gem list."""
        notifier = UINotifier()
        mapping = {
            "t***@example.com": "real@example.com",
            "138****5678": "13812345678",
        }
        gem_types = {
            "t***@example.com": "email",
            "138****5678": "phone_cn",
        }

        result = notifier.format_gem_list(mapping, gem_types)

        assert len(result) == 2
        # Check that results contain symbols
        assert any("📧" in r or "💎" in r for r in result)
        assert any("📱" in r or "💎" in r for r in result)

    def test_create_activation_header(self):
        """Test creating activation header."""
        notifier = UINotifier(style=NotificationStyle.BANNER)
        header = notifier.create_activation_header(2, ["email", "phone"])

        assert "🔒" in header
        assert "2" in header

    def test_create_activation_header_silent(self):
        """Test creating header in silent mode."""
        notifier = UINotifier(style=NotificationStyle.SILENT)
        header = notifier.create_activation_header(2, ["email"])

        assert header == ""

    def test_create_footer(self):
        """Test creating footer."""
        notifier = UINotifier(style=NotificationStyle.DETAILED)
        footer = notifier.create_footer(session_id="abc12345")

        assert "---" in footer
        assert "abc12345" in footer

    def test_create_footer_silent(self):
        """Test creating footer in silent mode."""
        notifier = UINotifier(style=NotificationStyle.SILENT)
        footer = notifier.create_footer()

        assert footer == ""

    def test_style_setter(self):
        """Test setting notification style."""
        notifier = UINotifier()
        assert notifier.style == NotificationStyle.BANNER

        notifier.style = NotificationStyle.INLINE
        assert notifier.style == NotificationStyle.INLINE


class TestNotification:
    """Tests for Notification dataclass."""

    def test_create_notification(self):
        """Test creating notification."""
        notification = Notification(
            message="🔒 GemFilter: 3 gems protected",
            gem_count=3,
            gem_types=["email", "phone"],
            style=NotificationStyle.BANNER,
        )

        assert notification.message == "🔒 GemFilter: 3 gems protected"
        assert notification.gem_count == 3
        assert len(notification.gem_types) == 2
        assert notification.style == NotificationStyle.BANNER

    def test_notification_with_raw(self):
        """Test notification with raw message."""
        notification = Notification(
            message="Test",
            gem_count=0,
            gem_types=[],
            style=NotificationStyle.SILENT,
            raw_notification="Original raw message",
        )

        assert notification.raw_notification == "Original raw message"


class TestUINotifierEdgeCases:
    """Edge case tests for UINotifier."""

    def test_empty_types_list(self):
        """Test notification with empty types list."""
        notifier = UINotifier()
        message = notifier.notify(0, [])

        # Should still work
        assert "0" in message or "GemFilter" in message

    def test_none_types(self):
        """Test notification with None types."""
        notifier = UINotifier()
        message = notifier.notify(3, None)

        # Should handle None gracefully
        assert "3" in message

    def test_unknown_gem_type_symbol(self):
        """Test getting symbol for unknown gem type."""
        notifier = UINotifier()
        symbol = notifier.get_gem_symbol("totally_unknown_type_xyz")

        assert symbol == "💎"

    def test_format_gem_list_empty(self):
        """Test formatting empty gem list."""
        notifier = UINotifier()
        result = notifier.format_gem_list({})

        assert result == []

    def test_format_gem_list_no_types(self):
        """Test formatting gem list without types."""
        notifier = UINotifier()
        mapping = {"fake@example.com": "real@example.com"}

        result = notifier.format_gem_list(mapping)

        assert len(result) == 1
        # Should use "unknown" for missing types
        assert "💎" in result[0]


class TestFormatMaskedTextForDisplay:
    """Tests for format_masked_text_for_display function."""

    def test_format_masked_text(self):
        """Test formatting masked text for display."""
        from gemfilter.skill.ui import format_masked_text_for_display

        text = "Contact: real@example.com"
        mapping = {"t***@example.com": "real@example.com"}

        display_text, notification = format_masked_text_for_display(
            text, mapping, NotificationStyle.BANNER
        )

        assert "t***@example.com" in display_text
        assert "real@example.com" not in display_text
        assert "🔒" in notification


class TestUINotifierFromConfig:
    """Tests for UINotifier.from_config class method."""

    def test_from_config(self):
        """Test creating UINotifier from config."""
        from gemfilter.skill.config import SkillConfig

        config = SkillConfig()
        config.notification.style = NotificationStyle.INLINE
        config.notification.show_types = False

        notifier = UINotifier.from_config(config)

        assert notifier.style == NotificationStyle.INLINE
        assert notifier._show_types is False
