"""Tests for text files."""
import io
from os.path import dirname, join
from aiofiles.threadpool import open as aioopen
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
def test_simple_iteration(mode):
    """Test iterating over lines from a file."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    file = yield from aioopen(filename, mode=mode)

    # Append mode needs us to seek.
    yield from file.seek(0)

    counter = 1

    # The recommended iteration pattern:
    while True:
        line = yield from file.readline()
        if not line:
            break
        assert line.strip() == 'line ' + str(counter)
        counter += 1

    yield from file.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
def test_simple_readlines(mode):
    """Test the readlines functionality."""
    filename = join(dirname(__file__), '..', 'resources', 'multiline_file.txt')

    with open(filename, mode='r') as f:
        expected = f.readlines()

    file = yield from aioopen(filename, mode=mode)

    # Append mode needs us to seek.
    yield from file.seek(0)

    actual = yield from file.readlines()

    yield from file.close()

    assert actual == expected


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r+', 'w', 'a'])
def test_simple_flush(mode, tmpdir):
    """Test flushing to a file."""
    filename = 'file.bin'

    full_file = tmpdir.join(filename)

    if 'r' in mode:
        full_file.ensure()  # Read modes want it to already exist.

    file = yield from aioopen(str(full_file), mode=mode)

    yield from file.write('0')  # Shouldn't flush.

    assert '' == full_file.read_text(encoding='utf8')

    yield from file.flush()

    assert '0' == full_file.read_text(encoding='utf8')

    yield from file.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
def test_simple_read(mode):
    """Just read some bytes from a test file."""
    filename = join(dirname(__file__), '..', 'resources', 'test_file1.txt')
    file = yield from aioopen(filename, mode=mode)

    yield from file.seek(0)  # Needed for the append mode.

    actual = yield from file.read()

    assert '' == (yield from file.read())
    assert actual == open(filename, mode='r').read()

    yield from file.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
def test_staggered_read(mode):
    """Read bytes repeatedly."""
    filename = join(dirname(__file__), '..', 'resources', 'test_file1.txt')
    file = yield from aioopen(filename, mode=mode)

    yield from file.seek(0)  # Needed for the append mode.

    actual = []
    while True:
        char = yield from file.read(1)
        if char:
            actual.append(char)
        else:
            break

    assert '' == (yield from file.read())

    expected = []
    with open(filename, mode='r') as f:
        while True:
            char = f.read(1)
            if char:
                expected.append(char)
            else:
                break

    assert actual == expected

    yield from file.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'r+', 'a+'])
def test_simple_seek(mode, tmpdir):
    """Test seeking and then reading."""
    filename = 'bigfile.bin'
    content = '0123456789' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    file = yield from aioopen(str(full_file), mode=mode)

    yield from file.seek(4)

    assert '4' == (yield from file.read(1))

    yield from file.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['w', 'r', 'r+', 'w+', 'a', 'a+'])
def test_simple_close(mode, tmpdir):
    """Open a file, read a byte, and close it."""
    filename = 'bigfile.bin'
    content = '0' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    file = yield from aioopen(str(full_file), mode=mode)

    assert not file.closed
    assert not file._file.closed

    yield from file.close()

    assert file.closed
    assert file._file.closed


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r+', 'w', 'a+'])
def test_simple_truncate(mode, tmpdir):
    """Test truncating files."""
    filename = 'bigfile.bin'
    content = '0123456789' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)
    full_file.write(content)

    file = yield from aioopen(str(full_file), mode=mode)

    # The append modes want us to seek first.
    yield from file.seek(0)

    if 'w' in mode:
        # We've just erased the entire file.
        yield from file.write(content)
        yield from file.flush()
        yield from file.seek(0)

    yield from file.truncate()

    yield from file.close()

    assert '' == full_file.read()


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['w', 'r+', 'w+', 'a', 'a+'])
def test_simple_write(mode, tmpdir):
    """Test writing into a file."""
    filename = 'bigfile.bin'
    content = '0' * 4 * io.DEFAULT_BUFFER_SIZE

    full_file = tmpdir.join(filename)

    if 'r' in mode:
        full_file.ensure()  # Read modes want it to already exist.

    file = yield from aioopen(str(full_file), mode=mode)
    bytes_written = yield from file.write(content)
    yield from file.close()

    assert bytes_written == len(content)
    assert content == full_file.read()


@pytest.mark.asyncio
def test_simple_detach(tmpdir):
    """Test detaching for buffered streams."""
    filename = 'file.bin'

    full_file = tmpdir.join(filename)
    full_file.write('0123456789')

    file = yield from aioopen(str(full_file), mode='r')

    raw_file = file.detach()

    assert raw_file

    with pytest.raises(ValueError):
        yield from file.read()

    assert b'0123456789' == raw_file.read(10)
