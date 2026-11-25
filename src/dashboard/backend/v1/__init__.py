"""Dashboard API v1: /api/v1 (HTTP) and /ws/v1 (WebSocket). Mounted by main.py.

Routers use paths relative to their prefix (for example `@router.get("/sessions")`). The events
router is the only WebSocket router and is mounted under /ws/v1.
"""

from __future__ import annotations

from fastapi import APIRouter

from .routers import arm, batch, benchmark, compare, events, exports, hardware, jobs, sessions

HTTP_ROUTERS = (sessions, exports, compare, benchmark, batch, jobs, hardware, arm)
ALL_ROUTER_MODULES = (*HTTP_ROUTERS, events)

api_router = APIRouter()
for _module in HTTP_ROUTERS:
    api_router.include_router(_module.router)

ws_router = events.router


async def startup() -> None:
    """Open the database and run every router module's optional `on_startup` hook."""
    from .state import get_db, get_jobs

    get_db()
    get_jobs()
    for module in ALL_ROUTER_MODULES:
        hook = getattr(module, "on_startup", None)
        if hook is not None:
            await hook()


async def shutdown() -> None:
    for module in reversed(ALL_ROUTER_MODULES):
        hook = getattr(module, "on_shutdown", None)
        if hook is not None:
            await hook()
    from .state import reset_state

    reset_state()


__all__ = ["api_router", "ws_router", "startup", "shutdown"]
