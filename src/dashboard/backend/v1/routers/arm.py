"""Sorting arm (placeholder) API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Sorting arm (placeholder)"])


# Optional lifecycle hooks, discovered by v1/__init__.py:
#   async def on_startup() -> None: ...
#   async def on_shutdown() -> None: ...
