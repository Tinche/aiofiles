import io
import sys
import threading

import pytest

from aiofiles import stderr, stderr_bytes, stdin, stdin_bytes, stdout, stdout_bytes


async def test_stdio(capsys):
    await stdout.write("hello")
    await stderr.write("world")
    out, err = capsys.readouterr()
    assert out == "hello"
    assert err == "world"
    with pytest.raises(OSError):
        await stdin.read()


async def test_stdio_bytes(capsysbinary):
    await stdout_bytes.write(b"hello")
    await stderr_bytes.write(b"world")
    out, err = capsysbinary.readouterr()
    assert out == b"hello"
    assert err == b"world"
    with pytest.raises(OSError):
        await stdin_bytes.read()


@pytest.mark.parametrize("arguments", [(), (0,), (1,), (1024,)])
async def test_stdin_bytes_peek(monkeypatch, arguments):
    data = b"first line\nsecond line\n"
    peek_threads = []

    class RecordingReader(io.BufferedReader):
        def peek(self, size=0):
            peek_threads.append(threading.get_ident())
            return super().peek(size)

    with io.TextIOWrapper(RecordingReader(io.BytesIO(data))) as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdin", stream)
            expected = stream.buffer.peek(*arguments)
            assert await stdin_bytes.peek(*arguments) == expected
            assert peek_threads[-1] != threading.get_ident()
            assert await stdin_bytes.tell() == 0
            assert await stdin_bytes.read() == data


async def test_stdin_bytes_peek_follows_replaced_stdin(monkeypatch):
    for data in (b"first", b"replacement"):
        with io.TextIOWrapper(io.BufferedReader(io.BytesIO(data))) as stream:
            with monkeypatch.context() as patch:
                patch.setattr(sys, "stdin", stream)
                assert await stdin_bytes.peek() == data
                assert await stdin_bytes.read() == data
