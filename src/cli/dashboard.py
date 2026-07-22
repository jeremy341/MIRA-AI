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

    from ..dashboard.main import app

    print(f"Starting MIRA Dashboard on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
