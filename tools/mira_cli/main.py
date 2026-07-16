"""MIRA-AI: Interactive AI assistant for the MIRA project."""
import sys
import os
from pathlib import Path

# Add tools dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api import chat
from models import MODELS, select_model_interactive, get_model_by_id
from context import build_context
from modes import plan, build

VERSION = "0.1.0"

HELP_TEXT = """
MIRA-AI Commands:
  /plan       Switch to Plan Mode (read-only analysis)
  /build      Switch to Build Mode (file modifications)
  /model      Change AI model
  /models     List available models
  /context    Show current project context
  /clear      Clear conversation history
  /help       Show this help
  /quit       Exit MIRA-AI
"""

def print_header():
    print("""
  ╔══════════════════════════════════════╗
  ║          MIRA-AI v{ver}             ║
  ║   Jugend Forscht AI Assistant        ║
  ╚══════════════════════════════════════╝
""".format(ver=VERSION))

def print_wrapped(text: str, width: int = 80):
    """Print text with basic word wrapping."""
    for line in text.split('\n'):
        if len(line) <= width:
            print(line)
        else:
            words = line.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 <= width:
                    current += (" " if current else "") + word
                else:
                    print(current)
                    current = word
            if current:
                print(current)

def main():
    print_header()

    # Select model
    print("  Select AI model (or press Enter for default: Gemini 3.1 Flash Lite)")
    model = select_model_interactive()
    if model is None:
        from api import DEFAULT_MODEL
        model_id = DEFAULT_MODEL
        model_name = "Gemini 3.1 Flash Lite (default)"
    else:
        model_id = model.id
        model_name = model.name

    print(f"\n  Using: {model_name} ({model_id})")

    # Build context
    print("  Building project context...")
    context = build_context()
    print(f"  Context ready ({len(context)} chars)\n")

    # State
    current_mode = "plan"
    messages = []
    mode_handlers = {"plan": plan, "build": build}

    # REPL
    while True:
        try:
            mode_label = f"[{current_mode.upper()}]"
            user_input = input(f"{mode_label} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye!")
            break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            cmd = user_input.split()[0].lower()
            arg = user_input[len(cmd):].strip()

            if cmd == "/quit" or cmd == "/exit":
                print("  Bye!")
                break
            elif cmd == "/help":
                print(HELP_TEXT)
            elif cmd == "/plan":
                current_mode = "plan"
                print("  Switched to Plan Mode (read-only)")
            elif cmd == "/build":
                current_mode = "build"
                print("  Switched to Build Mode (can modify files)")
            elif cmd == "/model":
                m = select_model_interactive()
                if m:
                    model_id = m.id
                    print(f"  Switched to: {m.name}")
            elif cmd == "/models":
                print("\n  Available models:")
                for m in MODELS:
                    print(f"    {m.id:40s} {m.name:25s} [{m.category}]")
            elif cmd == "/context":
                print(f"\n{context}")
            elif cmd == "/clear":
                messages.clear()
                print("  Conversation cleared.")
            else:
                print(f"  Unknown command: {cmd}. Type /help for commands.")
            continue

        # Process through current mode
        handler = mode_handlers[current_mode]
        try:
            response = handler.run(user_input, messages, model_id, context)
            print()
            print_wrapped(response)
            print()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()
