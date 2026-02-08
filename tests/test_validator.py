"""Tests for the validator module."""

from validator import is_blacklisted, is_whitelisted, validate_command


class TestBlacklist:
    """Tests for blacklist checking."""

    def test_blacklisted_rm_rf(self):
        blacklist = ["rm -rf"]
        assert is_blacklisted("rm -rf /", blacklist) is True

    def test_blacklisted_dd(self):
        blacklist = ["dd"]
        assert is_blacklisted("dd if=/dev/zero of=/dev/sda", blacklist) is True

    def test_blacklisted_shutdown(self):
        blacklist = ["shutdown"]
        assert is_blacklisted("shutdown -h now", blacklist) is True

    def test_not_blacklisted(self):
        blacklist = ["rm -rf", "dd", "mkfs"]
        assert is_blacklisted("ls -la", blacklist) is False

    def test_empty_command(self):
        blacklist = ["rm -rf"]
        assert is_blacklisted("", blacklist) is False

    def test_case_insensitive(self):
        blacklist = ["rm -rf"]
        assert is_blacklisted("RM -RF /home", blacklist) is True


class TestWhitelist:
    """Tests for whitelist checking."""

    def test_whitelisted_ls(self):
        whitelist = ["ls"]
        assert is_whitelisted("ls", whitelist) is True

    def test_whitelisted_with_args(self):
        whitelist = ["ls"]
        assert is_whitelisted("ls -la /home", whitelist) is True

    def test_not_whitelisted(self):
        whitelist = ["ls", "pwd"]
        assert is_whitelisted("rm file.txt", whitelist) is False

    def test_empty_command(self):
        whitelist = ["ls"]
        assert is_whitelisted("", whitelist) is False


class TestValidateCommand:
    """Tests for the full validation pipeline."""

    def test_empty_command(self):
        is_safe, reason = validate_command("")
        assert is_safe is False

    def test_safe_whitelisted(self):
        is_safe, reason = validate_command("ls -la")
        assert is_safe is True

    def test_blocked_command(self):
        is_safe, reason = validate_command("rm -rf /")
        assert is_safe is False

    def test_unknown_command(self):
        # Not blacklisted, not whitelisted — still allowed with caution
        is_safe, reason = validate_command("some_custom_tool --flag")
        assert is_safe is True
        assert "caution" in reason.lower()
