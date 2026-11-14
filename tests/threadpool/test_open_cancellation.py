import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from aiofiles import threadpool


@pytest.mark.parametrize("mode", ["r", "rb"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_cancelled_open_closes_eventual_file(
    tmp_path, monkeypatch, mode, buffering
):
    if mode == "r" and buffering == 0:
        pytest.skip("unbuffered text I/O is invalid")
    path = tmp_path / "input"
    path.write_bytes(b"data")
    loop = asyncio.get_running_loop()
    started = asyncio.Event()
    release = threading.Event()
    created = []
    sync_open = threadpool.sync_open

    def delayed_open(*args, **kwargs):
        file = sync_open(*args, **kwargs)
        created.append(file)
        loop.call_soon_threadsafe(started.set)
        if not release.wait(5):
            file.close()
            raise TimeoutError
        return file

    async def use_file(executor):
        async with threadpool.open(
            path, mode=mode, buffering=buffering, executor=executor
        ):
            pytest.fail("cancelled open entered its body")

    monkeypatch.setattr(threadpool, "sync_open", delayed_open)
    with ThreadPoolExecutor(max_workers=1) as executor:
        task = asyncio.create_task(use_file(executor))
        try:
            await asyncio.wait_for(started.wait(), 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)
            release.set()
            await loop.run_in_executor(executor, lambda: None)
            assert created[0].closed
        finally:
            release.set()
            await loop.run_in_executor(executor, lambda: None)
            for file in created:
                file.close()


@pytest.mark.parametrize("configured_executor", [False, True])
async def test_cancelled_real_opener(tmp_path, configured_executor, recwarn):

    path = tmp_path / "input"
    path.write_bytes(b"data")
    loop = asyncio.get_running_loop()
    entered = asyncio.Event()
    release = threading.Event()
    descriptor = []

    def delayed_opener(path, flags):
        descriptor.append(os.open(path, flags))
        loop.call_soon_threadsafe(entered.set)
        if not release.wait(5):
            os.close(descriptor[0])
            raise TimeoutError
        return descriptor[0]

    async def use_file(executor):
        async with threadpool.open(
            path, "rb", executor=executor, opener=delayed_opener
        ):
            pytest.fail("cancelled open entered its body")

    with ThreadPoolExecutor(max_workers=1) as pool:
        executor = pool if configured_executor else None
        task = asyncio.create_task(use_file(executor))
        try:
            await asyncio.wait_for(entered.wait(), 5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)
            release.set()
            if configured_executor:
                await loop.run_in_executor(pool, lambda: None)
            else:
                await loop.shutdown_default_executor()
            with pytest.raises(OSError):
                os.fstat(descriptor[0])
            assert not [w for w in recwarn if issubclass(w.category, ResourceWarning)]
        finally:
            release.set()


async def test_cancel_after_worker_completed(tmp_path, monkeypatch):
    path = tmp_path / "input"
    path.write_bytes(b"data")
    loop = asyncio.get_running_loop()
    created = []
    sync_open = threadpool.sync_open
    run_in_executor = loop.run_in_executor
    task = None
    opening = True
    release = threading.Event()

    def capture_open(*args, **kwargs):
        file = sync_open(*args, **kwargs)
        created.append(file)
        if not release.wait(5):
            file.close()
            raise TimeoutError
        return file

    def cancel_before_delivery(executor, func, *args):
        nonlocal opening
        future = run_in_executor(executor, func, *args)
        if opening:
            opening = False
            future.add_done_callback(lambda _: task.cancel())
            loop.call_soon(release.set)
        return future

    async def use_file(executor):
        async with threadpool.open(path, executor=executor):
            pytest.fail("cancelled open entered its body")

    monkeypatch.setattr(threadpool, "sync_open", capture_open)
    monkeypatch.setattr(loop, "run_in_executor", cancel_before_delivery)
    with ThreadPoolExecutor(max_workers=1) as executor:
        task = asyncio.create_task(use_file(executor))
        try:
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 5)
            await run_in_executor(executor, lambda: None)
            assert created[0].closed
        finally:
            for file in created:
                file.close()


async def test_cancel_before_worker_starts(tmp_path, monkeypatch):
    path = tmp_path / "input"
    path.write_bytes(b"data")
    loop = asyncio.get_running_loop()
    release = threading.Event()
    called = []
    sync_open = threadpool.sync_open

    def capture_open(*args, **kwargs):
        called.append(True)
        return sync_open(*args, **kwargs)

    async def use_file(executor):
        async with threadpool.open(path, executor=executor):
            pytest.fail("cancelled open entered its body")

    monkeypatch.setattr(threadpool, "sync_open", capture_open)
    with ThreadPoolExecutor(max_workers=1) as executor:
        blocker = executor.submit(release.wait, 5)
        task = asyncio.create_task(use_file(executor))
        try:
            # The task submits open behind the blocked worker before resuming us.
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)
        finally:
            release.set()
            await asyncio.wrap_future(blocker)
            await loop.run_in_executor(executor, lambda: None)
    assert not called
