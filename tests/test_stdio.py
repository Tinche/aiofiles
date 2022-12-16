import sys
import pytest
from aiofiles import stdin, stdout, stderr, stdin_bytes, stdout_bytes, stderr_bytes


@pytest.mark.asyncio
async def test_stdio(capsys):
    await stdout.write("hello")
    await stderr.write("world")
    out, err = capsys.readouterr()
    assert out == "hello"
    assert err == "world"
    with pytest.raises(OSError):
        await stdin.read()


@pytest.mark.asyncio
async def test_stdio_bytes(capsysbinary):
    await stdout_bytes.write(b"hello")
    await stderr_bytes.write(b"world")
    out, err = capsysbinary.readouterr()
    assert out == b"hello"
    assert err == b"world"
    with pytest.raises(OSError):
        await stdin_bytes.read()
