"""Model catalog and interactive selection for Hack Club AI."""
from dataclasses import dataclass

@dataclass
class Model:
    id: str
    name: str
    category: str  # "code", "reasoning", "all-around", "free"
    context: str

MODELS = [
    Model("openai/gpt-5.1-codex", "GPT-5.1 Codex", "code", "400K"),
    Model("qwen/qwen3-coder", "Qwen3 Coder (480B)", "code", "1M"),
    Model("moonshotai/kimi-k2.7-code", "Kimi K2.7 Code", "code", "262K"),
    Model("deepseek/deepseek-r1-0528", "DeepSeek R1", "reasoning", "163K"),
    Model("mistralai/codestral-2508", "Codestral", "code", "256K"),
    Model("google/gemini-2.5-pro", "Gemini 2.5 Pro", "all-around", "1M"),
    Model("anthropic/claude-opus-4.8", "Claude Opus 4.8", "reasoning", "1M"),
    Model("openai/o3-pro", "O3 Pro", "reasoning", "200K"),
    Model("qwen/qwen3-coder:free", "Qwen3 Coder (Free)", "free", "1M"),
    Model("openai/gpt-5-mini", "GPT-5 Mini", "all-around", "400K"),
]

def list_models(category: str | None = None) -> list[Model]:
    if category:
        return [m for m in MODELS if m.category == category]
    return MODELS

def get_model_by_id(model_id: str) -> Model | None:
    return next((m for m in MODELS if m.id == model_id), None)

def select_model_interactive() -> Model | None:
    """Arrow-key model picker. Returns selected Model or None."""
    import sys
    if sys.platform == "win32":
        import msvcrt
        def _getch():
            ch = msvcrt.getch()
            if ch == b'\xe0':
                second = msvcrt.getch()
                return {b'H': 'UP', b'P': 'DOWN', b'M': 'RIGHT', b'K': 'LEFT'}.get(second, '')
            if ch == b'\r': return 'ENTER'
            if ch == b'\x1b': return 'ESC'
            if ch == b'\x03': return 'CTRL_C'
            return ch.decode()
    else:
        import tty, termios
        def _getch():
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    nxt = sys.stdin.read(2)
                    return {'[A': 'UP', '[B': 'DOWN', '[C': 'RIGHT', '[D': 'LEFT'}.get(nxt, 'ESC')
                if ch == '\r': return 'ENTER'
                if ch == '\x03': return 'CTRL_C'
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    items = MODELS + [None]  # None = Cancel
    idx = 0
    while True:
        import os
        os.system("cls" if sys.platform == "win32" else "clear")
        print("\n  Select AI Model\n")
        for i, m in enumerate(items):
            prefix = "  " if idx != i else " ->"
            suffix = "  <--" if idx == i else ""
            if m is None:
                label = "Cancel"
            else:
                label = f"{m.name} [{m.category}] ({m.context})"
            print(f"  {prefix} {label}{suffix}")
        print(f"\n  UP/DOWN navigate | Enter select | Esc cancel")
        ch = _getch()
        if ch == 'UP': idx = (idx - 1) % len(items)
        elif ch == 'DOWN': idx = (idx + 1) % len(items)
        elif ch in ('ENTER', 'RIGHT'):
            return items[idx]
        elif ch in ('ESC', 'CTRL_C'):
            return None
