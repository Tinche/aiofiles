"""Test the open functionality."""
from aiofiles.threadpool import open as aioopen, wrap
import pytest
import io
from unittest.mock import patch, MagicMock


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
def test_builtins_monkeypatch():
    mock_open = MagicMock(return_value=io.TextIOBase(io.StringIO()))
    with patch('builtins.open', mock_open):
        yield from aioopen('foo')

        assert mock_open.call_count == 1
