"""
Unit tests for SandFilter core functionality.
"""

import pytest
from gemfilter import SandFilter, DetectionRule, Processors


class TestSandFilter:
    """Test SandFilter main class."""

    def test_basic_filter(self):
        """Test basic filtering with default settings."""
        sf = SandFilter()
        sf.enable_rules("email")
        result = sf.filter("我的邮箱是 test@example.com")

        assert "[EMAIL]" in result.text
        assert "test@example.com" not in result.text

    def test_multiple_detections(self):
        """Test filtering multiple sensitive items."""
        sf = SandFilter()
        sf.enable_rules("email", "phone_cn")
        text = "邮箱: test@example.com, 手机: 13800138000"
        result = sf.filter(text)

        assert result.text == "邮箱: [EMAIL], 手机: [PHONE_CN]"
        assert len(result.detections) == 2

    def test_disabled_rules(self):
        """Test disabling specific rules."""
        sf = SandFilter()
        sf.enable_rules("email")
        sf.disable_rules("email")

        result = sf.filter("test@example.com")
        assert "test@example.com" in result.text

    def test_enabled_rules(self):
        """Test enabling specific rules."""
        sf = SandFilter()
        sf.disable_rules()
        sf.enable_rules("email")

        result = sf.filter("test@example.com")
        assert "[EMAIL]" in result.text

    def test_group_operations(self):
        """Test group enable/disable."""
        sf = SandFilter()
        sf.enable_group("contact")
        sf.disable_group("contact")

        result = sf.filter("test@example.com and 13800138000")
        # Both should be unfiltered since contact group is disabled
        assert "test@example.com" in result.text


class TestCustomRules:
    """Test custom rule addition."""

    def test_add_custom_rule(self):
        """Test adding a custom detection rule."""
        sf = SandFilter()
        # Set higher priority to override built-in rules
        rule = DetectionRule(
            name="student_id",
            pattern=r"STU\d{8}",
            sensitive_type="education",
            priority=1,
        )
        sf.add_rule(rule)

        result = sf.filter("学生ID是 STU20240001")
        assert "[STUDENT_ID]" in result.text

    def test_custom_processor(self):
        """Test custom processor for a rule."""
        sf = SandFilter()
        rule = DetectionRule(
            name="custom",
            pattern=r"\d{6}",
        )
        sf.add_rule(rule, Processors.replace("[NUMBER]"))

        result = sf.filter("密码是 123456")
        assert "[NUMBER]" in result.text


class TestProcessors:
    """Test different processors."""

    def test_replace_processor(self):
        """Test replace processor."""
        processor = Processors.replace("[REDACTED]")
        result = processor.process("test@example.com", "email")
        assert result == "[REDACTED]"

    def test_partial_mask(self):
        """Test partial mask processor."""
        processor = Processors.partial_mask(preserve_prefix=2, preserve_suffix=2)
        result = processor.process("test@example.com", "email")
        # Email has special handling to preserve domain
        assert result == "t***@example.com"

    def test_delete_processor(self):
        """Test delete processor."""
        processor = Processors.delete()
        result = processor.process("secret", "password")
        assert result == ""

    def test_fixed_processor(self):
        """Test fixed value processor."""
        processor = Processors.fixed("[HIDDEN]")
        result = processor.process("secret", "password")
        assert result == "[HIDDEN]"


