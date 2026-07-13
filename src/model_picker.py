"""Interactive model picker for MIRA CLI.

Usage:
    from model_picker import pick_model
    selected = pick_model(items, labels)
    if selected:
        print(f"Selected: {selected}")
"""
import sys
import os


def _getch():
    """Read a single keypress without Enter."""
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getch()
        if ch == b'\xe0':
            return b'\x1b[' + msvcrt.getch()
        return ch.decode() if isinstance(ch, bytes) else ch
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(3)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch


def pick_model(items, labels=None, title="Available models", filter_func=None):
    """Interactive arrow-key model picker with y/N confirmation.

    Args:
        items: List of item names (e.g. model filenames)
        labels: Dict mapping name -> description string (optional)
        title: Header text shown above the list
        filter_func: Callable(name) -> bool, if False the item is hidden

    Returns:
        str: Selected item name, or None if cancelled
    """
    if filter_func:
        items = [i for i in items if filter_func(i)]

    if not items:
        print("No items available.")
        return None

    labels = labels or {}
    idx = 0
    state = "browse"

    # Add Cancel entry
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

        print(f"\n  \u2191\u2193 navigate  |  Enter: select  |  Esc: cancel")

        if state == "browse":
            ch = _getch()
            if ch == '\x1b' or ch == '\x1b[':
                extra = _getch() if ch == '\x1b[' else ''
                if extra == 'A':
                    idx = (idx - 1) % len(display_items)
                elif extra == 'B':
                    idx = (idx + 1) % len(display_items)
                else:
                    return None
            elif ch in ('\r', '\n'):
                selected = display_items[idx]
                if selected == "[Cancel]":
                    return None
                state = "confirm"
            elif ch == '\x03':
                return None
        elif state == "confirm":
            print(f"\n  Run {selected}? (y/N): ", end="", flush=True)
            ch = _getch()
            if ch in ('y', 'Y'):
                print("y")
                return selected
            elif ch in ('n', 'N', '\r', '\n', '\x1b'):
                if ch in ('\r', '\n', '\x1b'):
                    if ch == '\x1b':
                        pass
                state = "browse"
                continue
            else:
                state = "browse"
                continue
