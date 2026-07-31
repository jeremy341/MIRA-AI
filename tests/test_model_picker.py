"""Tests for model_picker interactive CLI component."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from src.model_picker import _getch, pick_model


# ── _getch Windows tests ──────────────────────────────────────────────


def _setup_win_mock(getch_return=None, getch_side_effect=None, kbhit_return=False):
    mock_msvcrt = MagicMock()
    if getch_side_effect is not None:
        mock_msvcrt.getch.side_effect = getch_side_effect
    else:
        mock_msvcrt.getch.return_value = getch_return
    mock_msvcrt.kbhit.return_value = kbhit_return
    return mock_msvcrt


def test_getch_win_enter():
    mock = _setup_win_mock(getch_return=b"\r")
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "ENTER"


def test_getch_win_arrow_up():
    mock = _setup_win_mock(getch_side_effect=[b"\xe0", b"H"])
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "UP"


def test_getch_win_arrow_down():
    mock = _setup_win_mock(getch_side_effect=[b"\xe0", b"P"])
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "DOWN"


def test_getch_win_esc():
    mock = _setup_win_mock(getch_return=b"\x1b")
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "ESC"


def test_getch_win_ctrl_c():
    mock = _setup_win_mock(getch_return=b"\x03")
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "CTRL_C"


def test_getch_win_regular_char():
    mock = _setup_win_mock(getch_return=b"a")
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == "a"


def test_getch_win_decode_error():
    mock = _setup_win_mock(getch_return=b"\xff")
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == ""


def test_getch_win_function_key():
    mock = _setup_win_mock(getch_side_effect=[b"\xe0", b"X"], kbhit_return=False)
    with patch.object(sys, "platform", "win32"):
        with patch.dict("sys.modules", {"msvcrt": mock}):
            assert _getch() == ""


# ── _getch Unix tests ─────────────────────────────────────────────────


def test_getch_unix_enter():
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.return_value = "\r"

    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    mock_termios.TCSADRAIN = 1

    with patch.object(sys, "platform", "linux"):
        with patch.dict(
            "sys.modules",
            {
                "termios": mock_termios,
                "tty": mock_tty,
                "select": mock_select,
            },
        ):
            with patch("sys.stdin", mock_stdin):
                assert _getch() == "ENTER"


def test_getch_unix_arrow_up():
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.side_effect = ["\x1b", "[", "A"]

    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    mock_termios.TCSADRAIN = 1
    mock_select.select.side_effect = [
        ([mock_stdin], [], []),
        ([mock_stdin], [], []),
        ([], [], []),
    ]

    with patch.object(sys, "platform", "linux"):
        with patch.dict(
            "sys.modules",
            {
                "termios": mock_termios,
                "tty": mock_tty,
                "select": mock_select,
            },
        ):
            with patch("sys.stdin", mock_stdin):
                assert _getch() == "UP"


def test_getch_unix_arrow_down():
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.side_effect = ["\x1b", "[", "B"]

    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    mock_termios.TCSADRAIN = 1
    mock_select.select.side_effect = [
        ([mock_stdin], [], []),
        ([mock_stdin], [], []),
        ([], [], []),
    ]

    with patch.object(sys, "platform", "linux"):
        with patch.dict(
            "sys.modules",
            {
                "termios": mock_termios,
                "tty": mock_tty,
                "select": mock_select,
            },
        ):
            with patch("sys.stdin", mock_stdin):
                assert _getch() == "DOWN"


def test_getch_unix_esc_alone():
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.return_value = "\x1b"

    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    mock_termios.TCSADRAIN = 1
    mock_select.select.return_value = ([], [], [])

    with patch.object(sys, "platform", "linux"):
        with patch.dict(
            "sys.modules",
            {
                "termios": mock_termios,
                "tty": mock_tty,
                "select": mock_select,
            },
        ):
            with patch("sys.stdin", mock_stdin):
                assert _getch() == "ESC"


def test_getch_unix_regular_char():
    mock_stdin = MagicMock()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.return_value = "a"

    mock_termios = MagicMock()
    mock_tty = MagicMock()
    mock_select = MagicMock()
    mock_termios.TCSADRAIN = 1

    with patch.object(sys, "platform", "linux"):
        with patch.dict(
            "sys.modules",
            {
                "termios": mock_termios,
                "tty": mock_tty,
                "select": mock_select,
            },
        ):
            with patch("sys.stdin", mock_stdin):
                assert _getch() == "a"


# ── pick_model tests ──────────────────────────────────────────────────


def test_pick_model_empty_items():
    with patch("os.system"):
        result = pick_model([])
    assert result is None


def test_pick_model_empty_after_filter():
    with patch("os.system"):
        result = pick_model(["model1", "model2"], filter_func=lambda x: False)
    assert result is None


def test_pick_model_single_item_select():
    mock_getch = MagicMock(side_effect=["ENTER", "y"])
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result == "model1"


def test_pick_model_filter_func():
    mock_getch = MagicMock(side_effect=["ENTER", "y"])
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(
                ["model1", "model2", "model3"],
                filter_func=lambda x: x == "model1",
            )
    assert result == "model1"


def test_pick_model_cancel_via_item():
    mock_getch = MagicMock(side_effect=["DOWN", "ENTER"])
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result is None


def test_pick_model_esc_cancel():
    mock_getch = MagicMock(return_value="ESC")
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result is None


def test_pick_model_ctrl_c_cancel():
    mock_getch = MagicMock(return_value="CTRL_C")
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result is None


def test_pick_model_confirm_reject():
    mock_getch = MagicMock(side_effect=["ENTER", "n", "ENTER", "y"])
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result == "model1"


def test_pick_model_navigation_wrap():
    mock_getch = MagicMock(side_effect=["UP", "UP", "ENTER", "y"])
    with patch("os.system"):
        with patch("src.model_picker._getch", mock_getch):
            result = pick_model(["model1"])
    assert result == "model1"
