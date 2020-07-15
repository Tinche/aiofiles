"""PEP 0492/Python 3.5+ tests for text files."""
import io
from os.path import dirname, join
from aiofiles.threadpool import open as aioopen
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_simple_iteration(mode):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    async with aioopen(filename, mode=mode) as file:
        # Append mode needs us to seek.
        await file.seek(0)

        counter = 1

        # The old iteration pattern:
        while True:
            line = await file.readline()
            if not line:
                break
            assert line.strip() == 'line ' + str(counter)
            counter += 1

        await file.seek(0)
        counter = 1

        # The new iteration pattern:
        async for line in file:
            assert line.strip() == 'line ' + str(counter)
            counter += 1

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_simple_readlines(mode):
    """Test the readlines functionality."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    with open(filename, mode='r') as f:
        expected = f.readlines()

    async with aioopen(filename, mode=mode) as file:
        # Append mode needs us to seek.
        await file.seek(0)

        actual = await file.readlines()

    assert file.closed

    assert actual == expected


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r+', 'w', 'a'])
async def test_simple_flush(mode, tmpdir):
    """Test flushing to a file."""
    filename = 'file.bin'

    full_file = tmpdir.join(filename)

    if 'r' in mode:
        full_file.ensure()  # Read modes want it to already exist.

    async with aioopen(str(full_file), mode=mode) as file:
        await file.write('0')  # Shouldn't flush.

        assert '' == full_file.read_text(encoding='utf8')

        await file.flush()

        assert '0' == full_file.read_text(encoding='utf8')

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_simple_read(mode):
    """Just read some bytes from a test file."""
    filename = join(dirname(__file__), '..', 'resources', 'test_file1.txt')
    async with aioopen(filename, mode=mode) as file:
        await file.seek(0)  # Needed for the append mode.

        actual = await file.read()

        assert '' == (await file.read())
    assert actual == open(filename, mode='r').read()

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['w', 'a'])
async def test_simple_read_fail(mode, tmpdir):
    """Try reading some bytes and fail."""
    filename = 'bigfile.bin'
    content = '0123456789' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)
    with pytest.raises(ValueError):
        async with aioopen(str(full_file), mode=mode) as file:
            await file.seek(0)  # Needed for the append mode.

            await file.read()

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_staggered_read(mode):
    """Read bytes repeatedly."""
    filename = join(dirname(__file__), '..', 'resources', 'test_file1.txt')
    async with aioopen(filename, mode=mode) as file:
        await file.seek(0)  # Needed for the append mode.

        actual = []
        while True:
            char = await file.read(1)
            if char:
                actual.append(char)
            else:
                break

        assert '' == (await file.read())

    expected = []
    with open(filename, mode='r') as f:
        while True:
            char = f.read(1)
            if char:
                expected.append(char)
            else:
                break

    assert actual == expected

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_simple_seek(mode, tmpdir):
    """Test seeking and then reading."""
    filename = 'bigfile.bin'
    content = '0123456789' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    async with aioopen(str(full_file), mode=mode) as file:
        await file.seek(4)
        assert '4' == (await file.read(1))

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['w', 'r', 'r+', 'w+', 'a', 'a+'])
async def test_simple_close(mode, tmpdir):
    """Open a file, read a byte, and close it."""
    filename = 'bigfile.bin'
    content = '0' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    async with aioopen(str(full_file), mode=mode) as file:
        assert not file.closed
        assert not file._file.closed

    assert file.closed
    assert file._file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r+', 'w', 'a+'])
async def test_simple_truncate(mode, tmpdir):
    """Test truncating files."""
    filename = 'bigfile.bin'
    content = '0123456789' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    async with aioopen(str(full_file), mode=mode) as file:
        # The append modes want us to seek first.
        await file.seek(0)

        if 'w' in mode:
            # We've just erased the entire file.
            await file.write(content)
            await file.flush()
            await file.seek(0)

        await file.truncate()

    assert '' == full_file.read()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['w', 'r+', 'w+', 'a', 'a+'])
async def test_simple_write(mode, tmpdir):
    """Test writing into a file."""
    filename = 'bigfile.bin'
    content = '0' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)

    if 'r' in mode:
        full_file.ensure()  # Read modes want it to already exist.

    async with aioopen(str(full_file), mode=mode) as file:
        bytes_written = await file.write(content)

    assert bytes_written == len(content)
    assert content == full_file.read()
    assert file.closed


@pytest.mark.asyncio
async def test_simple_detach(tmpdir):
    """Test detaching for buffered streams."""
    filename = 'file.bin'

    full_file = tmpdir.join(filename)
    full_file.write('0123456789')

    with pytest.raises(ValueError):  # Close will error out.
        async with aioopen(str(full_file), mode='r') as file:
            raw_file = file.detach()

            assert raw_file

            with pytest.raises(ValueError):
                await file.read()

            assert b'0123456789' == raw_file.read(10)


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_simple_iteration_ctx_mgr(mode):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    async with aioopen(filename, mode=mode) as file:
        assert not file.closed
        await file.seek(0)

        counter = 1

        async for line in file:
            assert line.strip() == 'line ' + str(counter)
            counter += 1

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_name_property(mode):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    async with aioopen(filename, mode=mode) as file:
        assert file.name == filename

    assert file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
async def test_mode_property(mode):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    async with aioopen(filename, mode=mode) as file:
        assert file.mode == mode

    assert file.closed
