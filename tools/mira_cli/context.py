"""Build project context string for AI conversations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "runs", "wandb", "datasets"}
SKIP_EXTS = {".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".pt", ".tflite", ".onnx", ".h5", ".keras", ".jpg", ".png", ".mp4", ".avi"}

def build_tree(root: Path = ROOT, prefix: str = "", max_depth: int = 3, _depth: int = 0) -> str:
    """Build a directory tree string."""
    if _depth >= max_depth:
        return ""
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    except PermissionError:
        return ""
    for entry in entries:
        if entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        if entry.suffix.lower() in SKIP_EXTS:
            continue
        is_last = entry == entries[-1] if entries else True
        connector = "--- " if is_last else "|-- "
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            ext = "    " if is_last else "|   "
            lines.append(build_tree(entry, prefix + ext, max_depth, _depth + 1))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")
    return "\n".join(lines)

KEY_FILES = [
    "src/config.py", "src/cli.py", "src/inference_engine.py",
    "src/visualize.py", "src/logger.py", "src/dashboard_flask/app.py",
    "pyproject.toml", "requirements.txt",
]

def read_key_files(max_chars: int = 8000) -> str:
    """Read key project files for context."""
    parts = []
    total = 0
    for rel in KEY_FILES:
        fp = ROOT / rel
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        if total + len(content) > max_chars:
            break
        parts.append(f"### {rel}\n```\n{content}\n```")
        total += len(content)
    return "\n\n".join(parts)

def build_context(max_chars: int = 8000) -> str:
    """Build full project context."""
    tree = build_tree()
    files = read_key_files(max_chars)
    return f"## Project Structure\n```\n{tree}\n```\n\n## Key Files\n{files}"
