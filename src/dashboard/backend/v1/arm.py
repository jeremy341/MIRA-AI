"""Injectable simulated sorting-arm driver; no hardware access is performed here."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ArmCommand:
    action: str
    class_name: str | None = None
    track_id: int | None = None


@dataclass(frozen=True)
class ArmResult:
    success: bool
    message: str


class ArmDriver(Protocol):
    async def send(self, command: ArmCommand) -> ArmResult: ...

    def status(self) -> dict[str, Any]: ...


class SimulatedArm:
    """A short async simulation that never opens a hardware or network connection."""

    def __init__(self, duration: float = 0.15):
        self.duration = max(0.0, duration)
        self._busy = False

    async def send(self, command: ArmCommand) -> ArmResult:
        if self._busy:
            return ArmResult(False, "Arm is busy")
        self._busy = True
        try:
            await asyncio.sleep(self.duration)
            return ArmResult(True, f"Simulated {command.action} completed")
        finally:
            self._busy = False

    def status(self) -> dict[str, Any]:
        return {"connected": False, "mode": "simulated", "state": "busy" if self._busy else "idle"}


_arm_lock = threading.Lock()
_arm: ArmDriver = SimulatedArm()


def get_arm() -> ArmDriver:
    with _arm_lock:
        return _arm


def set_arm(arm: ArmDriver) -> None:
    global _arm
    with _arm_lock:
        _arm = arm
