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
