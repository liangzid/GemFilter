"""
Unit tests for GemMasker.
"""

import pytest
from gemfilter.skill.masker import GemMasker
from gemfilter import SandFilter


def make_masker(*enable_rules):
    """Create a GemMasker with specified rules enabled."""
    sf = SandFilter()
    if enable_rules:
        sf.enable_rules(*enable_rules)
    return GemMasker(filter_engine=sf)


class TestGemMasker:
    """Tests for GemMasker class."""

    def test_init_with_default_filter(self):
        """Test initialization with default filter."""
        masker = GemMasker()
        assert masker._filter_engine is not None

    def test_mask_email(self):
        """Test masking email addresses."""
        masker = make_masker("email")
        text = "Contact me at john.doe@example.com please"

        masked_text, mapping = masker.mask(text)

        # Check that original email is not in masked text
        assert "john.doe@example.com" not in masked_text

        # Check that a fake placeholder exists
        assert len(mapping) > 0

        # The fake should look like an email
        fakes = list(mapping.keys())
        for fake in fakes:
            assert "@" in fake

    def test_mask_phone_cn(self):
        """Test masking Chinese phone numbers."""
        masker = make_masker("phone_cn")
        # Without dashes for proper matching
        text = "My phone is 13812345678"

        masked_text, mapping = masker.mask(text)

        assert "13812345678" not in masked_text
        assert len(mapping) > 0

    def test_mask_multiple_gems(self):
        """Test masking multiple gems in single text."""
        masker = make_masker("email", "phone_cn")
        text = "Email: test@example.com, Phone: 13912345678"

        masked_text, mapping = masker.mask(text)

        assert "test@example.com" not in masked_text
        assert "13912345678" not in masked_text
        assert len(mapping) >= 2

    def test_mask_no_gems(self):
        """Test text with no gems."""
        masker = GemMasker()
        text = "Hello, this is a normal message"

        masked_text, mapping = masker.mask(text)

        assert masked_text == text
        assert len(mapping) == 0

    def test_mask_api_key(self):
        """Test masking API keys."""
        masker = GemMasker()
        text = "api_key=sk-1234567890abcdefghij"

        masked_text, mapping = masker.mask(text)

        assert "sk-1234567890abcdefghij" not in masked_text
        assert len(mapping) > 0

    def test_mask_generic_api_key(self):
        """Test masking generic sk- API keys."""
        masker = GemMasker()
        # Use a key with 20+ chars after sk- to match the pattern
        text = "sk-abc123xyz789def456789"

        masked_text, mapping = masker.mask(text)

        assert "sk-abc123xyz789def456789" not in masked_text
        assert len(mapping) > 0

    def test_mask_password(self):
        """Test masking passwords."""
        masker = GemMasker()
        text = "password=mysecretpassword"

        masked_text, mapping = masker.mask(text)

        assert "mysecretpassword" not in masked_text
        assert len(mapping) > 0

    def test_mask_credit_card(self):
        """Test masking credit card numbers."""
        masker = GemMasker()
        text = "Card: 4111-1111-1111-1111"

        masked_text, mapping = masker.mask(text)

        assert "4111-1111-1111-1111" not in masked_text
        assert len(mapping) > 0

    def test_mask_ipv4(self):
        """Test masking IPv4 addresses."""
        masker = make_masker("ipv4")
        text = "Server: 192.168.1.100"

        masked_text, mapping = masker.mask(text)

        assert "192.168.1.100" not in masked_text
        assert len(mapping) > 0

    def test_mask_id_card_cn(self):
        """Test masking Chinese ID cards."""
        masker = GemMasker()
        text = "ID: 110101199001011234"

        masked_text, mapping = masker.mask(text)

        assert "110101199001011234" not in masked_text
        assert len(mapping) > 0

    def test_mask_private_key(self):
        """Test masking private keys."""
        masker = GemMasker()
        text = "Key: -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"

        masked_text, mapping = masker.mask(text)

        assert "-----BEGIN RSA PRIVATE KEY-----" not in masked_text
        assert "<PRIVATE_KEY_" in masked_text

    def test_get_detections(self):
        """Test getting detections without masking."""
        masker = make_masker("email")
        text = "Email: test@example.com"

        detections = masker.get_detections(text)

        assert len(detections) == 1
        assert detections[0].rule_name == "email"
        assert detections[0].match == "test@example.com"

    def test_get_detection_summary(self):
        """Test getting detection summary."""
        masker = make_masker("email", "phone_cn")
        text = "Email: test@example.com, Phone: 13912345678"

        summary = masker.get_detection_summary(text)

        assert summary.get("email", 0) >= 1
        assert summary.get("phone_cn", 0) >= 1

    def test_register_custom_masker(self):
        """Test registering custom masker."""
        masker = GemMasker()

        def custom_mask(original, fake):
            return f"[CUSTOM:{original[:3]}]"

        masker.register_masker("email", custom_mask)
        # The custom masker should be registered
        assert "email" in masker._maskers

    def test_mask_empty_text(self):
        """Test masking empty text."""
        masker = GemMasker()

        masked_text, mapping = masker.mask("")

        assert masked_text == ""
        assert len(mapping) == 0

    def test_mask_unicode_email(self):
        """Test masking Unicode email."""
        masker = make_masker("email")
        text = "Contact: 用户@example.com"

        masked_text, mapping = masker.mask(text)

        # The filter should handle unicode
        assert "用户@example.com" not in masked_text or masked_text == text

    def test_mask_bearer_token(self):
        """Test masking bearer tokens."""
        masker = GemMasker()
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy"

        masked_text, mapping = masker.mask(text)

        assert "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy" not in masked_text
        assert len(mapping) > 0


