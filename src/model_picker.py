# Interactive model picker for MIRA CLI.

import os
import sys


def _getch():
    # Read a single keypress. Returns a token string for easy comparison.
    if sys.platform == "win32":
        import msvcrt

        key_bytes = msvcrt.getch()
        if key_bytes == b"\xe0":
            direction_byte = msvcrt.getch()
            direction_by_byte = {
                b"H": "UP",
                b"P": "DOWN",
                b"M": "RIGHT",
                b"K": "LEFT",
            }
            direction = direction_by_byte.get(direction_byte)
            if direction:
                return direction
            # Function key or other extended key - consume remaining bytes
            for key_check in range(100):
                if not msvcrt.kbhit():
                    break
                msvcrt.getch()
            return ""
        if key_bytes == b"\r":
            return "ENTER"
        if key_bytes == b"\x1b":
            return "ESC"
        if key_bytes == b"\x03":
            return "CTRL_C"
        try:
            return key_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    else:
        # Unix: read up to 3 bytes for longer escape sequences
        import termios
        import tty
        import select

        input_file_descriptor = sys.stdin.fileno()
        original_terminal_settings = termios.tcgetattr(input_file_descriptor)
        try:
            tty.setraw(input_file_descriptor)
            key_text = sys.stdin.read(1)
            if key_text == "\x1b":
                # Check if more bytes available (non-blocking)
                remaining_escape_text = ""
                while select.select([sys.stdin], [], [], 0.01)[0]:
                    remaining_escape_text += sys.stdin.read(1)
                if remaining_escape_text == "[A":
                    return "UP"
                if remaining_escape_text == "[B":
                    return "DOWN"
                if remaining_escape_text == "[C":
                    return "RIGHT"
                if remaining_escape_text == "[D":
                    return "LEFT"
                return "ESC"  # Unknown escape sequence
            if key_text == "\r":
                return "ENTER"
            if key_text == "\x03":
                return "CTRL_C"
            return key_text
        finally:
            termios.tcsetattr(
                input_file_descriptor,
                termios.TCSADRAIN,
                original_terminal_settings,
            )


def pick_model(items, labels=None, title="Available models", filter_func=None):
    # Interactive arrow-key model picker with y/N confirmation. Returns selected item name, or None if cancelled.
    if filter_func:
        filtered_items = []
        for item in items:
            if filter_func(item):
                filtered_items.append(item)
        items = filtered_items

    if not items:
        print("No items available.")
        return None

    labels = labels or {}
    selected_index = 0
    pending_selection = None
    display_items = list(items) + ["[Cancel]"]

    while True:
        os.system("cls" if sys.platform == "win32" else "clear")
        print(f"\n  {title}")
        print()

        for item_index, item in enumerate(display_items):
            is_selected_item = selected_index == item_index
            if is_selected_item:
                prefix = "\u2192"
                suffix = "  <--"
            else:
                prefix = "  "
                suffix = ""
            if item == "[Cancel]":
                item_label = "Exit without selecting"
            else:
                item_label = labels.get(item, "")
            if item_label:
                label_text = " " + item_label
            else:
                label_text = ""
            print(f"  {prefix} {item}{label_text}{suffix}")

        print("\n  \u2191\u2193 navigate  |  Enter: select  |  Esc: cancel")

        if pending_selection is not None:
            print(f"\n  Run {pending_selection}? (y/N): ", end="", flush=True)
            confirmation_key = _getch()
            if confirmation_key == "y":
                print("y")
                return pending_selection
            print("n")
            pending_selection = None
            continue

        navigation_key = _getch()
        if navigation_key == "UP":
            selected_index = (selected_index - 1) % len(display_items)
        elif navigation_key == "DOWN":
            selected_index = (selected_index + 1) % len(display_items)
        elif navigation_key in ("ENTER", "RIGHT"):
            selected_item = display_items[selected_index]
            if selected_item == "[Cancel]":
                return None
            pending_selection = selected_item
        elif navigation_key in ("ESC", "CTRL_C"):
            return None
