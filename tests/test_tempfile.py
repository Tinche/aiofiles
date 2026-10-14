import asyncio
import io
import os
import platform
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from aiofiles import tempfile


@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
async def test_temporary_file(mode):
    """Test temporary file."""
    data = b"Hello World!\n" if "b" in mode else "Hello World!\n"

    async with tempfile.TemporaryFile(mode=mode) as f:
        for _ in range(3):
            await f.write(data)

        await f.flush()
        await f.seek(0)

        async for line in f:
            assert line == data


@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
@pytest.mark.skipif(
    sys.version_info >= (3, 12),
    reason=("3.12+ doesn't support tempfile.NamedTemporaryFile.delete"),
)
async def test_named_temporary_file(mode):
    data = b"Hello World!" if "b" in mode else "Hello World!"
    filename = None

    async with tempfile.NamedTemporaryFile(mode=mode) as f:
        await f.write(data)
        await f.flush()
        await f.seek(0)
        assert await f.read() == data

        filename = f.name
        assert os.path.exists(filename)
        assert os.path.isfile(filename)
        assert f.delete

    assert not os.path.exists(filename)


@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason=("3.12+ doesn't support tempfile.NamedTemporaryFile.delete"),
)
async def test_named_temporary_file_312(mode):
    data = b"Hello World!" if "b" in mode else "Hello World!"
    filename = None

    async with tempfile.NamedTemporaryFile(mode=mode) as f:
        await f.write(data)
        await f.flush()
        await f.seek(0)
        assert await f.read() == data

        filename = f.name
        assert os.path.exists(filename)
        assert os.path.isfile(filename)

    assert not os.path.exists(filename)


@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
@pytest.mark.skipif(
    sys.version_info < (3, 12), reason=("3.12+ supports delete_on_close")
)
async def test_named_temporary_delete_on_close(mode):
    data = b"Hello World!" if "b" in mode else "Hello World!"
    filename = None

    async with tempfile.NamedTemporaryFile(mode=mode, delete_on_close=True) as f:
        await f.write(data)
        await f.flush()
        await f.close()

        filename = f.name
        assert not os.path.exists(filename)

    async with tempfile.NamedTemporaryFile(mode=mode, delete_on_close=False) as f:
        await f.write(data)
        await f.flush()
        await f.close()

        filename = f.name
        assert os.path.exists(filename)

    assert not os.path.exists(filename)


@pytest.mark.parametrize("mode", ["r+", "w+", "rb+", "wb+"])
async def test_spooled_temporary_file(mode):
    """Test spooled temporary file."""
    data = b"Hello World!" if "b" in mode else "Hello World!"

    async with tempfile.SpooledTemporaryFile(max_size=len(data) + 1, mode=mode) as f:
        await f.write(data)
        await f.flush()
        if "b" in mode:
            assert type(f._file._file) is io.BytesIO

        await f.write(data)
        await f.flush()
        if "b" in mode:
            assert type(f._file._file) is not io.BytesIO

        await f.seek(0)
        assert await f.read() == data + data


@pytest.mark.parametrize("mode", ["w+b", "w+"])
@pytest.mark.parametrize("max_size, size", [(0, 1), (1, 2)])
async def test_spooled_truncate_rollover_uses_executor(
    mode, max_size, size, monkeypatch, tmp_path
):
    """Truncation must not roll an in-memory spool over on the event loop."""
    loop_thread = threading.get_ident()
    rollover_threads = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        worker_thread = await asyncio.get_running_loop().run_in_executor(
            executor, threading.get_ident
        )
        async with tempfile.SpooledTemporaryFile(
            max_size=max_size, mode=mode, dir=tmp_path, executor=executor
        ) as f:
            assert not f._file._rolled
            original_rollover = f._file.rollover

            def record_rollover():
                rollover_threads.append(threading.get_ident())
                return original_rollover()

            monkeypatch.setattr(f._file, "rollover", record_rollover)
            assert await f.truncate(size) == size
            assert f._file._rolled
            assert rollover_threads == [worker_thread]
            assert worker_thread != loop_thread
            assert await f.tell() == 0
            await f.seek(0, os.SEEK_END)
            assert await f.tell() == size


@pytest.mark.parametrize("mode", ["w+b", "w+"])
@pytest.mark.parametrize("rolled", [False, True])
async def test_spooled_truncate_preserves_behavior(mode, rolled, tmp_path):
    data = b"abc" if "b" in mode else "abc"
    async with tempfile.SpooledTemporaryFile(max_size=8, mode=mode, dir=tmp_path) as f:
        await f.write(data)
        if rolled:
            await f.rollover()
        await f.seek(2)
        assert await f.truncate() == 2
        assert f._file._rolled is rolled
        await f.seek(0)
        assert await f.read() == data[:2]
        with pytest.raises((ValueError, OSError)):
            await f.truncate(-1)


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Doesn't work on Win properly"
)
@pytest.mark.parametrize(
    "test_string, newlines", [("LF\n", "\n"), ("CRLF\r\n", "\r\n")]
)
async def test_spooled_temporary_file_newlines(test_string, newlines):
    """
    Test `newlines` property in spooled temporary file.
    issue https://github.com/Tinche/aiofiles/issues/118
    """

    async with tempfile.SpooledTemporaryFile(mode="w+") as f:
        await f.write(test_string)
        await f.flush()
        await f.seek(0)

        assert f.newlines is None

        await f.read()

        assert f.newlines == newlines


@pytest.mark.parametrize("prefix, suffix", [("a", "b"), ("c", "d"), ("e", "f")])
async def test_temporary_directory(prefix, suffix, tmp_path):
    """Test temporary directory."""
    dir_path = None

    async with tempfile.TemporaryDirectory(
        suffix=suffix, prefix=prefix, dir=tmp_path
    ) as d:
        dir_path = d
        assert os.path.exists(dir_path)
        assert os.path.isdir(dir_path)
        assert d[-1] == suffix
        assert d.split(os.sep)[-1][0] == prefix
    assert not os.path.exists(dir_path)


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="tempfile.TemporaryDirectory.delete added in 3.12",
)
async def test_temporary_directory_delete(tmp_path):
    """Test temporary directory delete parameter."""
    dir_path = None

    async with tempfile.TemporaryDirectory(dir=tmp_path, delete=False) as d:
        dir_path = d
        assert os.path.exists(dir_path)
    assert os.path.exists(dir_path)

    shutil.rmtree(dir_path)

    async with tempfile.TemporaryDirectory(dir=tmp_path, delete=True) as d:
        dir_path = d
        assert os.path.exists(dir_path)
    assert not os.path.exists(dir_path)
