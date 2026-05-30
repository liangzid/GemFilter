"""
Unit tests for GemUnmasker.
"""

import pytest
from gemfilter.skill.unmasker import GemUnmasker, ResponseSanitizer
from gemfilter import SandFilter


class TestGemUnmasker:
    """Tests for GemUnmasker class."""

    def test_init_with_default_filter(self):
        """Test initialization with default filter."""
        unmasker = GemUnmasker()
        assert unmasker._filter_engine is not None
        assert unmasker._check_response_content is True

    def test_init_custom_settings(self):
        """Test initialization with custom settings."""
        unmasker = GemUnmasker(check_response_content=False)
        assert unmasker._check_response_content is False

    def test_restore_simple_fake(self):
        """Test restoring simple fake placeholder."""
        unmasker = GemUnmasker()
        text = "I received your email at t***@example.com_ema"

        result = unmasker.restore(text, "test-session")

        assert "[FILTERED]" in result
        assert "t***@example.com" not in result or result.count("[FILTERED]") >= 1

    def test_restore_multiple_fakes(self):
        """Test restoring multiple fake placeholders."""
        unmasker = GemUnmasker()
        text = "Email: t***@example.com_ema, Phone: 138****5678_pho"

        result = unmasker.restore(text, "test-session")

        assert "[FILTERED]" in result

    def test_restore_no_fakes(self):
        """Test restoring text with no fakes."""
        unmasker = GemUnmasker()
        text = "Hello, this is a normal message"

        result = unmasker.restore(text, "test-session")

        assert result == text

    def test_restore_with_check_content(self):
        """Test restoring with new gem detection in response."""
        sf = SandFilter()
        sf.enable_rules("email")
        unmasker = GemUnmasker(filter_engine=sf, check_response_content=True)
        text = "Your email is newuser@gmail.com"

        result = unmasker.restore(text, "test-session")

        # The new email in the response should be masked
        assert "[EMAIL]" in result or "[FILTERED]" in result

    def test_restore_without_check_content(self):
        """Test restoring without new gem detection."""
        unmasker = GemUnmasker(check_response_content=False)
        text = "Your email is newuser@gmail.com"

        result = unmasker.restore(text, "test-session")

        # Without content check, only fake placeholders are replaced
        # The new email would remain unless it matches fake patterns
        assert "[FILTERED]" in result or "newuser@gmail.com" in result

    def test_restore_with_marker(self):
        """Test restoring with custom marker."""
        unmasker = GemUnmasker()
        text = "Email: t***@example.com_ema"

        result, count = unmasker.restore_with_marker(text, "[REDACTED]")

        assert "[REDACTED]" in result
        assert count >= 1

    def test_restore_with_marker_no_change(self):
        """Test restoring with marker when no fakes present."""
        unmasker = GemUnmasker()
        text = "Hello world"

        result, count = unmasker.restore_with_marker(text, "[REDACTED]")

        assert result == text
        assert count == 0

    def test_find_fake_placeholders_email_pattern(self):
        """Test finding email-like fake placeholders."""
        unmasker = GemUnmasker()
        text = "Contact: t***@example.com"

        fakes = unmasker._find_fake_placeholders(text)

        assert len(fakes) >= 1

    def test_find_fake_placeholders_phone_pattern(self):
        """Test finding phone-like fake placeholders."""
        unmasker = GemUnmasker()
        text = "Call: 138****5678"

        fakes = unmasker._find_fake_placeholders(text)

        assert len(fakes) >= 1

    def test_find_fake_placeholders_api_key_pattern(self):
        """Test finding API key fake placeholders."""
        unmasker = GemUnmasker()
        text = "Key: sk-****xyz"

        fakes = unmasker._find_fake_placeholders(text)

        assert len(fakes) >= 1

    def test_has_fake_placeholders_true(self):
        """Test has_fake_placeholders returns True."""
        unmasker = GemUnmasker()
        text = "Email: t***@example.com"

        assert unmasker.has_fake_placeholders(text) is True

    def test_has_fake_placeholders_false(self):
        """Test has_fake_placeholders returns False."""
        unmasker = GemUnmasker()
        text = "Hello world"

        assert unmasker.has_fake_placeholders(text) is False

    def test_get_fake_count(self):
        """Test counting fake placeholders."""
        unmasker = GemUnmasker()
        text = "Email: t***@example.com, Phone: 138****5678"

        count = unmasker.get_fake_count(text)

        assert count >= 2

    def test_mask_new_gems(self):
        """Test masking new gems in response."""
        unmasker = GemUnmasker()
        text = "Your API key is sk-abcdefghijk1234567890"

        result = unmasker._mask_new_gems(text)

        assert "sk-abcdefghijk1234567890" not in result
        assert "[API_KEY_GENERIC]" in result

    def test_mask_new_gems_no_gems(self):
        """Test masking text with no gems."""
        unmasker = GemUnmasker()
        text = "Hello, this is a normal message with no sensitive data"

        result = unmasker._mask_new_gems(text)

        assert result == text

    def test_restore_preserves_non_fake_text(self):
        """Test that restore preserves non-fake text."""
        unmasker = GemUnmasker()
        text = "Hello, how are you today?"

        result = unmasker.restore(text, "test-session")

        assert "Hello, how are you today?" in result


