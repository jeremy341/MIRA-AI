# Tests to verify _FrameBuffer instance isolation.

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

def test_frame_buffer_returns_independent_array_copy():
    import numpy as np
    from src.hardware import _FrameBuffer

    buffer = _FrameBuffer()
    source = np.array([1, 2, 3])
    buffer.update(True, source)

    _, first_read = buffer.get()
    first_read[0] = 99

    _, second_read = buffer.get()
    assert second_read.tolist() == [1, 2, 3]
    assert second_read is not source
