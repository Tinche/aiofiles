import asyncio
import io
import os
import platform
import shutil
import sys
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


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="tempfile.TemporaryDirectory.ignore_cleanup_errors added in 3.10",
)
@pytest.mark.parametrize("ignore_cleanup_errors", [False, True])
async def test_temporary_directory_ignore_cleanup_errors(
    tmp_path, monkeypatch, ignore_cleanup_errors
):
    """Test cleanup failures respect the requested suppression setting."""

    def rmtree(path, ignore_errors=False):
        if not ignore_errors:
            raise PermissionError
        os.rmdir(path)

    monkeypatch.setattr(
        tempfile.syncTemporaryDirectory, "_rmtree", staticmethod(rmtree)
    )
    manager = tempfile.TemporaryDirectory(
        dir=tmp_path, ignore_cleanup_errors=ignore_cleanup_errors
    )
    if ignore_cleanup_errors:
        async with manager as dir_path:
            assert os.path.isdir(dir_path)
        assert not os.path.exists(dir_path)
    else:
        with pytest.raises(PermissionError):
            async with manager as dir_path:
                assert os.path.isdir(dir_path)
        os.rmdir(dir_path)


@pytest.mark.skipif(
    not (3, 10) <= sys.version_info < (3, 12),
    reason="Test the Python 3.10/3.11 positional loop and executor signature",
)
async def test_temporary_directory_cleanup_positional_args(tmp_path):
    """Keep the existing positional loop and executor arguments."""
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        async with tempfile.TemporaryDirectory(
            None, None, tmp_path, loop, executor, ignore_cleanup_errors=True
        ) as dir_path:
            assert os.path.isdir(dir_path)
        assert not os.path.exists(dir_path)