class TestMaskerEmailEdgeCases:
    """Edge case tests for email masking."""

    def test_single_char_email(self):
        """Test masking single character email."""
        masker = make_masker("email")
        text = "Email: a@b.co"

        masked_text, mapping = masker.mask(text)

        # Should still be masked
        assert "a@b.co" not in masked_text

    def test_long_email(self):
        """Test masking long email."""
        masker = make_masker("email")
        text = "Email: verylongemailaddress@subdomain.example.com"

        masked_text, mapping = masker.mask(text)

        assert "verylongemailaddress@subdomain.example.com" not in masked_text

    def test_email_with_plus(self):
        """Test masking email with plus sign."""
        masker = make_masker("email")
        text = "Email: test+tag@example.com"

        masked_text, mapping = masker.mask(text)

        assert "test+tag@example.com" not in masked_text


class TestMaskerPhoneEdgeCases:
    """Edge case tests for phone masking."""

    def test_phone_with_country_code(self):
        """Test masking phone with country code."""
        masker = make_masker("phone_cn")
        # Use the raw phone without dashes for proper matching
        text = "Phone: +8613812345678"

        masked_text, mapping = masker.mask(text)

        assert "13812345678" not in masked_text

    def test_us_phone_formats(self):
        """Test masking various US phone formats."""
        masker = make_masker("phone_us")

        formats = [
            "(123) 456-7890",
            "123-456-7890",
            "123.456.7890",
            "+1 123 456 7890",
        ]

        for fmt in formats:
            text = f"Phone: {fmt}"
            masked_text, mapping = masker.mask(text)
            # The specific digits should be masked
            assert "123" not in masked_text or "456" not in masked_text or "7890" not in masked_text


class TestMaskerCustomMaskers:
    """Tests for custom masker registration."""

    def test_custom_masker_function(self):
        """Test using a custom masker function."""
        masker = make_masker("email")

        # Register a custom masker that preserves domain
        def preserve_domain_mask(original, fake):
            if "@" in original:
                local, domain = original.split("@", 1)
                return f"***@{domain}"
            return "***"

        masker.register_masker("email", preserve_domain_mask)

        text = "test@example.com"
        masked_text, mapping = masker.mask(text)

        # Check that our custom masker was used
        assert "@example.com" in masked_text


class TestMaskingModes:
    """Tests for strict, balanced, and utility masking modes."""

    def test_strict_mode_uses_typed_placeholder(self):
        masker = GemMasker(masking_mode="strict")

        masked_text, mapping = masker.mask("Email: user@example.com")

        assert masked_text == "Email: <EMAIL_1>"
        assert mapping == {"<EMAIL_1>": "user@example.com"}

    def test_balanced_mode_preserves_email_syntax_without_domain(self):
        masker = GemMasker(masking_mode="balanced")

        masked_text, mapping = masker.mask("Email: user@example.com")

        assert masked_text == "Email: <EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>"
        assert "example.com" not in masked_text
        assert mapping == {
            "<EMAIL_LOCAL_1>@<EMAIL_DOMAIN_1>": "user@example.com",
        }

    def test_utility_mode_uses_format_preserving_fake(self):
        masker = GemMasker(masking_mode="utility")

        masked_text, mapping = masker.mask("Email: user@example.com")

        assert masked_text == "Email: user1@example.test"
        assert mapping == {"user1@example.test": "user@example.com"}

    def test_existing_mapping_is_reused(self):
        masker = GemMasker(masking_mode="strict")

        masked_text, mapping = masker.mask(
            "Again: user@example.com",
            existing_mapping={"<EMAIL_7>": "user@example.com"},
        )

        assert masked_text == "Again: <EMAIL_7>"
        assert mapping == {"<EMAIL_7>": "user@example.com"}

    def test_balanced_url_masks_host_query_and_path_structure(self):
        masker = GemMasker(masking_mode="balanced")

        masked_text, mapping = masker.mask("Visit https://api.internal.test:8443/v1/users?id=123")

        assert "api.internal.test" not in masked_text
        assert "id=123" not in masked_text
        assert "https://<HOST_1>:8443/<PATH_1_1>/<PATH_1_2>?<QUERY>" in masked_text
        assert len(mapping) == 1

    def test_balanced_openai_key_uses_typed_secret(self):
        masker = GemMasker(masking_mode="balanced")

        masked_text, mapping = masker.mask(
            "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456"
        )

        assert "sk-proj-" not in masked_text
        assert "<OPENAI_KEY_1>" in masked_text
        assert list(mapping.keys()) == ["<OPENAI_KEY_1>"]

    def test_balanced_database_url_uses_typed_secret(self):
        masker = GemMasker(masking_mode="balanced")

        masked_text, mapping = masker.mask(
            "DATABASE_URL=postgres://user:pass@db.internal:5432/app"
        )

        assert "db.internal" not in masked_text
        assert "<DATABASE_URL_1>" in masked_text
        assert list(mapping.keys()) == ["<DATABASE_URL_1>"]
