"""Tests for asyncio's os module."""
import aiofiles.os
import asyncio
from os.path import join, dirname, exists, isdir
import pytest
import platform
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning,
                        message="\"@coroutine\" decorator is deprecated")


@asyncio.coroutine
@pytest.mark.asyncio
def test_stat():
    """Test the stat call."""
    filename = join(dirname(__file__), 'resources', 'test_file1.txt')

    stat_res = yield from aiofiles.os.stat(filename)

    assert stat_res.st_size == 10


@asyncio.coroutine
@pytest.mark.asyncio
def test_remove():
    """Test the remove call."""
    filename = join(dirname(__file__), 'resources', 'test_file2.txt')
    with open(filename, 'w') as f:
        f.write('Test file for remove call')

    assert exists(filename)
    yield from aiofiles.os.remove(filename)
    assert exists(filename) is False


@asyncio.coroutine
@pytest.mark.asyncio
def test_mkdir_and_rmdir():
    """Test the mkdir and rmdir call."""
    directory = join(dirname(__file__), 'resources', 'test_dir')
    yield from aiofiles.os.mkdir(directory)
    assert isdir(directory)
    yield from aiofiles.os.rmdir(directory)
    assert exists(directory) is False


@asyncio.coroutine
@pytest.mark.asyncio
def test_rename():
    """Test the rename call."""
    old_filename = join(dirname(__file__), 'resources', 'test_file1.txt')
    new_filename = join(dirname(__file__), 'resources', 'test_file2.txt')
    yield from aiofiles.os.rename(old_filename, new_filename)
    assert exists(old_filename) is False and exists(new_filename)
    yield from aiofiles.os.rename(new_filename, old_filename)
    assert exists(old_filename) and exists(new_filename) is False


@asyncio.coroutine
@pytest.mark.skipif('2.4' < platform.release() < '2.6.33',
                    reason = "sendfile() syscall doesn't allow file->file")
@pytest.mark.asyncio
def test_sendfile_file(tmpdir):
    """Test the sendfile functionality, file-to-file."""
    filename = join(dirname(__file__), 'resources', 'test_file1.txt')
    tmp_filename = tmpdir.join('tmp.bin')

    with open(filename) as f:
        contents = f.read()

    input_file = yield from aiofiles.open(filename)
    output_file = yield from aiofiles.open(str(tmp_filename), mode='w+')

    size = (yield from aiofiles.os.stat(filename)).st_size

    input_fd = input_file.fileno()
    output_fd = output_file.fileno()

    yield from aiofiles.os.sendfile(output_fd, input_fd, 0, size)

    yield from output_file.seek(0)

    actual_contents = yield from output_file.read()
    actual_size = (yield from aiofiles.os.stat(str(tmp_filename))).st_size

    assert contents == actual_contents
    assert size == actual_size


@asyncio.coroutine
@pytest.mark.asyncio
def test_sendfile_socket(unused_tcp_port):
    """Test the sendfile functionality, file-to-socket."""
    filename = join(dirname(__file__), 'resources', 'test_file1.txt')

    with open(filename, mode='rb') as f:
        contents = f.read()

    @asyncio.coroutine
    def serve_file(_, writer):
        out_fd = writer.transport.get_extra_info('socket').fileno()
        size = (yield from aiofiles.os.stat(filename)).st_size
        in_file = yield from aiofiles.open(filename)
        try:
            in_fd = in_file.fileno()
            yield from aiofiles.os.sendfile(out_fd, in_fd, 0, size)
        finally:
            yield from in_file.close()
            yield from writer.drain()
            writer.close()

    server = yield from asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, writer = yield from asyncio.open_connection('127.0.0.1',
                                                        unused_tcp_port)
    actual_contents = yield from reader.read()
    writer.close()

    assert contents == actual_contents
    server.close()

    yield from server.wait_closed()

