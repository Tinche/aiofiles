import asyncio
from pathlib import Path

from aiofiles.threadpool import open as aioopen

import pytest


RESOURCES_DIR = Path(__file__).parent.parent / "resources"
TEST_FILE = RESOURCES_DIR / "test_file1.txt"
TEST_FILE_CONTENTS = "0123456789"


@pytest.mark.parametrize("mode", ["r", "rb"])
async def test_file_not_found(mode):
    filename = "non_existent"

    try:
        open(filename, mode=mode)
    except Exception as e:
        expected = e

    assert expected

    try:
        await aioopen(filename, mode=mode)
    except Exception as e:
        actual = e

    assert actual

    assert actual.errno == expected.errno
    assert str(actual) == str(expected)


async def test_file_async_context_aexit():
    async with aioopen(TEST_FILE) as fp:
        pass

    with pytest.raises(ValueError):
        line = await fp.read()

    async with aioopen(TEST_FILE) as fp:
        line = await fp.read()
        assert line == TEST_FILE_CONTENTS


async def test_filetask_async_context_aexit():
    async def _process_test_file(file_ctx, sleep_time: float = 1.0):
        nonlocal file_ref
        async with file_ctx as fp:
            file_ref = file_ctx._obj
            await asyncio.sleep(sleep_time)
            await fp.read()

    cancel_time, sleep_time = 0.1, 10
    assert cancel_time <= (sleep_time / 10)

    file_ref = None
    file_ctx = aioopen(TEST_FILE)

    task = asyncio.create_task(
        _process_test_file(file_ctx=file_ctx, sleep_time=sleep_time)
    )
    try:
        await asyncio.wait_for(task, timeout=cancel_time)
    except asyncio.TimeoutError:
        assert task.cancelled

    assert file_ref.closed
