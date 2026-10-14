"""Open existing file descriptors through the public asynchronous interface."""

import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

import pytest

import aiofiles


@pytest.mark.parametrize("mode", ["r", "rb"])
async def test_fdopen_reads_and_retains_descriptor(tmp_path, mode):
    path = tmp_path / "input.txt"
    data = b"descriptor contents"
    path.write_bytes(data)
    with path.open("rb") as owner:
        async with aiofiles.fdopen(owner.fileno(), mode, closefd=False) as file:
            assert file.fileno() == owner.fileno()
            expected = data if "b" in mode else data.decode()
            assert await file.read() == expected
        assert file.closed
        owner.seek(0)
        assert owner.read() == data


async def test_fdopen_closes_descriptor_by_default(tmp_path):
    path = tmp_path / "input.bin"
    path.write_bytes(b"owned descriptor")
    descriptor = os.open(path, os.O_RDONLY)
    file = None
    try:
        async with aiofiles.fdopen(descriptor, "rb") as file:
            assert await file.read() == b"owned descriptor"
        assert file.closed
        with pytest.raises(OSError):
            os.fstat(descriptor)
    finally:
        if file is None:
            with suppress(OSError):
                os.close(descriptor)
        elif not file.closed:
            await file.close()


async def test_fdopen_forwards_text_options(tmp_path):
    path = tmp_path / "encoded.txt"
    with path.open("w+b") as owner:
        async with aiofiles.fdopen(
            owner.fileno(),
            "w",
            1,
            "ascii",
            errors="backslashreplace",
            newline="",
            closefd=False,
        ) as file:
            assert await file.write("café\n") == 5
        owner.seek(0)
        assert owner.read() == b"caf\\xe9\n"


@pytest.mark.parametrize("descriptor", [None, "filename", 1.5, object()])
def test_fdopen_rejects_non_integer_descriptor(descriptor):
    with pytest.raises(TypeError) as expected:
        os.fdopen(descriptor)
    with pytest.raises(TypeError) as actual:
        aiofiles.fdopen(descriptor)
    assert str(actual.value) == str(expected.value)


async def test_fdopen_propagates_invalid_descriptor():
    with pytest.raises((OSError, ValueError)) as expected:
        os.fdopen(-1)
    with pytest.raises(type(expected.value)) as actual:
        await aiofiles.fdopen(-1)
    assert str(actual.value) == str(expected.value)


async def test_fdopen_uses_configured_executor():
    loop = asyncio.get_running_loop()
    await loop.shutdown_default_executor()
    with tempfile.TemporaryFile() as owner, ThreadPoolExecutor() as executor:
        owner.write(b"custom executor")
        owner.seek(0)
        async with aiofiles.fdopen(
            owner.fileno(), "rb", closefd=False, loop=loop, executor=executor
        ) as file:
            assert await file.read() == b"custom executor"
        assert file.closed
        owner.seek(0)
        assert owner.read() == b"custom executor"
