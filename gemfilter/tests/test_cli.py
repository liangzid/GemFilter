"""
Tests for GemFilter CLI behavior.
"""

from argparse import Namespace
from unittest.mock import patch

from gemfilter.cli import filter_command, main


def _args(**overrides):
    defaults = {
        "text": "Login: password=mysecretpassword",
        "input": None,
        "config": None,
        "disable": None,
        "enable": None,
        "disable_group": None,
        "enable_group": None,
        "json": True,
        "verbose": False,
        "unsafe_include_matches": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_json_output_omits_raw_matches_by_default(capsys):
    exit_code = filter_command(_args())

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mysecretpassword" not in captured.out
    assert "match_length" in captured.out
    assert '"match"' not in captured.out


def test_json_output_can_include_raw_matches_with_unsafe_flag(capsys):
    exit_code = filter_command(_args(unsafe_include_matches=True))

    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"match": "password=mysecretpassword"' in captured.out


def test_verbose_output_omits_raw_matches_by_default(capsys):
    exit_code = filter_command(_args(json=False, verbose=True))

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mysecretpassword" not in captured.err
    assert "<redacted len=" in captured.err


def test_main_filter_command_smoke(capsys):
    with patch("sys.argv", ["gemfilter", "filter", "Login password=mysecretpassword"]):
        exit_code = main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "mysecretpassword" not in captured.out
    assert "[PASSWORD]" in captured.out


def test_main_rules_command_smoke(capsys):
    with patch("sys.argv", ["gemfilter", "rules"]):
        exit_code = main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Enabled rules:" in captured.out
