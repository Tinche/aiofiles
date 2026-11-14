import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import aiofiles
import aiofiles.os


async def test_fstat_matches_os_fstat(tmp_path):
    filename = tmp_path / "example.bin"
    filename.write_bytes(b"file metadata")

    with filename.open("rb") as handle:
        expected = os.fstat(handle.fileno())
        actual = await aiofiles.os.fstat(handle.fileno())

    assert isinstance(actual, os.stat_result)
    assert actual == expected


async def test_fstat_accepts_aiofiles_descriptor(tmp_path):
    filename = tmp_path / "example.bin"
    filename.write_bytes(b"hello")

    async with aiofiles.open(filename, "rb") as handle:
        actual = await aiofiles.os.fstat(handle.fileno())

    assert actual.st_size == 5


async def test_fstat_invalid_descriptor():
    with pytest.raises(OSError) as expected:
        os.fstat(-1)

    with pytest.raises(OSError) as actual:
        await aiofiles.os.fstat(-1)

    assert actual.value.errno == expected.value.errno


async def test_fstat_runs_in_custom_executor(tmp_path):
    class RecordingExecutor(ThreadPoolExecutor):
        def __init__(self):
            super().__init__(max_workers=1)
            self.worker_threads = []

        def submit(self, fn, *args, **kwargs):
            def run():
                self.worker_threads.append(threading.get_ident())
                return fn(*args, **kwargs)

            return super().submit(run)

    filename = tmp_path / "example.bin"
    filename.write_bytes(b"hello")
    event_loop_thread = threading.get_ident()

    with filename.open("rb") as handle, RecordingExecutor() as executor:
        actual = await aiofiles.os.fstat(
            handle.fileno(),
            loop=asyncio.get_running_loop(),
            executor=executor,
        )

    assert actual.st_size == 5
    assert len(executor.worker_threads) == 1
    assert executor.worker_threads[0] != event_loop_thread


def test_fstat_is_exported():
    assert "fstat" in aiofiles.os.__all__
