"""Bzip2 file operations run through the same async interface as ordinary files."""

import asyncio
import bz2
import threading
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest

import aiofiles.bz2


@pytest.mark.parametrize("mode", ["wb", "ab", "xb"])
async def test_binary_write(tmp_path, mode):
    path = tmp_path / "data.bz2"
    prefix = b"existing\n" if mode == "ab" else b""
    if prefix:
        path.write_bytes(bz2.compress(prefix))
    async with aiofiles.bz2.open(path, mode, compresslevel=1) as file:
        assert await file.write(b"first\nsecond\n") == 13
        await file.flush()
        assert not file.closed
    assert file.closed
    assert bz2.decompress(path.read_bytes()) == prefix + b"first\nsecond\n"


async def test_binary_read(tmp_path):
    path = tmp_path / "data.bz2"
    path.write_bytes(bz2.compress(b"first\nsecond\n"))
    async with aiofiles.bz2.open(str(path)) as file:
        assert (await file.peek(5)).startswith(b"first")
        assert await file.read1(5) == b"first"
        assert await file.tell() == 5
        assert await file.seek(0) == 0
        target = bytearray(6)
        assert await file.readinto(target) == 6
        assert target == b"first\n"
        assert [line async for line in file] == [b"second\n"]


async def test_text_encoding_and_newlines(tmp_path):
    path = tmp_path / "data.bz2"
    async with aiofiles.bz2.open(path, "wt", encoding="latin1", newline="\r\n") as file:
        await file.write("café\n")
    assert bz2.decompress(path.read_bytes()) == b"caf\xe9\r\n"
    async with aiofiles.bz2.open(path, "rt", encoding="latin1") as file:
        assert await file.read() == "café\n"
        await file.seek(0)
        assert [line async for line in file] == ["café\n"]
    async with aiofiles.bz2.open(
        path, "rt", encoding="ascii", errors="replace"
    ) as file:
        assert await file.read() == "caf\ufffd\n"


async def test_await_without_context_manager(tmp_path):
    path = tmp_path / "data.bz2"
    path.write_bytes(bz2.compress(b"content"))
    file = await aiofiles.bz2.open(path)
    try:
        assert await file.read() == b"content"
    finally:
        await file.close()
    assert file.closed


async def test_caller_owned_file_object():
    with BytesIO() as buffer:
        async with aiofiles.bz2.open(buffer, "wb") as file:
            await file.write(b"content")
        assert not buffer.closed
        assert bz2.decompress(buffer.getvalue()) == b"content"


async def test_closes_on_exception(tmp_path):
    with pytest.raises(RuntimeError, match="sentinel"):
        async with aiofiles.bz2.open(tmp_path / "data.bz2", "wb") as file:
            msg = "sentinel"
            raise RuntimeError(msg)
    assert file.closed


@pytest.mark.parametrize(
    "mode, content",
    [("wb", b"content"), ("wt", "content"), ("rb", b"content"), ("rt", "content")],
)
async def test_custom_executor(tmp_path, mode, content):
    threads = []
    path = tmp_path / "data.bz2"
    if mode.startswith("r"):
        path.write_bytes(bz2.compress(b"content"))

    class RecordingExecutor(ThreadPoolExecutor):
        def submit(self, fn, /, *args, **kwargs):
            def run():
                threads.append(threading.get_ident())
                return fn(*args, **kwargs)

            return super().submit(run)

    with RecordingExecutor(max_workers=1) as executor:
        async with aiofiles.bz2.open(
            path,
            mode,
            loop=asyncio.get_running_loop(),
            executor=executor,
        ) as file:
            if mode.startswith("r"):
                assert await file.read() == content
            else:
                await file.write(content)
    assert len(threads) == 3  # Open, read or write, and context exit.
    assert len(set(threads)) == 1
    assert threading.get_ident() not in threads


async def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        await aiofiles.bz2.open(tmp_path / "missing.bz2")


async def test_invalid_mode(tmp_path):
    with pytest.raises(ValueError):
        await aiofiles.bz2.open(tmp_path / "data.bz2", "invalid")


async def test_binary_encoding_rejected(tmp_path):
    with pytest.raises(ValueError):
        await aiofiles.bz2.open(tmp_path / "data.bz2", "wb", encoding="utf8")


async def test_invalid_bz2(tmp_path):
    path = tmp_path / "invalid.bz2"
    path.write_bytes(b"not a bz2 file")
    with pytest.raises(OSError):
        async with aiofiles.bz2.open(path) as file:
            await file.read()
    assert file.closed


async def test_exclusive_creation_preserves_existing_file(tmp_path):
    path = tmp_path / "existing.bz2"
    original = bz2.compress(b"existing content")
    path.write_bytes(original)
    with pytest.raises(FileExistsError):
        await aiofiles.bz2.open(path, "xb")
    assert path.read_bytes() == original
