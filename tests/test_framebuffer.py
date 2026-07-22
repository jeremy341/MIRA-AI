"""Tests to verify _FrameBuffer instance isolation."""

from src.hardware import _FrameBuffer


def test_framebuffer_locks_are_isolated():
    fb1 = _FrameBuffer()
    fb2 = _FrameBuffer()
    assert fb1._lock is not fb2._lock


def test_framebuffer_running_is_isolated():
    fb1 = _FrameBuffer()
    fb2 = _FrameBuffer()
    fb1._running = False
    assert fb2._running is True
