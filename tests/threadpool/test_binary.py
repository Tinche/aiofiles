"""PEP 0492/Python 3.5+ tests for binary files."""
import io
from os.path import dirname, join
from aiofiles.threadpool import open as aioopen
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_iteration(mode, buffering):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")

    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        # Append mode needs us to seek.
        await file.seek(0)

        counter = 1
        # The old iteration pattern:
        while True:
            line = await file.readline()
            if not line:
                break
            assert line.strip() == b"line " + str(counter).encode()
            counter += 1

        counter = 1
        await file.seek(0)
        # The new iteration pattern:
        async for line in file:
            assert line.strip() == b"line " + str(counter).encode()
            counter += 1

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_readlines(mode, buffering):
    """Test the readlines functionality."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")

    with open(filename, mode="rb") as f:
        expected = f.readlines()

    async with aioopen(str(filename), mode=mode) as file:
        # Append mode needs us to seek.
        await file.seek(0)

        actual = await file.readlines()

    assert actual == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb+", "wb", "ab"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_flush(mode, buffering, tmpdir):
    """Test flushing to a file."""
    filename = "file.bin"

    full_file = tmpdir.join(filename)

    if "r" in mode:
        full_file.ensure()  # Read modes want it to already exist.

    async with aioopen(str(full_file), mode=mode, buffering=buffering) as file:
        await file.write(b"0")  # Shouldn't flush.

        if buffering == -1:
            assert b"" == full_file.read_binary()
        else:
            assert b"0" == full_file.read_binary()

        await file.flush()

        assert b"0" == full_file.read_binary()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb+", "wb+", "ab+"])
async def test_simple_peek(mode, tmpdir):
    """Test flushing to a file."""
    filename = "file.bin"

    full_file = tmpdir.join(filename)
    full_file.write_binary(b"0123456789")

    async with aioopen(str(full_file), mode=mode) as file:
        if "a" in mode:
            await file.seek(0)  # Rewind for append modes.

        peeked = await file.peek(1)

        # Technically it's OK for the peek to return less bytes than requested.
        if peeked:
            assert peeked.startswith(b"0")

            read = await file.read(1)

            assert peeked.startswith(read)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_read(mode, buffering):
    """Just read some bytes from a test file."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")
    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        await file.seek(0)  # Needed for the append mode.

        actual = await file.read()

        assert b"" == (await file.read())
    assert actual == open(filename, mode="rb").read()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_staggered_read(mode, buffering):
    """Read bytes repeatedly."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")
    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        await file.seek(0)  # Needed for the append mode.

        actual = []
        while True:
            byte = await file.read(1)
            if byte:
                actual.append(byte)
            else:
                break

        assert b"" == (await file.read())

        expected = []
        with open(filename, mode="rb") as f:
            while True:
                byte = f.read(1)
                if byte:
                    expected.append(byte)
                else:
                    break

    assert actual == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_seek(mode, buffering, tmpdir):
    """Test seeking and then reading."""
    filename = "bigfile.bin"
    content = b"0123456789" * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write_binary(content)

    async with aioopen(str(full_file), mode=mode, buffering=buffering) as file:
        await file.seek(4)

        assert b"4" == (await file.read(1))


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["wb", "rb", "rb+", "wb+", "ab", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_close_ctx_mgr_iter(mode, buffering, tmpdir):
    """Open a file, read a byte, and close it."""
    filename = "bigfile.bin"
    content = b"0" * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write_binary(content)

    async with aioopen(str(full_file), mode=mode, buffering=buffering) as file:
        assert not file.closed
        assert not file._file.closed

    assert file.closed
    assert file._file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["wb", "rb", "rb+", "wb+", "ab", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_close_ctx_mgr(mode, buffering, tmpdir):
    """Open a file, read a byte, and close it."""
    filename = "bigfile.bin"
    content = b"0" * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write_binary(content)

    file = await aioopen(str(full_file), mode=mode, buffering=buffering)
    assert not file.closed
    assert not file._file.closed

    await file.close()

    assert file.closed
    assert file._file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_readinto(mode, buffering):
    """Test the readinto functionality."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")
    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        await file.seek(0)  # Needed for the append mode.

        array = bytearray(4)
        bytes_read = await file.readinto(array)

        assert bytes_read == 4
        assert array == open(filename, mode="rb").read(4)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb+", "wb", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_truncate(mode, buffering, tmpdir):
    """Test truncating files."""
    filename = "bigfile.bin"
    content = b"0123456789" * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write_binary(content)

    async with aioopen(str(full_file), mode=mode, buffering=buffering) as file:
        # The append modes want us to seek first.
        await file.seek(0)

        if "w" in mode:
            # We've just erased the entire file.
            await file.write(content)
            await file.flush()
            await file.seek(0)

        await file.truncate()

    assert b"" == full_file.read_binary()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["wb", "rb+", "wb+", "ab", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_simple_write(mode, buffering, tmpdir):
    """Test writing into a file."""
    filename = "bigfile.bin"
    content = b"0" * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)

    if "r" in mode:
        full_file.ensure()  # Read modes want it to already exist.

    async with aioopen(str(full_file), mode=mode, buffering=buffering) as file:
        bytes_written = await file.write(content)

    assert bytes_written == len(content)
    assert content == full_file.read_binary()


@pytest.mark.asyncio
async def test_simple_detach(tmpdir):
    """Test detaching for buffered streams."""
    filename = "file.bin"

    full_file = tmpdir.join(filename)
    full_file.write_binary(b"0123456789")

    with pytest.raises(ValueError):
        async with aioopen(str(full_file), mode="rb") as file:
            raw_file = file.detach()

            assert raw_file

            with pytest.raises(ValueError):
                await file.read()

    assert b"0123456789" == raw_file.read(10)


@pytest.mark.asyncio
async def test_simple_readall(tmpdir):
    """Test the readall function by reading a large file in.

    Only RawIOBase supports readall().
    """
    filename = "bigfile.bin"
    content = b"0" * 4 * io.DEFAULT_BUFFER_SIZE  # Hopefully several reads.

    sync_file = tmpdir.join(filename)
    sync_file.write_binary(content)

    file = await aioopen(str(sync_file), mode="rb", buffering=0)

    actual = await file.readall()

    assert actual == content

    await file.close()
    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_name_property(mode, buffering):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")

    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        assert file.name == filename

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["rb", "rb+", "ab+"])
@pytest.mark.parametrize("buffering", [-1, 0])
async def test_mode_property(mode, buffering):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), "..", "resources", "multiline_file.txt")

    async with aioopen(filename, mode=mode, buffering=buffering) as file:
        assert file.mode == mode

    assert file.closed
