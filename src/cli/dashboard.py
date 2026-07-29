"""CLI command to launch the real-time detection dashboard server."""

import sys

from src.pipeline.registry import register_command


def _add_dashboard_args(parser):
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")


@register_command("dashboard", "Launch the real-time detection dashboard", add_args=_add_dashboard_args)
def cmd_dashboard(args):
    """Start the MIRA dashboard server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required for the dashboard. Install it with: pip install uvicorn")
        sys.exit(1)

    import importlib.util
    from pathlib import Path

    # Determine absolute path to the dashboard backend
    project_root = Path(__file__).resolve().parent.parent.parent
    backend_dir = project_root / "src" / "dashboard" / "backend"

    if not backend_dir.exists():
        print(f"Error: Dashboard backend not found at {backend_dir}")
        sys.exit(1)

    # Ensure the src package is importable
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    # Add backend dir to sys.path so bare imports (from models, from camera_service, etc.) resolve
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

# Register src.config as "config" so "from config import ..." in camera_service.py works
    import src.config
    _prev_config = sys.modules.get("config")
    sys.modules["config"] = src.config

    # Load main.py from backend_dir
    try:
        spec = importlib.util.spec_from_file_location("dashboard_backend_main", backend_dir / "main.py")
        if spec is None or spec.loader is None:
            print("Error: Could not load dashboard backend spec")
            sys.exit(1)
        dashboard_main = importlib.util.module_from_spec(spec)
        sys.modules["dashboard_backend_main"] = dashboard_main
        spec.loader.exec_module(dashboard_main)
    except Exception as e:
        print(f"Error: Failed to load dashboard backend: {e}")
        sys.exit(1)
    finally:
        # Restore original config module to avoid polluting global module cache
        if _prev_config is not None:
            sys.modules["config"] = _prev_config
        else:
            sys.modules.pop("config", None)
    app = getattr(dashboard_main, "app", None)
    if app is None:
        print("Error: dashboard backend 'main.py' does not define 'app' attribute")
        sys.exit(1)

    print(f"Starting MIRA Dashboard on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

