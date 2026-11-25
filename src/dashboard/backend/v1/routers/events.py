"""WebSocket fan-out for process-wide EventBus messages."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..state import get_events

router = APIRouter(tags=["Events"])


@router.websocket("/events")
async def events_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    event_bus = get_events()
    queue = event_bus.subscribe()
    try:
        await websocket.send_json(
            {"type": "hello", "ts": datetime.now(timezone.utc).isoformat(), "data": {"version": 1}}
        )
        while True:
            queue_task = asyncio.create_task(queue.get())
            receive_task = asyncio.create_task(websocket.receive())
            done, pending = await asyncio.wait(
                (queue_task, receive_task), timeout=20, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if not done:
                await websocket.send_json({"type": "ping"})
                continue
            if receive_task in done:
                message = receive_task.result()
                if message["type"] == "websocket.disconnect":
                    break
            if queue_task in done:
                await websocket.send_json(queue_task.result())
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        event_bus.unsubscribe(queue)
