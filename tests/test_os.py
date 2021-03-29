"""Tests for asyncio's os module."""
import aiofiles.os
import asyncio
from os.path import join, dirname, exists, isdir
import pytest
import platform


@pytest.fixture
def test_file(tmp_path):
    f = tmp_path / "test_file1.txt"
    f.touch()
    return f


@pytest.mark.anyio
async def test_stat(test_file):
    """Test the stat call."""
    with test_file.open("w") as f:
        f.write(" " * 10)

    stat_res = await aiofiles.os.stat(str(test_file))

    assert stat_res.st_size == 10


@pytest.mark.anyio
async def test_remove(test_file):
    """Test the remove call."""
    with test_file.open("w") as f:
        f.write("Test file for remove call")

    assert test_file.exists()
    await aiofiles.os.remove(test_file)
    assert test_file.exists() is False


@pytest.mark.anyio
async def test_mkdir_and_rmdir(tmp_path):
    """Test the mkdir and rmdir call."""
    directory = tmp_path / "dir"
    await aiofiles.os.mkdir(directory)
    assert directory.is_dir()
    await aiofiles.os.rmdir(directory)
    assert directory.exists() is False


@pytest.mark.anyio
async def test_rename(test_file, tmp_path):
    """Test the rename call."""
    new_filename = tmp_path / "test_file2.txt"
    await aiofiles.os.rename(test_file, new_filename)
    assert test_file.exists() is False and new_filename.exists()
    await aiofiles.os.rename(new_filename, test_file)
    assert test_file.exists() and new_filename.exists() is False


@pytest.mark.skipif(
    "2.4" < platform.release() < "2.6.33",
    reason="sendfile() syscall doesn't allow file->file",
)
@pytest.mark.anyio
async def test_sendfile_file(tmpdir):
    """Test the sendfile functionality, file-to-file."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")
    tmp_filename = tmpdir.join("tmp.bin")

    with open(filename) as f:
        contents = f.read()

    input_file = await aiofiles.open(filename)
    output_file = await aiofiles.open(str(tmp_filename), mode="w+")

    size = (await aiofiles.os.stat(filename)).st_size

    input_fd = input_file.fileno()
    output_fd = output_file.fileno()

    await aiofiles.os.sendfile(output_fd, input_fd, 0, size)

    await output_file.seek(0)

    actual_contents = await output_file.read()
    actual_size = (await aiofiles.os.stat(str(tmp_filename))).st_size

    assert contents == actual_contents
    assert size == actual_size


@pytest.mark.anyio
async def test_sendfile_socket(unused_tcp_port, no_trio_support):
    """Test the sendfile functionality, file-to-socket."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")

    with open(filename, mode="rb") as f:
        contents = f.read()

    async def serve_file(_, writer):
        out_fd = writer.transport.get_extra_info("socket").fileno()
        size = (await aiofiles.os.stat(filename)).st_size
        in_file = await aiofiles.open(filename)
        try:
            in_fd = in_file.fileno()
            await aiofiles.os.sendfile(out_fd, in_fd, 0, size)
        finally:
            await in_file.close()
            await writer.drain()
            writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, writer = await asyncio.open_connection(
        "127.0.0.1", unused_tcp_port
    )
    actual_contents = await reader.read()
    writer.close()

    assert contents == actual_contents
    server.close()

    await server.wait_closed()
