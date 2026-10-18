"""Cancelling a pending open() must close the file it ends up opening."""

import asyncio
import gc
import os
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor

import aiofiles


async def test_cancelled_open_closes_file(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("data")
    release = threading.Event()
    started = threading.Event()
    fds = []

    def opener(name, flags):
        started.set()
        release.wait(5)
        fd = os.open(name, flags)
        fds.append(fd)
        return fd

    task = asyncio.ensure_future(aiofiles.open(path, opener=opener))
    while not started.is_set():
        await asyncio.sleep(0.01)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert task.cancelled()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        release.set()
        for _ in range(500):
            if fds:
                try:
                    os.fstat(fds[0])
                except OSError:
                    break
            await asyncio.sleep(0.01)
        gc.collect()

    assert len(fds) == 1
    assert not [w for w in caught if issubclass(w.category, ResourceWarning)]
    try:
        os.fstat(fds[0])
    except OSError:
        closed = True
    else:
        os.close(fds[0])
        closed = False
    assert closed, "the file opened by the cancelled open() was not closed"


async def test_open_still_returns_file(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("data")

    async with aiofiles.open(path) as f:
        assert await f.read() == "data"


async def _cancel_while_queued(path, mode):
    """Cancel an open() that is still waiting for the executor's only worker."""
    pool = ThreadPoolExecutor(max_workers=1)
    release = threading.Event()
    blocker = pool.submit(release.wait, 5)
    try:
        task = asyncio.ensure_future(aiofiles.open(path, mode, executor=pool))
        await asyncio.sleep(0.05)
        assert not task.done()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.cancelled()
    finally:
        release.set()
        blocker.result(5)
        pool.shutdown(wait=True)


async def test_cancel_queued_open_does_not_truncate(tmp_path):
    path = tmp_path / "data.bin"
    path.write_bytes(b"KEEP THIS CONTENT")

    await _cancel_while_queued(path, "wb")

    assert path.read_bytes() == b"KEEP THIS CONTENT"


async def test_cancel_queued_open_does_not_create(tmp_path):
    path = tmp_path / "missing.bin"

    await _cancel_while_queued(path, "wb")

    assert not path.exists()


async def test_cancelled_open_closes_file_after_executor_shutdown(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("data")
    pool = ThreadPoolExecutor(max_workers=1)
    release = threading.Event()
    started = threading.Event()
    fds = []

    def opener(name, flags):
        started.set()
        release.wait(5)
        fd = os.open(name, flags)
        fds.append(fd)
        return fd

    task = asyncio.ensure_future(aiofiles.open(path, opener=opener, executor=pool))
    while not started.is_set():
        await asyncio.sleep(0.01)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    # The executor is shut down before the started open() returns, so the
    # file cannot be closed in it any more.
    pool.shutdown(wait=False)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        release.set()
        for _ in range(500):
            if fds:
                try:
                    os.fstat(fds[0])
                except OSError:
                    break
            await asyncio.sleep(0.01)
        gc.collect()

    assert len(fds) == 1
    assert not [w for w in caught if issubclass(w.category, ResourceWarning)]
    try:
        os.fstat(fds[0])
    except OSError:
        closed = True
    else:
        os.close(fds[0])
        closed = False
    assert closed, "the file opened by the cancelled open() was not closed"
