"""Simple tests verifying basic functionality."""
import asyncio
from aiofiles import threadpool
import pytest


@pytest.mark.asyncio
async def test_serve_small_bin_file_sync(event_loop, tmpdir, unused_tcp_port):
    """Fire up a small simple file server, and fetch a file.

    The file is read into memory synchronously, so this test doesn't actually
    test anything except the general test concept.
    """
    # First we'll write a small file.
    filename = "test.bin"
    file_content = b"0123456789"
    file = tmpdir.join(filename)
    file.write_binary(file_content)

    async def serve_file(reader, writer):
        full_filename = str(file)
        with open(full_filename, "rb") as f:
            writer.write(f.read())
        writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, _ = await asyncio.open_connection(host="localhost", port=unused_tcp_port)
    payload = await reader.read()

    assert payload == file_content

    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_serve_small_bin_file(event_loop, tmpdir, unused_tcp_port):
    """Fire up a small simple file server, and fetch a file."""
    # First we'll write a small file.
    filename = "test.bin"
    file_content = b"0123456789"
    file = tmpdir.join(filename)
    file.write_binary(file_content)

    async def serve_file(reader, writer):
        full_filename = str(file)
        f = await threadpool.open(full_filename, mode="rb")
        writer.write((await f.read()))
        await f.close()
        writer.close()

    server = await asyncio.start_server(serve_file, port=unused_tcp_port)

    reader, _ = await asyncio.open_connection(host="localhost", port=unused_tcp_port)
    payload = await reader.read()

    assert payload == file_content

    server.close()
    await server.wait_closed()
