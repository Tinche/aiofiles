"""Test concurrency properties of the implementation."""
from os.path import dirname
from os.path import join
import time
import asyncio
import pytest

import aiofiles.threadpool


@asyncio.coroutine
@pytest.mark.asyncio
def test_slow_file(monkeypatch, unused_tcp_port):
    """Monkey patch open and file.read(), and assert the loop still works."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    with open(filename, mode='rb') as f:
        contents = f.read()

    def new_open(*args, **kwargs):
        time.sleep(1)
        return open(*args, **kwargs)

    monkeypatch.setattr(aiofiles.threadpool, 'sync_open', value=new_open)

    @asyncio.coroutine
    def serve_file(_, writer):
        file = yield from aiofiles.threadpool.open(filename, mode='rb')
        try:
            while True:
                data = yield from file.read(1)
                if not data:
                    break
                writer.write(data)
                yield from writer.drain()
            yield from writer.drain()
        finally:
            writer.close()
            yield from file.close()

    @asyncio.coroutine
    def return_one(_, writer):
        writer.write(b'1')
        yield from writer.drain()
        writer.close()

    counter = 0

    @asyncio.coroutine
    def spam_client():
        nonlocal counter
        while True:
            r, w = yield from asyncio.open_connection('127.0.0.1', port=30001)
            assert (yield from r.read()) == b'1'
            counter += 1
            w.close()
            yield from asyncio.sleep(0.01)

    file_server = yield from asyncio.start_server(serve_file,
                                                  port=unused_tcp_port)
    spam_server = yield from asyncio.start_server(return_one, port=30001)

    spam_task = asyncio.ensure_future(spam_client())

    reader, writer = yield from asyncio.open_connection('127.0.0.1',
                                                        port=unused_tcp_port)

    actual_contents = yield from reader.read()
    writer.close()

    yield from asyncio.sleep(0)

    file_server.close()
    spam_server.close()

    yield from file_server.wait_closed()
    yield from spam_server.wait_closed()

    spam_task.cancel()

    assert actual_contents == contents
    assert counter > 40
