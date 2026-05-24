"""
Tests for the GemFilter agent installer CLI.
"""

from unittest.mock import MagicMock, patch

import pytest

from gemfilter.skill import install


def test_status_all_agents(capsys):
    with patch("sys.argv", ["install", "--status"]):
        exit_code = install.main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "claude_code:" in captured.out
    assert "opencode:" in captured.out
    assert "coodex:" in captured.out


def test_install_agent_success(capsys):
    adapter = MagicMock()
    adapter.name = "claude_code"
    adapter.install.return_value = True

    with patch("gemfilter.skill.install.create_adapter", return_value=adapter):
        with patch("sys.argv", ["install", "--agent", "claude_code"]):
            exit_code = install.main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "installed for claude_code" in captured.out
    adapter.install.assert_called_once()


def test_uninstall_agent_success(capsys):
    adapter = MagicMock()
    adapter.name = "opencode"
    adapter.uninstall.return_value = True

    with patch("gemfilter.skill.install.create_adapter", return_value=adapter):
        with patch("sys.argv", ["install", "--agent", "opencode", "--uninstall"]):
            exit_code = install.main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "uninstalled for opencode" in captured.out
    adapter.uninstall.assert_called_once()


def test_agent_required_without_status():
    with patch("sys.argv", ["install"]):
        with pytest.raises(SystemExit):
            install.main()

