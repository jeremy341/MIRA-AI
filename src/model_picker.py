"""Interactive model picker for MIRA CLI."""

import os
import sys


def _getch():
    """Read a single keypress. Returns a token string for easy comparison."""
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch()
        if ch == b"\xe0":
            second = msvcrt.getch()
            mapped = {b"H": "UP", b"P": "DOWN", b"M": "RIGHT", b"K": "LEFT"}.get(second)
            if mapped:
                return mapped
            # Function key or other extended key — consume remaining bytes
            for _ in range(100):
                if not msvcrt.kbhit():
                    break
                msvcrt.getch()
            return ""
        if ch == b"\r":
            return "ENTER"
        if ch == b"\x1b":
            return "ESC"
        if ch == b"\x03":
            return "CTRL_C"
        try:
            return ch.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    else:
        # Unix: read up to 3 bytes for longer escape sequences
        import termios
        import tty
        import select

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Check if more bytes available (non-blocking)
                rest = ""
                while select.select([sys.stdin], [], [], 0.01)[0]:
                    rest += sys.stdin.read(1)
                if rest == "[A":
                    return "UP"
                if rest == "[B":
                    return "DOWN"
                if rest == "[C":
                    return "RIGHT"
                if rest == "[D":
                    return "LEFT"
                return "ESC"  # Unknown escape sequence
            if ch == "\r":
                return "ENTER"
            if ch == "\x03":
                return "CTRL_C"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def pick_model(items, labels=None, title="Available models", filter_func=None):
    """Interactive arrow-key model picker with y/N confirmation.

    Returns selected item name, or None if cancelled.
    """
    if filter_func:
        items = [i for i in items if filter_func(i)]

    if not items:
        print("No items available.")
        return None

    labels = labels or {}
    idx = 0
    selected = None
    display_items = list(items) + ["[Cancel]"]

    while True:
        os.system("cls" if sys.platform == "win32" else "clear")
        print(f"\n  {title}")
        print()

        for i, item in enumerate(display_items):
            prefix = "  " if idx != i else "\u2192"
            suffix = "  <--" if idx == i else ""
            if item == "[Cancel]":
                label = "Exit without selecting"
            else:
                label = labels.get(item, "")
            print(f"  {prefix} {item}{' ' + label if label else ''}{suffix}")

        print("\n  \u2191\u2193 navigate  |  Enter: select  |  Esc: cancel")

        if selected is not None:
            print(f"\n  Run {selected}? (y/N): ", end="", flush=True)
            ch = _getch()
            if ch == "y":
                print("y")
                return selected
            print("n")
            selected = None
            continue

        ch = _getch()
        if ch == "UP":
            idx = (idx - 1) % len(display_items)
        elif ch == "DOWN":
            idx = (idx + 1) % len(display_items)
        elif ch in ("ENTER", "RIGHT"):
            choice = display_items[idx]
            if choice == "[Cancel]":
                return None
            selected = choice
        elif ch in ("ESC", "CTRL_C"):
            return None
