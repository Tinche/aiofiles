"""Synchronize file descriptors through the asynchronous OS interface."""

import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import aiofiles.os

pytestmark = pytest.mark.skipif(not hasattr(os, "fsync"), reason="fsync is unavailable")


async def test_fsync_uses_executor(tmp_path):
    worker_threads = []

    class RecordingExecutor(ThreadPoolExecutor):
        def submit(self, fn, *args, **kwargs):
            def run():
                worker_threads.append(threading.get_ident())
                return fn(*args, **kwargs)

            return super().submit(run)

    path = tmp_path / "synced.bin"
    with path.open("wb") as file, RecordingExecutor(max_workers=1) as executor:
        file.write(b"flushed data")
        file.flush()
        result = await aiofiles.os.fsync(
            file.fileno(), loop=asyncio.get_running_loop(), executor=executor
        )
        assert result is None
        assert worker_threads
        assert all(thread != threading.get_ident() for thread in worker_threads)
    assert path.read_bytes() == b"flushed data"


@pytest.mark.parametrize("descriptor", [-1, 2**31 - 1])
async def test_fsync_propagates_native_error(descriptor):
    with pytest.raises((OSError, ValueError)) as expected:
        os.fsync(descriptor)
    with pytest.raises(type(expected.value)) as actual:
        await aiofiles.os.fsync(descriptor)
    assert str(actual.value) == str(expected.value)
