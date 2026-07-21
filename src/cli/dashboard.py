from pipeline.registry import register_command


@register_command("dashboard", "Launch the real-time detection dashboard")
def cmd_dashboard(args):
    """Start the MIRA dashboard server."""
    import uvicorn

    from dashboard.main import app

    print("Starting MIRA Dashboard on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