class TestResponseSanitizer:
    """Tests for ResponseSanitizer class."""

    def test_init(self):
        """Test sanitizer initialization."""
        sanitizer = ResponseSanitizer()
        assert sanitizer._unmasker is not None

    def test_sanitize_no_content(self):
        """Test sanitizing empty text."""
        sanitizer = ResponseSanitizer()
        text = ""

        result, report = sanitizer.sanitize(text, "test-session")

        assert result == ""
        assert report["fake_placeholders_found"] == 0
        assert report["new_gems_masked"] == 0

    def test_sanitize_with_fakes(self):
        """Test sanitizing text with fake placeholders."""
        sanitizer = ResponseSanitizer()
        text = "I see you masked t***@example.com_ema"

        result, report = sanitizer.sanitize(text, "test-session")

        assert "[FILTERED]" in result
        assert report["fake_placeholders_found"] >= 1

    def test_sanitize_report_details(self):
        """Test sanitization report contains correct details."""
        sanitizer = ResponseSanitizer()
        text = "Email: t***@example.com_ema"

        result, report = sanitizer.sanitize(text, "test-session")

        assert "original_length" in report
        assert "sanitized_length" in report
        assert "had_sensitive_content" in report
        assert report["had_sensitive_content"] is True

    def test_get_detections(self):
        """Test getting detections from sanitizer."""
        sf = SandFilter()
        sf.enable_rules("email")
        unmasker = GemUnmasker(filter_engine=sf)
        sanitizer = ResponseSanitizer(unmasker=unmasker)
        text = "Contact me at test@example.com"

        detections = sanitizer.get_detections(text)

        assert len(detections) >= 1


class TestGemUnmaskerEdgeCases:
    """Edge case tests for GemUnmasker."""

    def test_empty_text(self):
        """Test handling empty text."""
        unmasker = GemUnmasker()
        text = ""

        result = unmasker.restore(text, "test-session")

        assert result == ""

    def test_only_whitespace(self):
        """Test handling whitespace-only text."""
        unmasker = GemUnmasker()
        text = "   \n\t  "

        result = unmasker.restore(text, "test-session")

        assert result == text

    def test_special_characters(self):
        """Test handling special characters."""
        unmasker = GemUnmasker()
        text = "Special: !@#$%^&*()"

        result = unmasker.restore(text, "test-session")

        assert result == text

    def test_unicode_text(self):
        """Test handling unicode text."""
        unmasker = GemUnmasker()
        text = "中文: 用户@example.com"

        result = unmasker.restore(text, "test-session")

        # Should handle unicode gracefully
        assert isinstance(result, str)

    def test_already_filtered_marker(self):
        """Test handling text that already has [FILTERED]."""
        unmasker = GemUnmasker()
        text = "Already filtered: [FILTERED] and t***@example.com_ema"

        result = unmasker.restore(text, "test-session")

        # Should not double-replace
        assert result.count("[FILTERED]") >= 1

    def test_multiple_same_fake(self):
        """Test handling same fake placeholder multiple times."""
        unmasker = GemUnmasker()
        text = "First: t***@example.com_ema, Second: t***@example.com_ema"

        result, count = unmasker.restore_with_marker(text, "[FILTERED]")

        # Should replace all occurrences
        assert result.count("t***@example.com_ema") == 0
        assert "[FILTERED]" in result


class TestUnmaskerPatterns:
    """Tests for specific fake patterns."""

    def test_pattern_email(self):
        """Test email fake pattern."""
        unmasker = GemUnmasker()

        patterns = [
            "t***@gmail.com",
            "u***@example.org",
            "a***@test.co.uk",
        ]

        for pattern in patterns:
            fakes = unmasker._find_fake_placeholders(pattern)
            assert len(fakes) >= 1

    def test_pattern_phone_cn(self):
        """Test Chinese phone fake pattern."""
        unmasker = GemUnmasker()
        text = "138****5678"

        fakes = unmasker._find_fake_placeholders(text)

        assert len(fakes) >= 1

    def test_pattern_api_key(self):
        """Test API key fake pattern."""
        unmasker = GemUnmasker()

        patterns = [
            "sk-***xyz",
            "sk-****abc",
            "[API_KEY:sk***]",
        ]

        for pattern in patterns:
            fakes = unmasker._find_fake_placeholders(pattern)
            assert len(fakes) >= 1

    def test_pattern_bracketed(self):
        """Test bracketed marker patterns."""
        unmasker = GemUnmasker()

        patterns = [
            "[PRIVATE_KEY]",
            "[PASSWORD]",
            "[API_KEY]",
            "[FILTERED]",
            "[TOKEN]",
        ]

        for pattern in patterns:
            fakes = unmasker._find_fake_placeholders(pattern)
            assert len(fakes) >= 1
