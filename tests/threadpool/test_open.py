"""Test the open functionality."""
from aiofiles.threadpool import open as aioopen, run_threadpool, wrap
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize('mode', ['r', 'rb'])
def test_file_not_found(mode):
    filename = 'non_existent'

    try:
        open(filename, mode=mode)
    except Exception as e:
        expected = e

    assert expected

    try:
        yield from aioopen(filename, mode=mode)
    except Exception as e:
        actual = e

    assert actual

    assert actual.errno == expected.errno
    assert str(actual) == str(expected)


def test_unsupported_wrap():
    """A type error should be raised when wrapping something unsupported."""
    with pytest.raises(TypeError):
        wrap(int)


@pytest.mark.asyncio
def test_threadpool():
    def _sync():
        return "sync return"

    def _wrap(ret, loop=None, executor=None):
        return [ret]

    expected_nowrap = _sync()
    expected_wrap = _wrap(_sync())

    assert expected_nowrap != expected_wrap
    
    actual_nowrap = yield from run_threadpool(_sync)
    assert actual_nowrap == expected_nowrap

    actual_wrap = yield from run_threadpool(_sync, async_wrap=_wrap)
    assert actual_wrap == expected_wrap
