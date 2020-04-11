"""Test the open functionality."""
from aiofiles.threadpool import open as aioopen, wrap
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["r", "rb"])
async def test_file_not_found(mode):
    filename = "non_existent"

    try:
        open(filename, mode=mode)
    except Exception as e:
        expected = e

    assert expected

    try:
        await aioopen(filename, mode=mode)
    except Exception as e:
        actual = e

    assert actual

    assert actual.errno == expected.errno
    assert str(actual) == str(expected)


def test_unsupported_wrap():
    """A type error should be raised when wrapping something unsupported."""
    with pytest.raises(TypeError):
        wrap(int)
