"""Tests for asyncio's os module."""
import aiofiles.os
import asyncio
from os.path import join, dirname, exists, isdir
import pytest
import platform


@pytest.mark.asyncio
async def test_stat():
    """Test the stat call."""
    filename = join(dirname(__file__), "resources", "test_file1.txt")

    stat_res = await aiofiles.os.stat(filename)

    assert stat_res.st_size == 10


@pytest.mark.asyncio
async def test_remove():
    """Test the remove call."""
    filename = join(dirname(__file__), "resources", "test_file2.txt")
    with open(filename, "w") as f:
        f.write("Test file for remove call")

    assert exists(filename)
    await aiofiles.os.remove(filename)
    assert exists(filename) is False


@pytest.mark.asyncio
async def test_mkdir_and_rmdir():
    """Test the mkdir and rmdir call."""
    directory = join(dirname(__file__), "resources", "test_dir")
    await aiofiles.os.mkdir(directory)
    assert isdir(directory)
    await aiofiles.os.rmdir(directory)
    assert exists(directory) is False


@pytest.mark.asyncio
async def test_rename():
    """Test the rename call."""
    old_filename = join(dirname(__file__), "resources", "test_file1.txt")
    new_filename = join(dirname(__file__), "resources", "test_file2.txt")
    await aiofiles.os.rename(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    await aiofiles.os.rename(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False


@pytest.mark.skipif(
    "2.4" < platform.release() < "2.6.33",
    reason="sendfile() syscall doesn't allow file->file",
)
@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_sendfile_socket(unused_tcp_port):
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