class TestBuiltInRules:
    """Test built-in rules."""

    def test_email_detection(self):
        """Test email detection."""
        sf = SandFilter()
        sf.enable_rules("email")
        result = sf.filter("Contact: user@domain.com")
        assert "[EMAIL]" in result.text

    def test_phone_cn_detection(self):
        """Test Chinese phone detection."""
        sf = SandFilter()
        sf.enable_rules("phone_cn")
        result = sf.filter("手机号: 13912345678")
        assert "[PHONE_CN]" in result.text

    def test_id_card_detection(self):
        """Test Chinese ID card detection."""
        sf = SandFilter()
        # Disable financial rules to avoid false matches on ID card numbers
        sf.disable_group("financial")
        result = sf.filter("身份证: 110101199001011234")
        assert "[ID_CARD_CN]" in result.text

    def test_api_key_detection(self):
        """Test API key detection."""
        sf = SandFilter()
        result = sf.filter("api_key = sk-1234567890abcdefghij")
        # The api_key rule matches first (priority 1)
        assert "[API_KEY]" in result.text

    def test_openai_api_key_detection(self):
        """Test OpenAI API key detection."""
        sf = SandFilter()
        result = sf.filter("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456")

        assert "[OPENAI_API_KEY]" in result.text
        assert result.detections[0].rule_name == "openai_api_key"

    def test_anthropic_api_key_detection(self):
        """Test Anthropic API key detection."""
        sf = SandFilter()
        result = sf.filter("ANTHROPIC_API_KEY=sk-ant-abcdefghijklmnopqrstuvwxyz123456")

        assert "[ANTHROPIC_API_KEY]" in result.text
        assert result.detections[0].rule_name == "anthropic_api_key"

    def test_github_token_detection(self):
        """Test GitHub token detection."""
        sf = SandFilter()
        result = sf.filter("GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyzABCDE12345")

        assert "[GITHUB_TOKEN]" in result.text
        assert result.detections[0].rule_name == "github_token"

    def test_npm_token_detection(self):
        """Test npm token detection."""
        sf = SandFilter()
        result = sf.filter("NPM_TOKEN=npm_abcdefghijklmnopqrstuvwxyzABCDE12345")

        assert "[NPM_TOKEN]" in result.text
        assert result.detections[0].rule_name == "npm_token"

    def test_pypi_token_detection(self):
        """Test PyPI token detection."""
        sf = SandFilter()
        result = sf.filter("PYPI_TOKEN=pypi-abcdefghijklmnopqrstuvwxyz123456")

        assert "[PYPI_TOKEN]" in result.text
        assert result.detections[0].rule_name == "pypi_token"

    def test_jwt_detection(self):
        """Test JWT detection."""
        sf = SandFilter()
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.signature"
        result = sf.filter(f"JWT={token}")

        assert "[JWT]" in result.text
        assert result.detections[0].rule_name == "jwt"

    def test_database_url_detection(self):
        """Test database URL detection."""
        sf = SandFilter()
        url = "postgres://user:pass@db.internal:5432/app"
        result = sf.filter(f"DATABASE_URL={url}")

        assert "[DATABASE_URL]" in result.text
        assert result.detections[0].rule_name == "database_url"

    def test_dotenv_secret_detection(self):
        """Test generic .env-style secret detection."""
        sf = SandFilter()
        result = sf.filter("SERVICE_TOKEN=supersecretvalue123")

        assert "[DOTENV_SECRET]" in result.text
        assert result.detections[0].rule_name == "dotenv_secret"

    def test_password_detection(self):
        """Test password detection."""
        sf = SandFilter()
        result = sf.filter("password = mysecretpassword")
        assert "[PASSWORD]" in result.text

    def test_ipv4_detection(self):
        """Test IPv4 detection."""
        sf = SandFilter()
        sf.enable_rules("ipv4")
        result = sf.filter("Server: 192.168.1.1")
        assert "[IPV4]" in result.text


class TestFilterResult:
    """Test FilterResult class."""

    def test_summary_generation(self):
        """Test summary is generated correctly."""
        sf = SandFilter()
        sf.enable_rules("email")
        result = sf.filter("a@b.com c@d.com e@f.com")

        # Summary uses rule_name as key
        assert "email" in result.summary
        assert result.summary["email"] == 3

    def test_empty_text(self):
        """Test filtering empty text."""
        sf = SandFilter()
        result = sf.filter("")

        assert result.text == ""
        assert len(result.detections) == 0

    def test_result_to_dict_omits_matches_by_default(self):
        """Serialized results should not expose raw sensitive values."""
        sf = SandFilter()
        sf.enable_rules("email")
        result = sf.filter("Contact: user@example.com")

        data = result.to_dict()

        assert "user@example.com" not in str(data)
        assert "match" not in data["detections"][0]
        assert data["detections"][0]["match_length"] == len("user@example.com")

    def test_result_to_dict_can_include_matches_for_debug(self):
        """Raw matches require an explicit unsafe debug opt-in."""
        sf = SandFilter()
        sf.enable_rules("email")
        result = sf.filter("Contact: user@example.com")

        data = result.to_dict(include_matches=True)

        assert data["detections"][0]["match"] == "user@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
