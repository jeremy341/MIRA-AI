"""CLI command to launch the real-time detection dashboard server."""

import sys

from ..pipeline.registry import register_command


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

    # Determine absolute path to the restored backend directory
    project_root = Path(__file__).resolve().parent.parent.parent
    backend_dir = project_root / "dashboard_output" / "extracted" / "backend"

    if not backend_dir.exists():
        print(f"Error: Dashboard backend not found at {backend_dir}")
        sys.exit(1)

    # Insert backend_dir at the front of sys.path so internal imports resolve correctly
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Pre-register `src.config` under `config` in sys.modules to satisfy "from config import ..."
    # and avoid "attempted relative import with no known parent package" errors.
    import src.config
    sys.modules["config"] = src.config

    # Load main.py from backend_dir dynamically
    spec = importlib.util.spec_from_file_location("dashboard_backend_main", backend_dir / "main.py")
    if spec is None or spec.loader is None:
        print("Error: Could not load dashboard backend spec")
        sys.exit(1)
    dashboard_main = importlib.util.module_from_spec(spec)
    sys.modules["dashboard_backend_main"] = dashboard_main
    spec.loader.exec_module(dashboard_main)
    app = dashboard_main.app

    print(f"Starting MIRA Dashboard on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
