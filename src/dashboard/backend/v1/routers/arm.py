"""HTTP endpoints for the simulated sorting arm and feedback log."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator, model_validator

from src.config import CLASS_NAMES

from ..arm import ArmCommand, ArmDriver, get_arm
from ..state import get_db, get_events

router = APIRouter(tags=["Sorting arm (placeholder)"])
_active_task: asyncio.Task | None = None


class CommandRequest(BaseModel):
    action: Literal["sort", "home", "stop"]
    class_name: str | None = None
    track_id: int | None = None

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, value: str | None) -> str | None:
        if value is not None and value not in CLASS_NAMES:
            raise ValueError(f"class_name must be one of: {', '.join(CLASS_NAMES)}")
        return value

    @model_validator(mode="after")
    def require_sort_class(self) -> CommandRequest:
        if self.action == "sort" and self.class_name is None:
            raise ValueError("class_name is required for sort commands")
        return self


class FeedbackRequest(BaseModel):
    correct: bool


def _serialize_event(row) -> dict:
    return {
        "id": row["id"],
        "ts": datetime.fromtimestamp(row["ts"], timezone.utc).isoformat(),
        "kind": row["kind"],
        "class_name": row["class_name"],
        "track_id": row["track_id"],
        "payload": json.loads(row["payload_json"] or "{}"),
        "correct": None if row["correct"] is None else bool(row["correct"]),
    }


def _record_event(kind: str, command: ArmCommand, payload: dict | None = None) -> dict:
    ts = time.time()
    cursor = get_db().execute(
        "INSERT INTO arm_events (ts, kind, class_name, track_id, payload_json) VALUES (?, ?, ?, ?, ?)",
        (ts, kind, command.class_name, command.track_id, json.dumps(payload or {})),
    )
    event = _serialize_event(get_db().query_one("SELECT * FROM arm_events WHERE id=?", (cursor.lastrowid,)))
    get_events().publish("arm_event", event)
    return event


def get_accuracy_summary() -> dict:
    row = get_db().query_one(
        "SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct "
        "FROM arm_events WHERE kind='sort_completed' AND correct IS NOT NULL"
    )
    total, correct = int(row["total"]), int(row["correct"])
    return {"accuracy": correct / total if total else None, "correct": correct, "total": total}


async def _execute_command(driver: ArmDriver, command: ArmCommand, request_event: dict) -> None:
    try:
        result = await driver.send(command)
        suffix = "completed" if result.success else "failed"
        payload = {"request_id": request_event["id"], "message": result.message}
        _record_event(f"{command.action}_{suffix}", command, payload)
    except asyncio.CancelledError:
        _record_event(
            f"{command.action}_failed",
            command,
            {"request_id": request_event["id"], "message": "Command cancelled"},
        )
        raise
    except Exception as exc:
        _record_event(
            f"{command.action}_failed",
            command,
            {"request_id": request_event["id"], "message": str(exc) or exc.__class__.__name__},
        )


@router.get("/arm/status")
def arm_status() -> dict:
    driver_status = get_arm().status()
    last_event = get_db().query_one("SELECT ts FROM arm_events ORDER BY ts DESC, id DESC LIMIT 1")
    accuracy = get_accuracy_summary()
    return {
        "connected": bool(driver_status.get("connected", False)),
        "mode": driver_status.get("mode", "simulated"),
        "state": "busy"
        if (_active_task is not None and not _active_task.done())
        else driver_status.get("state", "idle"),
        "queue_length": 0,
        "last_event_at": datetime.fromtimestamp(last_event["ts"], timezone.utc).isoformat() if last_event else None,
        "accuracy": accuracy["accuracy"],
        "total_feedback": accuracy["total"],
    }


@router.post("/arm/commands", status_code=202)
async def submit_arm_command(request: CommandRequest) -> dict:
    global _active_task
    if _active_task is not None and not _active_task.done():
        raise HTTPException(status_code=409, detail="The sorting arm is busy")
    driver = get_arm()
    if driver.status().get("state") == "busy":
        raise HTTPException(status_code=409, detail="The sorting arm is busy")
    command = ArmCommand(action=request.action, class_name=request.class_name, track_id=request.track_id)
    request_event = _record_event(f"{request.action}_requested", command, {"action": request.action})
    _active_task = asyncio.create_task(_execute_command(driver, command, request_event), name="mira-arm-command")
    # Let the driver enter its busy state before another request can be admitted.
    await asyncio.sleep(0)
    return request_event


@router.get("/arm/events")
def arm_events(limit: int = Query(default=100, ge=1, le=1000), kind: str | None = None) -> dict:
    if kind:
        rows = get_db().query("SELECT * FROM arm_events WHERE kind=? ORDER BY ts DESC, id DESC LIMIT ?", (kind, limit))
    else:
        rows = get_db().query("SELECT * FROM arm_events ORDER BY ts DESC, id DESC LIMIT ?", (limit,))
    return {"events": [_serialize_event(row) for row in rows]}


@router.post("/arm/events/{event_id}/feedback")
def add_arm_feedback(event_id: int, feedback: FeedbackRequest) -> dict:
    row = get_db().query_one("SELECT * FROM arm_events WHERE id=?", (event_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Arm event not found")
    if row["kind"] != "sort_completed":
        raise HTTPException(status_code=409, detail="Feedback is only accepted for sort_completed events")
    get_db().execute("UPDATE arm_events SET correct=? WHERE id=?", (int(feedback.correct), event_id))
    updated = get_db().query_one("SELECT * FROM arm_events WHERE id=?", (event_id,))
    return _serialize_event(updated)


@router.get("/arm/accuracy")
def arm_accuracy() -> dict:
    return get_accuracy_summary()


async def on_shutdown() -> None:
    global _active_task
    if _active_task is not None and not _active_task.done():
        _active_task.cancel()
        try:
            await _active_task
        except asyncio.CancelledError:
            pass
    _active_task = None
