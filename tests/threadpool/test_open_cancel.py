"""Cancelling a pending open() must close the file it ends up opening."""

import asyncio
import gc
import os
import threading
import warnings

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
